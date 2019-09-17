from PySide2 import QtWidgets, QtGui, QtCore
from maya import cmds
import maya.OpenMaya as om

from ncachemanager.qtutils import get_icon
from ncachemanager.nodes import filtered_dynamic_nodes, create_dynamic_node
from ncachemanager.manager import filter_connected_cacheversions
from ncachemanager.versioning import (
    list_available_cacheversions, split_namespace_nodename)
from ncachemanager.cache import (
    DYNAMIC_NODES, clear_cachenodes, list_connected_cachefiles,
    list_connected_cacheblends)
from ncachemanager.filtering import FilterDialog

RANGE_CACHED_COLOR = "#44aa22"
RANGE_NOT_CACHED_COLOR = "#333333"
CURRENT_TIME_COLOR = "#CC5533"
NUCLEUS_START_TIME_COLOR = "#363430"
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
    selectionIsChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(DynamicNodesTableWidget, self).__init__(parent)
        self._workspace = None
        self._active_selection_callbacks = True
        self._callbacks = []
        self._jobs = []
        self._filter = FilterDialog()
        self._filter.updateRequested.connect(self._full_update_callback)
        self.script_jobs = []
        self.versions = []
        self.table_model = DynamicNodeTableModel()
        self.table_view = DynamicNodeTableView()
        self.table_view.set_model(self.table_model)
        method = self.selectionIsChanged.emit
        self.table_view.selectionIsChanged.connect(method)
        method = self._synchronise_from_selection_from_tableview
        self.table_view.selectionIsChanged.connect(method)
        self.table_color_square = ColorSquareDelegate(self.table_view)
        self.table_enable = EnableDelegate(self.table_view)
        self.table_visibility = VisibilityDelegate(self.table_view)
        self.table_cached_range = CachedRangeDelegate(self.table_view)
        self.table_view.set_color_delegate(self.table_color_square)
        self.table_view.set_enable_delegate(self.table_enable)
        self.table_view.set_visibility_delegate(self.table_visibility)
        self.table_view.set_cacherange_delegate(self.table_cached_range)
        self.table_model.set_nodes(filtered_dynamic_nodes())
        self.table_toolbar = TableToolBar(self.table_view)
        self.table_toolbar.updateRequested.connect(self.update_layout)
        self.table_toolbar.showFilterRequested.connect(self._filter.show)
        self.table_toolbar_layout = QtWidgets.QHBoxLayout()
        self.table_toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.table_toolbar_layout.addStretch(1)
        self.table_toolbar_layout.addWidget(self.table_toolbar)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.table_view)
        self.layout.addLayout(self.table_toolbar_layout)

    @property
    def selected_nodes(self):
        nodes = self.table_view.selected_nodes
        if nodes is None:
            return
        return [node.name for node in nodes]

    def set_workspace(self, workspace):
        self._workspace = workspace
        cacheversions = list_available_cacheversions(self._workspace)
        self.table_model.set_cacheversions(cacheversions)

    def register_callbacks(self):
        function = self._preconnection_made_callback
        cb = om.MDGMessage.addPreConnectionCallback(function)
        self._callbacks.append(cb)

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

        function = self._synchronise_selection_from_maya
        cb = om.MEventMessage.addEventCallback('SelectionChanged', function)

        function = self.update_layout
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

    def _preconnection_made_callback(self, inplug, outplug, *unused_args):
        for plug in (inplug, outplug):
            name = plug.name()
            if 'outputMesh' not in name and 'inputMesh' not in name:
                continue
            plug_node = om.MFnDagNode(plug.node()).name()
            for node in self.table_model.nodes:
                if node.name == plug_node:
                    node.reset_connections()
                    return

    def _created_node_callback(self, mobject, *unused_callbacks_args):
        if mobject.apiType() not in OM_DYNAMIC_NODES:
            return
        dynamic_node = create_dynamic_node(om.MFnDagNode(mobject).name())
        self.table_model.insert_node(dynamic_node)

    def _full_update_callback(self, *unused_callbacks_args):
        self.table_model.set_nodes(filtered_dynamic_nodes())
        if not self._workspace:
            return
        cacheversions = list_available_cacheversions(self._workspace)
        self.table_model.set_cacheversions(cacheversions)

    def _synchronise_selection_from_maya(self, *unused_callbacks_args):
        if self._active_selection_callbacks is False:
            return
        if not self.table_toolbar.interactive.isChecked():
            return
        self._active_selection_callbacks = False
        nodes = cmds.ls(selection=True, dag=True, type=DYNAMIC_NODES)
        dynamic_nodes = [n for n in self.table_model.nodes if n.name in nodes]
        rows = [self.table_model.nodes.index(n) for n in dynamic_nodes]
        self.table_view.select_rows(rows)
        self._active_selection_callbacks = True

    def _synchronise_from_selection_from_tableview(self):
        if self._active_selection_callbacks is False:
            return
        if not self.table_toolbar.interactive.isChecked():
            return
        self._active_selection_callbacks = False
        nodes = self.table_view.selected_nodes
        if nodes:
            cmds.select([node.name for node in nodes])
        self._active_selection_callbacks = True

    def update_layout(self, *unused_callbacks_args):
        self.table_model.layoutChanged.emit()

    def show(self):
        super(DynamicNodesTableWidget, self).show()
        self.register_callbacks()

    def closeEvent(self, event):
        self.unregister_callbacks()
        return super(DynamicNodesTableWidget, self).closeEvent(event)


