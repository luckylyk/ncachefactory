from maya import cmds
import maya.api.OpenMaya as om2

def get_clothnode_color(clothnode_name):
    outmeshes = cmds.listConnections(
        clothnode_name + '.outputMesh', type='mesh', shapes=True)
    if not outmeshes:
        return None

    shading_engines = cmds.listConnections(
        outmeshes[0] + '.instObjGroups', type='shadingEngine')
    if not shading_engines:
        return None

    shaders = cmds.listConnections(shading_engines[0] + '.surfaceShader')
    if not shaders:
        return None

    return cmds.getAttr(shaders[0] + '.color')[0]


def set_clothnode_color(clothnode_name, red, green, blue):
    outmeshes = cmds.listConnections(
        clothnode_name + '.outputMesh', type='mesh', shapes=True)
    if not outmeshes:
        return None
    old_shading_engines = cmds.listConnections(
        outmeshes[0] + '.instObjGroups', type='shadingEngine')
    if not old_shading_engines:
        return None

    blinn = cmds.shadingNode('blinn', asShader=True)
    cmds.setAttr(blinn + ".color", red, green, blue, type='double3')

    selection = cmds.ls(sl=True)
    cmds.select(outmeshes)
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


def find_input_mesh_dagpath(clothnode_name):
    input_meshes = cmds.listConnections(
        clothnode_name + '.inputMesh', shapes=True, type='mesh')
    if not input_meshes:
        return None
    dependnode = om2.MSelectionList().add(input_meshes[0]).getDependNode(0)
    return om2.MFnDagNode(dependnode)


def find_output_mesh_dagpath(clothnode_name):
    history = cmds.listHistory(clothnode_name, future=True)
    output_meshes = cmds.ls(history, dag=True, type='mesh')
    if not output_meshes:
        return None
    dependnode = om2.MSelectionList().add(output_meshes[0]).getDependNode(0)
    return om2.MFnDagNode(dependnode)


def is_mesh_visible(mesh):
    return (cmds.getAttr(mesh + ".intermediateObject") is False)


def switch_visibility(mesh_to_show, mesh_to_hide):
    cmds.setAttr(mesh_to_show + '.visibility', True)
    cmds.setAttr(mesh_to_show + '.intermediateObject', False)
    cmds.setAttr(mesh_to_hide + '.intermediateObject', True)
