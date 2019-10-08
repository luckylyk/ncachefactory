
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


def mayaui_to_qwidget(name):
    ptr = omui.MQtUtil.findControl(name)
    if ptr is None:
        ptr = omui.MQtUtil.findLayout(name)
    if ptr is None:
        ptr = omui.MQtUtil.findMenuItem(name)
    if ptr is not None:
        return wrapInstance(long(ptr), QtWidgets.QWidget)


def simulate_escape_key_pressed():
    QtTest.QTest.keyClick(get_maya_windows(), QtCore.Qt.Key_Escape)


def shoot(destination, mayaui_element_name):
    widget = mayaui_to_qwidget(mayaui_element_name)
    pixmap = QtGui.QPixmap.grabWindow(widget.winId())
    pixmap.save(destination, 'jpg')
