from maya import cmds
from ncachefactory.workspace import (
    WORKSPACE_NODENAME, ensure_workspaces_holder_exists,
    set_last_used_workspace, list_workspaces_recently_used,
    list_workspace_used, LAST_WORKSPACE_USED_ATTRIBUTE)
from ncachefactory.optionvars import WORKSPACES_RECENTLY_USED_OPTIONVAR


def test_workspaces_module():
    cmds.optionVar(stringValue=[WORKSPACES_RECENTLY_USED_OPTIONVAR, ""])
    if cmds.objExists(WORKSPACE_NODENAME):
        cmds.delete(WORKSPACE_NODENAME)
    ensure_workspaces_holder_exists()
    set_last_used_workspace("C:/")
    set_last_used_workspace("C:/SolideAngle")
    set_last_used_workspace("C:/")
    set_last_used_workspace("C:/SolideAngle")
    set_last_used_workspace("C:/SolideAngle")
    set_last_used_workspace("C:/Angle")
    assert list_workspace_used() == ["C:/Angle", "C:/SolideAngle", "C:/"]
    plug = WORKSPACE_NODENAME + '.' + LAST_WORKSPACE_USED_ATTRIBUTE
    assert cmds.getAttr(plug) == "C:/Angle"
    assert list_workspaces_recently_used() == ["C:/Angle", "C:/SolideAngle", "C:/"]
