
from PySide2 import QtWidgets
from ncachefactory.qtutils import dock_window_to_tab
from ncachefactory.main import NCacheManager

import maya.OpenMayaUI as omui
from maya import cmds


_ncachemanager_window = None


def launch():
    global _ncachemanager_window
    dock = False
    if _ncachemanager_window is None:
        dock = True
        _ncachemanager_window = NCacheManager()
    _ncachemanager_window.show(dockable=True)
    if dock is True:
        dock_window_to_tab(_ncachemanager_window, "NEXDockControl")