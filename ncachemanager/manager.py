"""
This module is on top of cache and version
It combine both to work in a defined workspace
"""

from datetime import datetime
import os
from maya import cmds
from ncachemanager.versioning import (
    create_cacheversion, ensure_workspace_exists, find_file_match,
    clear_cacheversion_content)
from ncachemanager.ncache import (
    import_ncache, record_ncache, DYNAMIC_NODES, clear_cachenodes,
    list_connected_cachefiles, list_connected_cacheblends, append_ncache)
from ncachemanager.attributes import (
    save_pervertex_maps, extract_xml_attributes, list_node_attributes_values,
    clean_namespaces_in_attributes_dict)


def create_and_record_cacheversion(
        workspace, start_frame, end_frame, comment=None, name=None, nodes=None,
        behavior=0):
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
    return cacheversion


def record_in_existing_cacheversion(
        cacheversion, start_frame, end_frame, nodes=None, behavior=0):
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


def append_to_cacheversion(cacheversion, nodes=None):
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


if __name__ == "__main__":
    create_and_record_cacheversion(
        workspace="C:/test/chrfx",
        nodes=None,
        start_frame=0,
        end_frame=100,
        behavior=2,
        name="Cache",
        comment="salut")
