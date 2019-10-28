"""
This is a standalone script which to by launched in a mayapy.
The ncache manager path has to be set in the PYTHONPATH.
The script create a ncache in background, this is the arguments orders
    -directory
    -scene
    -nodes
    -start_frame
    -end_frame
    -playblast_resolution
    -viewport_display_values
    -playblast_camera
"""

import argparse


PLAYBLAST_DISPLAY_HELP = """\
List of 0 and 1 for True and False in and string. e.i : "1 0 1 1 1 1 0 0 1 0"
Thats a list of option to display in the playblast render.
Here's the positional value:
    NURBS Curves, NURBS Surfaces, Polygons, Subdiv Surface, Particles,
    Particle Instance, Fluids, Strokes, Image Planes, UI, Lights, Cameras,
    Locators, Joints, IK Handles, Deformers, Motion Trails, Components,
    Hair Systems, Follicles, Misc. UI, Ornaments
"""
PLAYBLAST_RES_HELP = 'resolution of rendered playblast. e.i. "1024 768"'
parser = argparse.ArgumentParser()
parser.add_argument('directory', help="Cache Version directory")
parser.add_argument('scene', help="Maya file location")
parser.add_argument('nodes', help="Dynamic nodes to cache")
parser.add_argument('start_frame', help="NCache start frame", type=int)
parser.add_argument('end_frame', help="NCache end frame", type=int)
parser.add_argument('playblast_resolution', help=PLAYBLAST_RES_HELP)
parser.add_argument('viewport_display_values', help=PLAYBLAST_DISPLAY_HELP)
parser.add_argument('playblast_camera', help="camershape name")
arguments = parser.parse_args()


import os
import logging
# remove all the existing logging handlers that can already set by default
# by maya. If those handlers aren't deleted, the module refuse to set is output
# in an external log file.
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
LOG_FILE = os.path.join(arguments.directory, 'infos.log')
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
# Log the arguments informations.
arguments_infos = """\
Scripts Arguments:
    - CacheVersion directory = {arguments.directory}
    - Maya scene = {arguments.scene}
    - Nodes = {arguments.nodes}
    - Range = {arguments.start_frame} to {arguments.end_frame}
    - Resolution = {arguments.playblast_resolution}
    - Viewport display = {arguments.viewport_display_values}
    - Camera blaster = {arguments.playblast_camera}
""".format(arguments=arguments)
logging.info(arguments_infos)


import maya.standalone
maya.standalone.initialize(name='python')

from maya import cmds, mel
from ncachemanager.versioning import CacheVersion
from ncachemanager.api import record_in_existing_cacheversion
import maya.OpenMaya as om2


display_values = [
    bool(int(value))
    for value in arguments.viewport_display_values.split(' ')]
width, height = map(int, arguments.playblast_resolution.split(" "))
playblast_viewport_options = {
    'width': width,
    'height': height,
    'viewport_display_values': display_values,
    'camera': arguments.playblast_camera}

cmds.file(arguments.scene, open=True, force=True)
cacheversion = CacheVersion(arguments.directory)
record_in_existing_cacheversion(
    cacheversion=cacheversion,
    start_frame=arguments.start_frame,
    end_frame=arguments.end_frame,
    nodes=arguments.nodes.split(', '),
    behavior=0,
    verbose=True,
    timelimit=0,
    explosion_detection_tolerance=0,
    playblast=True,
    playblast_viewport_options=playblast_viewport_options)
