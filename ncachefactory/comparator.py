
import maya.api.OpenMaya as om2
from maya import cmds
from PySide2 import QtWidgets, QtCore
from ncachefactory.cachemanager import compare_node_and_version


WINDOW_TITLE = "Comparator"
NODENAME_LABEL = "Node: {}"
CACHEVERSION_LABEL = "Cache version: {}"


class ComparisonWidget(QtWidgets.QWidget):
    closed = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(ComparisonWidget, self).__init__(parent)
        self.setWindowTitle(WINDOW_TITLE)

        self._callbacks = []
        self.node = None
        self.cacheversion = None

        self.node_label = QtWidgets.QLabel(NODENAME_LABEL.format('None'))
        text = CACHEVERSION_LABEL.format('None')
        self.version_label = QtWidgets.QLabel(text)

        self.table_model = ComparisonTableModel()
        self.table_view = ComparisonTableView()
        self.table_view.set_model(self.table_model)

        self.revert_selected = QtWidgets.QPushButton("Revert selected")
        self.revert_selected.setFixedWidth(110)
        self.revert_selected.released.connect(self._call_revert_selected)
        self.revert_all = QtWidgets.QPushButton("Revert all")
        self.revert_all.released.connect(self._call_revert_all)
        self.revert_all.setFixedWidth(110)
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.revert_selected)
        self.button_layout.addWidget(self.revert_all)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.node_label)
        self.layout.addWidget(self.version_label)
        self.layout.addWidget(self.table_view)
        self.layout.addLayout(self.button_layout)

    def set_node_and_cacheversion(self, node, cacheversion):
        self.unregister_callbacks()
        self.node = node
        self.cacheversion = cacheversion
        if self.node and self.cacheversion:
            result = compare_node_and_version(self.node, self.cacheversion)
            self.node_label.setText(NODENAME_LABEL.format(self.node))
            name = self.cacheversion.name
            self.version_label.setText(CACHEVERSION_LABEL.format(name))
            self.register_callbacks()
        else:
            result = {}
            self.node_label.setText(NODENAME_LABEL.format('None'))
            self.version_label.setText(CACHEVERSION_LABEL.format('None'))
        self.table_model.set_comparison_result(result)
        self.table_view.update_header()

    def register_callbacks(self):
        node = om2.MSelectionList().add(self.node).getDependNode(0)
        function = self._update_comparison
        cb = om2.MNodeMessage.addAttributeChangedCallback(node, function)
        self._callbacks.append(cb)

    def unregister_callbacks(self):
        for callback in self._callbacks:
            om2.MMessage.removeCallback(callback)
        self._callbacks = []

    def _update_comparison(self, *unused_callbacks_args):
        # the callback has to be temporarily disabled to avoid an infinite
        # loop. Better way should be found, this is a bit ... yeah, ugly
        self.unregister_callbacks()
        result = compare_node_and_version(self.node, self.cacheversion)
        self.table_model.set_comparison_result(result)
        self.table_view.update_header()
        self.register_callbacks()

    def _call_revert_selected(self):
        self._match_values(self.table_view.selected_attributes)

    def _call_revert_all(self):
        self._match_values(self.table_model.nodes)

    def _match_values(self, attributes):
        # the callback has to be temporarily disabled to avoid an infinite
        # loop. Better way should be found, this is a bit ... yeah, ugly
        self.unregister_callbacks()
        if not attributes:
            return
        for plug, _, cached_value in attributes:
            try:
                cmds.setAttr(plug, cached_value)
            except RuntimeError:
                message = "{} is locked or connected and cannot be modifed"
                cmds.warning(message.format(plug))
        result = compare_node_and_version(self.node, self.cacheversion)
        self.table_model.set_comparison_result(result)
        self.table_view.update_header()
        self.register_callbacks()

    def show(self):
        super(ComparisonWidget, self).show()
        self.register_callbacks()

    def closeEvent(self, event):
        self.unregister_callbacks()
        self.closed.emit(self)
        return super(ComparisonWidget, self).closeEvent(event)


class ComparisonTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(ComparisonTableView, self).__init__(parent)
        self.configure()
        self._selection_model = None
        self._model = None
        self.horizontalHeader().show()

    def configure(self):
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        scrollmode = QtWidgets.QAbstractItemView.ScrollPerPixel
        self.setVerticalScrollMode(scrollmode)
        self.setHorizontalScrollMode(scrollmode)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(mode)
        self.horizontalHeader().setSectionResizeMode(mode)
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    def update_header(self):
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.horizontalHeader().setSectionResizeMode(mode)

    @property
    def selected_attributes(self):
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


class ComparisonTableModel(QtCore.QAbstractTableModel):
    HEADERS = "Node", "Scene value", "Cached value"

    def __init__(self, parent=None):
        super(ComparisonTableModel, self).__init__(parent=parent)
        self.nodes = []

    def set_comparison_result(self, comparison):
        self.layoutAboutToBeChanged.emit()
        self.nodes = []
        for key in sorted(comparison.keys()):
            current_value, cached_value = comparison[key]
            self.nodes.append((key, current_value, cached_value))
        self.layoutChanged.emit()

    def columnCount(self, _):
        return len(self.HEADERS)

    def rowCount(self, _):
        return len(self.nodes)

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]

    def data(self, index, role):
        if not index.isValid():
            return

        row, col = index.row(), index.column()
        if role == QtCore.Qt.DisplayRole:
            if col == 0:
                return self.nodes[row][0].split(".")[-1]
            return str(self.nodes[row][col])

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter

        if role == QtCore.Qt.UserRole:
            return self.nodes[row]
