
import os

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from ncachemanager.nodetable import DynamicNodesTableWidget
from ncachemanager.options import CacheOptions
from ncachemanager.qtutils import get_icon, get_maya_windows
from ncachemanager.versioning import ensure_workspace_exists


WINDOW_TITLE = "NCache Manager"


class NCacheManager(QtWidgets.QWidget):
    def __init__(self):
        parent = get_maya_windows()
        super(NCacheManager, self).__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle(WINDOW_TITLE)
        self.workspace = WorkspaceWidget()
        self.nodetable = DynamicNodesTableWidget()
        self.senders = CacheSendersWidget()
        self.cacheoptions = CacheOptions()
        self.cacheoptions_expander = Expander("Options", self.cacheoptions)
        self.comparison = QtWidgets.QWidget()
        self.comparison_expander = Expander("Comparisons", self.comparison)
        self.versions = QtWidgets.QWidget()
        text = "Available Versions"
        self.versions_expander = Expander(text, self.versions)

        self.workspace.workspaceSet.connect(self.set_workspace)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.workspace)
        self.layout.setSpacing(4)
        self.layout.addWidget(self.nodetable)
        self.layout.addWidget(self.senders)
        self.layout.addSpacing(8)
        self.layout.addWidget(self.cacheoptions_expander)
        self.layout.addWidget(self.cacheoptions)
        self.layout.addSpacing(2)
        self.layout.addWidget(self.comparison_expander)
        self.layout.addWidget(self.comparison)
        self.layout.addSpacing(2)
        self.layout.addWidget(self.versions_expander)
        self.layout.addWidget(self.versions)

    def show(self, **kwargs):
        super(NCacheManager, self).show(**kwargs)
        self.nodetable.show()

    def closeEvent(self, e):
        super(NCacheManager, self).closeEvent(e)
        self.nodetable.closeEvent(e)

    def set_workspace(self, workspace):
        self.nodetable.set_workspace(workspace)
        self.workspace.set_workspace(workspace)


TOGGLER_STYLESHEET = (
    'background: rgb(0, 0, 0, 75); text-align: left; font: bold')


class Expander(QtWidgets.QPushButton):
    def __init__(self, text, child, parent=None):
        super(Expander, self).__init__(parent)
        self.setStyleSheet('text-align: left; font: bold')
        self.setFixedHeight(20)
        self.icons = get_icon('arrow_close.png'), get_icon('arrow_open.png')
        self.setText(text)
        self.child = child
        self.state = True
        self.setIcon(self.icons[int(self.state)])
        self.clicked.connect(self._call_clicked)

    def _call_clicked(self):
        self.state = not self.state
        self.child.setVisible(self.state)
        self.setIcon(self.icons[int(self.state)])


class WorkspaceWidget(QtWidgets.QWidget):
    workspaceSet = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(WorkspaceWidget, self).__init__(parent)
        self.workspace = None
        self.label = QtWidgets.QLabel("Workspace")
        self.edit = QtWidgets.QLineEdit()
        self.edit.returnPressed.connect(self._call_set_workspace)
        self.browse = QtWidgets.QPushButton(get_icon("folder.png"), "")
        self.browse.setFixedSize(22, 22)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.label)
        self.layout.addSpacing(8)
        self.layout.addWidget(self.edit)
        self.layout.addWidget(self.browse)

    def set_wrong(self):
        self.edit.setStyleSheet('background-color: #DD5555')

    def set_workspace(self, workspace):
        certified = ensure_workspace_exists(workspace)
        self.workspace = certified
        self.edit.setText(workspace)
        if certified != workspace:
            self.workspaceSet.emit(certified)

    def _call_set_workspace(self):
        workspace = self.edit.text()
        if not os.path.exists(workspace):
            return self.set_wrong()
        self.edit.setStyleSheet('')
        self.workspace = ensure_workspace_exists(workspace)
        self.edit.setText(workspace)
        self.workspaceSet.emit(self.workspace)


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
        self.layout.setHorizontalSpacing(1)
        self.layout.setVerticalSpacing(4)
        self.layout.addWidget(self.erase_cache_in_version, 0, 0)
        self.layout.addWidget(self.erase_all_in_verion, 0, 1)
        self.layout.addWidget(self.create_cacheversion, 1, 0)
        self.layout.addWidget(self.create_cacheversion_all, 1, 1)
        self.layout.addWidget(self.append_cache, 2, 0)
        self.layout.addWidget(self.append_cache_all, 2, 1)
