
from PySide2 import QtWidgets
from ncachefactory.qtutils import dock_window_to_tab
from ncachefactory.main import NCacheManager

import maya.OpenMayaUI as omui
from maya import cmds



_ncachemanager_window = None


def launch():
    global _ncachemanager_window
    if _ncachemanager_window is None:
        _ncachemanager_window = NCacheManager()
    _ncachemanager_window.show(dockable=True)
    dock_window_to_tab(_ncachemanager_window, "NEXDockControl")