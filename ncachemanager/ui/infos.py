from PySide2 import QtWidgets, QtCore


class CacheInfosDialog(QtWidgets.QWidget):
    def __init__(self, parent):
        super(CacheInfosDialog, self).__init__(parent, QtCore.Qt.Window)
        self.name = QtWidgets.QLineEdit()
        self.comment = QtWidgets.QTextEdit()
        self.nodelist = QtWidgets.QListWidgets()
        self.close_btn = QtWidgets.QPushButton('close')

        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setMarginsContents(0, 0, 0, 0)
        self.form_layout.addRow("name", self.name)
        self.form_layout.addRow("comment", self.comment)
        self.form_layout.addRow("nodes", self.nodelist)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addLayout(self.form_layout)
        self.layout.addButton(self.close_btn)

    def set_version(self, version):
        self.name.setText(version.name)
        self.comment.setText(version["comment"])
        self.nodelist.clear()
        for node in version["nodes"]:
            self.nodelist.addItem(node)


class CompareDialog(QtWidgets.QDialog):
    def __init__(self, comparison, parent):
        super(CompareDialog, self).__init__(parent=parent)


class CompareTableView():

    def __init__(self, parent=None):
        super(CompareTableView, self).__init__(parent)
        self.configure()
        self._selection_model = None
        self._model = None

    def configure(self):
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(mode)
        self.horizontalHeader().setSectionResizeMode(mode)
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    def set_model(self, model):
        self.setModel(model)
        self._model = model
        self._selection_model = self.selectionModel()


class CompareTableModel(QtCore.QAbstractTableModel):
    HEADERS = "Node", "Maya value", "Cached value"

    def __init__(self, comparison, parent):
        super(CompareTableModel, self).__init__(parent=parent)
        self.nodes = []
        for key in sorted(comparison.keys()):
            current_value, cached_value = comparison[key]
            self.nodes.append((key, current_value, cached_value))

    def columnCount(self, _):
        return 3

    def rowCount(self, _):
        return len(self.nodes)

    def headerData(self, col, orientation):
        if orientation == QtCore.Qt.Vertical:
            return
        return self.HEADERS[col]

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        if role == QtCore.Qt.DisplayRole:
            return str(self.nodes[row][col])
