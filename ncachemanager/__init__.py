
from PySide2 import QtWidgets
from ncachemanager.qtutils import get_maya_windows
from ncachemanager.main import NCacheManager


_ncachemanager_window = None


def launch():
    global _ncachemanager_window
    if _ncachemanager_window is None:
        _ncachemanager_window = NCacheManager()
    _ncachemanager_window.show(dockable=True)
