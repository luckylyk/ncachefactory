from maya import cmds
from PySide2 import QtWidgets, QtGui, QtCore
from ncachefactory.optionvars import (
    RANGETYPE_OPTIONVAR, CACHE_BEHAVIOR_OPTIONVAR, VERBOSE_OPTIONVAR,
    VERBOSE_OPTIONVAR, SAMPLES_EVALUATED_OPTIONVAR, SAMPLES_SAVED_OPTIONVAR,
    ensure_optionvars_exists)


BLENDMODE_LABELS = (
    "Clear all existing cache nodes and blend \n"
    "nodes before the new cache. (default)",
    "Clear all existing cache nodes but blend \n"
    "the new caches if old ones are already \n"
    "connected to blend nodes.",
    "Doesn't clear anything and blend the \n"
    "new cache with all existing nodes.")


class CacheOptions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CacheOptions, self).__init__(parent)
        self._verbose = QtWidgets.QCheckBox('verbose')
        self._rangetype_timeline = QtWidgets.QRadioButton('timeline')
        self._rangetype_custom = QtWidgets.QRadioButton('custom range')
        self._rangetype = QtWidgets.QButtonGroup()
        self._rangetype.addButton(self._rangetype_timeline, 0)
        self._rangetype.addButton(self._rangetype_custom, 1)
        self._rangein = QtWidgets.QLineEdit('0')
        self._rangein.setMaxLength(5)
        self._rangein.setFixedWidth(60)
        self._rangein.setValidator(QtGui.QIntValidator())
        self._rangeout = QtWidgets.QLineEdit('100')
        self._rangeout.setMaxLength(5)
        self._rangeout.setFixedWidth(60)
        self._rangeout.setValidator(QtGui.QIntValidator())
        self._behavior_clear = QtWidgets.QRadioButton(BLENDMODE_LABELS[0])
        self._behavior_blend = QtWidgets.QRadioButton(BLENDMODE_LABELS[1])
        self._behavior_force_blend = QtWidgets.QRadioButton(BLENDMODE_LABELS[2])
        self._behavior = QtWidgets.QButtonGroup()
        self._behavior.addButton(self._behavior_clear, 0)
        self._behavior.addButton(self._behavior_blend, 1)
        self._behavior.addButton(self._behavior_force_blend, 2)
        self._samples_evaluated = QtWidgets.QLineEdit()
        self._samples_evaluated.setValidator(QtGui.QDoubleValidator())
        self._samples_evaluated.setFixedWidth(60)
        self._samples_recorded = QtWidgets.QLineEdit()
        self._samples_recorded.setValidator(QtGui.QIntValidator())
        self._samples_recorded.setFixedWidth(60)

        self._custom_range = QtWidgets.QWidget()
        self._range_layout = QtWidgets.QHBoxLayout(self._custom_range)
        self._range_layout.addWidget(self._rangein)
        self._range_layout.addWidget(self._rangeout)
        self._range_layout.addStretch(1)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.addRow("", self._verbose)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow("Range: ", self._rangetype_timeline)
        self.layout.addRow("", self._rangetype_custom)
        self.layout.addRow("", self._custom_range)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow("Attach method: ", self._behavior_clear)
        self.layout.addRow("", self._behavior_blend)
        self.layout.addRow("", self._behavior_force_blend)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 10))
        self.layout.addRow("Evaluation sample: ", self._samples_evaluated)
        self.layout.addRow("Save every evaluation(s): ", self._samples_recorded)

        self.set_optionvars()
        self.update_ui_states()
        self._verbose.stateChanged.connect(self.save_optionvars)
        self._rangetype.buttonToggled.connect(self.save_optionvars)
        self._rangetype.buttonToggled.connect(self.update_ui_states)
        self._behavior.buttonToggled.connect(self.save_optionvars)
        self._samples_evaluated.textEdited.connect(self.save_optionvars)
        self._samples_recorded.textEdited.connect(self.save_optionvars)

    def update_ui_states(self, *signals_args):
        self._custom_range.setEnabled(bool(self._rangetype.checkedId()))

    def set_optionvars(self):
        ensure_optionvars_exists()
        value = cmds.optionVar(query=VERBOSE_OPTIONVAR)
        self._verbose.setChecked(value)
        id_ = cmds.optionVar(query=RANGETYPE_OPTIONVAR)
        button = self._rangetype.button(id_)
        button.setChecked(True)
        id_ = cmds.optionVar(query=CACHE_BEHAVIOR_OPTIONVAR)
        button = self._behavior.button(id_)
        button.setChecked(True)
        value = cmds.optionVar(query=SAMPLES_EVALUATED_OPTIONVAR)
        self._samples_evaluated.setText(str(value))
        value = cmds.optionVar(query=SAMPLES_SAVED_OPTIONVAR)
        self._samples_recorded.setText(str(value))

    def save_optionvars(self, *signals_args):
        value = self._verbose.isChecked()
        cmds.optionVar(intValue=[VERBOSE_OPTIONVAR, value])
        value = self._rangetype.checkedId()
        cmds.optionVar(intValue=[RANGETYPE_OPTIONVAR, value])
        value = self._behavior.checkedId()
        cmds.optionVar(intValue=[CACHE_BEHAVIOR_OPTIONVAR, value])
        value = float(self._samples_recorded.text())
        cmds.optionVar(floatValue=[SAMPLES_EVALUATED_OPTIONVAR, value])
        value = int(self._samples_recorded.text())
        cmds.optionVar(intValue=[SAMPLES_SAVED_OPTIONVAR, value])

    @property
    def range(self):
        if self._rangetype.checkedId() == 0:
            startframe = int(cmds.playbackOptions(minTime=True, query=True))
            endframe = int(cmds.playbackOptions(maxTime=True, query=True))
        else:
            startframe = int(self._rangein.text())
            endframe = int(self._rangeout.text())
        return startframe, endframe

    @property
    def behavior(self):
        return self._behavior.checkedId()

    @property
    def verbose(self):
        return self._verbose.isChecked()

    @property
    def samples_evaluated(self):
        return float(self._samples_evaluated.text())

    @property
    def samples_recorded(self):
        return int(self._samples_recorded.text())