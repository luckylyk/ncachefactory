
import os
from functools import partial

from PySide2 import QtCore, QtWidgets
from maya import cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from ncachemanager.nodetable import DynamicNodesTableWidget
from ncachemanager.comparator import ComparisonWidget
from ncachemanager.ncache import DYNAMIC_NODES
from ncachemanager.cacheoptions import CacheOptions
from ncachemanager.qtutils import get_icon, get_maya_windows
from ncachemanager.playblastoptions import PlayblastOptions
from ncachemanager.api import (
    filter_connected_cacheversions, create_and_record_cacheversion,
    record_in_existing_cacheversion, append_to_cacheversion)
from ncachemanager.infos import WorkspaceCacheversionsExplorer
from ncachemanager.versioning import (
    ensure_workspace_exists, list_available_cacheversions,
    filter_cacheversions_containing_nodes, cacheversion_contains_node)
from ncachemanager.optionvars import (
    CACHEOPTIONS_EXP_OPTIONVAR, COMPARISON_EXP_OPTIONVAR,
    VERSION_EXP_OPTIONVAR, PLAYBLAST_EXP_OPTIONVAR, FFMPEG_PATH_OPTIONVAR,
    MAYAPY_PATH_OPTIONVAR, MEDIAPLAYER_PATH_OPTIONVAR,
    MULTICACHE_EXP_OPTIONVAR, ensure_optionvars_exists)
from ncachemanager.multincacher import MultiCacher, send_batch_ncache_jobs
from ncachemanager.timecallbacks import (
    register_time_callback, add_to_time_callback, unregister_time_callback,
    time_verbose, clear_time_callback_functions)


WINDOW_TITLE = "NCache Manager"


