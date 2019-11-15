import os
from math import ceil, sqrt
from PySide2 import QtWidgets, QtGui, QtCore
from maya import cmds
from ncachemanager.sequencereader import SequenceImageReader, ImageViewer
from ncachemanager.playblast import compile_movie
from ncachemanager.api import connect_cacheversion
from ncachemanager.ncache import list_connected_cachefiles
from ncachemanager.versioning import (
    get_log_filename, list_tmp_jpeg_under_cacheversion)

WINDOW_TITLE = "Multi NCache Monitoring"


class MultiCacheMonitor(QtWidgets.QWidget):
    def __init__(self, cacheversions, processes, parent=None):
        super(MultiCacheMonitor, self).__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle(WINDOW_TITLE)
        self.tab_widget = QtWidgets.QTabWidget()
        self.job_panels = []

        for cacheversion, process in zip(cacheversions, processes):
            job_panel = JobPanel(cacheversion, process)
            self.job_panels.append(job_panel)
            self.tab_widget.addTab(job_panel, cacheversion.name)
        imageviewers = [jp.images.image for jp in self.job_panels]
        names = [cv.name for cv in cacheversions]
        # Add a multi cache monitoring only if there's more than one cache job
        # sent.
        if len(cacheversions) > 1:
            self.monitor = Monitor(names=names, imageviewers=imageviewers)
            self.tab_widget.insertTab(0, self.monitor, 'Monitor')
            self.tab_widget.setCurrentIndex(0)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.addWidget(self.tab_widget)

        self.timer = QtCore.QBasicTimer()
        self.timer.start(1000, self)

    def closeEvent(self, *event):
        super(MultiCacheMonitor, self).closeEvent(*event)
        self.timer.stop()

    def timerEvent(self, event):
        for job_panel in self.job_panels:
            job_panel.update()


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
    def __init__(self, cacheversion, process, parent=None):
        super(JobPanel, self).__init__(parent)
        self.finished = False
        self.process = process
        self.cacheversion = cacheversion
        self.logfile = get_log_filename(cacheversion)
        self.imagepath = []

        startframe = cacheversion.infos['start_frame']
        endframe = cacheversion.infos['end_frame']
        self.images = SequenceImageReader(range_=[startframe, endframe])
        self.log = InteractiveLog(filepath=self.logfile)
        self.kill = QtWidgets.QPushButton('kill')
        self.kill.released.connect(self._call_kill)
        self.connect_cache = QtWidgets.QPushButton('connect cache')
        self.connect_cache.released.connect(self._call_connect_cache)
        self.log_widget = QtWidgets.QWidget()
        self.log_layout = QtWidgets.QVBoxLayout(self.log_widget)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(2)
        self.log_layout.addWidget(self.log)
        self.log_layout.addWidget(self.connect_cache)
        self.log_layout.addWidget(self.kill)

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
        for jpeg in list_tmp_jpeg_under_cacheversion(self.cacheversion):
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
        if self.images.isfull() is True:
            self.finished = True
            self.images.finish()
            self.kill.setEnabled(False)

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
        if self.finished is True:
            return
        self.finished = True
        self.process.kill()
        self.images.kill()
        images = list_tmp_jpeg_under_cacheversion(self.cacheversion)
        source = compile_movie(images)
        for image in images:
            os.remove(image)
        directory = self.cacheversion.directory
        destination = os.path.join(directory, os.path.basename(source))
        os.rename(source, destination)
        self.kill.setEnabled(False)


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
