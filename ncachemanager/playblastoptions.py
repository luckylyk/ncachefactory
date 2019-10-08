from functools import partial
from PySide2 import QtCore, QtWidgets, QtGui
from maya import cmds
from ncachemanager.qtutils import get_icon
from ncachemanager.playblast import MODELEDITOR_OPTIONS
from ncachemanager.optionvars import (
    RECORD_PLAYBLAST_OPTIONVAR, PLAYBLAST_RESOLUTION_OPTIONVAR,
    FFMPEG_PATH_OPTIONVAR)


RESOLUTION_PRESETS = {
    "VGA 4:3": (640,480),
    "Amiga OCS PAL 5:3": (640, 512),
    "Wide VGA 8:5": (768, 480),
    "Wide VGA 5:3": (800, 480),
    "Wide PAL 16:9": (848, 480),
    "Super VGA 4:3": (800, 600),
    "PAL 16:9": (1024, 576),
    "Wide SVGA 16:9": (1024, 600),
    "720p Wide XGA": (1280, 720),
    "Wide XGA 8:5": (1280, 800),
    "Super XGA 4:3": (1280, 960),
    "Wide SXGA 8:5": (1440, 900),
    "Super XGA 5:4": (1280, 1024),
    "900p HD+ 16:9": (1600, 900),
    "Super XGA Plus 4:3": (1400, 1050),
    "HDV 1080i 4:3": (1440, 1080),
    "Wide SXGA+ 8:5": (1680, 1050),
    "Ultra XGA 4:3": (1600, 1200),
    "1080p Full HDTV 16:9": (1920, 1080),
    "DCI 2K 256:135": (2048, 1080),
    "Wide UXGA 8:5": (1920, 1200),
    "Full HD Plus 3:2": (1920, 1280),
    "UltraWide FHD 21:9": (2560, 1080),
    "Ultra-Wide 4K 2.35": (3840, 1600),
    "2160p 4K Ultra HD 16:9": (3840, 2160),
    "DCI 4K 256:135": (4096, 2160)
}


class PlayblastOptions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(PlayblastOptions, self).__init__(parent=parent)
        self._record_playblast = QtWidgets.QCheckBox('record playblast')

        self._ffmpeg_widget = QtWidgets.QWidget()
        self._ffmpeg_path = QtWidgets.QLineEdit()
        self._ffmpeg_browse = QtWidgets.QPushButton(get_icon("folder.png"), "")
        self._ffmpeg_browse.setFixedSize(22, 22)
        self._ffmpeg_browse.released.connect(self.select_ffmpeg_path)
        self._ffmpeg_layout = QtWidgets.QHBoxLayout(self._ffmpeg_widget)
        self._ffmpeg_layout.setContentsMargins(0, 0, 0, 0)
        self._ffmpeg_layout.addWidget(self._ffmpeg_path)
        self._ffmpeg_layout.addWidget(self._ffmpeg_browse)

        self._resolution = ResolutionSelecter()
        self._viewport_options = ViewportOptions()
        self._viewport_optios_scroll_area = QtWidgets.QScrollArea()
        self._viewport_optios_scroll_area.setWidget(self._viewport_options)
        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.addRow('', self._record_playblast)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow('ffmpeg path: ', self._ffmpeg_widget)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow('resolution: ', self._resolution)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        text = 'viewport options: '
        self.layout.addRow(text, self._viewport_optios_scroll_area)

        self.set_states()
        self._record_playblast.stateChanged.connect(self.save_states)
        self._resolution.width.textEdited.connect(self.save_states)
        self._resolution.height.textEdited.connect(self.save_states)
        self._ffmpeg_path.textChanged.connect(self.save_states)

    def set_states(self):
        state = cmds.optionVar(query=RECORD_PLAYBLAST_OPTIONVAR)
        self._record_playblast.setChecked(state)
        text = cmds.optionVar(query=FFMPEG_PATH_OPTIONVAR)
        self._ffmpeg_path.setText(text)
        resolution = cmds.optionVar(query=PLAYBLAST_RESOLUTION_OPTIONVAR)
        width, height = map(int, resolution.split('x'))
        self._resolution.set_resolution(width, height)

    def save_states(self):
        state = self._record_playblast.isChecked()
        cmds.optionVar(intValue=[RECORD_PLAYBLAST_OPTIONVAR, state])
        text = self._ffmpeg_path.text()
        cmds.optionVar(stringValue=[FFMPEG_PATH_OPTIONVAR, text])
        resolution = "x".join(map(str, self._resolution.resolution))
        cmds.optionVar(stringValue=[PLAYBLAST_RESOLUTION_OPTIONVAR, resolution])

    def select_ffmpeg_path(self):
        ffmpeg = QtWidgets.QFileDialog.getOpenFileName()
        if not ffmpeg:
            return
        self._ffmpeg_path.setText(ffmpeg[0])
        self.save_states

    @property
    def viewport_options(self):
        options = self._viewport_options.options
        options['width'] = self._resolution.resolution[0]
        options['height'] = self._resolution.resolution[1]
        return options

    @property
    def record_playblast(self):
        return self._record_playblast.isChecked()


