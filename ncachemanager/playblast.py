import os
import re
import tempfile
import random
from functools import partial
import shutil
import subprocess

import maya.api.OpenMaya as om2
from maya import cmds
# PyMel this exceptionnaly used for attribute.get() facilities
import pymel.core as pm
from ncachemanager.optionvars import FFMPEG_PATH_OPTIONVAR


FFMPEG_COMMAND = "{ffmpeg} -framerate 24 -i {images_expression} -codec copy {output}.mp4"
TEMP_FILENAME_NAME = 'tmp_playblast_{id}_{scenename}'
DEFAULT_SCENE_NAME = 'untitled'
FFMPEG_PATH_NOT_SET_WARNING = (
    'No valid FFMPEG path set for the ncache manager. Playblast flag skip !')
RENDER_GLOBALS_FILTERVALUES = "hardwareRenderingGlobals.objectTypeFilterValueArray"
RENDER_GLOBALS_FILTERNAMES = "hardwareRenderingGlobals.objectTypeFilterNameArray"

# place where are stored all the temp playblast images.
# this store should never contain more than one key.
PLAYBLAST_STORE = {}
PLAYBLAST_CALLBACKS = []
BACKUPED_RENDER_SETTINGS = {}
# This is a global variable used for batch rendering.
# the cmds.render command behave differently with a batch maya than ui maya.
# In batch mode, the command render, kick automatically a range. That use the
# defaultRenderGlobals startFrame and endFrame attribute. Which change
# change the frames automatically two times. As the playblast render is
# triggered by the timeChanged event, the render goes in infinite loop using
# using batch mode. This global variable is a check to disable the callback
# if that's triggered during the cmds.render command.
PLAYBLAST_DISABLE_CALLBACK = False


def start_playblast_record(
        camera='perspShape', width=1024, height=748,
        viewport_display_values=None):
    """ This function is triggered at the beginning of a cache. That register a
    callback stick to the timeChanged event. It render the frame with maya
    hardware 2.0 renderer. Store every frame in the global dictionnary:
    PLAYBLAST_STORE. Ok I know, that's a bit weak design, but that the simplest
    I found. When the playblast is done, FFMPEG encode the temporary files to a
    non compressed jpg mp4 assembly.
    viewport_display_values is a dict, here the available keys:
        'NURBS Curves': False,
        'NURBS Surfaces': True,
        'Polygons': True,
        'Subdiv Surface': True,
        'Particles': True,
        'Particle Instance': True,
        'Fluids': True,
        'Strokes': True,
        'Image Planes': True,
        'UI': False,
        'Lights': False,
        'Cameras': False,
        'Locators': False,
        'Joints': False,
        'IK Handles': False,
        'Deformers': False,
        'Motion Trails': False,
        'Components': False,
        'Hair Systems': False,
        'Follicles': False,
        'Misc. UI': False,
        'Ornaments': False,
    """

    if not is_ffmpeg_path_valid():
        cmds.warning(FFMPEG_PATH_NOT_SET_WARNING)
        return None

    # the current global render settings are backup to be reset at the end of
    # the record. That's saved in the global dict BACKUPED_RENDER_SETTINGS
    # which is cleaned at the end. Ok global variables are evil, but there the
    # simplest solution found and I don't see case where this function will be
    # called two time before a stop_record_playblast call
    backup_current_render_settings()
    # A random id is given to the playblast. This id is used in the temporary
    # filename to prevent that two different maya are caching in the same time
    # has a render name clash.
    playblast_id = random.randrange(1000)
    # change the maya settings for the playblast
    # set the camera background to grey, that black by default
    attribute = "{}.backgroundColor".format(camera)
    cmds.setAttr(attribute, 0.375, 0.375, 0.375, type="double3")
    cmds.workspace(fileRule=['images', tempfile.gettempdir()])
    set_render_settings_for_playblast(playblast_id, viewport_display_values)

    function = partial(playblast_callback, playblast_id, camera, width, height)
    callback = om2.MEventMessage.addEventCallback('timeChanged', function)
    PLAYBLAST_CALLBACKS.append(callback)
    return playblast_id


def set_render_settings_for_playblast(playblast_id, viewport_display_values):
    cmds.setAttr("defaultRenderGlobals.extensionPadding", 6)
    attribute = "defaultRenderGlobals.currentRenderer"
    cmds.setAttr(attribute, "mayaHardware2", type="string")
    cmds.setAttr("defaultRenderGlobals.imageFormat", 8)
    attribute = "defaultRenderGlobals.imageFilePrefix"
    filename = build_output_filename(playblast_id)
    cmds.setAttr(attribute, filename, type="string")
    cmds.setAttr("defaultRenderGlobals.animation", True)
    cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", True)
    cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)
    if not viewport_display_values:
        return
    cmds.setAttr(RENDER_GLOBALS_FILTERVALUES, viewport_display_values, type="Int32Array")


