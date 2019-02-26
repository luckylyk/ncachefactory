from PySide2 import QtWidgets


VIEWPORT_ACTIVE_OPTIONVAR = 'ncachemanager_viewportactive'
RANGETYPE_OPTIONVAR = 'ncachemanager_rangetype'
CUSTOM_RANGE_OPTIONVAR = 'ncachemanager_customrange'
CACHE_BEHAVIOR_OPTIONVAR = 'ncachemanager_behavior'

BLENDMODE_LABELS = (
    "Clear all existing cache nodes and blend nodes "
    "before the new cache (default)",
    "Clear all existing cache nodes but blend "
    "the new caches if old ones are already connected to blend nodes",
    "Doesn't clear anything and blend the new cache with all existing nodes")


class CacheOptions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CacheOptions, self).__init__(parent)
        self.viewport = QtWidgets.QCheckBox("Viewport active during the cache")
        self.rangetype_timeline = QtWidgets.QRadioButton('active timeline')
        self.rangetype_custom = QtWidgets.QRadioButton('custom range')
        self.rangetype = QtWidgets.QButtonGroup()
        self.rangetype.addButton(self.rangetype_timeline, 0)
        self.rangetype.addButton(self.rangetype_custom, 1)
        self.behavior_clear = QtWidgets.QRadioButton(BLENDMODE_LABELS[0])
        self.behavior_blend = QtWidgets.QRadioButton(BLENDMODE_LABELS[1])
        self.behavior_force_blend = QtWidgets.QRadioButton(BLENDMODE_LABELS[2])
        self.behavior = QtWidgets.QButtonGroup()
        self.behavior.addButton(self.behavior_clear, 0)
        self.behavior.addButton(self.behavior_blend, 1)
        self.behavior.addButton(self.behavior_force_blend, 2)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.addRow("", self.viewport)
        self.layout.addRow("Range: ", self.rangetype_timeline)
        self.layout.addRow("", self.rangetype_custom)
        self.layout.addRow("Attach method: ", self.behavior_clear)
        self.layout.addRow("", self.behavior_blend)
        self.layout.addRow("", self.behavior_force_blend)