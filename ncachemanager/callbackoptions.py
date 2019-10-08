from PySide2 import QtCore, QtWidgets, QtGui
from maya import cmds
from ncachemanager.optionvars import (
    VERBOSE_OPTIONVAR, EXPLOSION_TOLERENCE_OPTIONVAR,
    EXPLOSION_DETECTION_OPTIONVAR, TIMELIMIT_ENABLED_OPTIONVAR,
    TIMELIMIT_OPTIONVAR, ensure_optionvars_exists)


class CallbackOptions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CallbackOptions, self).__init__(parent)

        self._verbose = QtWidgets.QCheckBox('verbose')
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
        self.layout.addRow("", self._verbose)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow("stretch limit:", self._detect_explosion)
        self.layout.addRow("", self._explosion_widget)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow("time limit:", self._timelimit_widget)

        self.set_optionvars()
        self.update_ui_states()
        self._verbose.stateChanged.connect(self.save_optionvars)
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
        value = cmds.optionVar(query=VERBOSE_OPTIONVAR)
        self._verbose.setChecked(value)
        value = cmds.optionVar(query=TIMELIMIT_ENABLED_OPTIONVAR)
        self._timelimit_enable.setChecked(value)
        value = cmds.optionVar(query=TIMELIMIT_OPTIONVAR)
        self._timelimit.setText(str(value))
        value = cmds.optionVar(query=EXPLOSION_DETECTION_OPTIONVAR)
        self._detect_explosion.setChecked(value)
        value = cmds.optionVar(query=EXPLOSION_TOLERENCE_OPTIONVAR)
        self._explosion_tolerance.setValue(value)

    def save_optionvars(self, *signals_args):
        value = self._verbose.isChecked()
        cmds.optionVar(intValue=[VERBOSE_OPTIONVAR, value])
        value = self._timelimit_enable.isChecked()
        cmds.optionVar(intValue=[TIMELIMIT_ENABLED_OPTIONVAR, value])
        value = int(self._timelimit.text())
        cmds.optionVar(intValue=[TIMELIMIT_OPTIONVAR, value])
        value = self._detect_explosion.isChecked()
        cmds.optionVar(intValue=[EXPLOSION_DETECTION_OPTIONVAR, value])
        value = self._explosion_tolerance.value()
        cmds.optionVar(intValue=[EXPLOSION_TOLERENCE_OPTIONVAR, value])

    @property
    def verbose(self):
        return self._verbose.isChecked()

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
