from PySide2 import QtWidgets, QtGui, QtCore
from maya import cmds
from qtutils import get_icon
from ncachemanager.manager import filter_connected_cacheversions


class OnOffLabel(QtWidgets.QWidget):
    """ on/off switch icon for delegate
    / | \
    \___/
    """
    ICONSIZE = 22, 22

    def __init__(self, dynamic_node, parent=None):
        super(OnOffLabel, self).__init__(parent)

        self.icons = get_icon(dynamic_node.on), get_icon(dynamic_node.off)
        self.dynamic_node = dynamic_node
        self.setFixedSize(24, 24)
        self.repaint()

    def mousePressEvent(self, _):
        self.dynamic_node.switch()
        self.repaint()

    def paintEvent(self, _):
        painter = QtGui.QPainter()
        icon = self.icons[bool(self.dynamic_node.enable)]
        pixmap = icon.pixmap(32, 32).scaled(
            QtCore.QSize(*self.ICONSIZE),
            transformMode=QtCore.Qt.SmoothTransformation)
        painter.drawPixmap(self.rect(), pixmap)


class DynamicNodeTableModel(QtCore.QAbstractTableModel):
    HEADERS = "", "Node", "Cache"

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

    def set_cacheversions(self, cacheversions):
        self.layoutAboutToBeChanged.emit()
        self.cacheversions = cacheversions
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
            if column == 1:
                return node.parent
            elif column == 2:
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

    def configure(self):
        self.setMinimumWidth(500)
        self.setShowGrid(False)
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
            self.item_delegate.createEditor(None, None, index)

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

    def set_item_delegate(self, item_delegate):
        self.item_delegate = item_delegate
        self.setItemDelegateForColumn(0, item_delegate)


class ColorSquareDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, table):
        super(ColorSquareDelegate, self).__init__(table)
        self._model = table.model()
        self._table = table

    def paint(self, painter, option, index):
        dynamic_node = self._model.data(index, QtCore.Qt.UserRole)
        rect = QtCore.QRect(
            option.rect.center().x() - 7,
            option.rect.center().y() - 7,
            14, 14)
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
