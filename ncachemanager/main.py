
import os

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from ncachemanager.nodetable import DynamicNodesTableWidget
from ncachemanager.comparator import ComparisonWidget
from ncachemanager.options import CacheOptions
from ncachemanager.qtutils import get_icon, get_maya_windows
from ncachemanager.manager import filter_connected_cacheversions
from ncachemanager.infos import CacheversionInfosWidget
from ncachemanager.versioning import (
    ensure_workspace_exists, list_available_cacheversions)

WINDOW_TITLE = "NCache Manager"


class NCacheManager(QtWidgets.QWidget):
    def __init__(self):
        parent = get_maya_windows()
        super(NCacheManager, self).__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle(WINDOW_TITLE)
        self.workspace_widget = WorkspaceWidget()
        self.nodetable = DynamicNodesTableWidget()
        self.senders = CacheSendersWidget()
        self.cacheoptions = CacheOptions()
        self.cacheoptions_expander = Expander("Options", self.cacheoptions)
        self.comparison = ComparisonWidget()
        self.comparison.setFixedHeight(250)
        self.comparison_expander = Expander("Comparisons", self.comparison)
        self.versions = CacheversionInfosWidget()
        text = "Available Versions"
        self.versions_expander = Expander(text, self.versions)

        self.workspace_widget.workspaceSet.connect(self.set_workspace)
        self.nodetable.selectionIsChanged.connect(self.selection_changed)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.workspace_widget)
        self.layout.setSpacing(4)
        self.layout.addWidget(self.nodetable)
        self.layout.addWidget(self.senders)
        self.layout.addSpacing(8)
        self.layout.addWidget(self.cacheoptions_expander)
        self.layout.addWidget(self.cacheoptions)
        self.layout.addSpacing(0)
        self.layout.addWidget(self.comparison_expander)
        self.layout.addWidget(self.comparison)
        self.layout.addSpacing(0)
        self.layout.addWidget(self.versions_expander)
        self.layout.addWidget(self.versions)

    def show(self, **kwargs):
        super(NCacheManager, self).show(**kwargs)
        self.nodetable.show()

    def closeEvent(self, e):
        super(NCacheManager, self).closeEvent(e)
        self.nodetable.closeEvent(e)
        self.comparison.closeEvent(e)

    def set_workspace(self, workspace):
        self.nodetable.set_workspace(workspace)
        self.workspace_widget.set_workspace(workspace)

    def selection_changed(self):
        # update comparisons table
        if not self.nodetable.selected_nodes:
            return self.comparison.set_node_and_cacheversion(None, None)
        node = self.nodetable.selected_nodes[0].name
        workspace = self.workspace_widget.workspace
        cacheversions = list_available_cacheversions(workspace)
        cacheversions = filter_connected_cacheversions(node, cacheversions)
        if not cacheversions:
            self.comparison.set_node_and_cacheversion(None, None)
            self.comparison.versions.set_cacheversion(None)
            return
        self.comparison.set_node_and_cacheversion(node, cacheversions[0])
        self.versions.set_cacheversion(cacheversions[0])


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

    @property
    def directory(self):
        return self.workspace

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
