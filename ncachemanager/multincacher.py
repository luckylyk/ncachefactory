
import os
from PySide2 import QtWidgets, QtCore, QtGui
from maya import cmds
from ncachemanager.qtutils import get_icon
from ncachemanager.batch import (
    clean_batch_temp_folder, flash_current_scene, list_flashed_scenes,
    send_batch_ncache_jobs, is_temp_folder_empty)
from ncachemanager.optionvars import (
    EXPLOSION_TOLERENCE_OPTIONVAR, EXPLOSION_DETECTION_OPTIONVAR,
    TIMELIMIT_ENABLED_OPTIONVAR, TIMELIMIT_OPTIONVAR, ensure_optionvars_exists)


class MultiCacher(QtWidgets.QWidget):
    sendMultiCacheRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(MultiCacher, self).__init__(parent)
        self.workspace = None
        self.selection_model = None
        self.model = MultiCacheTableModel()
        self.table = MultiCacheTableView()
        self.table.set_model(self.model)

        self.flash = QtWidgets.QAction(get_icon("flash.png"), '', self)
        self.flash.setToolTip("Save current scene and add it to job queue")
        self.flash.triggered.connect(self._call_flash_scene)
        self.remove = QtWidgets.QAction(get_icon("trash.png"), '', self)
        self.remove.setToolTip("Remove selected scene from job queue")
        self.remove.triggered.connect(self._call_remove_selected_jobs)
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(15, 15))
        self.toolbar.addAction(self.flash)
        self.toolbar.addAction(self.remove)
        self.cache = QtWidgets.QPushButton('Cache')
        self.cache.released.connect(self.sendMultiCacheRequested.emit)

        self.killer_group = QtWidgets.QGroupBox('Auto kill simulation options')
        self.options = SimulationKillerOptions()

        self.menu_layout = QtWidgets.QHBoxLayout()
        self.menu_layout.addStretch(1)
        self.menu_layout.addWidget(self.toolbar)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.addWidget(self.table)
        self.layout.addLayout(self.menu_layout)
        self.layout.addSpacing(4)
        self.layout.addWidget(self.cache)
        self.layout.addWidget(self.options)

    def set_workspace(self, workspace):
        self.workspace = workspace
        if self.model and self.model.jobs:
            self.model.clear_jobs()
        if is_temp_folder_empty(self.workspace):
            return
        if get_clean_tempfile_confirmation_dialog() is True:
            clean_batch_temp_folder(workspace)
            return
        for scene in list_flashed_scenes(self.workspace):
            job = {'name': 'flashed scene', 'comment': '', 'scene': scene}
            self.model.add_job(job)

    def clear(self):
        self.model.clear_jobs()

    @property
    def jobs(self):
        return self.model.jobs

    def _call_remove_selected_jobs(self):
        jobs = self.table.selected_jobs
        for job in jobs:
            self.model.remove_job(job)
            os.remove(job[2])

    def _call_flash_scene(self):
        if self.workspace is None:
            return
        scene = flash_current_scene(self.workspace)
        job = {'name': 'flashed scene', 'comment': '', 'scene': scene}
        self.model.add_job(job)


class MultiCacheTableView(QtWidgets.QTableView):

    def __init__(self, parent=None):
        super(MultiCacheTableView, self).__init__(parent)
        self._model = None
        self._selection_model = None
        self.configure()

    def configure(self):
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        scrollmode = QtWidgets.QAbstractItemView.ScrollPerPixel
        self.setVerticalScrollMode(scrollmode)
        self.setHorizontalScrollMode(scrollmode)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.verticalHeader().setSectionResizeMode(mode)
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    @property
    def selected_jobs(self):
        if self._model is None:
            return
        indexes = self._selection_model.selectedIndexes()
        if not indexes:
            return None
        indexes = [i.row() for i in indexes if i.column() == 0]
        return [self._model.jobs[i] for i in indexes]

    def set_model(self, model):
        self.setModel(model)
        self._model = model
        self._selection_model = self.selectionModel()


class MultiCacheTableModel(QtCore.QAbstractTableModel):
    HEADERS = "Name", "Comment", "Scene"
    KEYS = "name", "comment", "scene"

    def __init__(self, parent=None):
        super(MultiCacheTableModel, self).__init__(parent)
        self.jobs = []

    def clear_jobs(self):
        self.layoutAboutToBeChanged.emit()
        self.jobs = []
        self.layoutChanged.emit()

    def add_job(self, job):
        self.layoutAboutToBeChanged.emit()
        self.jobs.append(job)
        self.layoutChanged.emit()

    def remove_job(self, job):
        self.layoutAboutToBeChanged.emit()
        self.jobs.remove(job)
        self.layoutChanged.emit()

    def columnCount(self, _=None):
        return len(self.HEADERS)

    def rowCount(self, _=None):
        return len(self.jobs)

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]
        else:
            return str(section + 1)

    def setData(self, index, data, role):
        if role != QtCore.Qt.EditRole:
            return
        row, column = index.row(), index.column()
        self.layoutAboutToBeChanged.emit()
        self.jobs[row][self.KEYS[column]] = data
        self.layoutChanged.emit()
        return True

    def flags(self, index):
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() < 2:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def data(self, index, role):
        if not index.isValid():
            return
        row, column = index.row(), index.column()
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return self.jobs[row][self.KEYS[column]]


