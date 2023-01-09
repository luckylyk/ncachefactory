import os
import sys
import json
from maya import cmds
from PySide2 import QtWidgets, QtCore

from ncachefactory.qtutils import BrowserLine
from ncachefactory.optionvars import (
    CUSTOM_ENV_PATH_OPTIONVAR, USE_CUSTOM_ENV_OPTIONVAR)


def get_environment():
    if not cmds.optionVar(query=USE_CUSTOM_ENV_OPTIONVAR):
        return copy_current_environment()
    with open(cmds.optionVar(query=CUSTOM_ENV_PATH_OPTIONVAR), 'r') as f:
        data = json.load(f)
        return {str(k): str(v) for k, v in data.items()}


def copy_current_environment():
    pythonpaths = os.environ["PYTHONPATH"].split(os.pathsep)
    pythonpaths = [p.replace("\\", "/") for p in pythonpaths]
    for path in sys.path:
        path = path.replace("\\", "/")
        if path in pythonpaths:
            continue
        pythonpaths.append(path)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(os.pathsep.join(pythonpaths))
    return environment


class EnvironmentOptions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(EnvironmentOptions, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle('Environment Options')
        state = cmds.optionVar(query=USE_CUSTOM_ENV_OPTIONVAR)
        text = 'Use custom environment.'
        self.use_custom_env = QtWidgets.QCheckBox(text, checked=state)
        self.use_custom_env.released.connect(self.save_options)

        self.browser = BrowserLine()
        path = cmds.optionVar(query=CUSTOM_ENV_PATH_OPTIONVAR)
        self.browser.text.setText(path)
        self.browser.button.released.connect(self.get_environment_path)
        self.browser.text.textEdited.connect(self.set_filepath)
        self.edit_environment = QtWidgets.QPushButton('Edit')
        self.edit_environment.released.connect(self.call_edit_environment)
        self.edit_environment.setEnabled(os.path.exists(path))
        self.create_environment = QtWidgets.QPushButton('Create')
        self.create_environment.released.connect(self.call_create_environment)

        self.browser_widget = QtWidgets.QWidget()
        self.browser_widget.setEnabled(state)
        self.browser_layout = QtWidgets.QHBoxLayout(self.browser_widget)
        self.browser_layout.setContentsMargins(0, 0, 0, 0)
        self.browser_layout.addWidget(self.browser)
        self.browser_layout.addWidget(self.edit_environment)
        self.browser_layout.addWidget(self.create_environment)
        self.browser_widget.setEnabled(state)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.use_custom_env)
        layout.addWidget(self.browser_widget)

    def get_environment_path(self):
        environment_filepath = QtWidgets.QFileDialog.getOpenFileName()
        if not environment_filepath:
            return
        self.text.setText(environment_filepath)

    def set_filepath(self, text):
        if os.path.exists(text):
            cmds.optionVar(stringValue=[CUSTOM_ENV_PATH_OPTIONVAR, text])
            self.browser.text.setStyleSheet('')
            return
        self.browser.text.setStyleSheet('background-color: red')

    def save_options(self):
        state = self.use_custom_env.isChecked()
        cmds.optionVar(intValue=[USE_CUSTOM_ENV_OPTIONVAR, int(state)])
        path = self.browser.text.text()
        self.edit_environment.setEnabled(os.path.exists(path))
        self.browser_widget.setEnabled(state)

    def call_edit_environment(self):
        if not os.path.exists(self.browser.text.text()):
            return
        EnvironmentSettingsDialog(self.browser.text.text()).exec_()

    def call_create_environment(self):
        filepath, result = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Select path', os.path.expanduser('~'), '*.json')
        if not result:
            return
        with open(filepath, 'w') as f:
            json.dump(copy_current_environment(), f)
        self.browser.text.setText(filepath)
        self.edit_environment.setEnabled(True)
        cmds.optionVar(stringValue=[CUSTOM_ENV_PATH_OPTIONVAR, filepath])


class EnvironmentSettingsDialog(QtWidgets.QDialog):
    def __init__(self, filepath, parent=None):
        super(EnvironmentSettingsDialog, self).__init__(parent)
        self.setWindowTitle('Edit environment')
        self.table = EnvironmentTableView()
        self.filepath = filepath
        with open(filepath, 'r') as f:
            environment = json.load(f)
            self.table.model.environment = environment
        self.save = QtWidgets.QPushButton('Save')
        self.save.released.connect(self.do_save)
        self.save.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.cancel.released.connect(self.reject)
        buttons = QtWidgets.QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.addStretch(1)
        buttons.addWidget(self.save)
        buttons.addWidget(self.cancel)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(buttons)

    def do_save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.table.model.environment, f)


class EnvironmentTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(EnvironmentTableView, self).__init__(parent)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setWordWrap(True)

        self.model = EnvironmentTableModel(self)
        self.setModel(self.model)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu_execute)

    def context_menu_execute(self, point):
        add_row = QtWidgets.QAction('Add key')
        add_row.triggered.connect(self.add_row)
        delete_row = QtWidgets.QAction('Remove key')
        delete_row.triggered.connect(self.delete_selected_row)
        self.context_menu = QtWidgets.QMenu(self)
        self.context_menu.addAction(add_row)
        self.context_menu.addAction(delete_row)
        self.context_menu.exec_(self.mapToGlobal(point))

    def add_row(self):
        key, result = QtWidgets.QInputDialog.getText(
            self, 'Environment', 'Add environment key')
        if not all((key, result)):
            return
        self.model.add_key(key)

    def delete_selected_row(self):
        index = next(self.selectionModel().selectedIndexes().__iter__(), None)
        if not index:
            return
        self.model.delete_row(index.row())


class EnvironmentTableModel(QtCore.QAbstractTableModel):
    HEADERS = 'Key', 'Value(s)'

    def __init__(self, parent=None):
        super(EnvironmentTableModel, self).__init__(parent)
        self._environment = []

    @property
    def environment(self):
        return {row[0]: row[1] for row in self._environment}

    @environment.setter
    def environment(self, environment):
        self.layoutAboutToBeChanged.emit()
        self._environment = [list(it) for it in sorted(environment.items())]
        self.layoutChanged.emit()

    def rowCount(self, *_):
        return len(self._environment)

    def columnCount(self, *_):
        return 2

    def headerData(self, section, orientation, role):
        if orientation != QtCore.Qt.Horizontal:
            return
        if role != QtCore.Qt.DisplayRole:
            return
        return self.HEADERS[section]

    def delete_row(self, row):
        self.layoutAboutToBeChanged.emit()
        del self._environment[row]
        self.layoutChanged.emit()

    def add_key(self, key):
        self.layoutAboutToBeChanged.emit()
        self._environment.append([key, ''])
        self._environment.sort()
        self.layoutChanged.emit()

    def flags(self, index):
        if not index.isValid():
            return
        flags = super(EnvironmentTableModel, self).flags(index)
        if index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        if not index.isValid() or index.column() != 1:
            return False
        self._environment[index.row()][1] = value
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        return self._environment[index.row()][index.column()]
