
import ConfigParser

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
from maya import cmds

from ncachefactory.optionvars import CONFIGFILE_PATH


# get current camera from config file
cfg = ConfigParser.ConfigParser()
cfg.read(CONFIGFILE_PATH)
PRODUCTION_CAMERAS_KNOWN = [elt[1] for elt in cfg.items('production_cameras')]
DEFAULT_CAMERA = "perspShape"


def find_existing_production_cameras():
    cameras = []
    for camera in PRODUCTION_CAMERAS_KNOWN:
        for star in ["", "*:", "*:*:", "*:*:*:"]:
            cameras.extend(cmds.ls(star + camera))
    return cameras


def find_current_camera():
    view = omui.M3dView.active3dView()
    camera = om.MDagPath()
    view.getCamera(camera)
    return camera.partialPathName()