class NCacheManager(MayaQWidgetDockableMixin, QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(NCacheManager, self).__init__(parent=parent)
        self.setWindowTitle(WINDOW_TITLE)
        self.workspace = None
        self.processes = []

        self.pathoptions = PathOptions(self)
        self.workspace_widget = WorkspaceWidget()
        self.nodetable = DynamicNodesTableWidget()

        self.senders = CacheSendersWidget()
        method = partial(self.create_cache, selection=False)
        self.senders.cache_all_inc.released.connect(method)
        method = partial(self.create_cache, selection=True)
        self.senders.cache_selection_inc.released.connect(method)
        method = partial(self.erase_cache, selection=False)
        self.senders.cache_all.released.connect(method)
        method = partial(self.erase_cache, selection=True)
        self.senders.cache_selection.released.connect(method)
        method = partial(self.append_cache, selection=True)
        self.senders.append_cache.released.connect(method)
        method = partial(self.append_cache, selection=False)
        self.senders.append_cache_all.released.connect(method)

        self.cacheoptions = CacheOptions()
        self.cacheoptions_expander = Expander("Options", self.cacheoptions)
        self.cacheoptions_expander.clicked.connect(self.adjust_size)
        self.multicacher = MultiCacher()
        self.multicacher.sendMultiCacheRequested.connect(self.send_multi_cache)
        self.multicacher_expander = Expander('Multi Cacher', self.multicacher)
        self.multicacher_expander.clicked.connect(self.adjust_size)
        self.playblast = PlayblastOptions()
        self.playblast_expander = Expander("Playblast", self.playblast)
        self.playblast_expander.clicked.connect(self.adjust_size)
        self.comparison = ComparisonWidget()
        self.comparison.setFixedHeight(250)
        self.comparison_expander = Expander("Comparisons", self.comparison)
        self.comparison_expander.clicked.connect(self.adjust_size)
        self.versions = WorkspaceCacheversionsExplorer()
        self.versions.infosModified.connect(self.nodetable.update_layout)
        self.versions.cacheApplied.connect(self.nodetable.update_layout)
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
        self.layout.addWidget(self.multicacher_expander)
        self.layout.addWidget(self.multicacher)
        self.layout.addSpacing(0)
        self.layout.addWidget(self.cacheoptions_expander)
        self.layout.addWidget(self.cacheoptions)
        self.layout.addSpacing(0)
        self.layout.addWidget(self.playblast_expander)
        self.layout.addWidget(self.playblast)
        self.layout.addSpacing(0)
        self.layout.addWidget(self.comparison_expander)
        self.layout.addWidget(self.comparison)
        self.layout.addSpacing(0)
        self.layout.addWidget(self.versions_expander)
        self.layout.addWidget(self.versions)

        self.menubar = QtWidgets.QMenuBar(self)
        self.menufile = QtWidgets.QMenu('edit', self.menubar)
        self.menubar.addMenu(self.menufile)
        self.editpath = QtWidgets.QAction('edit external path', self.menufile)
        self.menufile.addAction(self.editpath)
        self.editpath.triggered.connect(self.pathoptions.show)
        self.layout.setMenuBar(self.menubar)

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
        self.workspace = workspace
        self.nodetable.set_workspace(workspace)
        self.multicacher.set_workspace(workspace)
        self.workspace_widget.set_workspace(workspace)
        self.nodetable.update_layout()

    def selection_changed(self):
        nodes = self.nodetable.selected_nodes
        if not self.nodetable.selected_nodes:
            self.versions.set_nodes_and_cacheversions(None, None)
            self.comparison.set_node_and_cacheversion(None, None)
            return
        workspace = self.workspace_widget.workspace
        all_cacheversions = list_available_cacheversions(workspace)
        available_cacheversions = filter_cacheversions_containing_nodes(
            cmds.ls(type=DYNAMIC_NODES), all_cacheversions)

        connected_cacheversions = filter_connected_cacheversions(
            nodes, available_cacheversions)
        if not connected_cacheversions:
            self.comparison.set_node_and_cacheversion(None, None)
            self.versions.set_nodes_and_cacheversions(nodes, available_cacheversions)
            return

        self.versions.set_nodes_and_cacheversions(nodes, available_cacheversions)
        if not cacheversion_contains_node(nodes[0], connected_cacheversions[0]):
            self.comparison.set_node_and_cacheversion(None, None)
            return
        self.comparison.set_node_and_cacheversion(nodes[0], connected_cacheversions[0])

    def apply_optionvars(self):
        ensure_optionvars_exists()
        state = cmds.optionVar(query=MULTICACHE_EXP_OPTIONVAR)
        self.multicacher_expander.set_state(state)
        state = cmds.optionVar(query=CACHEOPTIONS_EXP_OPTIONVAR)
        self.cacheoptions_expander.set_state(state)
        state = cmds.optionVar(query=PLAYBLAST_EXP_OPTIONVAR)
        self.playblast_expander.set_state(state)
        state = cmds.optionVar(query=COMPARISON_EXP_OPTIONVAR)
        self.comparison_expander.set_state(state)
        state = cmds.optionVar(query=VERSION_EXP_OPTIONVAR)
        self.versions_expander.set_state(state)

    def save_optionvars(self):
        value = self.multicacher_expander.state
        cmds.optionVar(intValue=[MULTICACHE_EXP_OPTIONVAR, value])
        value = self.cacheoptions_expander.state
        cmds.optionVar(intValue=[CACHEOPTIONS_EXP_OPTIONVAR, value])
        value = self.playblast_expander.state
        cmds.optionVar(intValue=[PLAYBLAST_EXP_OPTIONVAR, value])
        value = self.comparison_expander.state
        cmds.optionVar(intValue=[COMPARISON_EXP_OPTIONVAR, value])
        value = self.versions_expander.state
        cmds.optionVar(intValue=[VERSION_EXP_OPTIONVAR, value])

    def sizeHint(self):
        return QtCore.QSize(350, 650)

    def create_cache(self, selection=True):
        register_time_callback()
        if self.cacheoptions.verbose is True:
            add_to_time_callback(time_verbose)

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
            behavior=self.cacheoptions.behavior,
            playblast=self.playblast.record_playblast,
            playblast_viewport_options=self.playblast.viewport_options)

        self.nodetable.set_workspace(workspace)
        self.nodetable.update_layout()
        self.selection_changed()
        unregister_time_callback()
        clear_time_callback_functions()

    def erase_cache(self, selection=True):
        register_time_callback()
        if self.cacheoptions.verbose is True:
            add_to_time_callback(time_verbose)

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
            return

        record_in_existing_cacheversion(
            cacheversion=cacheversions[0],
            start_frame=start_frame,
            end_frame=end_frame,
            nodes=nodes,
            behavior=self.cacheoptions.behavior,
            playblast=self.playblast.record_playblast,
            playblast_viewport_options=self.playblast.viewport_options)
        self.nodetable.update_layout()
        self.selection_changed()
        unregister_time_callback()
        clear_time_callback_functions()

    def append_cache(self, selection=True):
        register_time_callback()
        if self.cacheoptions.verbose is True:
            add_to_time_callback(time_verbose)

        workspace = self.workspace_widget.directory
        if workspace is None:
            return cmds.warning("no workspace set")
        if selection is True:
            nodes = self.nodetable.selected_nodes or []
        else:
            nodes = cmds.ls(type=DYNAMIC_NODES)
        if not nodes:
            return cmds.warning("no nodes selected")

        cacheversion = None
        for node in nodes:
            cacheversions = filter_connected_cacheversions(
                [node], list_available_cacheversions(workspace))
            if not cacheversions:
                message = "some nodes doesn't have cache connected to append"
                return cmds.warning(message)
            if cacheversion is None:
                cacheversion = cacheversions[0]
            if cacheversions[0] != cacheversion:
                message = "append cache on multiple version is not suppported."
                return cmds.warning(message)

        append_to_cacheversion(
            nodes=nodes,
            cacheversion=cacheversion,
            playblast=self.playblast.record_playblast,
            playblast_viewport_options=self.playblast.viewport_options)
        self.nodetable.update_layout()
        self.selection_changed()
        unregister_time_callback()
        clear_time_callback_functions()

    def send_multi_cache(self):
        if self.workspace is None:
            None
        start_frame, end_frame = self.cacheoptions.range
        self.processes = send_batch_ncache_jobs(
            workspace=self.workspace,
            jobs=self.multicacher.jobs,
            start_frame=start_frame,
            end_frame=end_frame,
            nodes=cmds.ls(type=DYNAMIC_NODES),
            playblast_viewport_options=self.playblast.viewport_options,
            timelimit=self.multicacher.options.timelimit,
            stretchmax=self.multicacher.options.explosion_detection_tolerance)
        self.multicacher.clear()


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
        self.browse = BrowserLine()
        self.browse.button.released.connect(self.get_directory)
        self.browse.text.returnPressed.connect(self._call_set_workspace)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.label)
        self.layout.addSpacing(8)
        self.layout.addWidget(self.browse)

    def get_directory(self):
        directory = self.directory
        workspace = QtWidgets.QFileDialog.getExistingDirectory(dir=directory)
        if not workspace:
            return
        self.set_workspace(workspace)

    @property
    def directory(self):
        return self.workspace

    def set_wrong(self):
        self.browse.text.setStyleSheet('background-color: #DD5555')

    def set_workspace(self, workspace):
        certified = ensure_workspace_exists(workspace)
        self.workspace = certified
        self.browse.text.setText(workspace)
        if certified != workspace:
            self.workspaceSet.emit(certified)

    def _call_set_workspace(self):
        workspace = self.edit.text()
        if not os.path.exists(workspace):
            return self.set_wrong()
        self.browse.text.setStyleSheet('')
        self.workspace = ensure_workspace_exists(workspace)
        self.browse.text.setText(workspace)
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


