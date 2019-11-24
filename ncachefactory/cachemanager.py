"""
This module is on top of ncache and versioning
It combine both to work in a defined workspace
This is the main api used by the ui and can be useb from external script as
well.
"""

import os
import shutil
from datetime import datetime
from functools import partial
import subprocess

from maya import cmds
import maya.api.OpenMaya as om2

from ncachefactory.versioning import (
    create_cacheversion, ensure_workspace_exists, find_file_match,
    clear_cacheversion_content, cacheversion_contains_node,
    move_playblast_to_cacheversion)
from ncachefactory.mesh import (
    create_mesh_for_geo_cache, attach_geo_cache,
    is_deformed_mesh_too_stretched)
from ncachefactory.ncloth import (
    find_input_mesh_dagpath, clean_inputmesh_connection,
    find_output_mesh_dagpath)
from ncachefactory.ncache import (
    import_ncache, record_ncache, DYNAMIC_NODES, clear_cachenodes,
    list_connected_cachefiles, list_connected_cacheblends, append_ncache)
from ncachefactory.playblast import (
    start_playblast_record, stop_playblast_record)
from ncachefactory.attributes import (
    save_pervertex_maps, extract_xml_attributes, list_node_attributes_values,
    clean_namespaces_in_attributes_dict, ORIGINAL_INPUTSHAPE_ATTRIBUTE)
from ncachefactory.optionvars import MEDIAPLAYER_PATH_OPTIONVAR


ALTERNATE_INPUTSHAPE_GROUP = "alternative_inputshapes"
ALTERNATE_RESTSHAPE_GROUP = "alternative_restshapes"
INPUTSHAPE_SUFFIX = "_alternate_inputshape"
RESTSHAPE_SUFFIX = "_alternate_restshapes"


def create_and_record_cacheversion(
        workspace, start_frame, end_frame, comment=None, name=None,
        nodes=None, behavior=0, playblast=False,
        playblast_viewport_options=None):

    cloth_nodes = cmds.ls(nodes, type="nCloth")

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

    if playblast is True:
        start_playblast_record(
            directory=cacheversion.directory, **playblast_viewport_options)
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

    if playblast is True:
        temp_path = stop_playblast_record(cacheversion.directory)
        move_playblast_to_cacheversion(temp_path, cacheversion)
    return cacheversion


def record_in_existing_cacheversion(
        cacheversion, start_frame, end_frame, nodes=None, behavior=0,
        playblast=False, playblast_viewport_options=None):

    if playblast is True:
        start_playblast_record(
            directory=cacheversion.directory,**playblast_viewport_options)

    cloth_nodes = cmds.ls(nodes, type="nCloth")
    nodes = nodes or cmds.ls(type=DYNAMIC_NODES)
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

    if playblast is True:
        temp_path = stop_playblast_record(cacheversion.directory)
        move_playblast_to_cacheversion(temp_path, cacheversion)


def append_to_cacheversion(
        cacheversion, nodes=None, playblast=False,
        playblast_viewport_options=None):

    if playblast is True:
        start_playblast_record(
            directory=cacheversion.directory,**playblast_viewport_options)

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

    if playblast is True:
        temp_path = stop_playblast_record(cacheversion.directory)
        move_playblast_to_cacheversion(temp_path, cacheversion)


def plug_cacheversion(cacheversion, groupname, suffix, inattr, nodes=None):
    """ This function will plug a ncache to a given attribute.
    Basically, it create a static mesh based on the dynamic node input.
    Import the ncache as geo cache file and drive the created mesh with.
    And finally connect it to the input attribute given.
    """
    if not cmds.objExists(groupname):
        cmds.group(name=groupname, world=True, empty=True)
    group_content = cmds.listRelatives(groupname)
    group_content = cmds.ls(
        group_content,
        shapes=True,
        dag=True,
        noIntermediate=True)

    nodes = nodes or cmds.ls(type='nCloth')
    new_input_meshes = []
    for node in nodes:
        if not cacheversion_contains_node(node, cacheversion):
            continue
        ensure_original_input_is_stored(node)
        input_mesh = get_orignial_input_mesh(node)
        mesh = create_mesh_for_geo_cache(input_mesh, suffix)
        new_input_meshes.append(cmds.listRelatives(mesh, parent=True)[0])
        xml_file = find_file_match(node, cacheversion, extention='xml')
        attach_geo_cache(mesh, xml_file)
        clean_inputmesh_connection(node, inattr)
        cmds.connectAttr(mesh + '.worldMesh[0]', node + '.' + inattr)
    cmds.parent(new_input_meshes, groupname)
    # Parse the original group content and clean all the shape which are
    # not used anymore.
    content_to_clean = [
        cmds.listRelatives(node, parent=True)[0] for node in group_content
        if not cmds.ls(cmds.listConnections(node, type='nCloth'))]
    if content_to_clean:
        cmds.delete(content_to_clean)


def plug_cacheversion_to_inputmesh(cacheversion, nodes=None):
    plug_cacheversion(
        cacheversion=cacheversion,
        groupname=ALTERNATE_INPUTSHAPE_GROUP,
        suffix=INPUTSHAPE_SUFFIX,
        inattr='inputMesh',
        nodes=nodes)


def plug_cacheversion_to_restshape(cacheversion, nodes=None):
    plug_cacheversion(
        cacheversion=cacheversion,
        groupname=ALTERNATE_RESTSHAPE_GROUP,
        suffix=RESTSHAPE_SUFFIX,
        inattr='restShapeMesh',
        nodes=nodes)


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


def recover_original_inputmesh(nodes):
    """ this function replug the original input in a cloth node if this one as
    an alternate input connected. As an other simulation mesh """
    nodes_to_clean = []
    for node in nodes:
        store_plug = node + '.' + ORIGINAL_INPUTSHAPE_ATTRIBUTE
        stored_input_plugs = cmds.listConnections(
            store_plug,
            plugs=True,
            connections=True)
        if not stored_input_plugs:
            cmds.warning('no stored input for ' + node)
            continue
        inputmeshattr = node + '.inputMesh'
        current_inputs = cmds.listConnections(
            inputmeshattr,
            plugs=True,
            connections=True)
        if current_inputs:
            cmds.disconnectAttr(current_inputs[1], inputmeshattr)
        cmds.connectAttr(stored_input_plugs[1], inputmeshattr)
        disconnected_node = current_inputs[1].split('.')[0]
        if not cmds.listConnections(disconnected_node, source=True):
            nodes_to_clean.append(disconnected_node)
    if nodes_to_clean:
        cmds.delete(nodes_to_clean)


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


def ensure_original_input_is_stored(dynamicnode):
    store_plug = dynamicnode + '.' + ORIGINAL_INPUTSHAPE_ATTRIBUTE
    if cmds.listConnections(store_plug):
        # original input already saved
        return
    input_plug = dynamicnode + '.inputMesh'
    input_mesh_connections = cmds.listConnections(input_plug, plugs=True)
    if not input_mesh_connections:
        raise ValueError("No input attract mesh found for " + dynamicnode)
    cmds.connectAttr(input_mesh_connections[0], store_plug)


def get_orignial_input_mesh(dynamicnode):
    store_plug = dynamicnode + '.' + ORIGINAL_INPUTSHAPE_ATTRIBUTE
    connections = cmds.listConnections(store_plug, shapes=True)
    if connections:
        return connections[0]
    return


if __name__ == "__main__":
    create_and_record_cacheversion(
        workspace="C:/test/chrfx",
        nodes=None,
        start_frame=0,
        end_frame=100,
        behavior=2,
        name="Cache",
        comment="salut")