class DynamicNodeTableView(QtWidgets.QTableView):
    selectionIsChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(DynamicNodeTableView, self).__init__(parent)
        self.configure()
        self._selection_model = None
        self._model = None
        self.color_delegate = None
        self.enable_delegate = None
        self.visibility_delegate = None
        self.cacherange_delegate = None

    def configure(self):
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        scrollmode = QtWidgets.QAbstractItemView.ScrollPerPixel
        self.setVerticalScrollMode(scrollmode)
        self.setHorizontalScrollMode(scrollmode)
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
            self.enable_delegate.createEditor(None, None, index)
        if index.column() == 2:
            self.visibility_delegate.createEditor(None, None, index)
        self._model.layoutChanged.emit()
        return super(DynamicNodeTableView, self).mouseReleaseEvent(event)

    @property
    def selected_nodes(self):
        if self._model is None:
            return
        indexes = self._selection_model.selectedIndexes()
        if not indexes:
            return None
        indexes = [i for i in indexes if i.column() == 0]
        return [self._model.data(i, QtCore.Qt.UserRole) for i in indexes]

    def set_model(self, model):
        self.setModel(model)
        self._model = model
        self._selection_model = self.selectionModel()
        self._selection_model.selectionChanged.connect(self.selection_changed)

    def selection_changed(self, *unused_signals_args):
        self.selectionIsChanged.emit()

    def select_rows(self, rows):
        self.blockSignals(True)
        if self._selection_model is None:
            return
        self._selection_model.clearSelection()
        flag = QtCore.QItemSelectionModel.Select
        for row in range(self._model.rowCount()):
            if row not in rows:
                continue
            for col in range(self._model.columnCount()):
                index = self._model.index(row, col, QtCore.QModelIndex())
                self._selection_model.select(index, flag)
        self.blockSignals(False)
        self.selectionIsChanged.emit()

    def set_color_delegate(self, item_delegate):
        self.color_delegate = item_delegate
        self.setItemDelegateForColumn(0, item_delegate)

    def set_enable_delegate(self, item_delegate):
        self.enable_delegate = item_delegate
        self.setItemDelegateForColumn(1, item_delegate)

    def set_visibility_delegate(self, item_delegate):
        self.visibility_delegate = item_delegate
        self.setItemDelegateForColumn(2, item_delegate)

    def set_cacherange_delegate(self, item_delegate):
        self.cacherange_delegate = item_delegate
        self.setItemDelegateForColumn(5, item_delegate)


