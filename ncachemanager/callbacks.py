"""
This module contains a collection of callback which can be stick to a cache
to check explosions, give simulation time warning or add verbose on the cache
to help user to check every frame cached. The verbose is especially usefull on
mayapy process.
"""

from functools import partial
from datetime import datetime
import maya.api.OpenMaya as om2
from maya import cmds
from ncachemanager.qtutils import simulate_escape_key_pressed
from ncachemanager.mesh import is_deformed_mesh_too_stretched
from ncachemanager.ncache import kill_current_simulation
from ncachemanager.ncloth import (
    find_input_mesh_dagpath, find_output_mesh_dagpath)


ROOT_MESSAGE = "INFO ncache: frame {frame_number}, {body}"
EXPLOSION_BODY = "excessive strech detect on mesh: {mesh}"
TIMESPENT_BODY = "is cached in {timespent}"
TIMELIMIT_BODY = "simulation time exceeds the limit allowed"


def register_simulation_callbacks(
        cloth_nodes, verbose=False, timelimit=0,
        explosion_detection_tolerance=0):
    callbacks = []
    callback = register_timecheck_callback(verbose, timelimit)
    callbacks.append(callback)
    if explosion_detection_tolerance >= 1 and cloth_nodes:
        cbs = register_explosion_detection_callbacks(
            cloth_nodes, explosion_detection_tolerance)
        callbacks.extend(cbs)
    return callbacks


def explosion_detection_callback(
        deformed_mesh, reference_mesh, tolerance, *useless_callback_args):
    result = is_deformed_mesh_too_stretched(
        deformed_mesh, reference_mesh, tolerence_factor=tolerance)
    if result is True:
        print ROOT_MESSAGE.format(
            frame_number=cmds.currentTime(query=True),
            body=EXPLOSION_BODY.format(mesh=deformed_mesh))
        # dirty wait to stop simulation. Probably not possible in batch
        kill_current_simulation()


def register_explosion_detection_callbacks(nodes, tolerance):
    """ this function add a callback per dynamic node to check is the geometry
    explode during the simulation. It returns the call back to clean them on
    output.
    """
    callbacks = []
    for node in nodes:
        inputmesh = find_input_mesh_dagpath(node).name()
        outputmesh = find_output_mesh_dagpath(node).name()
        function = partial(
            explosion_detection_callback, outputmesh, inputmesh, tolerance)
        callback = om2.MEventMessage.addEventCallback('timeChanged', function)
        callbacks.append(callback)
    return callbacks


def timecheck_callback(times, verbose, timelimit, *useless_callback_args):
    times[0] = times[1]
    times[1] = datetime.now()
    timespent = (times[1] - times[0])
    frame = cmds.currentTime(query=True)
    # Time limit to 0 means no limit
    if 0 < timelimit < timespent.total_seconds():
        print ROOT_MESSAGE.format(frame_number=frame, body=TIMELIMIT_BODY)
        # dirty wait to stop simulation. Probably not possible in batch
        kill_current_simulation()
    if verbose is True:
        print ROOT_MESSAGE.format(
            frame_number=frame,
            body=TIMESPENT_BODY.format(timespent=timespent))


def register_timecheck_callback(verbose=False, timelimit=0):
    """ This function register a callback which print current frame and time
    spent on every frame cached. That mainly interesting to know the progress
    during a batch job.
    """
    # the list is created and passed to the verbose callback the function
    # directly edit the list which allow to compare the times between to frame
    # and compute the time spent per frame simulated.
    times = [None, datetime.now()]
    function = partial(timecheck_callback, times, verbose, timelimit)
    return om2.MEventMessage.addEventCallback('timeChanged', function)
