from PySide2 import QtWidgets, QtGui, QtCore
from maya import cmds
import maya.OpenMaya as om
import maya.api.OpenMaya as om2  # match api2

from ncachemanager.ui.qtutils import get_icon
from ncachemanager.manager import filter_connected_cacheversions
from ncachemanager.versioning import list_available_cacheversions
from ncachemanager.cache import DYNAMIC_NODES


RANGE_CACHED_COLOR = "#44aa22"
RANGE_NOT_CACHED_COLOR = "#333333"
CURRENT_TIME_COLOR = "#CC5533"
FULL_UPDATE_REQUIRED_EVENTS = (
    om.MSceneMessage.kAfterNew,
    om.MSceneMessage.kAfterImport,
    om.MSceneMessage.kAfterOpen,
    om.MSceneMessage.kAfterRemoveReference,
    om.MSceneMessage.kAfterUnloadReference,
    om.MSceneMessage.kAfterCreateReference)
UPDATE_LAYOUT_EVENTS = "playbackRangeChanged", "timeChanged"
OM_DYNAMIC_NODES = om.MFn.kNCloth, om.MFn.kHairSystem


class DynamicNodesTableWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(DynamicNodesTableWidget, self).__init__(parent)
        self._callbacks = []
        self._jobs = []
        self.script_jobs = []
        self.versions = []
        self.table_model = DynamicNodeTableModel()
        self.table_view = DynamicNodeTableView()
        self.table_view.set_model(self.table_model)
        self.table_color_square = ColorSquareDelegate(self.table_view)
        self.table_switcher = SwitcherDelegate(self.table_view)
        self.table_cached_range = CachedRangeDelegate(self.table_view)
        self.table_view.set_color_delegate(self.table_color_square)
        self.table_view.set_switcher_delegate(self.table_switcher)
        self.table_view.set_cacherange_delegate(self.table_cached_range)
        self.table_model.set_nodes(list_dynamic_nodes())

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.table_view)

    @property
    def selected_nodes(self):
        if self.table_model is None:
            return
        indexes = self.table_view.selectionModel().selectedIndexes()
        if not indexes:
            return None
        indexes = [i for i in indexes if i.column() == 0]
        return [self._model.data(i, QtCore.Qt.UserRole) for i in indexes]

    def set_workspace(self, workspace):
        cacheversions = list_available_cacheversions(workspace)
        self.table_model.set_cacheversions(cacheversions)

    def register_callbacks(self):
        for nodetype in DYNAMIC_NODES:
            function = self._remove_node_callback
            cb = om.MDGMessage.addNodeRemovedCallback(function, nodetype)
            self._callbacks.append(cb)

            function = self._created_node_callback
            cb = om.MDGMessage.addNodeAddedCallback(function, nodetype)
            self._callbacks.append(cb)

        function = self._full_update_callback
        for event in FULL_UPDATE_REQUIRED_EVENTS:
            cb = om.MSceneMessage.addCallback(event, function)
            self._callbacks.append(cb)

        function = self._update_layout
        cb = om.MNodeMessage.addNameChangedCallback(om.MObject(), function)
        self._callbacks.append(cb)
        for event in UPDATE_LAYOUT_EVENTS:
            job = cmds.scriptJob(event=[event, function])
            self._jobs.append(job)

    def unregister_callbacks(self):
        for callback in self._callbacks:
            om.MMessage.removeCallback(callback)
        self._callbacks = []
        for job in self._jobs:
            cmds.scriptJob(kill=job, force=True)

    def _remove_node_callback(self, mobject, *unused_callbacks_args):
        if mobject.apiType() not in OM_DYNAMIC_NODES:
            return
        node = om.MFnDagNode(mobject).name()
        dynamic_nodes = [n for n in self.table_model.nodes if n.name == node]
        if not dynamic_nodes:
            return
        for dynamic_node in dynamic_nodes:
            self.table_model.remove_node(dynamic_node)

    def _created_node_callback(self, mobject, *unused_callbacks_args):
        if mobject.apiType() not in OM_DYNAMIC_NODES:
            return
        dynamic_node = create_dynamic_node(om.MFnDagNode(mobject).name())
        self.table_model.insert_node(dynamic_node)

    def _full_update_callback(self, *unused_callbacks_args):
        self.table_model.set_nodes(list_dynamic_nodes())

    def _update_layout(self, *unused_callbacks_args):
        self.table_model.layoutChanged.emit()

    def show(self):
        super(DynamicNodesTableWidget, self).show()
        self.register_callbacks()

    def closeEvent(self, event):
        self.unregister_callbacks()
        return super(DynamicNodesTableWidget, self).closeEvent(event)


