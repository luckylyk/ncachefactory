
import os
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtGui, QtWidgets, QtCore
import maya.OpenMayaUI as omui
from maya import cmds


ICONPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'icons')


def get_icon(filename):
    return QtGui.QIcon(os.path.join(ICONPATH, filename))


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