
import os
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtGui, QtWidgets, QtCore
import maya.OpenMayaUI as omui
from maya import cmds


ICONPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'icons')


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


def dock_window_to_tab(window, tabname):
    workspaceControlName = window.objectName() + 'WorkspaceControl'
    try:
        cmds.deleteUI(workspaceControlName)
    except RuntimeError:
        # ui doesn't exists yet, we don't care
        pass

    workspaceControlName = cmds.workspaceControl(
        workspaceControlName, label=window.windowTitle(),
        tabToControl=[tabname, -1], initialWidth=420, minimumWidth=True,
        widthProperty="preferred", heightProperty="free")

    currParent = omui.MQtUtil.getCurrentParent()
    mixinPtr = omui.MQtUtil.findControl(window.objectName())
    if mixinPtr is not None:
        omui.MQtUtil.addWidgetToMayaLayout(long(mixinPtr), long(currParent))