class DynamicNode(object):
    """this object is a model for the DynamicNodeTableView and his delegate.
    It's linked to a maya node and contain method and properties needed for
    the table view"""
    ENABLE_ATTRIBUTE = None
    TYPE = None
    ICONS = {'on': None, 'off': None}

    def __init__(self, nodename):
        if cmds.nodeType(nodename) != self.TYPE:
            raise ValueError('wrong node type, {} excepted'.format(self.TYPE))
        self._dagnode = om2.MFnDagNode(
            om2.MSelectionList().add(nodename).getDependNode(0))
        self._color = None

    @property
    def name(self):
        return self._dagnode.name()

    @property
    def parent(self):
        return cmds.listRelatives(self.name, parent=True)

    @property
    def is_cached(self):
        return bool(cmds.listConnections(self.name + '.playFromCache'))

    @property
    def cache_nodetype(self):
        if not self.is_cached:
            return None
        connections = cmds.listConnections(self.name + '.playFromCache')
        if not connections:
            return None
        return cmds.nodeType(connections[0])

    @property
    def enable(self):
        return cmds.getAttr(self.name + '.' + self.ENABLE_ATTRIBUTE)

    def switch(self):
        value = not self.enable
        cmds.setAttr(self.name + '.' + self.ENABLE_ATTRIBUTE, value)


class HairNode(DynamicNode):
    ENABLE_ATTRIBUTE = 'simulationMethod'
    TYPE = "hairSystem"
    ICONS = {'on': 'hairsystem.png', 'off': 'hairsystem_off.png'}

    @property
    def color(self):
        return cmds.getAttr(self.name + '.displayColor')[0]

    def set_color(self, red, green, blue):
        cmds.setAttr(self.name + '.displayColor', red, green, blue)


class ClothNode(DynamicNode):
    ENABLE_ATTRIBUTE = 'isDynamic'
    TYPE = "nCloth"
    ICONS = {'on': 'ncloth.png', 'off': 'ncloth_off.png'}

    def __init__(self, nodename):
        super(ClothNode, self).__init__(nodename)
        self._color = None

    @property
    def color(self):
        if self._color is None:
            self._color = get_clothnode_color(self.name)
        return self._color

    def set_color(self, red, green, blue):
        set_clothnode_color(self.name, red, green, blue)
        self._color = red, green, blue


class DynamicNodeTableModel(QtCore.QAbstractTableModel):
    HEADERS = "", "", "Node", "Cache", "Range Cached", ""

    def __init__(self, parent=None):
        super(DynamicNodeTableModel, self).__init__(parent)
        self.nodes = []
        self.cacheversions = []

    def columnCount(self, _):
        return len(self.HEADERS)

    def rowCount(self, _):
        return len(self.nodes)

    def set_nodes(self, nodes):
        self.layoutAboutToBeChanged.emit()
        self.nodes = nodes
        self.layoutChanged.emit()

    def insert_node(self, node):
        self.layoutAboutToBeChanged.emit()
        self.nodes.append(node)
        self.nodes = sorted(self.nodes, key=lambda x: x.name)
        self.layoutChanged.emit()

    def set_cacheversions(self, cacheversions):
        self.layoutAboutToBeChanged.emit()
        self.cacheversions = cacheversions
        self.layoutChanged.emit()

    def remove_node(self, node):
        self.layoutAboutToBeChanged.emit()
        self.nodes.remove(node)
        self.layoutChanged.emit()

    def sort(self, column, order):
        if column != 2:
            return
        reverse_ = order == QtCore.Qt.AscendingOrder
        self.layoutAboutToBeChanged.emit()
        self.nodes = sorted(self.nodes, key=lambda x: x.name, reverse=reverse_)
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]

    def data(self, index, role):
        if not index.isValid():
            return
        row, column = index.row(), index.column()
        node = self.nodes[row]
        if role == QtCore.Qt.DisplayRole:
            if column == 2:
                return node.parent
            elif column == 3:
                cvs = filter_connected_cacheversions(
                    node.name, self.cacheversions)
                return ", ".join([cv.name for cv in cvs])
        elif role == QtCore.Qt.UserRole:
            return node


