import os
from math import ceil, sqrt
from PySide2 import QtWidgets, QtGui, QtCore
from maya import cmds

from ncachefactory.playblast import compile_movie
from ncachefactory.cachemanager import connect_cacheversion
from ncachefactory.ncache import list_connected_cachefiles
from ncachefactory.arrayutils import overlap_lists_from_ranges, range_ranges
from ncachefactory.sequencereader import (
    SequenceImageReader, ImageViewer, SequenceStackedImagesReader)
from ncachefactory.versioning import (
    get_log_filename, list_tmp_jpeg_under_cacheversion)


WINDOW_TITLE = "Batch cacher monitoring"
CACHEVERSION_SELECTION_TITLE = "Select cache to compare"


class MultiCacheMonitor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MultiCacheMonitor, self).__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle(WINDOW_TITLE)
        self.comparators = []
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.tab_closed)
        self.job_panels = []

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.addWidget(self.tab_widget)

        self.timer = QtCore.QBasicTimer()
        self.updater = wooden_legged_centipede(47)

    def tab_closed(self, index):
        self.tab_widget.widget(index).kill()
        self.tab_widget.removeTab(index)
        self.job_panels.pop(index)

    def add_job(self, cacheversion, process):
        job_panel = JobPanel(cacheversion, process)
        job_panel.comparisonRequested.connect(self._call_comparison)
        self.job_panels.append(job_panel)
        self.tab_widget.addTab(job_panel, cacheversion.name)
        self.tab_widget.setCurrentIndex(len(self.job_panels) - 1)

    def showEvent(self, *events):
        super(MultiCacheMonitor, self).showEvent(*events)
        self.timer.start(47, self)

    def closeEvent(self, *events):
        super(MultiCacheMonitor, self).closeEvent(*events)
        self.timer.stop()
        kill_them_all = None
        for job_panel in self.job_panels:
            if not job_panel.finished:
                if kill_them_all is None:
                    kill_them_all = kill_them_all_confirmation_dialog()
                if kill_them_all is True:
                    job_panel.kill()

    def timerEvent(self, event):
        current_job_panel = self.job_panels[self.tab_widget.currentIndex()]
        if current_job_panel.is_playing:
            current_job_panel.images.set_next_image()
            return

        if next(self.updater) is True:
            for job_panel in self.job_panels:
                job_panel.update()

    def _call_comparison(self, job_panel):
        cacheversions = [jp.cacheversion for jp in self.job_panels]
        names = [cv.name for cv in cacheversions]
        dialog = CacheVersionSelection(names=names)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Rejected or dialog.index is None:
            return
        job_panel2 = self.job_panels[dialog.index]
        names = job_panel.cacheversion.name, job_panel2.cacheversion.name
        slider = job_panel.images.slider
        range1 = slider.minimum, slider.maximum_settable_value
        slider = job_panel2.images.slider
        range2 = slider.minimum, slider.maximum_settable_value
        pixmaps1, pixmaps2 = overlap_lists_from_ranges(
            elements1=job_panel.images._pixmaps,
            elements2=job_panel2.images._pixmaps,
            range1=range1,
            range2=range2)
        frames = range_ranges(range1, range2)
        comparator = SequenceStackedImagesReader(
            pixmaps1=pixmaps1,
            pixmaps2=pixmaps2,
            frames=frames,
            names=names)
        comparator.show()
        self.comparators.append(comparator)


class Monitor(QtWidgets.QWidget):
    def __init__(self, names, imageviewers, parent=None):
        super(Monitor, self).__init__(parent)
        self.imageviewers = []
        for name, imageviewer_master in zip(names, imageviewers):
            imageviewer = ImageViewer(name=name)
            imageviewer_master.imageChanged.connect(imageviewer.set_image)
            self.imageviewers.append(imageviewer)
        self.layout = QtWidgets.QGridLayout(self)
        row = 0
        column = 0
        column_lenght = ceil(sqrt(len(self.imageviewers)))
        for imageviewer in self.imageviewers:
            self.layout.addWidget(imageviewer, row, column)
            column += 1
            if column >= column_lenght:
                column = 0
                row += 1


