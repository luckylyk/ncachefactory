from PySide2 import QtCore, QtWidgets
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from ncachemanager.ui.nodetable import DynamicNodesTableWidget
from ncachemanager.ui.options import CacheOptions


WINDOW_TITLE = "NCache Manager"


class NCacheManager(QtWidgets.QWidget):
    def __init__(self):
        mainWindowPtr = omui.MQtUtil.mainWindow()
        mainWindow = wrapInstance(long(mainWindowPtr), QtWidgets.QMainWindow)
        super(NCacheManager, self).__init__(mainWindow, QtCore.Qt.Window)
        self.setWindowTitle(WINDOW_TITLE)
        self.nodetable = DynamicNodesTableWidget()
        self.cacheoptions = CacheOptions()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.nodetable)
        self.layout.addWidget(self.cacheoptions)

    def show(self, **kwargs):
        super(NCacheManager, self).show(**kwargs)
        self.nodetable.show()

    def closeEvent(self, e):
        super(NCacheManager, self).closeEvent(e)
        self.nodetable.closeEvent(e)