class DynamicNodeTableView(QtWidgets.QTableView):

    def __init__(self, parent=None):
        super(DynamicNodeTableView, self).__init__(parent)
        self.configure()
        self._selection_model = None
        self._model = None
        self.color_delegate = None
        self.switcher_delegate = None
        self.cacherange_delegate = None

    def configure(self):
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setSortingEnabled(True)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(mode)
        self.horizontalHeader().setSectionResizeMode(mode)
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    def mouseReleaseEvent(self, event):
        # this is a workaround because for a reason that I don't understand
        # the function createEditor doesn't triggered properly ...
        # so i force it here (but it's an horrible Fix)
        index = self.indexAt(event.pos())
        if index.column() == 0:
            self.color_delegate.createEditor(None, None, index)
        if index.column() == 1:
            self.switcher_delegate.createEditor(None, None, index)
        self._model.layoutChanged.emit()
        return super(DynamicNodeTableView, self).mouseReleaseEvent(event)

    def set_model(self, model):
        self.setModel(model)
        self._model = model
        self._selection_model = self.selectionModel()

    def set_color_delegate(self, item_delegate):
        self.color_delegate = item_delegate
        self.setItemDelegateForColumn(0, item_delegate)

    def set_switcher_delegate(self, item_delegate):
        self.switcher_delegate = item_delegate
        self.setItemDelegateForColumn(1, item_delegate)

    def set_cacherange_delegate(self, item_delegate):
        self.cacherange_delegate = item_delegate
        self.setItemDelegateForColumn(4, item_delegate)