class PathOptions(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(PathOptions, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle("Set external applications paths")
        self.ffmpeg = BrowserLine()
        self.ffmpeg.text.textEdited.connect(self.save_options)
        function = partial(self.get_executable_path, self.ffmpeg)
        self.ffmpeg.button.released.connect(function)
        self.mayapy = BrowserLine()
        self.mayapy.text.textEdited.connect(self.save_options)
        function = partial(self.get_executable_path, self.mayapy)
        self.mayapy.button.released.connect(function)
        self.mediaplayer = BrowserLine()
        self.mediaplayer.text.textEdited.connect(self.save_options)
        function = partial(self.get_executable_path, self.mediaplayer)
        self.mediaplayer.button.released.connect(function)
        self.ok = QtWidgets.QPushButton("ok")
        self.ok.setFixedWidth(85)
        self.ok.released.connect(self.hide)
        self.ok_layout = QtWidgets.QHBoxLayout()
        self.ok_layout.addStretch(1)
        self.ok_layout.addWidget(self.ok)
        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.addRow("FFMPEG:", self.ffmpeg)
        self.form_layout.addRow("mayapy", self.mayapy)
        self.form_layout.addRow("media player", self.mediaplayer)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.ok_layout)
        self.set_ui_states()

    def get_executable_path(self, browseline):
        executables = QtWidgets.QFileDialog.getOpenFileName()
        if not executables:
            return
        browseline.text.setText(executables[0])

    def set_ui_states(self):
        ensure_optionvars_exists()
        text = cmds.optionVar(query=FFMPEG_PATH_OPTIONVAR)
        self.ffmpeg.text.setText(text)
        text = cmds.optionVar(query=MAYAPY_PATH_OPTIONVAR)
        self.mayapy.text.setText(text)
        text = cmds.optionVar(query=MEDIAPLAYER_PATH_OPTIONVAR)
        self.mediaplayer.text.setText(text)

    def save_options(self, *useless_signal_args):
        cmds.optionVar(stringValue=[FFMPEG_PATH_OPTIONVAR, self.ffmpeg.text()])
        cmds.optionVar(stringValue=[MAYAPY_PATH_OPTIONVAR, self.mayapy.text()])
        text = self.mediaplayer.text()
        cmds.optionVar(stringValue=[MEDIAPLAYER_PATH_OPTIONVAR, text])


def get_default_workspace():
    filename = cmds.file(expandName=True, query=True)
    if os.path.basename(filename) == 'untitled':
        return cmds.workspace(query=True, directory=True)
    return os.path.dirname(filename)


class BrowserLine(QtWidgets.QWidget):

    def __init__(self):
        super(BrowserLine, self).__init__()
        self.text = QtWidgets.QLineEdit()
        self.button = QtWidgets.QPushButton(get_icon("folder.png"), "")
        self.button.setFixedSize(22, 22)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