def get_clean_tempfile_confirmation_dialog():
    message = (
        "Some flashed scenes already exists.\n"
        "Do you want to fush them ?")
    buttons = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
    result = QtWidgets.QMessageBox.question(
        None,
        'Exist flashed scene',
        message,
        buttons,
        QtWidgets.QMessageBox.Yes)
    return result == QtWidgets.QMessageBox.Yes


class SimulationKillerOptions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SimulationKillerOptions, self).__init__(parent)

        text = 'detect edge to streched (cloth only)'
        self._detect_explosion = QtWidgets.QCheckBox(text)
        self._explosion_tolerance = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._explosion_tolerance.setMinimum(2)
        self._explosion_tolerance.setMaximum(100)
        self._explosion_tolerance_label = QtWidgets.QLabel()

        self._explosion_widget = QtWidgets.QWidget()
        self._explosion_layout = QtWidgets.QHBoxLayout(self._explosion_widget)
        self._explosion_layout.setContentsMargins(0, 0, 0, 0)
        self._explosion_layout.addWidget(self._explosion_tolerance)
        self._explosion_layout.addWidget(self._explosion_tolerance_label)

        text = 'max seconds spent per frame'
        self._timelimit_enable = QtWidgets.QCheckBox(text)
        self._timelimit = QtWidgets.QLineEdit()
        self._timelimit.setMaxLength(5)
        self._timelimit.setValidator(QtGui.QIntValidator())
        self._timelimit.setFixedWidth(75)
        self._timelimit_widget = QtWidgets.QWidget()
        self._timelimit_layout = QtWidgets.QHBoxLayout(self._timelimit_widget)
        self._timelimit_layout.setContentsMargins(0, 0, 0, 0)
        self._timelimit_layout.addWidget(self._timelimit_enable)
        self._timelimit_layout.addWidget(self._timelimit)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.addRow("stretch limit:", self._detect_explosion)
        self.layout.addRow("", self._explosion_widget)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow("time limit:", self._timelimit_widget)

        self.set_optionvars()
        self.update_ui_states()
        self._detect_explosion.stateChanged.connect(self.save_optionvars)
        self._detect_explosion.stateChanged.connect(self.update_ui_states)
        self._explosion_tolerance.valueChanged.connect(self.save_optionvars)
        self._explosion_tolerance.valueChanged.connect(self.update_ui_states)
        self._timelimit_enable.stateChanged.connect(self.save_optionvars)
        self._timelimit_enable.stateChanged.connect(self.update_ui_states)
        self._timelimit.textEdited.connect(self.save_optionvars)

    def update_ui_states(self, *signals_args):
        state = self._detect_explosion.isChecked()
        self._explosion_tolerance.setEnabled(state)
        text = str(self._explosion_tolerance.value()).zfill(3)
        text += " * input edge length"
        self._explosion_tolerance_label.setText(text)
        state = self._timelimit_enable.isChecked()
        self._timelimit.setEnabled(state)

    def set_optionvars(self):
        ensure_optionvars_exists()
        value = cmds.optionVar(query=TIMELIMIT_ENABLED_OPTIONVAR)
        self._timelimit_enable.setChecked(value)
        value = cmds.optionVar(query=TIMELIMIT_OPTIONVAR)
        self._timelimit.setText(str(value))
        value = cmds.optionVar(query=EXPLOSION_DETECTION_OPTIONVAR)
        self._detect_explosion.setChecked(value)
        value = cmds.optionVar(query=EXPLOSION_TOLERENCE_OPTIONVAR)
        self._explosion_tolerance.setValue(value)

    def save_optionvars(self, *signals_args):
        value = self._timelimit_enable.isChecked()
        cmds.optionVar(intValue=[TIMELIMIT_ENABLED_OPTIONVAR, value])
        value = int(self._timelimit.text())
        cmds.optionVar(intValue=[TIMELIMIT_OPTIONVAR, value])
        value = self._detect_explosion.isChecked()
        cmds.optionVar(intValue=[EXPLOSION_DETECTION_OPTIONVAR, value])
        value = self._explosion_tolerance.value()
        cmds.optionVar(intValue=[EXPLOSION_TOLERENCE_OPTIONVAR, value])

    @property
    def detect_explosion(self):
        return self._detect_explosion.isChecked()

    @property
    def explosion_detection_tolerance(self):
        if self._detect_explosion.isChecked():
            return self._explosion_tolerance.value()
        return 0

    @property
    def timelimit(self):
        if not self._timelimit_enable.isChecked():
            return 0
        return int(self._timelimit.text())
