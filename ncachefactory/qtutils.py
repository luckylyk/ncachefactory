
import os
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtGui, QtWidgets, QtTest, QtCore
import maya.OpenMayaUI as omui


ICONPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons')


def get_icon(filename):
    return QtGui.QIcon(os.path.join(ICONPATH, filename))


def get_maya_windows():
    """
    Get the main Maya window as a QtWidgets.QMainWindow instance
    @return: QtWidgets.QMainWindow instance of the top level Maya windows
    """
    main_window = omui.MQtUtil.mainWindow()
    if main_window is not None:
        return wrapInstance(long(main_window), QtWidgets.QWidget)