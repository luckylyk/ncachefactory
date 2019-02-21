
import os
import shiboken2
from PySide2 import QtWidgets, QtGui
import maya.OpenMayaUI as omui


def get_maya_windows():
    """
    Get the main Maya window as a QtWidgets.QMainWindow instance
    @return: QtWidgets.QMainWindow instance of the top level Maya windows
    """
    main_window = omui.MQtUtil.mainWindow()
    if main_window is not None:
        return shiboken2.wrapInstance(long(main_window), QtWidgets.QWidget)


ICONPATH = os.path.join(os.path.dirname(os.realpath(__file__)), 'icons')

def get_icon(filename):
    return QtGui.QIcon(os.path.join(ICONPATH, filename))