class ColorSquareDelegate(QtWidgets.QStyledItemDelegate):
    """ this delegate is a color square. It read the color from a DynamicNode
    and is able to change it."""

    def __init__(self, table):
        super(ColorSquareDelegate, self).__init__(table)
        self._model = table.model()

    def paint(self, painter, option, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        left = option.rect.center().x() - 7
        top = option.rect.center().y() - 7
        rect = QtCore.QRect(left, top, 14, 14)
        pen = QtGui.QPen(QtGui.QColor("black"))
        pen.setWidth(2)
        color = QtGui.QColor(*[c * 255 for c in dynamic_node.color])
        brush = QtGui.QBrush(color)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(rect)

    def createEditor(self, _, __, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        red, green, blue = map(float, cmds.colorEditor().split()[:3])
        if cmds.colorEditor(query=True, result=True) is False:
            return
        dynamic_node.set_color(red, green, blue)
        return

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def sizeHint(self, _, __):
        return QtCore.QSize(22, 22)


class SwitcherDelegate(QtWidgets.QStyledItemDelegate):
    """ this delegate is an icon 'on' or 'off' defined by the dynamic node
    given by the table model. It switch the dynamic node state en clic
    """
    ICONSIZE = 24, 24

    def __init__(self, table):
        super(SwitcherDelegate, self).__init__(table)
        self._model = table.model()
        self.icons = None

    def createEditor(self, _, __, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        dynamic_node.switch()
        return

    def paint(self, painter, option, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        if self.icons is None:
            self.icons = (
                get_icon(dynamic_node.ICONS['off']),
                get_icon(dynamic_node.ICONS['on']))

        icon = self.icons[bool(dynamic_node.enable)]
        pixmap = icon.pixmap(24, 24).scaled(
            QtCore.QSize(*self.ICONSIZE),
            transformMode=QtCore.Qt.SmoothTransformation)
        left = option.rect.center().x() - 8
        top = option.rect.center().y() - 8
        rect = QtCore.QRect(left, top, 16, 16)
        painter.drawPixmap(rect, pixmap)

    def sizeHint(self, *args):
        return QtCore.QSize(24, 24)


class CachedRangeDelegate(QtWidgets.QStyledItemDelegate):
    """ this is an informative delegate (not interaction possible).
    It draws a bar who represents the current maya timeline. The green part
    represent the cached frames. The red line is the current time.
    """

    def __init__(self, table):
        super(CachedRangeDelegate, self).__init__(table)
        self._model = table.model()

    def paint(self, painter, option, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        node = dynamic_node.name
        cacheversions = self._model.cacheversions
        cacheversions = filter_connected_cacheversions(node, cacheversions)
        if not cacheversions:
            return
        cachedstart, cachedend = cacheversions[0].infos["nodes"][node]["range"]
        scenestart = cmds.playbackOptions(query=True, minTime=True)
        sceneend = cmds.playbackOptions(query=True, maxTime=True)
        invalue = percent(cachedstart, scenestart, sceneend)
        outvalue = percent(cachedend, scenestart, sceneend)
        bg_rect = QtCore.QRect(
            option.rect.left() + 8,
            option.rect.top() + 10,
            option.rect.width() - 16,
            option.rect.height() - 20)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
        brush = QtGui.QBrush(QtGui.QColor(RANGE_NOT_CACHED_COLOR))
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(bg_rect)

        if outvalue != invalue:
            left = from_percent(invalue, bg_rect.left(), bg_rect.right())
            right = from_percent(outvalue, bg_rect.left(), bg_rect.right())
            top = bg_rect.top()
            height = bg_rect.height()
            cached_rect = QtCore.QRect(left, top, right, height)
            cached_rect.setRight(right)
            brush = QtGui.QBrush(QtGui.QColor(RANGE_CACHED_COLOR))
            painter.setBrush(brush)
            painter.drawRect(cached_rect)

        time = cmds.currentTime(query=True)
        left = percent(time, scenestart, sceneend)
        left = from_percent(left, bg_rect.left(), bg_rect.right())
        pen = QtGui.QPen(QtGui.QColor(CURRENT_TIME_COLOR))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(left, bg_rect.top(), left, bg_rect.bottom())

    def sizeHint(self, _, __):
        return QtCore.QSize(60, 22)


def percent(value, rangein=0, rangeout=100):
    if value < rangein:
        return 0
    elif value > rangeout:
        return 100
    value = value - rangein
    rangeout = rangeout - rangein
    return (value / rangeout) * 100


def from_percent(value, rangein=0, rangeout=100):
    rangeout -= rangein
    value = (value / 100) * rangeout
    return value + rangein


def list_dynamic_nodes():
    return [
        create_dynamic_node(n) for n in cmds.ls(type=('hairSystem', 'nCloth'))]


def create_dynamic_node(nodename):
    if cmds.nodeType(nodename) == 'hairSystem':
        return HairNode(nodename)
    if cmds.nodeType(nodename) == 'nCloth':
        return ClothNode(nodename)
    cmds.warning(nodename + ' is not a dynamic node')


def get_clothnode_color(clothnode_name):
    outmeshes = cmds.listConnections(
        clothnode_name + '.outputMesh', type='mesh', shapes=True)
    if not outmeshes:
        return None

    shading_engines = cmds.listConnections(
        outmeshes[0] + '.instObjGroups', type='shadingEngine')
    if not shading_engines:
        return None

    shaders = cmds.listConnections(shading_engines[0] + '.surfaceShader')
    if not shaders:
        return None

    return cmds.getAttr(shaders[0] + '.color')[0]


def set_clothnode_color(clothnode_name, red, green, blue):
    outmeshes = cmds.listConnections(
        clothnode_name + '.outputMesh', type='mesh', shapes=True)
    if not outmeshes:
        return None
    old_shading_engines = cmds.listConnections(
        outmeshes[0] + '.instObjGroups', type='shadingEngine')
    if not old_shading_engines:
        return None

    blinn = cmds.shadingNode('blinn', asShader=True)
    cmds.setAttr(blinn + ".color", red, green, blue, type='double3')

    selection = cmds.ls(sl=True)
    cmds.select(outmeshes)
    cmds.hyperShade(assign=blinn)
    # old_shading_engines should contain only one shading engine
    for shading_engine in old_shading_engines:
        connected = cmds.listConnections(shading_engine + ".dagSetMembers")
        if connected:
            return
        blinns = cmds.listConnections(shading_engine, type='blinn')
        cmds.delete(shading_engine)
        cmds.delete(blinns)
    cmds.select(selection)
