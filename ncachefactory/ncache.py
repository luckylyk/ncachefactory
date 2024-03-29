"""
This module is a collection of functions changing the automatic cache connection
system provided by maya. It's wrap aronud the mel command: doCreateNclothCache

By default maya allow the possibility to write cache for different node in a
single file. But this case is a nightmare to manage. So the manager force
a ncache with the flag : oneFilePerGeometry.
That's where the complexity start, cause maya doesn't allow this flag if a
cache is already connected in a dynamic node.
That's why this module is modifying the doCreateNclothCache behaviour.
The main module function is record_ncache. For more informations, refere to his
docstring.

The module respect a nomenclature:
    nodes = are maya dynamics nodes as string (type: 'nCloth', 'hairSystem')
    cacheblend = represent maya 'cacheBlend' node
    cachefile = represent maya 'cacheFile' node
    cachenodes = represent maya 'cacheFile' and 'cacheBlend' nodes

"""
import sys
from maya import cmds, mel
from ncachefactory.attributes import filter_invisible_nodes_for_manager


if sys.version_info[0] == 3:
    unicode = str


DYNAMIC_NODES = 'nCloth', 'hairSystem'
CACHE_COMMAND_TEMPLATE = """
doCreateNclothCache 5 {{ "0", "{start_frame}", "{end_frame}", \
"OneFilePerFrame", "1", "{output}", "1", "", "0", "replace", "1", \
"{evaluate_every_frame}", "{save_every_evaluation}", "0", "1","mcc"}}"""


def record_ncache(
        nodes=None, start_frame=0, end_frame=100, output=None, behavior=0,
        evaluate_every_frame=1.0, save_every_evaluation=1):
    '''
    this function is a wrap around the mel command doCreateNclothCache
    it force an cache with one cache per geometry (containing all frame).
    :nodes: one or list of dynamic nodes as string ('hairSystem' and 'nCloth')
    :output: output folder (without filename)
    :behavior: as int
        0: replace all old connected cachenodes and blendnodes
        1: replace all old connected cachenodes but add new cache in blendnodes
        2: blend all existing cachenodes with new cache
    :evaluate: eveluate every frames
    :evaluation: record every samples
    '''
    nodes = nodes or cmds.ls(DYNAMIC_NODES)
    nodes = filter_invisible_nodes_for_manager(nodes)
    output = output or ''

    if behavior == 0:
        cmds.delete(list_connected_cachefiles(nodes))
        cmds.delete(list_connected_cacheblends(nodes))
    elif behavior == 1:
        cmds.delete(list_connected_cachefiles(nodes))
        connections = disconnect_cachenodes(nodes)
    elif behavior == 2:
        connections = disconnect_cachenodes(nodes)

    cmds.select(nodes)
    command = CACHE_COMMAND_TEMPLATE.format(
        start_frame=start_frame,
        end_frame=end_frame,
        output=output,
        evaluate_every_frame=evaluate_every_frame,
        save_every_evaluation=save_every_evaluation)
    cache_nodes = mel.eval(command)

    if behavior:
        reconnect_cachenodes(connections)
    return cache_nodes


def append_ncache(nodes=None, evaluate_every_frame=1.0, save_every_evaluation=1):
    nodes = nodes or cmds.ls(DYNAMIC_NODES)
    nodes = filter_invisible_nodes_for_manager(nodes)
    cmds.cacheFile(
        refresh=True,
        noBackup=True,
        simulationRate=evaluate_every_frame,
        sampleMultiplier=save_every_evaluation,
        cacheableNode=nodes,
        startTime=cmds.currentTime(query=True),
        endTime=cmds.playbackOptions(max=True, query=True))


