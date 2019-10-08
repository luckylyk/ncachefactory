"""
This module contains all preferences saved available for the ncachemanager app
"""
from maya import cmds


VIEWPORT_ACTIVE_OPTIONVAR = 'ncachemanager_viewportactive'
RANGETYPE_OPTIONVAR = 'ncachemanager_rangetype'
CACHE_BEHAVIOR_OPTIONVAR = 'ncachemanager_behavior'
VERBOSE_OPTIONVAR = 'ncachemanager_verbose'
RECORD_PLAYBLAST_OPTIONVAR = 'ncachemanager_record_playblast'
PLAYBLAST_RESOLUTION_OPTIONVAR = 'ncachemanager_resolution_playblast'
EXPLOSION_DETECTION_OPTIONVAR = 'ncachemanager_explosion_detection'
EXPLOSION_TOLERENCE_OPTIONVAR = 'ncachemanager_explosion_tolerence'
TIMELIMIT_ENABLED_OPTIONVAR = 'ncachemanager_timelimit_enabled'
TIMELIMIT_OPTIONVAR = 'ncachemanager_timelimit'
FFMPEG_PATH_OPTIONVAR = 'ncachemanager_ffmpeg_path'

CACHEOPTIONS_EXP_OPTIONVAR = 'ncachemanager_cacheoptions_expanded'
PLAYBLAST_EXP_OPTIONVAR = 'ncachemanager_playblast_expanded'
CALLBACKS_EXP_OPTIONVAR = 'ncachemanager_callbacks_expanded'
COMPARISON_EXP_OPTIONVAR = 'ncachemanager_comparison_expanded'
VERSION_EXP_OPTIONVAR = 'ncachemanager_version_expanded'


OPTIONVARS = {
    VIEWPORT_ACTIVE_OPTIONVAR: 1,
    RANGETYPE_OPTIONVAR: 0,
    CACHE_BEHAVIOR_OPTIONVAR: 0,
    VERBOSE_OPTIONVAR: 0,
    RECORD_PLAYBLAST_OPTIONVAR: 1,
    PLAYBLAST_RESOLUTION_OPTIONVAR: '1024x640',
    EXPLOSION_DETECTION_OPTIONVAR: 0,
    EXPLOSION_TOLERENCE_OPTIONVAR: 3,
    TIMELIMIT_ENABLED_OPTIONVAR: 0,
    TIMELIMIT_OPTIONVAR: 1,
    FFMPEG_PATH_OPTIONVAR: '',
    CACHEOPTIONS_EXP_OPTIONVAR: 0,
    COMPARISON_EXP_OPTIONVAR: 0,
    CALLBACKS_EXP_OPTIONVAR: 0,
    PLAYBLAST_EXP_OPTIONVAR: 0,
    VERSION_EXP_OPTIONVAR: 0}


def ensure_optionvars_exists():
    for optionvar, default_value in OPTIONVARS.items():
        if cmds.optionVar(exists=optionvar):
            continue
        if isinstance(default_value, str):
            cmds.optionVar(stringValue=[optionvar, default_value])
            continue
        cmds.optionVar(intValue=[optionvar, default_value])
