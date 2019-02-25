from PySide2 import QtWidgets


class CacheInfosDialog(QtWidgets.QWidget):
    def __init__(self, parent):
        super(CacheInfosWidget, self).__init__(parent=parent, QtCore.Qt.Window)
        self.name = QtWidgets.QLineEdit()
        self.comment = QtWidgets.QTextEdit()
        self.nodelist = QtWidgets.QListWidgets()

        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.addRow("name", self.name)
        self.form_layout.addRow("comment", self.comment)
        self.form_layout.addRow("nodes", self.nodelist)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addLayout(self.form_layout)

    def set_version(self, version):
        self.name.setText(version.name)
        self.comment.setText(version["comment"])
        self.nodelist.clear()
        for node in verion["nodes"]:
            self.nodelist.addItem(node)