def stop_playblast_record(playblast_id):
    """ this function close the recording context. That unregister the callback
    who render every frame, compile a movie using ffmpeg and remove all the
    temporary jpg generated. That clean the playblast store from the given
    playblast id.
    """
    if playblast_id is None:
        return

    images = PLAYBLAST_STORE[playblast_id]
    destination = compile_movie(images)

    for image in images:
        os.remove(image)
    del PLAYBLAST_STORE[playblast_id]
    clean_playblack_callbacks()
    gather_backuped_render_settings()
    return destination


def backup_current_render_settings():
    # clean existing backup
    for key in BACKUPED_RENDER_SETTINGS.keys():
        del BACKUPED_RENDER_SETTINGS[key]

    settings = {}
    settings['viewport_filters'] = list_render_filter_options()
    node = pm.PyNode('defaultRenderGlobals')
    settings['rendersettings'] = {a: a.get() for a in node.listAttr()}
    BACKUPED_RENDER_SETTINGS.update(settings)


def gather_backuped_render_settings():
    values = [s[1] for s in  BACKUPED_RENDER_SETTINGS['viewport_filters']]
    cmds.setAttr(RENDER_GLOBALS_FILTERVALUES, values, type="Int32Array")
    for attribute, value in BACKUPED_RENDER_SETTINGS['rendersettings'].items():
        try:
            attribute.set(value)
        except:
            pass


def list_render_filter_options():
    """ this function list the object type displayed by the maya hardware 2.0
    renderer. e.i. Nurbs Curves, Camera, etc ...
    The function return a list of tuple: [("camera", True), ("mesh", True), ..]
    """
    keys = cmds.getAttr(RENDER_GLOBALS_FILTERNAMES)
    values = cmds.getAttr(RENDER_GLOBALS_FILTERVALUES)
    return zip(keys, values)


def compile_movie(images):
    ffmpeg = cmds.optionVar(query=FFMPEG_PATH_OPTIONVAR)
    output = images[0][:-11]
    # this line analyse the filename given and build a filename expression
    # understood by FFMMPEG. %6d mean 6 digit frame number.
    images_expression = re.sub(r".\d\d\d\d\d\d.jpg", ".%6d.jpg", (images[0]))
    command = FFMPEG_COMMAND.format(
        ffmpeg=ffmpeg,
        images_expression=images_expression,
        output=output)

    process = subprocess.Popen(command)
    process.wait()
    return output + ".mp4"


def build_output_filename(playblast_id):
    """ the playblast_id ensure unique filename.
    That's generated when the callback is registered.
    """
    scenename = cmds.file(query=True, sceneName=True)
    if scenename:
        scenename = os.path.basename(scenename)[:-3]
    else:
        scenename = DEFAULT_SCENE_NAME
    return TEMP_FILENAME_NAME.format(id=playblast_id, scenename=scenename)


def playblast_callback(
        playblast_id, camera, width, height, *unused_callback_kwargs):
    """ this function is the callback sticked to the "timeChanged" event.
    This callback shoot a render and store the result in the store.
    """
    global PLAYBLAST_DISABLE_CALLBACK
    if PLAYBLAST_DISABLE_CALLBACK is True:
        return
    PLAYBLAST_DISABLE_CALLBACK = True
    frame = cmds.currentTime(query=True)
    cmds.setAttr("defaultRenderGlobals.startFrame", frame)
    cmds.setAttr("defaultRenderGlobals.endFrame", frame)
    destination = cmds.render(camera, xresolution=width, yresolution=height)
    # record render in the store
    if PLAYBLAST_STORE.get(playblast_id) is None:
        PLAYBLAST_STORE[playblast_id] = []
    PLAYBLAST_STORE[playblast_id].append(destination)
    PLAYBLAST_DISABLE_CALLBACK = False


def is_ffmpeg_path_valid():
    ffmpeg = cmds.optionVar(query=FFMPEG_PATH_OPTIONVAR)
    return ffmpeg and os.path.exists(ffmpeg)


def clean_playblack_callbacks():
    for callback in PLAYBLAST_CALLBACKS:
        om2.MMessage.removeCallback(callback)
        PLAYBLAST_CALLBACKS.remove(callback)