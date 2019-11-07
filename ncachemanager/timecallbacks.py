""" This module manage all the function triggered between every frame cached.
That allow to install custom functions. That use for playblast system, verbose,
time check, explosion check etc etc ...
Only one callback is automatically registered on timeChanged event during the
caches. But this callback execute the functions contained by the _functions
list.
To add a function to the callback, use add_to_time_callback and to remove it,
use function: remove_from_time_callback
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
    """ this is the main function, the one triggered on every time changed
    maya event. That call all the callable objects stored in the _functions
    global list. To avoid infinite recursive cycles, that check the global var
    _is_time_callback_muted. Some function can trigger the maya time changed
    event. Which will call the time_callback. When the value's True, the
    callback is exit. The value is set True during the functions call.
    """
    if is_time_callback_muted():
        return
    mute_time_callback()
    for func in _functions:
        func()
    unmute_time_callback()
    update_time_infos()


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


def add_to_time_callback(callable_object):
    global _functions
    if callable_object not in _functions:
        _functions.append(callable_object)
    try:
        name = callable_object.__name__
    except AttributeError:
        name = callable_object.__repr__()
    logging.warning(name + ' is already registered to callback')
    return


def remove_from_time_callback(callable_object):
    global _functions
    for func in _functions:
        if callable_object is func:
            _functions.remove(func)


def update_time_infos():
    """ this function update some info about time which can be used during the
    callback. It store in variable global, the current time and the current
    frame. e.i. _last_time is used to know how much time is spent for a
    simulated
    frame.
    """
    if is_time_callback_muted():
        return
    global _last_frame, _last_time
    _last_frame = int(cmds.currentTime(query=True))
    _last_time = datetime.now()


def time_verbose():
    """ this method is an utils which can be add to the time_callback. That
    properly log every frame done.
    """
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
