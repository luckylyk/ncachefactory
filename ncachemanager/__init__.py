
from PySide2 import QtWidgets
from ncachemanager.qtutils import get_maya_windows
from ncachemanager.main import NCacheManager


_ncachemanager_window = None


def launch():
    if _ncachemanager_window is None:
        global _ncachemanager_window
        _ncachemanager_window = NCacheManager(get_maya_windows())
    _ncachemanager_window.show()

