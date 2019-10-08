from maya import cmds, mel
import maya.api.OpenMaya as om2


CONNECT_GEO_CACHE_MEL_COMMAND = """\
string $filename = "{}";
string $filetype = "mcc";
string $geometries[] = {{"{}"}};
doImportCacheFile($filename, $filetype, $geometries, {{}});\
"""


def get_mesh_color(mesh):
    if not mesh:
        return None

    shading_engines = cmds.listConnections(
        mesh + '.instObjGroups', type='shadingEngine')
    if not shading_engines:
        return None

    shaders = cmds.listConnections(shading_engines[0] + '.surfaceShader')
    if not shaders:
        return None

    return cmds.getAttr(shaders[0] + '.color')[0]


def set_mesh_color(mesh, red, green, blue):
    old_shading_engines = cmds.listConnections(
        mesh + '.instObjGroups', type='shadingEngine')

    if not old_shading_engines:
        return None

    blinn = cmds.shadingNode('blinn', asShader=True)
    cmds.setAttr(blinn + ".color", red, green, blue, type='double3')

    selection = cmds.ls(sl=True)
    cmds.select(mesh)
    cmds.hyperShade(assign=blinn)
    # old_shading_engines should contain only one shading engine
    for shading_engine in old_shading_engines:
        connected = cmds.listConnections(shading_engine + ".dagSetMembers")
        if connected:
            return
        blinns = cmds.listConnections(shading_engine, type='blinn')
        cmds.delete(shading_engine)
        cmds.delete(blinns)
    cmds.select(selection)


def is_mesh_visible(mesh):
    return cmds.getAttr(mesh + ".intermediateObject") is False


def switch_meshes_visibilities(mesh_to_show, mesh_to_hide):
    cmds.setAttr(mesh_to_show + '.visibility', True)
    cmds.setAttr(mesh_to_show + '.intermediateObject', False)
    cmds.setAttr(mesh_to_hide + '.intermediateObject', True)


def create_mesh_for_geo_cache(mesh, suffix):
    copy = cmds.createNode('mesh')
    # get the copy mesh dag node because his parent is renamed during process
    # which rename the copy mesh node as well. This deprecate the copy variable
    dependnode = om2.MSelectionList().add(copy).getDependNode(0)
    dagnode = om2.MFnDagNode(dependnode)

    # cmds.setAttr(copy + '.intermediateObject', True)
    cmds.connectAttr(mesh + ".outMesh", copy + ".inMesh")
    cmds.refresh()
    cmds.disconnectAttr(mesh + ".outMesh", copy + ".inMesh")
    mesh_transform = cmds.listRelatives(mesh, parent=True)[0]
    copy_transform = cmds.listRelatives(copy, parent=True)[0]
    # create a unique name
    name = mesh_transform + suffix + '_'
    index = 0
    while cmds.objExists(name + str(index).zfill(3)):
        index += 1
    copy_transform = cmds.rename(copy_transform, name + str(index).zfill(3))

    return dagnode.name()


def attach_geo_cache(mesh, xml_file):
    transform = cmds.listRelatives(mesh, parent=True)[0]
    command = CONNECT_GEO_CACHE_MEL_COMMAND.format(xml_file, transform)
    mel.eval(command)


def is_deformed_mesh_too_stretched(
        deformed_mesh, reference_mesh, tolerence_factor=2):
    """ This function compare a deformed mesh to a reference mesh and query if
    some edges seems too stretched. The algorytm is simple, is parse the two
    meshes, compare edge per edge. If mesh deformed edge is longer than the
    reference mesh one multiplied by the tolerence factor, the function return
    False, else it return True.
    """
    selection_list = om2.MSelectionList()
    selection_list.add(deformed_mesh)
    selection_list.add(reference_mesh)
    deformed_edge_iterator = om2.MItMeshEdge(selection_list.getDagPath(0))
    reference_edge_iterator = om2.MItMeshEdge(selection_list.getDagPath(1))
    while not reference_edge_iterator.isDone():
        limit = tolerence_factor * reference_edge_iterator.length()
        if deformed_edge_iterator.length() > limit:
            return True
        reference_edge_iterator.next()
        deformed_edge_iterator.next()
    return False