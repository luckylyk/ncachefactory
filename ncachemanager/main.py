
import os
from functools import partial

from PySide2 import QtCore, QtWidgets
from maya import cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from ncachemanager.nodetable import DynamicNodesTableWidget
from ncachemanager.comparator import ComparisonWidget
from ncachemanager.cache import DYNAMIC_NODES
from ncachemanager.cacheoptions import CacheOptions
from ncachemanager.qtutils import get_icon, get_maya_windows
from ncachemanager.manager import (
    filter_connected_cacheversions, create_and_record_cacheversion,
    record_in_existing_cacheversion)
from ncachemanager.infos import WorkspaceCacheversionsExplorer
from ncachemanager.versioning import (
    ensure_workspace_exists, list_available_cacheversions)
from ncachemanager.optionvars import (
    CACHEOPTIONS_EXP_OPTIONVAR, COMPARISON_EXP_OPTIONVAR,
    VERSION_EXP_OPTIONVAR, ensure_optionvars_exists)


WINDOW_TITLE = "NCache Manager"


class NCacheManager(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(NCacheManager, self).__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle(WINDOW_TITLE)
        self.workspace_widget = WorkspaceWidget()
        self.nodetable = DynamicNodesTableWidget()

        self.senders = CacheSendersWidget()
        method = partial(self.create_cache, selection=False)
        self.senders.cache_all_inc.released.connect(method)
        method = partial(self.create_cache, selection=True)
        self.senders.cache_selection.released.connect(method)
        method = partial(self.erase_cache, selection=False)
        self.senders.cache_all.released.connect(method)
        method = partial(self.erase_cache, selection=True)
        self.senders.cache_selection.released.connect(method)

        self.cacheoptions = CacheOptions()
        self.cacheoptions_expander = Expander("Options", self.cacheoptions)
        self.cacheoptions_expander.clicked.connect(self.adjust_size)
        self.comparison = ComparisonWidget()
        self.comparison.setFixedHeight(250)
        self.comparison_expander = Expander("Comparisons", self.comparison)
        self.comparison_expander.clicked.connect(self.adjust_size)
        self.versions = WorkspaceCacheversionsExplorer()
        text = "Available Versions"
        self.versions_expander = Expander(text, self.versions)
        self.versions_expander.clicked.connect(self.adjust_size)

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

        self.set_workspace(get_default_workspace())

    def show(self, **kwargs):
        super(NCacheManager, self).show(**kwargs)
        self.apply_optionvars()
        self.nodetable.show()
        self.adjust_size()

    def adjust_size(self, *unused_signals_args):
        self.adjustSize()

    def closeEvent(self, e):
        super(NCacheManager, self).closeEvent(e)
        self.nodetable.closeEvent(e)
        self.comparison.closeEvent(e)
        self.save_optionvars()

    def set_workspace(self, workspace):
        self.nodetable.set_workspace(workspace)
        self.workspace_widget.set_workspace(workspace)

    def selection_changed(self):
        # update comparisons table
        if not self.nodetable.selected_nodes:
            return self.comparison.set_node_and_cacheversion(None, None)
        nodes = self.nodetable.selected_nodes
        workspace = self.workspace_widget.workspace
        cacheversions = list_available_cacheversions(workspace)

        self.versions.set_nodes_and_cacheversions(nodes, cacheversions)
        cacheversions = filter_connected_cacheversions(nodes[0], cacheversions)
        if not cacheversions:
            self.comparison.set_node_and_cacheversion(None, None)
            return
        self.comparison.set_node_and_cacheversion(nodes[0], cacheversions[0])

    def apply_optionvars(self):
        ensure_optionvars_exists()
        state = cmds.optionVar(query=CACHEOPTIONS_EXP_OPTIONVAR)
        self.cacheoptions_expander.set_state(state)
        state = cmds.optionVar(query=COMPARISON_EXP_OPTIONVAR)
        self.comparison_expander.set_state(state)
        state = cmds.optionVar(query=VERSION_EXP_OPTIONVAR)
        self.versions_expander.set_state(state)

    def save_optionvars(self):
        value = self.cacheoptions_expander.state
        cmds.optionVar(intValue=[CACHEOPTIONS_EXP_OPTIONVAR, value])
        value = self.comparison_expander.state
        cmds.optionVar(intValue=[COMPARISON_EXP_OPTIONVAR, value])
        value = self.versions_expander.state
        cmds.optionVar(intValue=[VERSION_EXP_OPTIONVAR, value])

    def sizeHint(self):
        return QtCore.QSize(350, 650)

    def create_cache(self, selection=True):
        start_frame, end_frame = self.cacheoptions.range
        workspace = self.workspace_widget.directory
        if workspace is None:
            return cmds.warning("no workspace set")
        if selection is True:
            nodes = self.nodetable.selected_nodes or []
        else:
            nodes = cmds.ls(type=DYNAMIC_NODES)

        create_and_record_cacheversion(
            workspace=workspace,
            start_frame=start_frame,
            end_frame=end_frame,
            nodes=nodes,
            behavior=self.cacheoptions.behavior)
        return

    def erase_cache(self, selection=True):
        start_frame, end_frame = self.cacheoptions.range
        workspace = self.workspace_widget.directory
        if workspace is None:
            return cmds.warning("no workspace set")
        if selection is True:
            nodes = self.nodetable.selected_nodes or []
        else:
            nodes = cmds.ls(type=DYNAMIC_NODES)
        cacheversions = filter_connected_cacheversions(
            nodes, list_available_cacheversions(workspace))

        if not cacheversions or len(cacheversions) > 1:
            cmds.warning(
                'no valid cache version or more than one cacheversion are '
                'connected to the selected dynamic nodes')
            self.create_cache(selection=selection)

        record_in_existing_cacheversion(
            cacheversion=cacheversions[0],
            start_frame=start_frame,
            end_frame=end_frame,
            nodes=nodes,
            behavior=self.cacheoptions.behavior)
        return


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

    def set_state(self, state):
        self.state = state
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
        self.browse.released.connect(self.get_directory)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.label)
        self.layout.addSpacing(8)
        self.layout.addWidget(self.edit)
        self.layout.addWidget(self.browse)

    def get_directory(self):
        if os.path.exists(self.edit.text()):
            directory = os.path.exists(self.edit.text())
        else:
            directory = os.path.expanduser("~")
        workspace = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='select workspace',
            dir=directory)
        self.set_workspace(workspace)

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
        text = "Cache selection"
        self.cache_selection = QtWidgets.QPushButton(text)
        self.cache_selection_inc = QtWidgets.QPushButton("+")
        self.cache_selection_inc.setFixedWidth(12)
        text = "Cache all"
        self.cache_all = QtWidgets.QPushButton(text)
        self.cache_all_inc = QtWidgets.QPushButton("+")
        self.cache_all_inc.setFixedWidth(12)
        self.append_cache = QtWidgets.QPushButton("Append selection")
        self.append_cache_all = QtWidgets.QPushButton("all")
        self.append_cache_all.setFixedWidth(40)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.cache_selection)
        self.layout.addSpacing(1)
        self.layout.addWidget(self.cache_selection_inc)
        self.layout.addSpacing(4)
        self.layout.addWidget(self.cache_all)
        self.layout.addSpacing(1)
        self.layout.addWidget(self.cache_all_inc)
        self.layout.addSpacing(4)
        self.layout.addWidget(self.append_cache)
        self.layout.addSpacing(1)
        self.layout.addWidget(self.append_cache_all)


def get_default_workspace():
    filename = cmds.file(expandName=True, query=True)
    if os.path.basename(filename) == 'untitled':
        return cmds.workspace(query=True, active=True)
    return os.path.dirname(filename)
