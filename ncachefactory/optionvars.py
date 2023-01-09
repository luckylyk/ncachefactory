"""
This module contains all preferences saved available for the ncachefactory app
"""
import os
from maya import cmds

# Ensure compatibility Py2 and Py3
try:
    import ConfigParser
except BaseException:
    import configparser as ConfigParser

_current_dir = os.path.dirname(os.path.realpath(__file__))
CONFIGFILE_PATH = os.path.join(_current_dir, '..', 'config.cfg')

CACHE_BEHAVIOR_OPTIONVAR = 'ncachefactory_behavior'
CACHEVERSION_SORTING_TYPE_OPTIONVAR = 'ncachefactory_cacherversion_sorting_type'
COMPARISON_EXP_OPTIONVAR = 'ncachefactory_comparison_expanded'
CACHEOPTIONS_EXP_OPTIONVAR = 'ncachefactory_cacheoptions_expanded'
CUSTOM_ENV_PATH_OPTIONVAR = 'ncachefactory_environment_path'
EXPLOSION_DETECTION_OPTIONVAR = 'ncachefactory_explosion_detection'
EXPLOSION_TOLERENCE_OPTIONVAR = 'ncachefactory_explosion_tolerence'
FFMPEG_PATH_OPTIONVAR = 'ncachefactory_ffmpeg_path'
MEDIAPLAYER_PATH_OPTIONVAR = 'ncachefactory_mediaplayer_path'
MAYAPY_PATH_OPTIONVAR = 'ncachefactory_mayapy_path'
MULTICACHE_EXP_OPTIONVAR = 'ncachefactory_multicache_expanded'
PLAYBLAST_RESOLUTION_OPTIONVAR = 'ncachefactory_resolution_playblast'
PLAYBLAST_VIEWPORT_OPTIONVAR = 'ncachefactory_playblast_viewport'
PLAYBLAST_CAMERA_SELECTION_TYPE = 'ncachefactory_camera_selection_type'
PLAYBLAST_EXP_OPTIONVAR = 'ncachefactory_playblast_expanded'
RANGETYPE_OPTIONVAR = 'ncachefactory_rangetype'
RECORD_PLAYBLAST_OPTIONVAR = 'ncachefactory_record_playblast'
SAMPLES_EVALUATED_OPTIONVAR = 'ncachefactory_samples_evaluated'
SAMPLES_SAVED_OPTIONVAR = 'ncachefactory_samples_saved'
TIMELIMIT_ENABLED_OPTIONVAR = 'ncachefactory_timelimit_enabled'
TIMELIMIT_OPTIONVAR = 'ncachefactory_timelimit'
USE_CUSTOM_ENV_OPTIONVAR = 'ncachefactory_use_custom_environment'
VERBOSE_OPTIONVAR = 'ncachefactory_verbose'
VERSION_EXP_OPTIONVAR = 'ncachefactory_version_expanded'
WORKSPACES_RECENTLY_USED_OPTIONVAR = 'ncachefactory_recent_workspaces_used'

OPTIONVARS = {
    CACHE_BEHAVIOR_OPTIONVAR: 0,
    CACHEOPTIONS_EXP_OPTIONVAR: 0,
    CACHEVERSION_SORTING_TYPE_OPTIONVAR: 0,
    CUSTOM_ENV_PATH_OPTIONVAR: '',
    COMPARISON_EXP_OPTIONVAR: 0,
    EXPLOSION_DETECTION_OPTIONVAR: 0,
    EXPLOSION_TOLERENCE_OPTIONVAR: 3,
    FFMPEG_PATH_OPTIONVAR: '',
    MEDIAPLAYER_PATH_OPTIONVAR: '',
    MAYAPY_PATH_OPTIONVAR: '',
    MULTICACHE_EXP_OPTIONVAR: 0,
    PLAYBLAST_RESOLUTION_OPTIONVAR: '1024x640',
    PLAYBLAST_CAMERA_SELECTION_TYPE: 0,
    PLAYBLAST_VIEWPORT_OPTIONVAR: '0 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0',
    PLAYBLAST_EXP_OPTIONVAR: 0,
    RANGETYPE_OPTIONVAR: 0,
    RECORD_PLAYBLAST_OPTIONVAR: 1,
    SAMPLES_EVALUATED_OPTIONVAR: 1.0,
    SAMPLES_SAVED_OPTIONVAR: 1,
    TIMELIMIT_ENABLED_OPTIONVAR: 0,
    TIMELIMIT_OPTIONVAR: 1,
    USE_CUSTOM_ENV_OPTIONVAR: 0,
    VERBOSE_OPTIONVAR: 0,
    VERSION_EXP_OPTIONVAR: 0,
    WORKSPACES_RECENTLY_USED_OPTIONVAR: ''
}


# set default values from config file
cfg = ConfigParser.ConfigParser()
cfg.read(CONFIGFILE_PATH)
_match = (
    ('mayapy_default_path', MAYAPY_PATH_OPTIONVAR),
    ('ffmpeg_default_path', FFMPEG_PATH_OPTIONVAR),
    ('mediaplayer_default_path', MEDIAPLAYER_PATH_OPTIONVAR))
for option, optionvar in _match:
    custom_value = cfg.get('default_paths', option)
    OPTIONVARS[optionvar] = custom_value


def ensure_optionvars_exists():
    types = {int: 'intValue', float: 'floatValue', str: 'stringValue'}
    for optionvar, default_value in OPTIONVARS.items():
        if cmds.optionVar(exists=optionvar):
            continue
        kwargs = {types.get(type(default_value)): [optionvar, default_value]}
        cmds.optionVar(**kwargs)
