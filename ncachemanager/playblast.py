import os
import re
import tempfile
import random
from functools import partial
import shutil
import subprocess

import maya.api.OpenMaya as om2
from maya import cmds
from ncachemanager.qtutils import shoot
from ncachemanager.optionvars import FFMPEG_PATH_OPTIONVAR


FFMPEG_COMMAND = "{ffmpeg} -framerate 24 -i {images_expression} -codec copy {output}.mp4"
TEMP_FILENAME_NAME = 'tmp_playblast_{id}_{scenename}_{frame}.jpg'
DEFAULT_SCENE_NAME = 'untitled'
PLAYBLAST_TEAROFF_NAME = "NCacheManagerPlayblast"
PLAYBLAST_PANEL_NAME = "NCacheManagerPanel"
PLAYBLAST_ID_CAMERA_ATTRIBUTE = "ncachemanager_playblast_id"
PLAYBLAST_CALLBACKS = []
PLAYBLAST_STORE = {}  # place where are stored all the temp playblast images
FFMPEG_PATH_NOT_SET_WARNING = (
    'No valid FFMPEG path set for the ncache manager. Playblast flag skip !')
MODELEDITOR_OPTIONS = {
    "displayAppearance": "smoothShaded",
    "displayLights": "default",
    "activeView": True,
    "backfaceCulling": True,
    "camera": False,
    "displayTextures": True,
    "dynamicConstraints": False,
    "dynamics": True,
    "fluids": True,
    "follicles": False,
    "grid": False,
    "hairSystems": True,
    "handles": False,
    "headsUpDisplay": True,
    "hulls": True,
    "ikHandles": False,
    "joints": False,
    "lights": False,
    "locators": False,
    "lowQualityLighting": False,
    "manipulators": False,
    "nCloths": False,
    "nRigids": False,
    "nurbsCurves": True,
    "nurbsSurfaces": True,
    "occlusionCulling": True,
    "pivots": False,
    "planes": True,
    "polymeshes": True,
    "selectionHiliteDisplay": False,
    "shadows": False,
    "smoothWireframe": False,
    "sortTransparent": True,
    "strokes": False,
    "subdivSurfaces": False,
    "textures": True,
    "transpInShadows": True,
    "twoSidedLighting": True,
    "useDefaultMaterial": False,
    "wireframeOnShaded": False}


def start_playblast_record(
        camera='perspShape', width=1024, height=748, **model_editor_kwargs):
    if not is_ffmpeg_path_valid():
        cmds.warning(FFMPEG_PATH_NOT_SET_WARNING)
        return None

    ensure_playblast_id_attribute_exists(camera)
    playblast_id = random.randrange(1000)
    cmds.setAttr(camera + '.' + PLAYBLAST_ID_CAMERA_ATTRIBUTE, playblast_id)
    options = MODELEDITOR_OPTIONS.copy()
    options.update(model_editor_kwargs)
    model_editor = create_playblast_tearoff(camera, width, height, **options)
    function = partial(playblast_callback, playblast_id, model_editor)
    callback = om2.MEventMessage.addEventCallback('timeChanged', function)
    PLAYBLAST_CALLBACKS.append(callback)
    return playblast_id


def stop_playblast_record(playblast_id):
    if playblast_id is None:
        clean_playblack_callbacks()
        return
    if PLAYBLAST_TEAROFF_NAME in cmds.lsUI(windows=True):
        cmds.deleteUI(PLAYBLAST_TEAROFF_NAME)
    images = PLAYBLAST_STORE[playblast_id]
    destination = compile_movie(images)
    for image in images:
        os.remove(image)
    del PLAYBLAST_STORE[playblast_id]
    clean_playblack_callbacks()
    return destination


def compile_movie(images):
    ffmpeg = cmds.optionVar(query=FFMPEG_PATH_OPTIONVAR)
    output = images[0][:-4]
    images_expression = re.sub(r"_\d\d\d\d\d.jpg", "_%5d.jpg", (images[0]))
    command = FFMPEG_COMMAND.format(
        ffmpeg=ffmpeg,
        images_expression=images_expression,
        output=output)

    process = subprocess.Popen(command)
    process.wait()
    return output + ".mp4"


def create_playblast_tearoff(cam, width, height, **model_editor_kwargs):
    cmds.window(PLAYBLAST_TEAROFF_NAME, widthHeight=[1024, 748])
    cmds.frameLayout(labelVisible=False)
    panel = cmds.modelPanel(
        label=PLAYBLAST_PANEL_NAME,
        menuBarVisible=False,
        barLayout=False,
        modelEditor=False,
        camera=cam)

    model_editor = cmds.modelPanel(panel, query=True, modelEditor=True)
    cmds.modelEditor(model_editor, edit=True, **model_editor_kwargs)
    cmds.showWindow()
    return model_editor


def get_temp_jpeg_destination(playblast_id):
    """ The playblast_id ensure unique filename.
    That's generated when the callback is registered.
    """
    scenename = cmds.file(query=True, sceneName=True)
    if scenename:
        scenename = os.path.basename(scenename)[:-3]
    else:
        scenename = DEFAULT_SCENE_NAME
    frame = str(int(cmds.currentTime(query=True))).zfill(5)
    filename = TEMP_FILENAME_NAME.format(
        id=playblast_id, scenename=scenename, frame=frame)
    return os.path.join(tempfile.gettempdir(), filename)


def playblast_callback(playblast_id, model_editor, *unused_callback_kwargs):
    destination = get_temp_jpeg_destination(playblast_id)
    shoot(destination, model_editor)
    if PLAYBLAST_STORE.get(playblast_id) is None:
        PLAYBLAST_STORE[playblast_id] = []
    PLAYBLAST_STORE[playblast_id].append(destination)


def is_ffmpeg_path_valid():
    ffmpeg = cmds.optionVar(query=FFMPEG_PATH_OPTIONVAR)
    return ffmpeg and os.path.exists(ffmpeg)


def clean_playblack_callbacks():
    for callback in PLAYBLAST_CALLBACKS:
        om2.MMessage.removeCallback(callback)
        PLAYBLAST_CALLBACKS.remove(callback)


def ensure_playblast_id_attribute_exists(camera):
    if cmds.objExists(camera + '.' + PLAYBLAST_ID_CAMERA_ATTRIBUTE):
        return
    cmds.addAttr(
        camera,
        longName=PLAYBLAST_ID_CAMERA_ATTRIBUTE,
        attributeType='long')