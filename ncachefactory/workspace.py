'''
This module provide functions to manage and save the workspaces used to cache
with the factory. There 2 places where are stored the workspaces.
The tool store all the workspaces use to cache the scene in a "network" node.
It also save the 10 last differents workspaces used in an option var which
doesn't depend of the scene.
'''

import os
from maya import cmds
from ncachefactory.optionvars import WORKSPACES_RECENTLY_USED_OPTIONVAR


WORKSPACE_NODENAME = 'ncachefactory_workspaces_holder'
LAST_WORKSPACE_USED_ATTRIBUTE = 'ncache_factory_last_workspace_used'
WORKSPACES_USED_ATTRIBUTE = 'ncache_factory_workspaces_used'


def normpath(path):
    return path.replace("\\\\", "/")


def get_default_workspace():
    filename = cmds.file(expandName=True, query=True)
    if os.path.basename(filename) == 'untitled':
        return cmds.workspace(query=True, directory=True)
    return normpath(os.path.dirname(filename))


def get_last_used_workspace():
    if not cmds.objExists(WORKSPACE_NODENAME):
        return
    plug = WORKSPACE_NODENAME + '.' + LAST_WORKSPACE_USED_ATTRIBUTE
    workspace = cmds.getAttr(plug)
    if not os.path.exists(workspace):
        return None
    return workspace


def ensure_workspaces_holder_exists():
    cmds.namespace(set=':')
    if cmds.objExists(WORKSPACE_NODENAME):
        return
    holder = cmds.createNode('network', name=WORKSPACE_NODENAME)
    cmds.addAttr(holder, longName=LAST_WORKSPACE_USED_ATTRIBUTE, dataType='string')
    cmds.addAttr(holder, longName=WORKSPACES_USED_ATTRIBUTE, dataType='string')


def list_workspace_used():
    if not cmds.objExists(WORKSPACE_NODENAME):
        return []
    plug = WORKSPACE_NODENAME + '.' + WORKSPACES_USED_ATTRIBUTE
    workspaces = cmds.getAttr(plug)
    if not workspaces:
        return []
    return [normpath(workspace) for workspace in workspaces.split(";")]


def list_workspaces_recently_used():
    workspaces = cmds.optionVar(query=WORKSPACES_RECENTLY_USED_OPTIONVAR)
    if not workspaces:
        return []
    return [normpath(workspace) for workspace in workspaces.split(";")]


def set_last_used_workspace(workspace_directory):
    ensure_workspaces_holder_exists()
    workspace_directory = normpath(workspace_directory)
    plug = WORKSPACE_NODENAME + '.' + LAST_WORKSPACE_USED_ATTRIBUTE
    cmds.setAttr(plug, workspace_directory, type='string')
    existing_workspaces_used = list_workspace_used()
    if workspace_directory in existing_workspaces_used:
        existing_workspaces_used.remove(workspace_directory)
    existing_workspaces_used.insert(0, workspace_directory)
    plug = WORKSPACE_NODENAME + '.' + WORKSPACES_USED_ATTRIBUTE
    cmds.setAttr(plug, ";".join(existing_workspaces_used), type="string")
    workspaces_recently_used = list_workspaces_recently_used()
    if workspace_directory in workspaces_recently_used:
        workspaces_recently_used.remove(workspace_directory)
    workspaces_recently_used.insert(0, workspace_directory)
    value = ";".join(workspaces_recently_used[:10])
    cmds.optionVar(stringValue=[WORKSPACES_RECENTLY_USED_OPTIONVAR, value])


