
from PySide2 import QtWidgets
from ncachefactory.qtutils import get_maya_windows
from ncachefactory.main import NCacheManager


_ncachemanager_window = None


def launch():
    global _ncachemanager_window
    if _ncachemanager_window is None:
        _ncachemanager_window = NCacheManager()
    _ncachemanager_window.show(dockable=True)
