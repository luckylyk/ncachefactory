
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
    -timelimit
    -stretchmax
"""

import os
import logging
import argparse
from datetime import datetime
from functools import partial

PLAYBLAST_DISPLAY_HELP = """\
List of 0 and 1 for True and False in and string. e.i : "1 0 1 1 1 1 0 0 1 0"
Thats a list of option to display in the playblast render.
Here's the positional value:
    NURBS Curves, NURBS Surfaces, Polygons, Subdiv Surface, Particles,
    Particle Instance, Fluids, Strokes, Image Planes, UI, Lights, Cameras,
    Locators, Joints, IK Handles, Deformers, Motion Trails, Components,
    Hair Systems, Follicles, Misc. UI, Ornaments."""
PLAYBLAST_RES_HELP = 'resolution of rendered playblast. e.i. "1024 768"'
TIMELIMIT_HELP = "time limit per frame evaluated in second (0 is no limit)"
STRETCH_LIMIT_HELP = "Stretch max supported by output mesh (0 is no limit)"


try:
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help="Cache Version directory")
    parser.add_argument('scene', help="Maya file location")
    parser.add_argument('nodes', help="Dynamic nodes to cache")
    parser.add_argument('start_frame', help="NCache start frame", type=int)
    parser.add_argument('end_frame', help="NCache end frame", type=int)
    parser.add_argument('playblast_resolution', help=PLAYBLAST_RES_HELP)
    parser.add_argument('viewport_display_values', help=PLAYBLAST_DISPLAY_HELP)
    parser.add_argument('playblast_camera', help="camershape name")
    parser.add_argument('timelimit', help=TIMELIMIT_HELP, type=int)
    parser.add_argument('stretchmax', help=STRETCH_LIMIT_HELP, type=int)
    arguments = parser.parse_args()
    # remove all the existing logging handlers that can already set by default
    # by maya. If those handlers aren't deleted, the module refuse to set is output
    # in an external log file.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logfile = os.path.join(arguments.directory, 'infos.log')
    logging.basicConfig(filename=logfile, level=logging.INFO)
    # Log the arguments informations.
    arguments_infos = """\
    Scripts Arguments:
        - CacheVersion directory = {arguments.directory}
        - Maya scene = {arguments.scene}
        - Nodes = {arguments.nodes}
        - Range = {arguments.start_frame} to {arguments.end_frame}
        - Resolution = {arguments.playblast_resolution}
        - Viewport display = {arguments.viewport_display_values}
        - Blasted camera = {arguments.playblast_camera}
        - Time limit = {arguments.timelimit}
        - Stretch max supported = {arguments.stretchmax} * input edge length
    """.format(arguments=arguments)
    logging.info(arguments_infos)

    from maya import cmds, mel
    import maya.OpenMaya as om2
    from ncachemanager.versioning import CacheVersion
    from ncachemanager.api import record_in_existing_cacheversion
    from ncachemanager.ncloth import is_output_too_streched
    from ncachemanager.timecallbacks import (
        add_to_time_callback, get_timespent_since_last_frame_set, time_verbose,
        register_time_callback)

    import maya.standalone
    maya.standalone.initialize(name='python')

    def simulation_sanity_checks(nodes, timelimit, stretchmax):
        """ this function is a time changed callback which kill the
        simulation in case of explosion detected """
        result = False
        if stretchmax > 0:
            for node in nodes:
                if is_output_too_streched(node, stretchmax):
                    result = True
                    message = "excessive strech detect for node: " + node
                    logging.error(message)
                    break

        timespent = get_timespent_since_last_frame_set()
        if timespent is not None:
            if 0 < timelimit < timespent:
                message = "simulation time exceeds the limit allowed: {}"
                logging.error(message.format(timespent))
                result = True

        if result is True:
            logging.error("User defined explosion limit reached.")
            cmds.quit(force=True)

    cmds.file(arguments.scene, open=True, force=True)
    logging.info('maya scene opened')

    cmds.currentTime(arguments.start_frame, edit=True)
    func = partial(
        simulation_sanity_checks,
        arguments.nodes,
        arguments.timelimit,
        arguments.stretchmax)
    register_time_callback()
    add_to_time_callback(func)
    add_to_time_callback(time_verbose)

    display_values = [
        bool(int(value))
        for value in arguments.viewport_display_values.split(' ')]
    width, height = map(int, arguments.playblast_resolution.split(" "))
    playblast_viewport_options = {
        'width': width,
        'height': height,
        'viewport_display_values': display_values,
        'camera': arguments.playblast_camera}

    cacheversion = CacheVersion(arguments.directory)
    record_in_existing_cacheversion(
        cacheversion=cacheversion,
        start_frame=arguments.start_frame,
        end_frame=arguments.end_frame,
        nodes=arguments.nodes.split(', '),
        behavior=0,
        playblast=True,
        playblast_viewport_options=playblast_viewport_options)
    logging.info("process is terminated")

except Exception:
    import traceback
    logging.error(traceback.format_exc())
    logging.info("process is terminated")