def import_ncache(node, filename, behavior=0):
    """
    This fubction create a cachenode and connect it to the corresponding
    dynamic node. It respect the record_ncache behavior system.
    :nodes: one or list of dynamic nodes as string ('hairSystem' and 'nCloth')
    :filename: path pointing an mcc file
    :behavior: as int
        0: replace all old connected cachenodes and blendnodes
        1: replace all old connected cachenodes but add new cache in blendnodes
        2: blend all existing cachenodes with new cache
    """
    connected_cachenode = get_connected_cachenode([node])
    if behavior == 0:
        cmds.delete(connected_cachenode)
    if behavior == 1:
        if cmds.nodeType(connected_cachenode) == "cacheFile":
            cmds.delete(connected_cachenode)
    connections = disconnect_cachenodes(node)

    def convert_channelname_to_inattr(channelname):
        plug = "_".join(channelname.split("_")[:-1])
        attribute = channelname.split("_")[-1]
        return plug + "." + attribute

    if cmds.nodeType(node) == 'hairSystem':
        channels = cmds.cacheFile(
            fileName=filename,
            query=True,
            channelName=True)
        inattrs = [
            convert_channelname_to_inattr(channel)
            for channel in channels]
    # doesn't need channel check for cloth nodes
    else:
        inattrs = node + '.positions'

    cachefile = cmds.cacheFile(
        attachFile=True,
        fileName=filename,
        inAttr=inattrs)
    cmds.connectAttr(cachefile + '.inRange', node + '.playFromCache')

    if connections:
        reconnect_cachenodes(connections)

    return cachefile

def reconnect_cachenodes(connections, nodetypes=None):
    '''
    this function reconnect the cache receveiving a dict with the connections
    setup before the cache.
    '''
    for cachenode, node in connections.iteritems():
        cachefile = get_connected_cachenode(node)
        if not cachefile:
            attach_cachenode(cachenode, node)
            continue

        cf_type = cmds.nodeType(cachefile)
        assert cf_type == 'cacheFile', '{} not cacheFile'.format(cachefile)

        if cmds.nodeType(cachenode) == 'cacheBlend':
            attach_cachefile_to_cacheblend(cachefile, cachenode, node)
            disconnect_cachenodes(node)
            attach_cachenode(cachenode, node)

        elif cmds.nodeType(cachenode) == 'cacheFile':
            cacheblend = cmds.createNode('cacheBlend')
            attach_cachefile_to_cacheblend(cachefile, cacheblend, node)
            attach_cachefile_to_cacheblend(cachenode, cacheblend, node)
            disconnect_cachenodes(node)
            attach_cachenode(cacheblend, node)


def list_connected_cachefiles(nodes=None):
    '''
    :nodes: one or list of dynamic nodes as string ('hairSystem' and 'nCloth')
    '''
    nodes = nodes or filter_invisible_nodes_for_manager(cmds.ls(DYNAMIC_NODES))
    if not nodes:
        return []
    cachenodes = cmds.listConnections(nodes, type='cacheFile')
    if cachenodes:
        return list(set(cachenodes))


def list_connected_cacheblends(nodes=None):
    '''
    :nodes: one or list of dyna,ic nodes as string ('hairSystem' and 'nCloth')
    '''
    nodes = nodes or filter_invisible_nodes_for_manager(cmds.ls(DYNAMIC_NODES))
    if not nodes:
        return []
    blendnodes = cmds.listConnections(nodes, type='cacheBlend')
    if blendnodes:
        return list(set(blendnodes))


def get_connected_cachenode(node):
    '''
    :node: dynamic node DYNAMIC_NODES as string
    :return: the connected cacheFile or cacheBlend as string or None
    '''
    assert cmds.nodeType(node) in DYNAMIC_NODES
    cachenodes = (
        (list_connected_cachefiles(node) or []) +
        (list_connected_cacheblends(node) or []))

    if not cachenodes:
        return
    elif len(cachenodes) > 1:
        raise ValueError(
            "More than 1 cache node is connected to {}".format(node))
    return cachenodes[0]


