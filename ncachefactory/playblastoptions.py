from functools import partial
from PySide2 import QtCore, QtWidgets, QtGui
from maya import cmds
from ncachefactory.qtutils import get_icon
from ncachefactory.playblast import list_render_filter_options
from ncachefactory.optionvars import (
    RECORD_PLAYBLAST_OPTIONVAR, PLAYBLAST_RESOLUTION_OPTIONVAR,
    PLAYBLAST_VIEWPORT_OPTIONVAR)

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
        self.setFixedHeight(250)
        self._record_playblast = QtWidgets.QCheckBox('record playblast')
        self._camera = CamerasCombo()
        self._resolution = ResolutionSelecter()
        self._viewport_options = DisplayOptions()
        self._viewport_options.optionModified.connect(self.save_states)
        self._viewport_optios_scroll_area = QtWidgets.QScrollArea()
        self._viewport_optios_scroll_area.setWidget(self._viewport_options)
        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.addRow('', self._record_playblast)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow('camera: ', self._camera)
        self.layout.addRow('resolution: ', self._resolution)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        text = 'viewport options: '
        self.layout.addRow(text, self._viewport_optios_scroll_area)

        self.set_states()
        self._record_playblast.stateChanged.connect(self.save_states)
        self._resolution.width.textEdited.connect(self.save_states)
        self._resolution.height.textEdited.connect(self.save_states)

    def set_states(self):
        state = cmds.optionVar(query=RECORD_PLAYBLAST_OPTIONVAR)
        self._record_playblast.setChecked(state)

        resolution = cmds.optionVar(query=PLAYBLAST_RESOLUTION_OPTIONVAR)
        width, height = map(int, resolution.split('x'))
        self._resolution.set_resolution(width, height)

    def save_states(self):
        state = self._record_playblast.isChecked()
        cmds.optionVar(intValue=[RECORD_PLAYBLAST_OPTIONVAR, state])

        resolution = "x".join(map(str, self._resolution.resolution))
        cmds.optionVar(stringValue=[PLAYBLAST_RESOLUTION_OPTIONVAR, resolution])

        opt = ["1" if v is True else "0" for v in self._viewport_options.values]*
        opt = " ".join(opt)*
        cmds.optionVar(stringValue=[PLAYBLAST_VIEWPORT_OPTIONVAR, opt])

    def select_ffmpeg_path(self):
        ffmpeg = QtWidgets.QFileDialog.getOpenFileName()
        if not ffmpeg:
            return
        self._ffmpeg_path.setText(ffmpeg[0])
        self.save_states

    @property
    def viewport_options(self):
        return {
            'viewport_display_values': self._viewport_options.values,
            'width': self._resolution.resolution[0],
            'height': self._resolution.resolution[1],
            'camera': self._camera.currentText()}

    @property
    def record_playblast(self):
        return self._record_playblast.isChecked()


class CamerasCombo(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(CamerasCombo, self).__init__(parent)
        self._call_update()

    def _call_update(self):
        cameras = cmds.ls(type='camera')
        known_cameras = self.cameras()
        for camera in cameras:
            if camera not in known_cameras:
                self.addItem(camera)
        for camera in known_cameras:
            if camera not in cameras:
                index = self.text_index(camera)
                self.removeItem(index)

    def text_index(self, text):
        for i in range(self.count() + 1):
            if text == self.itemText(i):
                return i

    def cameras(self):
        return [self.itemText(i) for i in range(self.count() + 1)]

    def mousePressEvent(self, event):
        self._call_update()
        super(CamerasCombo, self).mousePressEvent(event)


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


class DisplayOptions(QtWidgets.QWidget):
    optionModified = QtCore.Signal()

    def __init__(self, parent=None):
        super(DisplayOptions, self).__init__(parent=parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.checkboxes = []
        for option, state in list_render_filter_options():
            checkbox = QtWidgets.QCheckBox(option)
            checkbox.released.connect(self.optionModified.emit)
            checkbox.option = option
            checkbox.setChecked(bool(state))
            self.checkboxes.append(checkbox)
            self.layout.addWidget(checkbox)

    @property
    def values(self):
        return [cb.isChecked() for cb in self.checkboxes]


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