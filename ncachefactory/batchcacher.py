
import os
from functools import partial

from PySide2 import QtWidgets, QtCore, QtGui
from maya import cmds

from ncachefactory.qtutils import get_icon
from ncachefactory.attributes import (
    list_wedgable_attributes, list_channelbox_highlited_plugs)
from ncachefactory.batch import (
    clean_batch_temp_folder, flash_current_scene, list_temp_multi_scenes,
    is_temp_folder_empty, BATCHCACHE_NAME, WEDGINGCACHE_NAME)
from ncachefactory.optionvars import (
    EXPLOSION_TOLERENCE_OPTIONVAR, EXPLOSION_DETECTION_OPTIONVAR,
    TIMELIMIT_ENABLED_OPTIONVAR, TIMELIMIT_OPTIONVAR, ensure_optionvars_exists)
from ncachefactory.arrayutils import compute_wedging_values


ATTRIBUTEPICKER_WINDOW_NAME = "Pick plug from selection"
VALUES_BUIDLER_NAME = "Values builder"


class BatchCacher(QtWidgets.QWidget):
    sendMultiCacheRequested = QtCore.Signal()
    sendMultiCacheSelectionRequested = QtCore.Signal()
    sendWedgingCacheRequested = QtCore.Signal()
    sendWedgingCacheSelectionRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(BatchCacher, self).__init__(parent)
        self.setFixedHeight(350)
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
        self.cache_selection = QtWidgets.QPushButton('Cache selection')
        self.cache_selection.setEnabled(False)
        method = self.sendMultiCacheSelectionRequested.emit
        self.cache_selection.released.connect(method)
        self.cache_all = QtWidgets.QPushButton('Cache all')
        self.cache_all.setEnabled(False)
        self.cache_all.released.connect(self.sendMultiCacheRequested.emit)

        self.menu_layout = QtWidgets.QHBoxLayout()
        self.menu_layout.addStretch(1)
        self.menu_layout.addWidget(self.toolbar)
        self.multicache = QtWidgets.QWidget()
        self.multicache_layout = QtWidgets.QVBoxLayout(self.multicache)
        self.multicache_layout.setSpacing(2)
        self.multicache_layout.addWidget(self.table)
        self.multicache_layout.addLayout(self.menu_layout)
        self.multicache_layout.addSpacing(4)
        self.multicache_layout.addWidget(self.cache_selection)
        self.multicache_layout.addWidget(self.cache_all)

        self._wedging_name = QtWidgets.QLineEdit()
        self._wedging_name.textEdited.connect(self.update_wedging_tabs_states)
        self._wedging_name.setText(WEDGINGCACHE_NAME)
        self._attribute = QtWidgets.QLineEdit()
        self._attribute.textEdited.connect(self.update_wedging_tabs_states)
        self._pick = QtWidgets.QPushButton(get_icon("pipette.png"), "")
        self._pick.setToolTip("Pick selected channel in channel editor")
        self._pick.setFixedSize(18, 18)
        self._pick.released.connect(self._call_pick_attribute)
        self._find = QtWidgets.QPushButton(get_icon("magnifyingglass.png"), "")
        self._find.setToolTip("Find attribute in selection")
        self._find.setFixedSize(18, 18)
        self._find.released.connect(self._call_find_attribute)
        self._values = QtWidgets.QLineEdit()
        self._values.textEdited.connect(self.update_wedging_tabs_states)
        self._values_builder = QtWidgets.QPushButton(get_icon("hammer.png"), "")
        self._values_builder.setToolTip("Build value list")
        self._values_builder.setFixedSize(18, 18)
        self._values_builder.released.connect(self._call_values_builder)

        self.cache_wedging = QtWidgets.QPushButton("Cache all")
        method = partial(self._send_wedging_cache, selection=False)
        self.cache_wedging.released.connect(method)
        self.cache_wedging.setEnabled(False)
        self.cache_wedging_selection = QtWidgets.QPushButton("Cache selection")
        method = partial(self._send_wedging_cache, selection=True)
        self.cache_wedging_selection.released.connect(method)
        self.cache_wedging_selection.setEnabled(False)

        self.attribute_layout = QtWidgets.QHBoxLayout()
        self.attribute_layout.setContentsMargins(0, 0, 0, 0)
        self.attribute_layout.setSpacing(0)
        self.attribute_layout.addWidget(self._attribute)
        self.attribute_layout.addWidget(self._pick)
        self.attribute_layout.addWidget(self._find)

        self.values_layout = QtWidgets.QHBoxLayout()
        self.values_layout.setContentsMargins(0, 0, 0, 0)
        self.values_layout.setSpacing(0)
        self.values_layout.addWidget(self._values)
        self.values_layout.addWidget(self._values_builder)

        self.wedging = QtWidgets.QWidget()
        self.wedging_form = QtWidgets.QFormLayout()
        self.wedging_form.setSpacing(2)
        self.wedging_form.addRow("Name", self._wedging_name)
        self.wedging_form.addRow("Attribute", self.attribute_layout)
        self.wedging_form.addRow("Values", self.values_layout)
        self.wedging_layout = QtWidgets.QVBoxLayout(self.wedging)
        self.wedging_layout.setSpacing(2)
        self.wedging_layout.addLayout(self.wedging_form)
        self.wedging_layout.addWidget(self.cache_wedging_selection)
        self.wedging_layout.addWidget(self.cache_wedging)

        self.tabwidget = QtWidgets.QTabWidget()
        self.tabwidget.addTab(self.multicache, "Multi scenes")
        self.tabwidget.addTab(self.wedging, "Attribute wedging")

        self.options = SimulationKillerOptions()
        self.options_layout = QtWidgets.QHBoxLayout()
        self.options_layout.addWidget(self.options)
        self.killer_group = QtWidgets.QGroupBox('Auto kill simulation options')
        self.killer_group.setLayout(self.options_layout)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tabwidget)
        self.layout.addWidget(self.killer_group)

    def set_workspace(self, workspace):
        self.workspace = workspace
        if self.model and self.model.jobs:
            self.model.clear_jobs()
        if is_temp_folder_empty(self.workspace):
            return
        if get_clean_tempfile_confirmation_dialog() is True:
            clean_batch_temp_folder(workspace)
            return
        for scene in list_temp_multi_scenes(self.workspace):
            job = {'name': BATCHCACHE_NAME, 'comment': '', 'scene': scene}
            self.model.add_job(job)
        self.cache_all.setEnabled(bool(self.model.jobs))
        self.cache_selection.setEnabled(bool(self.model.jobs))

    def clear(self):
        self.model.clear_jobs()
        self.cache_all.setEnabled(False)
        self.cache_selection.setEnabled(False)

    def update_wedging_tabs_states(self, *signals_args):
        enable = all([
            self._wedging_name.text() != "",
            cmds.objExists(self._attribute.text()),
            self._values.text().split(",") != [""],
            all([is_float(n) for n in self._values.text().split(",")])])
        self.cache_wedging.setEnabled(enable)
        self.cache_wedging_selection.setEnabled(enable)

    @property
    def jobs(self):
        return self.model.jobs

    @property
    def attribute(self):
        return self._attribute.text()

    @property
    def wedging_name(self):
        return self._wedging_name.text()

    @property
    def wedging_values(self):
        return map(float, self._values.text().split(","))

    def _call_remove_selected_jobs(self):
        jobs = self.table.selected_jobs
        if jobs is None:
            return
        for job in jobs:
            self.model.remove_job(job)
            os.remove(job['scene'])
        self.cache_all.setEnabled(bool(self.model.jobs))
        self.cache_selection.setEnabled(bool(self.model.jobs))

    def _call_flash_scene(self):
        if self.workspace is None:
            return
        scene = flash_current_scene(self.workspace)
        job = {'name': BATCHCACHE_NAME, 'comment': '', 'scene': scene}
        self.model.add_job(job)
        self.cache_all.setEnabled(bool(self.model.jobs))
        self.cache_selection.setEnabled(bool(self.model.jobs))

    def _call_find_attribute(self):
        dialog = AttributePicker()
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Rejected:
            return
        self._attribute.setText(dialog.plug)
        self.update_wedging_tabs_states()

    def _call_pick_attribute(self):
        plugs = list_channelbox_highlited_plugs()
        if not plugs:
            return cmds.warning('No plug selected in channelbox')
        self._attribute.setText(plugs[-1])
        self.update_wedging_tabs_states()

    def _call_values_builder(self):
        dialog = ValuesBuilder()
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Rejected:
            return
        self._values.setText(", ".join(map(str, dialog.values)))
        self.update_wedging_tabs_states()

    def _send_wedging_cache(self, selection=False):
        if not cmds.objExists(self._attribute.text()):
            return QtWidgets.QMessageBox.warning(
                None, "Error", "Attribute specified doesn't exists.")
        try:
            self.wedging_values
        except:
            return QtWidgets.QMessageBox.warning(
                None, "Error", "Invalid wedging values. Must be list of float")
        if selection is True:
            self.sendWedgingCacheSelectionRequested.emit()
        else:
            self.sendWedgingCacheRequested.emit()


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
        "Some old scenes aren't cleaned.\n"
        "Do you want to flush them ?")
    buttons = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
    result = QtWidgets.QMessageBox.question(
        None,
        'old scenes exist',
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
        self.layout.addRow("Stretch limit:", self._detect_explosion)
        self.layout.addRow("", self._explosion_widget)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow("Time limit:", self._timelimit_widget)

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


class ValuesBuilder(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ValuesBuilder, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(VALUES_BUIDLER_NAME)
        self._start_value = QtWidgets.QLineEdit()
        self._start_value.setValidator(QtGui.QDoubleValidator())
        self._end_value = QtWidgets.QLineEdit()
        self._end_value.setValidator(QtGui.QDoubleValidator())
        self._iterations = QtWidgets.QLineEdit()
        self._iterations.setText("3")
        validator = QtGui.QIntValidator()
        validator.setBottom(3)
        self._iterations.setValidator(validator)

        self.ok = QtWidgets.QPushButton("ok")
        self.ok.released.connect(self.accept)
        self.layout = QtWidgets.QFormLayout(self)
        self.layout.addRow("Start value", self._start_value)
        self.layout.addRow("End value", self._end_value)
        self.layout.addRow("Iteration", self._iterations)
        self.layout.addWidget(self.ok)

    @property
    def values(self):
        return compute_wedging_values(
            float(self._start_value.text()),
            float(self._end_value.text()),
            int(self._iterations.text()))


class AttributePicker(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AttributePicker, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(ATTRIBUTEPICKER_WINDOW_NAME)
        self.selection = QtWidgets.QListWidget()
        self.selection.itemSelectionChanged.connect(self.node_selected)
        self.selection.setFixedHeight(50)
        self.selection.addItems(cmds.ls(selection=True, dag=True))
        self.attributes = QtWidgets.QListWidget()
        self.ok = QtWidgets.QPushButton("ok")
        self.ok.released.connect(self.accept)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.selection)
        self.layout.addWidget(self.attributes)
        self.layout.addWidget(self.ok)

    def node_selected(self):
        self.attributes.clear()
        items = self.selection.selectedItems()
        if not items:
            return
        node = items[0].text()
        attributes = list_wedgable_attributes(node)
        self.attributes.addItems(attributes)

    @property
    def plug(self):
        items = self.selection.selectedItems()
        if not items:
            return
        node = items[0].text()
        items = self.attributes.selectedItems()
        if not items:
            return
        attribute = items[0].text()
        return node + "." + attribute


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
