import os
from PySide2 import QtWidgets, QtCore
import maya.OpenMaya as om
from ncachefactory.versioning import ensure_workspace_folder_exists
from ncachefactory.qtutils import get_icon
from ncachefactory.workspace import (
    list_workspace_used, list_workspaces_recently_used,
    get_last_used_workspace, get_default_workspace)


MESSAGES = (
    om.MSceneMessage.kAfterOpen,
    om.MSceneMessage.kAfterNew)


class WorkspaceWidget(QtWidgets.QWidget):
    workspaceSet = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(WorkspaceWidget, self).__init__(parent)
        self.workspace = None
        self.callbacks = []
        self.label = QtWidgets.QLabel("Workspace")
        self.label.setFixedWidth(60)
        self.workspace_combo = QtWidgets.QComboBox()
        self.workspace_combo.setFixedWidth(300)
        self.workspace_combo.setEditable(True)
        self.workspace_combo.activated.connect(self._call_set_workspace)
        self.button = QtWidgets.QPushButton(get_icon("folder.png"), "")
        self.button.setFixedSize(22, 22)
        self.button.released.connect(self.get_directory)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)
        self.layout.addSpacing(8)
        self.layout.addWidget(self.workspace_combo)
        self.layout.addWidget(self.button)

        self.populate()
        self.register_callbacks()

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
        self.workspace_combo.setStyleSheet('background-color: #DD5555')

    def set_workspace(self, workspace):
        certified = ensure_workspace_folder_exists(workspace)
        self.workspace = certified
        self.workspace_combo.setCurrentText(certified)
        if certified != workspace:
            self.workspaceSet.emit(certified)

    def _call_set_workspace(self):
        workspace = self.workspace_combo.currentText()
        if not os.path.exists(workspace):
            return self.set_wrong()
        self.workspace_combo.setStyleSheet('')
        self.workspace = ensure_workspace_folder_exists(workspace)
        self.workspace_combo.setCurrentText(self.workspace)
        self.workspaceSet.emit(self.workspace)

    def _detect_workspace(self, *useless_callback_args):
        workspace = get_last_used_workspace() or get_default_workspace()
        self.set_workspace(workspace)

    def populate(self):
        self.workspace_combo.clear()
        workspaces = list_workspace_used()
        for workspace in workspaces:
            self.workspace_combo.addItem(workspace)
        self.workspace_combo.insertSeparator(len(workspaces))
        for workspace in list_workspaces_recently_used():
            self.workspace_combo.addItem(workspace)

    def unregister_callbacks(self):
        for callback in self.callbacks:
            om.MMessage.removeCallback(callback)
        self.callbacks = []

    def register_callbacks(self):
        if self.callbacks:
            self.unregister_callbacks()
        for message in MESSAGES:
            function = self._detect_workspace
            cb = om.MSceneMessage.addCallback(message, function)
            self.callbacks.append(cb)

    def closeEvent(self, event):
        self.unregister_callbacks()
        return super(WorkspaceWidget, self).closeEvent(event)
