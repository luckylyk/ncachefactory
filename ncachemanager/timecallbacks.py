""" This module manage all the function triggered between every frame cached.
That allow to install custom functions. That use for playblast system, verbose,
time check, explosion check etc etc ...
"""

from datetime import datetime
import logging
from maya import cmds
import maya.api.OpenMaya as om2


ROOT_MESSAGE = "frame {frame_number}, {body}"
TIMESPENT_BODY = "is cached in {timespent}"


_time_callback_muted = False
_time_callback = None
_last_frame = None
_last_time = None
_functions = []


def mute_time_callback():
    global _time_callback_muted
    _time_callback_muted = True


def unmute_time_callback():
    global _time_callback_muted
    _time_callback_muted = False


def is_time_callback_muted():
    global _time_callback_muted
    return _time_callback_muted


def clear_time_callback_functions():
    global _functions
    _functions = []


def add_to_time_callback(func):
    global _functions
    if func in _functions:
        try:
            name = func.__name__
        except AttributeError:
            name = func.__repr__()
        logging.warning(name + ' is already registered to callback')
        return
    _functions.append(func)


def remove_from_time_callback(func):
    global _functions
    for registered_func in _functions:
        if func is registered_func:
            _functions.remove(registered_func)


def update_time_infos():
    global _last_frame, _last_time
    if is_time_callback_muted():
        _last_time = None
        _last_time = None
        return
    _last_frame = int(cmds.currentTime(query=True))
    _last_time = datetime.now()


def register_time_callback():
    global _time_callback
    if _time_callback is not None:
        unregister_time_callback()
    _time_callback = om2.MEventMessage.addEventCallback(
        'timeChanged', time_callback)


def unregister_time_callback():
    global _time_callback
    om2.MEventMessage.removeCallback(_time_callback)
    _time_callback = None


def time_callback(*useless_callback_args):
    if is_time_callback_muted():
        return
    mute_time_callback()
    for func in _functions:
        func()
    unmute_time_callback()
    update_time_infos()


def time_verbose():
    if _last_time is None:
        return
    timespent = get_timespent_since_last_frame_set()
    message = ROOT_MESSAGE.format(
        frame_number=int(cmds.currentTime(query=True)),
        body=TIMESPENT_BODY.format(timespent=timespent))
    logging.info(message)


def get_timespent_since_last_frame_set():
    if _last_time is None:
        return None
    return datetime.now() - _last_time
