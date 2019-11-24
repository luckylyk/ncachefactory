
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
ATTRIBUTE_OVERRIDE_HELP = "Plug name which is overrided for simlulation"
ATTRIBUTE_OVERRIDE_VALUE_HELP = "Attribute overrided value"

INFOS = """\
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
    - Attribute override = {arguments.attribute_override}
    - Attribute override value = {arguments.attribute_override_value}
"""

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
    parser.add_argument('attribute_override', help=ATTRIBUTE_OVERRIDE_HELP)
    parser.add_argument('attribute_override_value', help=ATTRIBUTE_OVERRIDE_VALUE_HELP, type=float)
    arguments = parser.parse_args()

    def force_log_info(message):
        # remove all the existing logging handlers that can already set by
        # default by maya. If those handlers aren't deleted, the module refuse
        # to set is output in an external log file.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logfile = os.path.join(arguments.directory, 'infos.log')
        logging.basicConfig(filename=logfile, level=logging.INFO)
        logging.info(message)

    # Log the arguments informations.
    if arguments.attribute_override == "":
        arguments.attribute_override = None
        arguments.attribute_override_value = None
    force_log_info(INFOS.format(arguments=arguments))

    from maya import cmds, mel
    import maya.OpenMaya as om2
    from ncachefactory.versioning import CacheVersion
    from ncachefactory.cachemanager import record_in_existing_cacheversion
    from ncachefactory.ncloth import is_output_too_streched
    from ncachefactory.viewporttext import create_viewport_text
    from ncachefactory.timecallbacks import (
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
            if 0 < timelimit < timespent.seconds:
                message = "simulation time exceeds the limit allowed: {}"
                logging.error(message.format(timespent))
                result = True

        if result is True:
            logging.error("User defined explosion limit reached.")
            cmds.quit(force=True)
            exit()

    # force dg evaluation to DG to ensure not multi thread usage.
    cmds.evaluationManager(mode="off")
    force_log_info('open maya scene ...')
    cmds.file(arguments.scene, open=True, force=True)
    force_log_info('maya scene opened')
    cacheversion = CacheVersion(arguments.directory)

    attribute = arguments.attribute_override
    value = arguments.attribute_override_value
    if attribute:
        if not cmds.objExists(attribute):
            msg = "{} doesn't exists and cannot be overrided".format(attribute)
            raise ValueError(msg)
        cmds.setAttr(attribute, value)
        force_log_info("attribute \"{}\" set to {}".format(attribute, value))

    text = '{}\n{}'.format(cacheversion.name, cacheversion.infos['comment'])
    create_viewport_text(text, arguments.playblast_camera)

    cmds.currentTime(arguments.start_frame, edit=True)
    # add the check to callbacks
    add_to_time_callback(time_verbose)
    func = partial(
        simulation_sanity_checks,
        arguments.nodes.split(', '),
        arguments.timelimit,
        arguments.stretchmax)
    add_to_time_callback(func)
    register_time_callback()

    display_values = [
        bool(int(value))
        for value in arguments.viewport_display_values.split(' ')]
    if display_values[-1] == 1:
        display_values[-1] = 0
        msg = 'Ornament option in viewport is not supported and turned off'
        force_log_info(msg)

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
    force_log_info("process is terminated")

except Exception:
    import traceback
    logging.error(traceback.format_exc())
    force_log_info("process is terminated")

