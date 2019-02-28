from PySide2 import QtCore, QtWidgets
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from ncachemanager.ui.nodetable import DynamicNodesTableWidget
from ncachemanager.ui.options import CacheOptions
from ncachemanager.ui.qtutils import get_icon


WINDOW_TITLE = "NCache Manager"


class NCacheManager(QtWidgets.QWidget):
    def __init__(self):
        mainWindowPtr = omui.MQtUtil.mainWindow()
        mainWindow = wrapInstance(long(mainWindowPtr), QtWidgets.QMainWindow)
        super(NCacheManager, self).__init__(mainWindow, QtCore.Qt.Window)
        self.setWindowTitle(WINDOW_TITLE)
        self.nodetable = DynamicNodesTableWidget()
        self.senders = CacheSendersWidget()
        self.cacheoptions = CacheOptions()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.nodetable)
        self.layout.addWidget(self.senders)
        self.layout.addWidget(self.cacheoptions)

    def show(self, **kwargs):
        super(NCacheManager, self).show(**kwargs)
        self.nodetable.show()

    def closeEvent(self, e):
        super(NCacheManager, self).closeEvent(e)
        self.nodetable.closeEvent(e)

    def set_workspace(self, workspace):
        self.nodetable.set_workspace(workspace)


class CacheSendersWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CacheSendersWidget, self).__init__(parent)
        text = "Erase current cache"
        self.erase_cache_in_version = QtWidgets.QPushButton(text)
        self.erase_all_in_verion = QtWidgets.QPushButton("all")
        self.erase_all_in_verion.setFixedWidth(40)
        text = "Create new version"
        self.create_cacheversion = QtWidgets.QPushButton(text)
        self.create_cacheversion_all = QtWidgets.QPushButton("all")
        self.create_cacheversion_all.setFixedWidth(40)
        self.append_cache = QtWidgets.QPushButton("append cache")
        self.append_cache_all = QtWidgets.QPushButton("all")
        self.append_cache_all.setFixedWidth(40)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(0)
        self.layout.setVerticalSpacing(4)
        self.layout.addWidget(self.erase_cache_in_version, 0, 0)
        self.layout.addWidget(self.erase_all_in_verion, 0, 1)
        self.layout.addWidget(self.create_cacheversion, 1, 0)
        self.layout.addWidget(self.create_cacheversion_all, 1, 1)
        self.layout.addWidget(self.append_cache, 2, 0)
        self.layout.addWidget(self.append_cache_all, 2, 1)
