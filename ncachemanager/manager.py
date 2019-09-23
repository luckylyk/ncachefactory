"""
This module is on top of ncache and versioning
It combine both to work in a defined workspace
"""

import os
from datetime import datetime
from functools import partial

from maya import cmds
import maya.api.OpenMaya as om2

from ncachemanager.versioning import (
    create_cacheversion, ensure_workspace_exists, find_file_match,
    clear_cacheversion_content, cacheversion_contains_node)
from ncachemanager.mesh import create_mesh_for_geo_cache, attach_geo_cache
from ncachemanager.ncloth import (
    find_input_mesh_dagpath, clean_inputmesh_connection)
from ncachemanager.ncache import (
    import_ncache, record_ncache, DYNAMIC_NODES, clear_cachenodes,
    list_connected_cachefiles, list_connected_cacheblends, append_ncache)

from ncachemanager.attributes import (
    save_pervertex_maps, extract_xml_attributes, list_node_attributes_values,
    clean_namespaces_in_attributes_dict, ORIGINAL_INPUTSHAPE_ATTRIBUTE)


ALTERNATE_INPUTSHAPE_GROUP = "alternative_inputshapes"
ALTERNATE_RESTSHAPE_GROUP = "alternative_restshapes"
INPUTSHAPE_SUFFIX = "_alternate_inputshape"
RESTSHAPE_SUFFIX = "_alternate_restshapes"


def create_and_record_cacheversion(
        workspace, start_frame, end_frame, comment=None, name=None, nodes=None,
        behavior=0, verbose=False):
    if verbose is True:
        callback = register_verbose_callback()

    nodes = nodes or cmds.ls(type=DYNAMIC_NODES)
    workspace = ensure_workspace_exists(workspace)
    cacheversion = create_cacheversion(
        workspace=workspace,
        name=name,
        comment=comment,
        nodes=nodes,
        start_frame=start_frame,
        end_frame=end_frame,
        timespent=None)
    # hairSystems doesn't contains vertex maps
    cloth_nodes = cmds.ls(nodes, type="nCloth")
    save_pervertex_maps(nodes=cloth_nodes, directory=cacheversion.directory)
    start_time = datetime.now()
    record_ncache(
        nodes=nodes,
        start_frame=start_frame,
        end_frame=end_frame,
        output=cacheversion.directory,
        behavior=behavior)
    end_time = datetime.now()
    timespent = (end_time - start_time).total_seconds()
    time = cmds.currentTime(query=True)
    cacheversion.set_range(nodes, start_frame=start_frame, end_frame=time)
    cacheversion.set_timespent(nodes=nodes, seconds=timespent)

    if verbose is True:
        om2.MMessage.removeCallback(callback)
    return cacheversion


def record_in_existing_cacheversion(
        cacheversion, start_frame, end_frame, nodes=None, behavior=0,
        verbose=False):
    if verbose is True:
        callback = register_verbose_callback()

    nodes = nodes or cmds.ls(type=DYNAMIC_NODES)
    # hairSystems doesn't contains vertex maps
    cloth_nodes = cmds.ls(nodes, type="nCloth")
    save_pervertex_maps(nodes=cloth_nodes, directory=cacheversion.directory)
    start_time = datetime.now()
    record_ncache(
        nodes=nodes,
        start_frame=start_frame,
        end_frame=end_frame,
        output=cacheversion.directory,
        behavior=behavior)
    end_time = datetime.now()
    timespent = (end_time - start_time).total_seconds()
    time = cmds.currentTime(query=True)
    cacheversion.set_range(nodes, start_frame=start_frame, end_frame=time)
    cacheversion.set_timespent(nodes=nodes, seconds=timespent)

    if verbose is True:
        om2.MMessage.removeCallback(callback)


def append_to_cacheversion(cacheversion, nodes=None, verbose=False):
    if verbose is True:
        callback = register_verbose_callback()

    nodes = nodes or cmds.ls(type=DYNAMIC_NODES)
    start_time = datetime.now()
    append_ncache(nodes=nodes)
    end_time = datetime.now()
    # Add up the second spent for the append cache to the cache time spent
    # already recorded.
    timespent = (end_time - start_time).total_seconds()
    for node in cacheversion.infos['nodes']:
        if node not in nodes:
            continue
        seconds = cacheversion.infos['nodes'][node]["timespent"] + timespent
        cacheversion.set_timespent(nodes=[node], seconds=seconds)
    # Update the cached range in the cache info if the append cache
    # finished further the original cache
    time = cmds.currentTime(query=True)
    end_frame = cacheversion.infos['nodes'][node]['range'][1]
    if time > end_frame:
        cacheversion.set_range(nodes=nodes, end_frame=time)

    if verbose is True:
        om2.MMessage.removeCallback(callback)


def connect_cacheversion_to_inputshape(cacheversion, nodes=None):
    if not cmds.objExists(ALTERNATE_INPUTSHAPE_GROUP):
        cmds.group(name=ALTERNATE_INPUTSHAPE_GROUP, world=True, empty=True)
    group_content = cmds.listRelatives(ALTERNATE_INPUTSHAPE_GROUP)
    cmds.delete(group_content)
    nodes = nodes or cmds.ls(type='nCloth')
    new_input_meshes = []
    for node in nodes:
        if not cacheversion_contains_node(node, cacheversion):
            continue
        ensure_original_input_is_saved(node)
        input_mesh = find_input_mesh_dagpath(node).name()
        mesh = create_mesh_for_geo_cache(input_mesh, INPUTSHAPE_SUFFIX)
        new_input_meshes.append(cmds.listRelatives(mesh, parent=True)[0])
        xml_file = find_file_match(node, cacheversion, extention='xml')
        attach_geo_cache(mesh, xml_file)
        clean_inputmesh_connection(node)
        cmds.connectAttr(mesh + '.outMesh', node + '.inputMesh')
    cmds.parent(new_input_meshes, ALTERNATE_INPUTSHAPE_GROUP)


