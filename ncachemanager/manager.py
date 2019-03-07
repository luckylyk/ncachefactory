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
from ncachemanager.cache import (
    import_ncache, record_ncache, DYNAMIC_NODES, clear_cachenodes,
    list_connected_cachefiles, list_connected_cacheblends)
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
    save_pervertex_maps(nodes=nodes, directory=cacheversion.directory)
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
    save_pervertex_maps(nodes=nodes, directory=cacheversion.directory)
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


def connect_cacheversion(cacheversion, nodes=None, behavior=0):
    nodes = nodes or cmds.ls(type=DYNAMIC_NODES)
    for node in nodes:
        mcx_file = find_file_match(node, cacheversion, extention='mcx')
        if not mcx_file:
            continue
        import_ncache(node, mcx_file, behavior=behavior)


def delete_cacheversion(cacheversion):
    cachenames = [f[:-4] for f in cacheversion.get_files('mcx')]
    clear_cachenodes(cachenames=cachenames, workspace=cacheversion.workspace)
    clear_cacheversion_content(cacheversion)


def filter_connected_cacheversions(nodes=None, cacheversions=None):
    assert cacheversions is not None
    nodes = nodes or []
    cachenodes = (
        (list_connected_cacheblends(nodes) or []) +
        (list_connected_cachefiles(nodes) or []))
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
        # value in xml are slightly less precise than the current value
        # in maya, it doesn't compare the exact result but the difference
        if current_value is None or abs(current_value - value) < 1e-6:
            continue
        differences[key] = (current_value, value)
    return differences


if __name__ == "__main__":
    create_and_record_cacheversion(
        workspace="C:/test/chrfx", nodes=None, start_frame=0, end_frame=100,
        behavior=2, name="Cache", comment="salut")
