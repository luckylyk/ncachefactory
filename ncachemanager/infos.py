
from PySide2 import QtWidgets, QtCore


class CacheInfosWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CacheInfosWidget, self).__init__(parent)
        self.name = QtWidgets.QLineEdit()
        self.comment = QtWidgets.QTextEdit()
        self.nodelist = QtWidgets.QListWidgets()
        self.close_btn = QtWidgets.QPushButton('close')

        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
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