def connect_cacheversion_to_restshape(cacheversion, nodes=None):
    if not cmds.objExists(ALTERNATE_RESTSHAPE_GROUP):
        cmds.group(name=ALTERNATE_RESTSHAPE_GROUP, world=True)
    group_content = cmds.listRelatives(ALTERNATE_RESTSHAPE_GROUP)
    cmds.delete(group_content)

    nodes = nodes or cmds.ls(type='nCloth')
    new_input_meshes = []
    for node in nodes:
        if not cacheversion_contains_node(node, cacheversion):
            continue
        input_mesh = find_input_mesh_dagpath(node).name()
        mesh = create_mesh_for_geo_cache(input_mesh, INPUTSHAPE_SUFFIX)
        new_input_meshes.append(cmds.listRelatives(mesh, parent=True)[0])
        xml_file = find_file_match(node, cacheversion, extention='xml')
        attach_geo_cache(mesh, xml_file)
        cmds.connectAttr(mesh + '.outMesh', node + '.restShapeMesh')
    cmds.parent(new_input_meshes, ALTERNATE_RESTSHAPE_GROUP)


def connect_cacheversion(cacheversion, nodes=None, behavior=0):
    nodes = nodes or cmds.ls(type=DYNAMIC_NODES)
    for node in nodes:
        xml_file = find_file_match(node, cacheversion, extention='xml')
        if not xml_file:
            cmds.warning("no cache to connect for {}".format(xml_file))
            continue
        import_ncache(node, xml_file, behavior=behavior)


def delete_cacheversion(cacheversion):
    cachenames = [f[:-4] for f in cacheversion.get_files('mcc')]
    clear_cachenodes(cachenames=cachenames, workspace=cacheversion.workspace)
    clear_cacheversion_content(cacheversion)


def filter_connected_cacheversions(nodes=None, cacheversions=None):
    assert cacheversions is not None
    nodes = nodes or []
    blends = list_connected_cacheblends(nodes) or []
    cachenodes = list_connected_cachefiles(nodes) or []
    cachenodes += list_connected_cachefiles(blends) or []
    directories = list({cmds.getAttr(n + '.cachePath') for n in cachenodes})
    directories = [os.path.normpath(directory) for directory in directories]
    return [
        cacheversion for cacheversion in cacheversions
        if os.path.normpath(cacheversion.directory) in directories]


def compare_node_and_version(node, cacheversion):
    filename = find_file_match(node, cacheversion, extention='xml')
    xml_attributes = extract_xml_attributes(filename)
    xml_attributes = clean_namespaces_in_attributes_dict(xml_attributes)
    node_attributes = list_node_attributes_values(node)
    node_attributes = clean_namespaces_in_attributes_dict(node_attributes)
    differences = {}
    for key, value in xml_attributes.items():
        current_value = node_attributes.get(key)
        # in case of value are store in format like: "-1e5", that's stored in
        # string instead of float. So we reconverted it to float
        if isinstance(value, str):
            value = float(value)
        # value in xml are slightly less precise than the current value
        # in maya, it doesn't compare the exact result but the difference
        if current_value is None or abs(current_value - value) < 1e-6:
            continue
        differences[key] = (current_value, value)
    return differences


def apply_settings(cacheversion, nodes):
    for node in nodes:
        filename = find_file_match(node, cacheversion, extention='xml')
        xml_attributes = extract_xml_attributes(filename)
        xml_attributes = clean_namespaces_in_attributes_dict(xml_attributes)
        for key, value in xml_attributes.items():
            attributes = cmds.ls([key, "*" + key, "*:" + key, "*:*:" + key])
            for attribute in attributes:
                atype = cmds.getAttr(attribute, type=True)
                cmds.setAttr(attribute, value, type=atype)


def register_verbose_callback():
    """ This function register a callback which print current frame and time
    spent on every frame cached. That mainly interesting to know the progress
    during a batch job.
    """
    # the list is created and passed to the verbose callback the function
    # directly edit the list which allow to compare the times between to frame
    # and compute the time spent per frame simulated.
    times = [None, datetime.now()]

    def verbose_callback(times, *useless_callback_args):
        times[0] = times[1]
        times[1] = datetime.now()
        timespent = str(times[1] - times[0])
        frame = cmds.currentTime(query=True)
        print "INFO ncache: frame {} cached, timespent {}".format(
            frame, timespent)

    function = partial(verbose_callback, times)
    return om2.MEventMessage.addEventCallback('timeChanged', function)


def ensure_original_input_is_saved(dynamicnode):
    save_plug = dynamicnode + '.' + ORIGINAL_INPUTSHAPE_ATTRIBUTE
    if cmds.listConnections(save_plug):
        # original input already saved
        return
    input_plug = dynamicnode + '.inputMesh'
    input_mesh_connections = cmds.listConnections(input_plug, plugs=True)
    if not input_mesh_connections:
        raise ValueError("No input attract mesh found for " + dynamicnode)
    cmds.connectAttr(input_mesh_connections[0], save_plug)


if __name__ == "__main__":
    create_and_record_cacheversion(
        workspace="C:/test/chrfx",
        nodes=None,
        start_frame=0,
        end_frame=100,
        behavior=2,
        name="Cache",
        comment="salut")
