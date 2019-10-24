
import os
from PySide2 import QtWidgets, QtCore
from ncachemanager.batch import (
    clean_batch_temp_folder, flash_current_scene,
    send_batch_ncache_jobs)


class MultiCacher(QtWidgets.QWidget):
    sendMultiCacheRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(MultiCacher, self).__init__(parent)
        self.workspace = None
        self.selection_model = None
        self.model = MultiCacheTableModel()
        self.table = MultiCacheTableView()
        self.table.set_model(self.model)
        self.flash = QtWidgets.QPushButton('flash scene')
        self.flash.released.connect(self._call_flash_scene)
        self.remove = QtWidgets.QPushButton('remove selected flash')
        self.remove.released.connect(self._call_remove_selected_jobs)
        self.start_all = QtWidgets.QPushButton('start multi caching all nodes')
        self.start_all.released.connect(self.sendMultiCacheRequested.emit)
        self.start_sel = QtWidgets.QPushButton('start multi caching selection')

        self.table_buttons_layout = QtWidgets.QHBoxLayout()
        self.table_buttons_layout.setSpacing(2)
        self.table_buttons_layout.addStretch(1)
        self.table_buttons_layout.addWidget(self.flash)
        self.table_buttons_layout.addWidget(self.remove)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.addWidget(self.table)
        self.layout.addLayout(self.table_buttons_layout)
        self.layout.addSpacing(4)
        self.layout.addWidget(self.start_all)
        self.layout.addWidget(self.start_sel)

    def set_workspace(self, workspace):
        self.workspace = workspace
        if self.model and self.model.jobs:
            clean_batch_temp_folder(workspace)
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
        self.jobs[row][column] = data

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
