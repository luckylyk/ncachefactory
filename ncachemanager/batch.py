import os
import subprocess
import shutil
import sys
from maya import cmds
from ncachemanager.optionvars import MAYAPY_PATH_OPTIONVAR
from ncachemanager.versioning import create_cacheversion

SCRIPT_FILENAME = 'batch_ncache.py'
NCACHESCENE_FILENAME = 'ncache_scene.ma'
TEMPFOLDER_NAME = 'tmp_multicache'
FLASHSCENE_NAME = 'flash_scene_{}.ma'
TEMPLATE_SCRIPT = """
import maya.standalone
maya.standalone.initialize(name='python')

from maya import cmds, mel
import sys
import os

from ncachemanager.versioning import CacheVersion
from ncachemanager.api import record_in_existing_cacheversion
import maya.OpenMaya as om2


directory = r"{directory}"
scene_location = r"{scene_location}"
nodes = {nodes}
start_frame = {start_frame}
end_frame = {end_frame}
playblast_viewport_options = {playblast_viewport_options}


cmds.file(scene_location, open=True, force=True)
cacheversion = CacheVersion(directory)
record_in_existing_cacheversion(
    cacheversion=cacheversion,
    start_frame=start_frame,
    end_frame=end_frame,
    nodes=nodes,
    behavior=0,
    verbose=True,
    timelimit=0,
    explosion_detection_tolerance=0,
    playblast=True,
    playblast_viewport_options=playblast_viewport_options)
"""


def build_unique_flashscene_name(workspace):
    i = 0
    name = FLASHSCENE_NAME.format(str(i).zfill(2))
    while os.path.exists(os.path.join(workspace, TEMPFOLDER_NAME, name)):
        i += 1
        name = FLASHSCENE_NAME.format(str(i).zfill(2))
    return name


def get_current_environment():
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
    flashname = build_unique_flashscene_name(workspace)
    folder = os.path.join(workspace, TEMPFOLDER_NAME)
    filename = os.path.join(folder, flashname)
    if not os.path.exists(folder):
        os.makedirs(folder)
    cmds.file(rename=filename)
    cmds.file(save=True, type="mayaAscii")
    cmds.file(rename=currentname)
    return filename


def generate_script_file(cacheversion, playblast_viewport_options):
    destination = os.path.join(cacheversion.directory, SCRIPT_FILENAME)
    scene_location = os.path.join(cacheversion.directory, NCACHESCENE_FILENAME)
    script = TEMPLATE_SCRIPT.format(
        directory=cacheversion.directory,
        nodes=cacheversion.infos['nodes'].keys(),
        start_frame=cacheversion.infos['start_frame'],
        end_frame=cacheversion.infos['end_frame'],
        scene_location=scene_location,
        playblast_viewport_options=playblast_viewport_options)

    with open(destination, 'w') as f:
        f.write(script)
    return destination


def send_batch_ncache_jobs(
        workspace, jobs, start_frame, end_frame, nodes,
        playblast_viewport_options):
    ''' this function precreate the python script and the folder where will
    be cached the giver jobs. A job is a dict containing tree key:
    {'name': str, 'comment': str, 'scene': str}
    '''
    processes = []
    for job in jobs:
        cacheversion = create_cacheversion(
            workspace=workspace,
            name=job['name'],
            comment=job['comment'],
            nodes=nodes,
            start_frame=start_frame,
            end_frame=end_frame)
        dst = os.path.join(cacheversion.directory, NCACHESCENE_FILENAME)
        os.rename(job['scene'], dst)
        mayapy = cmds.optionVar(query=MAYAPY_PATH_OPTIONVAR)
        python_script_file = generate_script_file(
            cacheversion,
            playblast_viewport_options)

        command_args = [mayapy, python_script_file]
        process = subprocess.Popen(command_args, env=get_current_environment())
        processes.append(process)

    clean_batch_temp_folder(workspace)
    return processes


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