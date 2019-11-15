import os
import subprocess
import shutil
import sys

from maya import cmds
from ncachemanager.optionvars import MAYAPY_PATH_OPTIONVAR
from ncachemanager.versioning import create_cacheversion


_CURRENTDIR = os.path.dirname(os.path.realpath(__file__))
_SCRIPT_FILENAME = "record_in_cacheversion.py"
_SCRIPT_FILEPATH = os.path.join(_CURRENTDIR, '..', 'script', _SCRIPT_FILENAME)

FLASHCACHE_NAME = 'flashed cache'
WEDGINGCACHE_NAME = 'wedging cache'
NCACHESCENE_FILENAME = 'scene.ma'
TEMPFOLDER_NAME = 'flash_scenes'
WEDGINGFOLDER_NAME = 'wedging_scenes'
FLASHSCENE_NAME = 'flash_scene_{}.ma'
WEDGINGSCENE_NAME = 'scene_{}.ma'
WEDGING_COMMENT_TEMPLATE = """\
Wedging Cache:
\tattribute {}
\tvalue {}"""


def build_unique_scene_name(workspace, scenename_template, foldername):
    i = 0
    name = scenename_template.format(str(i).zfill(2))
    while os.path.exists(os.path.join(workspace, foldername, name)):
        i += 1
        name = scenename_template.format(str(i).zfill(2))
    return name


def gather_current_environment():
    pythonpaths = os.environ["PYTHONPATH"].split(os.pathsep)
    pythonpaths = [p.replace("\\", "/") for p in pythonpaths]
    for path in sys.path:
        path = path.replace("\\", "/")
        if path in pythonpaths:
            continue
        pythonpaths.append(path)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(os.pathsep.join(pythonpaths))
    return environment


def flash_current_scene(workspace):
    currentname = cmds.file(query=True, sceneName=True)
    flashname = build_unique_scene_name(workspace, FLASHSCENE_NAME, TEMPFOLDER_NAME)
    folder = os.path.join(workspace, TEMPFOLDER_NAME)
    filename = os.path.join(folder, flashname)
    if not os.path.exists(folder):
        os.makedirs(folder)
    cmds.file(rename=filename)
    cmds.file(save=True, type="mayaAscii")
    cmds.file(rename=currentname)
    return filename


def save_scene_for_wedging(workspace):
    currentname = cmds.file(query=True, sceneName=True)
    flashname = build_unique_scene_name(workspace, WEDGINGSCENE_NAME, WEDGINGFOLDER_NAME)
    folder = os.path.join(workspace, WEDGINGFOLDER_NAME)
    filename = os.path.join(folder, flashname)
    if not os.path.exists(folder):
        os.makedirs(folder)
    cmds.file(rename=filename)
    cmds.file(save=True, type="mayaAscii")
    cmds.file(rename=currentname)
    return filename


def send_batch_ncache_jobs(
        workspace, jobs, start_frame, end_frame, nodes,
        playblast_viewport_options, timelimit, stretchmax):
    ''' this function precreate the python script and the folder where will
    be cached the giver jobs. A job is a dict containing tree key:
    {'name': str, 'comment': str, 'scene': str}
    '''
    processes = []
    cacheversions = []
    # build the arguments list. The two None values are differents for every
    # job and will be redefine during the loop
    arguments = build_batch_script_arguments(
        start_frame, end_frame, nodes, playblast_viewport_options, timelimit,
        stretchmax)
    environment = gather_current_environment()
    for job in jobs:
        cacheversion = create_cacheversion(
            workspace=workspace,
            name=job['name'],
            comment=job['comment'],
            nodes=nodes,
            start_frame=start_frame,
            end_frame=end_frame)
        cacheversions.append(cacheversion)
        scene = os.path.join(cacheversion.directory, NCACHESCENE_FILENAME)
        os.rename(job['scene'], scene)
        # replace the two arguments which are different for each jobs
        arguments[2] = cacheversion.directory
        arguments[3] = scene
        process = subprocess.Popen(
            arguments,
            bufsize=-1,
            env=environment,
            creationflags=subprocess.CREATE_NEW_CONSOLE)
        processes.append(process)

    clean_batch_temp_folder(workspace)
    return cacheversions, processes


def send_wedging_ncaches_jobs(
        workspace, name, start_frame, end_frame, nodes,
        playblast_viewport_options, timelimit, stretchmax, attribute, values):
    processes = []
    cacheversions = []
    environment = gather_current_environment()
    scene = save_scene_for_wedging(workspace)
    for value in values:
        comment = WEDGING_COMMENT_TEMPLATE.format(attribute, value)
        cacheversion = create_cacheversion(
            workspace=workspace,
            name=name,
            comment=comment,
            nodes=nodes,
            start_frame=start_frame,
            end_frame=end_frame)
        cacheversions.append(cacheversion)
        arguments = build_batch_script_arguments(
            start_frame, end_frame, nodes, playblast_viewport_options,
            timelimit, stretchmax, attribute_override_name=attribute,
            attribute_override_value=value, scene=scene,
            directory=cacheversion.directory)
        process = subprocess.Popen(
            arguments,
            env=environment,
            bufsize=-1,
            creationflags=subprocess.CREATE_NEW_CONSOLE)
        processes.append(process)
    return cacheversions, processes


def build_batch_script_arguments(
        start_frame, end_frame, nodes, playblast_viewport_options, timelimit,
        stretchmax, scene=None, directory=None, attribute_override_name="",
        attribute_override_value=0.0):
    arguments = []
    # mayapy executable
    arguments.append(cmds.optionVar(query=MAYAPY_PATH_OPTIONVAR))
    # script executed
    arguments.append(_SCRIPT_FILEPATH)
    # directory
    arguments.append(directory)
    # maya scene
    arguments.append(scene)
    # cached nodes
    arguments.append(', '.join(nodes))
    # start frame
    arguments.append(str(start_frame))
    # end frame
    arguments.append(str(end_frame))
    # playblast resolution
    width = playblast_viewport_options['width']
    height = playblast_viewport_options['height']
    arguments.append(' '.join(map(str, [width, height])))
    # display values for playblast render
    display_values = playblast_viewport_options['viewport_display_values']
    arguments.append(' '.join(map(str, map(int, display_values))))
    # camera shape
    arguments.append(playblast_viewport_options['camera'])
    # timelimit
    arguments.append(str(timelimit))
    # stretch max
    arguments.append(str(stretchmax))
    # Attribute override name
    arguments.append(attribute_override_name)
    # Attribute overide value
    arguments.append(str(attribute_override_value))

    return arguments


def clean_batch_temp_folder(workspace):
    shutil.rmtree(os.path.join(workspace, TEMPFOLDER_NAME))


def is_temp_folder_empty(workspace):
    tempfolder = os.path.join(workspace, TEMPFOLDER_NAME)
    if os.path.exists(tempfolder) is False:
        return True
    if not os.listdir(tempfolder):
        return True
    return False


def list_flashed_scenes(workspace):
    tempfolder = os.path.join(workspace, TEMPFOLDER_NAME)
    scenes = []
    for scene in os.listdir(tempfolder):
        if scene.endswith('.ma'):
            scenes.append(os.path.join(tempfolder, scene))
    return scenes