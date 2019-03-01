
from PySide2 import QtWidgets, QtCore
import datetime


class CacheversionInfosWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CacheversionInfosWidget, self).__init__(parent)
        self.setFixedHeight(200)
        self.cacheversion = None
        self.name = QtWidgets.QLineEdit()
        self.name.setEnabled(False)
        self.name.textEdited.connect(self._call_name_changed)
        self.comment = QtWidgets.QTextEdit()
        self.comment.setFixedHeight(40)
        self.comment.setEnabled(False)
        self.comment.textChanged.connect(self._call_comment_changed)
        self.nodes_table_model = NodeInfosTableModel()
        self.nodes_table_view = NodeInfosTableView()
        self.nodes_table_view.setModel(self.nodes_table_model)

        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.addRow("name", self.name)
        self.form_layout.addRow("comment", self.comment)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.nodes_table_view)

    def set_cacheversion(self, cacheversion):
        self.blockSignals(True)
        self.cacheversion = cacheversion
        self.nodes_table_model.set_cacheversion(cacheversion)
        self.name.setEnabled(bool(cacheversion))
        self.comment.setEnabled(bool(cacheversion))
        if cacheversion is None:
            self.name.setText("")
            self.comment.setText("")
            return
        self.name.setText(cacheversion.name)
        self.comment.setText(cacheversion.infos["comment"])
        self.nodes_table_view.update_header()
        self.blockSignals(False)

    def _call_name_changed(self, text):
        if self.cacheversion is None:
            return
        self.cacheversion.set_name(text)

    def _call_comment_changed(self, *unused_signal_args):
        if self.cacheversion is None:
            return
        self.cacheversion.set_comment(self.comment.toHtml())


class NodeInfosTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(NodeInfosTableView, self).__init__(parent)
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
        scrollmode = QtWidgets.QAbstractItemView.ScrollPerPixel
        self.setVerticalScrollMode(scrollmode)
        self.setHorizontalScrollMode(scrollmode)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(mode)
        self.horizontalHeader().setSectionResizeMode(mode)
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    def update_header(self):
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.horizontalHeader().setSectionResizeMode(mode)


class NodeInfosTableModel(QtCore.QAbstractTableModel):
    HEADERS = "Node", "Range", "Namespace", "Time spent"

    def __init__(self, parent=None):
        super(NodeInfosTableModel, self).__init__(parent)
        self.infos = None
        self.nodes = None

    def columnCount(self, _):
        return len(self.HEADERS)

    def rowCount(self, _):
        if self.nodes is None:
            return 0
        return len(self.nodes)

    def set_cacheversion(self, cacheversion):
        self.layoutAboutToBeChanged.emit()
        if cacheversion is None:
            self.infos = None
            self.nodes = None
            self.layoutChanged.emit()
            return
        self.infos = cacheversion.infos
        self.nodes = sorted([n for n in self.infos['nodes']])
        self.layoutChanged.emit()

    def sort(self, column, order):
        if column != 2:
            return
        reverse_ = order == QtCore.Qt.AscendingOrder
        self.layoutAboutToBeChanged.emit()
        self.nodes = sorted(self.nodes, reverse=reverse_)
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        node = self.nodes[row]
        if role == QtCore.Qt.DisplayRole:
            if col == 0:
                return node
            if col == 1:
                frames = self.infos['nodes'][node]['range']
                return ", ".join([str(f) for f in frames])
            if col == 2:
                self.infos['nodes'][node]['namespace']
                return self.infos['nodes'][node]['namespace'] or 'None'
            if col == 3:
                seconds = self.infos['nodes'][node]['timespent']
                delta = datetime.timedelta(seconds=seconds)
                return str(delta)

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter
