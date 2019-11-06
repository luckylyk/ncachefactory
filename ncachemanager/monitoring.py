import os
from math import ceil, sqrt
from PySide2 import QtWidgets, QtGui, QtCore
from ncachemanager.sequencereader import SequenceImageReader, ImageViewer
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
        self.process = process
        self.cacheversion = cacheversion
        self.logfile = get_log_filename(cacheversion)
        self.imagepath = []

        startframe = cacheversion.infos['start_frame']
        endframe = cacheversion.infos['end_frame']
        self.images = SequenceImageReader(range_=[startframe, endframe])
        self.log = InteractiveLog(filepath=self.logfile)

        self.splitter = QtWidgets.QSplitter()
        self.splitter.addWidget(self.images)
        self.splitter.addWidget(self.log)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.splitter)

    def update(self):
        if self.log.is_log_changed() is False:
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
