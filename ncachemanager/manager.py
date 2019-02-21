"""
This module is on top of cache and version
It combine both to work in a defined workspace
"""

from datetime import datetime
from maya import cmds
from .version import (
    create_cacheversion, ensure_workspace_exists, find_mcx_file_match,
    clear_cacheversion_content)
from .cache import (
    import_ncache, record_ncache, DYNAMIC_NODES, import_ncache,
    clear_cachenodes, list_connected_cachefiles, list_connected_cacheblends)
from .maps import save_pervertex_maps


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
        mcx_file = find_mcx_file_match(node, cacheversion)
        if not mcx_file:
            continue
        import_ncache(node, mcx_file, behavior=behavior)


def delete_cacheversion(cacheversion):
    cachenames = [f[:-4] for f in cacheversion.mcx_file]
    clear_cachenodes(cachenames=cachenames, workspace=cacheversion.workspace)
    clear_cacheversion_content(cacheversion)


def filter_connected_cacheversions(nodes=None, cacheversions=None):
    assert cacheversions is not None
    nodes.extend(list_connected_cacheblends(nodes) or [])
    cachenodes = list_connected_cachefiles(nodes)
    directories = list({cmds.getAttr(n + '.filePath') for n in cachenodes})
    return [
        cacheversion for cacheversion in cacheversions
        if cacheversion.directory in directories]



if __name__ == "__main__":
    create_and_record_cacheversion(
        workspace="C:/test/chrfx", nodes=None, start_frame=0, end_frame=100,
        behavior=2, name="Cache", comment="salut")