class ResolutionSelecter(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ResolutionSelecter, self).__init__(parent=parent)
        self.select_preset = QtWidgets.QPushButton('select presets')
        self.resolution_preset_menu = ResolutionPresetsMenu(self.select_preset)
        func = self.set_resolution
        self.resolution_preset_menu.widthHeightTriggered.connect(func)
        self.select_preset.setMenu(self.resolution_preset_menu)

        self.width = QtWidgets.QLineEdit()
        self.width.setFixedWidth(50)
        self.width.setMaxLength(5)
        self.width.setValidator(QtGui.QIntValidator())
        self.height = QtWidgets.QLineEdit()
        self.height.setFixedWidth(50)
        self.height.setMaxLength(5)
        self.height.setValidator(QtGui.QIntValidator())
        self.wh_layout = QtWidgets.QHBoxLayout()
        self.wh_layout.setContentsMargins(0, 0, 0, 0)
        self.wh_layout.setSpacing(2)
        self.wh_layout.addWidget(QtWidgets.QLabel("width"))
        self.wh_layout.addWidget(self.width)
        self.wh_layout.addSpacing(15)
        self.wh_layout.addWidget(QtWidgets.QLabel("height"))
        self.wh_layout.addWidget(self.height)
        self.wh_layout.addStretch(1.0)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.select_preset)
        self.layout.addLayout(self.wh_layout)

    def set_resolution(self, width, height):
        self.width.setText(str(width))
        self.height.setText(str(height))

    @property
    def resolution(self):
        return int(self.width.text()), int(self.height.text())


class ViewportOptions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ViewportOptions, self).__init__(parent=parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.checkboxes = []
        for option, state in MODELEDITOR_OPTIONS.items():
            if not isinstance(state, bool):
                return
            nicename = "".join([l if l.lower() else " " + l for l in option])
            checkbox = QtWidgets.QCheckBox(nicename)
            checkbox.option = option
            checkbox.setChecked(state)
            self.checkboxes.append(checkbox)
            self.layout.addWidget(checkbox)

    @property
    def options(self):
        return {cb.option: cb.isChecked() for cb in self.checkboxes}


class ResolutionPresetsMenu(QtWidgets.QMenu):
    widthHeightTriggered = QtCore.Signal(int, int)

    def __init__(self, parent=None):
        super(ResolutionPresetsMenu, self).__init__(parent=parent)
        self.width = None
        self.height = None

        keys = sorted(RESOLUTION_PRESETS, key=lambda x: RESOLUTION_PRESETS[x][0])
        for key in keys:
            width, height = RESOLUTION_PRESETS[key]
            name = "{}x{} | {}".format(width, height, key)
            action = QtWidgets.QAction(name, self)
            func = partial(self.set_resolution, width, height)
            action.triggered.connect(func)
            self.addAction(action)

    def set_resolution(self, width, height):
        self.widthHeightTriggered.emit(width, height)