class JobPanel(QtWidgets.QWidget):
    comparisonRequested = QtCore.Signal(object)

    def __init__(self, cacheversion, process, parent=None):
        super(JobPanel, self).__init__(parent)
        self.finished = False
        self.is_playing = False
        self.process = process
        self.cacheversion = cacheversion
        self.logfile = get_log_filename(cacheversion)
        self.imagepath = []

        startframe = cacheversion.infos['start_frame']
        endframe = cacheversion.infos['end_frame']
        self.images = SequenceImageReader(range_=[startframe, endframe])
        self.log = InteractiveLog(filepath=self.logfile)
        self.compare = QtWidgets.QPushButton('compare with')
        self.compare.setEnabled(False)
        self.compare.released.connect(self._call_compare)
        self.kill_button = QtWidgets.QPushButton('kill')
        self.kill_button.released.connect(self._call_kill)
        self.connect_cache = QtWidgets.QPushButton('connect cache')
        self.connect_cache.released.connect(self._call_connect_cache)
        self.connect_cache.setEnabled(False)
        self.playstop = QtWidgets.QPushButton("play")
        self.playstop.setEnabled(False)
        self.playstop.released.connect(self._call_playstop)
        self.log_widget = QtWidgets.QWidget()
        self.log_layout = QtWidgets.QVBoxLayout(self.log_widget)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(2)
        self.log_layout.addWidget(self.log)
        self.log_layout.addWidget(self.compare)
        self.log_layout.addWidget(self.connect_cache)
        self.log_layout.addWidget(self.kill_button)
        self.log_layout.addWidget(self.playstop)

        self.splitter = QtWidgets.QSplitter()
        self.splitter.addWidget(self.images)
        self.splitter.addWidget(self.log_widget)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.splitter)

    def update(self):
        if self.log.is_log_changed() is False or self.finished is True:
            return
        self.log.update()
        jpegs = list_tmp_jpeg_under_cacheversion(self.cacheversion)
        for jpeg in jpegs:
            # often, jpeg files are listed before to be fully written or the
            # file pysically exist. This create null pixmap and the viewport
            # has dead frames. Those checks stop the update in case of issue
            # forcing the new files to be add on next update.
            if jpeg not in self.imagepath and os.path.exists(jpeg):
                pixmap = QtGui.QPixmap(jpeg)
                if pixmap.isNull():
                    break
                self.imagepath.append(jpeg)
                self.images.add_pixmap(pixmap)

        if jpegs:
            # allow to use option which need at least one frame cached
            if self.connect_cache.isEnabled() is False:
                self.connect_cache.setEnabled(True)
            if self.playstop.isEnabled() is False :
                self.playstop.setEnabled(True)
            if self.compare.isEnabled() is False:
                self.compare.setEnabled(True)

        if self.images.isfull() is True:
            self.finished = True
            self.images.finish()
            self.kill_button.setEnabled(False)

    def _call_connect_cache(self):
        startframe = self.cacheversion.infos['start_frame']
        endframe = self.cacheversion.infos['end_frame']
        connect_cacheversion(self.cacheversion)
        cachenodes = list_connected_cachefiles()
        # because that connect a cache with is currently caching from
        # an external maya, that change the start frame and end frame of
        # the cache file node. That allow an interactive update of the
        # cache when each frame is cached.
        for cachenode in cachenodes:
            cmds.setAttr(cachenode + '.sourceStart', startframe)
            cmds.setAttr(cachenode + '.originalStart', startframe)
            cmds.setAttr(cachenode + '.originalEnd', endframe)
            cmds.setAttr(cachenode + '.sourceEnd', endframe)

    def _call_kill(self):
        self.kill()
        self.kill_button.setEnabled(False)

    def _call_playstop(self):
        self.is_playing = not self.is_playing
        self.playstop.setText("stop" if self.is_playing else "play")

    def _call_compare(self):
        self.comparisonRequested.emit(self)

    def kill(self):
        if self.finished is True:
            return
        self.finished = True
        self.process.kill()
        self.images.kill()
        images = list_tmp_jpeg_under_cacheversion(self.cacheversion)
        # if the cache is not started yet, no images are already recorded
        if not images:
            return
        source = compile_movie(images)
        for image in images:
            os.remove(image)
        directory = self.cacheversion.directory
        destination = os.path.join(directory, os.path.basename(source))
        os.rename(source, destination)


class InteractiveLog(QtWidgets.QWidget):
    def __init__(self, parent=None, filepath=''):
        super(InteractiveLog, self).__init__(parent)
        self.logsize = None
        self.document = QtGui.QTextDocument()
        self.text = QtWidgets.QTextEdit()
        self.text.setReadOnly(True)
        self.text.setDocument(self.document)
        self.filepath = filepath
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.text)

    def is_log_changed(self):
        # This is an otpimization. To check if the logfile changed, that
        # compare the logfile size stored durung last update called.
        if not os.path.exists(self.filepath):
            return False
        logsize = os.path.getsize(self.filepath)
        if logsize == self.logsize:
            return False
        self.logsize = logsize
        return True

    def update(self):
        with open(self.filepath, "r") as f:
            content = f.read()
            self.document.setPlainText(content)
        scrollbar = self.text.verticalScrollBar()
        scrollbar.setSliderPosition(scrollbar.maximum())
        return True


class CacheVersionSelection(QtWidgets.QDialog):
    def __init__(self, names, parent=None):
        super(CacheVersionSelection, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(CACHEVERSION_SELECTION_TITLE)
        self.list = QtWidgets.QListWidget()
        self.list.addItems(names)
        self.ok = QtWidgets.QPushButton("ok")
        self.ok.released.connect(self.accept)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.list)
        self.layout.addWidget(self.ok)

    @property
    def index(self):
        indexes = [i.row() for i in self.list.selectedIndexes()]
        if not indexes:
            return
        return indexes[0]


def kill_them_all_confirmation_dialog():
    message = (
        "Some caching processes still running, do you want to kill them all ?")
    buttons = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
    result = QtWidgets.QMessageBox.question(
        None,
        'Cache running',
        message,
        buttons,
        QtWidgets.QMessageBox.Yes)
    return result == QtWidgets.QMessageBox.Yes


def wooden_legged_centipede(leg_number):
    """ Sorry for the metaphorical name, didn't find something more explicite.
    This is an iterator which return False everytime except when the cycle
    reach the specified number, then it returns True, and the cycle restart"""
    leg = 0
    while True:
        if leg > leg_number:
            leg = 0
        yield leg == leg_number
        leg += 1
