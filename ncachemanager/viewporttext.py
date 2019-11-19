
from maya import cmds
from PySide2 import QtGui


VIEWPORT_TEXT_SHADDER_NAME = "ncache_viewport_text_shader"
ORTOGRAPHIC_OFFSET = -14, 5, -1
ORTOGRAPHIC_SCALE = 0.04, 0.04, 0.04
NORMAL_OFFSET = -0.48, 0.15, -1
NORMAL_SCALE = 0.0015, 0.0015, 0.0015


def create_viewport_text(text, camera):
    group = cmds.group(empty=True, world=True)
    meshtext = create_text(text)
    meshparent = cmds.listRelatives(meshtext, parent=True)[0]
    cmds.parent(meshparent, group)
    constrain_group_to_camera(group, camera)
    if cmds.getAttr(camera + '.orthographic'):
        cmds.setAttr(meshparent + ".translate", *ORTOGRAPHIC_OFFSET)
        cmds.setAttr(meshparent + ".scale", *ORTOGRAPHIC_SCALE)
    else:
        cmds.setAttr(meshparent + ".translate", *NORMAL_OFFSET)
        cmds.setAttr(meshparent + ".scale", *NORMAL_SCALE)
    return text


def check_type_plugin():
    if cmds.pluginInfo("Type", loaded=True, query=True):
        return
    cmds.loadPlugin("Type")


def constrain_group_to_camera(group, camera):
    camera = cmds.listRelatives(camera, parent=True)[0]
    px, py, pz = cmds.xform(
        camera, query=True, translation=True, absolute=True, worldSpace=True)
    rx, ry, rz = cmds.xform(
        camera, query=True, rotation=True, absolute=True, worldSpace=True)
    camera_rotate_order = cmds.getAttr(camera + ".rotateOrder")
    cmds.setAttr(group + ".rotateOrder", camera_rotate_order)
    cmds.move(px, py, pz, group, worldSpace=True)
    cmds.rotate(rx, ry, rz, group, worldSpace=True)
    cmds.parentConstraint(camera, group, maintainOffset=True)


def create_text(text):
    check_type_plugin()
    typenode = cmds.createNode("type")
    mesh = cmds.createNode("mesh")
    text = string_to_hexadecimal(text)
    cmds.setAttr(typenode + '.textInput', text, type="string")
    cmds.setAttr(typenode + '.currentFont', "Arial", type="string")
    cmds.connectAttr(typenode +".outputMesh", mesh + '.inMesh')
    apply_text_shading(mesh)
    return mesh


def apply_text_shading(mesh):
    lambert = cmds.shadingNode(
        'lambert',
        asShader=True,
        name=VIEWPORT_TEXT_SHADDER_NAME,
        skipSelect=True)
    cmds.setAttr(lambert + '.color', 1, 1, 1, type="double3" )
    cmds.setAttr(lambert + '.incandescence', 1, 1, 1, type="double3")
    shadinggroup = cmds.sets(
        name=lambert + 'SG',
        renderable=True,
        noSurfaceShader=True,
        empty=True)
    cmds.connectAttr(lambert + '.outColor', shadinggroup + '.surfaceShader')
    transform = cmds.listRelatives(mesh, parent=True)
    cmds.sets(transform, add=lambert + 'SG')


def string_to_hexadecimal(string):
    """Convert a byte string to it's hex string representation e.g. for output.
    """
    return ''.join(["%02X " % ord(x) for x in string]).strip()


if __name__ == "__main__":
    create_viewport_text("salutlacompagnie", "perspShape")