def get_connected_dynamicnodes(cachenode):
    connected_dynamicnodes = []
    for nodetype in DYNAMIC_NODES:
        nodes = cmds.listConnections(
            cachenode, shapes=True, source=False, type=nodetype)
        if nodes:
            connected_dynamicnodes += list(set(nodes))
    return connected_dynamicnodes


def disconnect_cachenodes(nodes=None):
    '''
    This function disconnect all cache node and return all connected nodes
    as dict.
    :nodes: one or list of dynamic nodes as string ('hairSystem' and 'nCloth')
    '''
    if isinstance(nodes, (str, unicode)):
        nodes = [nodes]

    attributes = {
        'hairSystem': [
            'playFromCache',
            'positions',
            'hairCounts',
            'vertexCounts'],
        'nCloth': [
            'playFromCache',
            'positions']}

    connections = {}
    for node in nodes:
        for attribute in attributes[cmds.nodeType(node)]:
            attribute_connections = cmds.listConnections(
                node + "." + attribute, plugs=True, connections=True)
            if not attribute_connections:
                continue
            inplug, outplug = attribute_connections
            cmds.disconnectAttr(outplug, inplug)
            # retrieve node connected
            connections[outplug.split(".")[0]] = inplug.split(".")[0]

    return connections


def find_free_cachedata_channel_index(cacheblend):
    i = 0
    while cmds.listConnections(cacheblend + '.cacheData[{}].start'.format(i)):
        i += 1
    return i


def connect_attributes(outnode, innode, connections):
    '''
    Connect a series of attribute from two nodes
    '''
    for out_attribute, in_attribute in connections.iteritems():
        cmds.connectAttr(
            '{}.{}'.format(outnode, out_attribute),
            '{}.{}'.format(innode, in_attribute))


def attach_cachefile_to_cacheblend(cachefile, cacheblend, node):
    i = find_free_cachedata_channel_index(cacheblend)
    connections = {
        'end': 'cacheData[{}].end'.format(i),
        'inRange': 'cacheData[{}].range'.format(i),
        'start': 'cacheData[{}].start'.format(i),
        'outCacheData[0]': 'inCache[0].vectorArray[{}]'.format(i)}

    if cmds.nodeType(node) == "hairSystem":
        connections.update({
            'outCacheData[1]': 'inCache[1].vectorArray[{}]'.format(i),
            'outCacheData[2]': 'inCache[2].vectorArray[{}]'.format(i)})

    connect_attributes(cachefile, cacheblend, connections)


def attach_cachenode(cachenode, node):
    if cmds.nodeType(node) == "nCloth":
        connections = {
            'outCacheData[0]': 'positions',
            'inRange': 'playFromCache'}
    else:
        connections = {
            'outCacheData[0]': 'hairCounts',
            'outCacheData[1]': 'vertexCounts',
            'outCacheData[2]': 'positions',
            'inRange': 'playFromCache'}
    connect_attributes(cachenode, node, connections)


def clear_cachenodes(nodes=None, cachenames=None, workspace=None):
    if nodes:
        cachenodes = (
            (list_connected_cachefiles(nodes) or []) +
            (list_connected_cacheblends(nodes) or []))
    else:
        cachenodes = cmds.ls(type=('cacheFile', 'cacheBlend'))
    cmds.delete(cachenodes)
    if (cachenames and workspace) is None:
        return
    cachenodes = cmds.ls(type='cacheFile')
    for cachenode in cachenodes:
        if cmds.getAttr(cachenode + '.cachePath') != workspace:
            continue
        if cmds.getAttr(cachenode + '.cacheName') in cachenames:
            cmds.delete(cachenode)


if __name__ == "__main__":
    #import_cachefile(r"hairSyst_emShape1", r"C:\test\chrfx\hairSyst_emShape1.mcc", behavior=2)
    #connections = disconnect_cachenodes("hairSyst_emShape1Cache1")
    record_ncache(
        nodes=None, start_frame=0, end_frame=100,
        output="C:/test/chrfx", behavior=2)
