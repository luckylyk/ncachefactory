from PySide2 import QtCore, QtWidgets
from maya import cmds
from ncachemanager.cache import DYNAMIC_NODES
from ncachemanager.attributes import FILTERED_FOR_NCACHEMANAGER


WINDOW_TITLE = "Visible for cachemanager"


class FilterDialog(QtWidgets.QWidget):
    updateRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(FilterDialog, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(WINDOW_TITLE)
        self.list = QtWidgets.QListWidget()
        self.list.itemChanged.connect(self.item_changed)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.list)

    def show(self):
        super(FilterDialog, self).show()
        self.fill_list()

    def fill_list(self):
        self.list.clear()
        flags = QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
        for node in sorted(cmds.ls(type=DYNAMIC_NODES)):
            name = cmds.listRelatives(node, parent=True)[0]
            state = not cmds.getAttr(node + '.' + FILTERED_FOR_NCACHEMANAGER)
            checkstate = QtCore.Qt.Checked if state else QtCore.Qt.Unchecked
            item = QtWidgets.QListWidgetItem(name)
            item.setFlags(flags)
            item.setCheckState(checkstate)
            item.node = node
            self.list.addItem(item)

    def item_changed(self, item):
        state = not item.checkState() == QtCore.Qt.Checked
        cmds.setAttr(item.node + '.' + FILTERED_FOR_NCACHEMANAGER, state)
        self.updateRequested.emit()
