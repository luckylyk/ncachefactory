import os
import re
import sys
import subprocess
from functools import partial

from maya import cmds
import pymel.core as pm

from ncachefactory.timecallbacks import (
    add_to_time_callback, remove_from_time_callback)
from ncachefactory.optionvars import (
    FFMPEG_PATH_OPTIONVAR, PLAYBLAST_VIEWPORT_OPTIONVAR,
    ensure_optionvars_exists)


if int(sys.version[0]) > 2:
    long = int


OUTPUT_RENDER_FILENAME = 'ncache_playblast'
RENDER_GLOBALS_FILTERVALUES = "hardwareRenderingGlobals.objectTypeFilterValueArray"
RENDER_GLOBALS_FILTERNAMES = "hardwareRenderingGlobals.objectTypeFilterNameArray"

_backuped_render_settings = {}
_registered_callback_function = None
_blasted_images = []


def start_playblast_record(
        directory, camera='perspShape', width=1024, height=748,
        viewport_display_values=None):
    for cam in cmds.ls(type="camera"):
        cmds.setAttr(cam + '.renderable', cam == camera)
    # the current global render settings are backup to be reset at the end of
    # the record. That's saved in the global dict BACKUPED_RENDER_SETTINGS
    # which is cleaned at the end. Ok global variables are evil, but there the
    # simplest solution found and I don't see case where this function will be
    # called two time before a stop_record_playblast call
    backup_current_render_settings()
    set_render_settings_for_playblast(viewport_display_values)
    # change the maya settings for the playblast
    # set the camera background to grey, that black by default
    attribute = "{}.backgroundColor".format(camera)
    cmds.setAttr(attribute, 0.375, 0.375, 0.375, type="double3")
    cmds.workspace(fileRule=['images', directory])

    global _registered_callback_function
    _registered_callback_function = partial(shoot_frame, camera, width, height)
    add_to_time_callback(_registered_callback_function)


def shoot_frame(camera, width, height):
    frame = cmds.currentTime(query=True)
    cmds.setAttr("defaultRenderGlobals.startFrame", frame)
    cmds.setAttr("defaultRenderGlobals.endFrame", frame)
    image = cmds.ogsRender(width=width, height=height)
    global _blasted_images
    _blasted_images.append(image)


def stop_playblast_record(directory):
    global _blasted_images
    source = compile_movie(_blasted_images)
    # for image in _blasted_images:
    #     os.remove(image)
    _blasted_images = []
    destination = os.path.join(directory, os.path.basename(source))
    os.rename(source, destination)
    global _registered_callback_function
    remove_from_time_callback(_registered_callback_function)
    _registered_callback_function = None
    gather_backuped_render_settings()
    return destination


def backup_current_render_settings():
    # clean existing backup
    for key in _backuped_render_settings.keys():
        del _backuped_render_settings[key]

    settings = {}
    settings['viewport_filters'] = list_render_filter_options()
    node = pm.PyNode('defaultRenderGlobals')
    settings['rendersettings'] = {a: a.get() for a in node.listAttr()}
    _backuped_render_settings.update(settings)


def gather_backuped_render_settings():
    values = [s[1] for s in _backuped_render_settings['viewport_filters']]
    cmds.setAttr(RENDER_GLOBALS_FILTERVALUES, values, type="Int32Array")
    for attribute, value in _backuped_render_settings['rendersettings'].items():
        try:
            attribute.set(value)
        except:
            pass


def set_render_settings_for_playblast(viewport_display_values):
    cmds.setAttr("defaultRenderGlobals.extensionPadding", 6)
    attribute = "defaultRenderGlobals.currentRenderer"
    cmds.setAttr(attribute, "mayaHardware2", type="string")
    cmds.setAttr("defaultRenderGlobals.imageFormat", 8)
    attribute = "defaultRenderGlobals.imageFilePrefix"
    filename = OUTPUT_RENDER_FILENAME
    cmds.setAttr(attribute, filename, type="string")
    cmds.setAttr("defaultRenderGlobals.animation", True)
    cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", True)
    cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)
    if viewport_display_values is None:
        return
    cmds.setAttr(
        RENDER_GLOBALS_FILTERVALUES,
        map(long, viewport_display_values),
        type="Int32Array")


def list_render_filter_options():
    """ this function list the object type displayed by the maya hardware 2.0
    renderer. e.i. Nurbs Curves, Camera, etc ...
    The function return a list of tuple: [("camera", True), ("mesh", True), ..]
    """
    ensure_optionvars_exists()
    keys = cmds.getAttr(RENDER_GLOBALS_FILTERNAMES)
    values = cmds.optionVar(query=PLAYBLAST_VIEWPORT_OPTIONVAR)
    values = [bool(int(value)) for value in values.split(" ")]
    return zip(keys, values)


def compile_movie(images):
    """ this function an mp4 video from the jpgeg given. In the same folder.
    The jpeg filenames pattern must finish by ".%6d.jpg" to be understood by
    the function
    """
    ffmpeg = cmds.optionVar(query=FFMPEG_PATH_OPTIONVAR)
    output = images[0][:-11] + ".mp4"
    # this line analyse the filename given and build a filename expression
    # understood by FFMMPEG. %6d mean 6 digit frame number.
    images_expression = re.sub(r".\d\d\d\d\d\d.jpg", ".%6d.jpg", (images[0]))
    # on some ffmpeg versions, that need the start frame specified for images
    # sequences. This line infer the first frame from the first filename
    startframe = int(images[0].split('.')[-2])
    arguments = [
        ffmpeg, "-framerate", "24", "-start_number", str(startframe),
        "-i", images_expression, "-codec", "copy", output]
    process = subprocess.Popen(arguments)
    process.wait()
    return output
