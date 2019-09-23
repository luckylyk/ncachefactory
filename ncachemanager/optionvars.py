from maya import cmds

VIEWPORT_ACTIVE_OPTIONVAR = 'ncachemanager_viewportactive'
RANGETYPE_OPTIONVAR = 'ncachemanager_rangetype'
CACHE_BEHAVIOR_OPTIONVAR = 'ncachemanager_behavior'
VERBOSE_OPTIONVAR = 'ncachemanager_verbose'

CACHEOPTIONS_EXP_OPTIONVAR = 'ncachemanager_cacheoptions_expanded'
COMPARISON_EXP_OPTIONVAR = 'ncachemanager_comparison_expanded'
VERSION_EXP_OPTIONVAR = 'ncachemanager_version_expanded'

OPTIONVARS = {
    VIEWPORT_ACTIVE_OPTIONVAR: 1,
    RANGETYPE_OPTIONVAR: 0,
    CACHE_BEHAVIOR_OPTIONVAR: 0,
    VERBOSE_OPTIONVAR: 0,
    CACHEOPTIONS_EXP_OPTIONVAR: 0,
    COMPARISON_EXP_OPTIONVAR: 0,
    VERSION_EXP_OPTIONVAR: 0}


def ensure_optionvars_exists():
    for optionvar, default_value in OPTIONVARS.items():
        if not cmds.optionVar(exists=optionvar):
            print optionvar, default_value
            cmds.optionVar(intValue=[optionvar, default_value])