class DynamicNodeTableModel(QtCore.QAbstractTableModel):
    HEADERS = "", "", "", "Node", "Cache(s)", "Range Cached", ""

    def __init__(self, parent=None):
        super(DynamicNodeTableModel, self).__init__(parent)
        self.nodes = []
        self.cacheversions = []

    def columnCount(self, _=None):
        return len(self.HEADERS)

    def rowCount(self, _=None):
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
        if column != 3:
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
            if column == 3:
                return node.parent
            elif column == 4:
                return get_connected_cache_names(node.name, self.cacheversions)
        elif role == QtCore.Qt.UserRole:
            return node

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter


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
        color = dynamic_node.color or (0, 0, 0)
        color = QtGui.QColor(*[c * 255 for c in color])
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

    def get_icon(self, dynamic_node):
        raise NotImplementedError

    def paint(self, painter, option, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        icon = self.get_icon(dynamic_node)
        pixmap = icon.pixmap(24, 24).scaled(
            QtCore.QSize(*self.ICONSIZE),
            transformMode=QtCore.Qt.SmoothTransformation)
        left = option.rect.center().x() - 8
        top = option.rect.center().y() - 8
        rect = QtCore.QRect(left, top, 16, 16)
        painter.drawPixmap(rect, pixmap)

    def sizeHint(self, *args):
        return QtCore.QSize(24, 24)


class VisibilityDelegate(SwitcherDelegate):

    def createEditor(self, _, __, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        state = not dynamic_node.visible
        dynamic_node.set_visible(state)
        return

    def get_icon(self, dynamic_node):
        if self.icons is None:
            self.icons = (
                get_icon(dynamic_node.ICONS['hidden']),
                get_icon(dynamic_node.ICONS['visible']))
        return self.icons[bool(dynamic_node.visible)]


class EnableDelegate(SwitcherDelegate):

    def createEditor(self, _, __, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        dynamic_node.switch()
        return

    def get_icon(self, dynamic_node):
        if self.icons is None:
            self.icons = (
                get_icon(dynamic_node.ICONS['off']),
                get_icon(dynamic_node.ICONS['on']))
        return self.icons[bool(dynamic_node.enable)]


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
        _, node = split_namespace_nodename(dynamic_node.name)
        cacheversions = self._model.cacheversions
        cacheversions = filter_connected_cacheversions(
            dynamic_node.name, cacheversions)

        scenestart = cmds.playbackOptions(query=True, minTime=True)
        sceneend = cmds.playbackOptions(query=True, maxTime=True)
        bg_rect = QtCore.QRect(
            option.rect.left() + 8,
            option.rect.top() + 8,
            option.rect.width() - 16,
            option.rect.height() - 16)

        if cacheversions and not len(cacheversions) > 1:
            cachedstart, cachedend = cacheversions[0].infos["nodes"][node]["range"]
            invalue = percent(cachedstart, scenestart, sceneend)
            outvalue = percent(cachedend, scenestart, sceneend)
            brush = QtGui.QBrush(QtGui.QColor(RANGE_NOT_CACHED_COLOR))
            pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
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
        if time > scenestart and time < sceneend:
            left = percent(time, scenestart, sceneend)
            left = from_percent(left, bg_rect.left(), bg_rect.right())
            pen = QtGui.QPen(QtGui.QColor(CURRENT_TIME_COLOR))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(left, option.rect.top(), left, option.rect.bottom())

        for nucleus in cmds.ls(type='nucleus'):
            time = cmds.getAttr(nucleus + '.startFrame')
            if time < scenestart or time > sceneend:
                continue
            left = percent(time, scenestart, sceneend)
            left = from_percent(left, bg_rect.left(), bg_rect.right())
            pen = QtGui.QPen(QtGui.QColor(NUCLEUS_START_TIME_COLOR))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawLine(left, option.rect.top(), left, option.rect.bottom())

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


class TableToolBar(QtWidgets.QToolBar):
    updateRequested = QtCore.Signal()
    showFilterRequested = QtCore.Signal()

    def __init__(self, table, parent=None):
        super(TableToolBar, self).__init__(parent)
        self.table = table
        self.setIconSize(QtCore.QSize(15, 15))
        self.selection = QtWidgets.QAction(get_icon('select.png'), '', self)
        self.selection.setToolTip('select maya dynamic shapes')
        self.selection.triggered.connect(self.select_nodes)
        self.interactive = QtWidgets.QAction(get_icon('link.png'), '', self)
        self.interactive.setCheckable(True)
        self.interactive.setToolTip('interactive selection')
        self.switch = QtWidgets.QAction(get_icon('on_off.png'), '', self)
        self.switch.setToolTip('on/off selected dynamic shapes')
        self.switch.triggered.connect(self.switch_nodes)
        icon = get_icon('visibility.png')
        self.visibility = QtWidgets.QAction(icon, '', self)
        self.visibility.setToolTip('swith visibility state')
        self.visibility.triggered.connect(self.switch_nodes_visibility)
        self.delete = QtWidgets.QAction(get_icon('trash.png'), '', self)
        self.delete.setToolTip('remove cache connected')
        self.delete.triggered.connect(self.clear_connected_caches)
        self.filter = QtWidgets.QAction(get_icon('filter.png'), '', self)
        self.filter.setToolTip('exclude node to manager')
        self.filter.triggered.connect(self.showFilterRequested.emit)

        self.addAction(self.selection)
        self.addAction(self.interactive)
        self.addSeparator()
        self.addAction(self.switch)
        self.addAction(self.visibility)
        self.addAction(self.delete)
        self.addSeparator()
        self.addAction(self.filter)

    def clear_connected_caches(self):
        nodes = self.table.selected_nodes or self.table.model().nodes
        nodes = [node.name for node in nodes]
        clear_cachenodes(nodes=nodes)
        self.updateRequested.emit()

    def switch_nodes_visibility(self):
        nodes = self.table.selected_nodes or self.table.model().nodes
        state = not nodes[0].visible
        for node in nodes:
            node.set_visible(state)
        self.updateRequested.emit()

    def switch_nodes(self):
        nodes = self.table.selected_nodes or self.table.model().nodes
        state = not nodes[0].enable
        for node in nodes:
            if node.enable != state:
                node.switch()
        self.updateRequested.emit()

    def select_nodes(self):
        if not self.table.selected_nodes:
            return
        nodes = [node.name for node in self.table.selected_nodes]
        if not nodes:
            return
        cmds.select(nodes)


def get_connected_cache_names(node, cacheversions):
    cacheversions = filter_connected_cacheversions(node, cacheversions)
    if cacheversions:
        return ", ".join([cacheversion.name for cacheversion in cacheversions])
    cachenodes = (
        (list_connected_cachefiles(node) or []) +
        (list_connected_cacheblends(node) or []))
    if not cachenodes:
        return 'no cache'
    return 'out of workspace'
