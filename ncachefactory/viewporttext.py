"""
Ornament option is not supported for hardware render 2.0 maya on batch. This
option crash maya. So this module allow a basic physical text creation in the
scene which is aligned to the camera. That's a bit stupid solution, but I
doesn't have other for playblast in batch :(.
"""


from maya import cmds
from PySide2 import QtGui


VIEWPORT_TEXT_SHADDER_NAME = "ncache_viewport_text_shader"
ORTOGRAPHIC_OFFSET = -14, 5, -1
ORTOGRAPHIC_SCALE = 0.04, 0.04, 0.04
NORMAL_OFFSET = -0.48, 0.15, 0
NORMAL_SCALE = 0.0015, 0.0015, 0.0015
REFERENCE_FOCAL = 35


def create_viewport_text(text, camera):
    group = cmds.group(empty=True, world=True)
    meshtext = create_text(text)
    meshparent = cmds.listRelatives(meshtext, parent=True)[0]
    if cmds.getAttr(camera + '.orthographic'):
        cmds.parent(meshparent, group)
        cmds.setAttr(meshparent + ".translate", *ORTOGRAPHIC_OFFSET)
        cmds.setAttr(meshparent + ".scale", *ORTOGRAPHIC_SCALE)
    else:
        cmds.setAttr(meshparent + ".translate", *NORMAL_OFFSET)
        cmds.setAttr(meshparent + ".scale", *NORMAL_SCALE)
        link_text_to_non_orthographic_camera(group, camera, meshparent)
    constrain_group_to_camera(group, camera)
    return text


def link_text_to_non_orthographic_camera(group, camera, text):
    ''' this function create a simple setup which drive the text scale
    by the camera focalLength.
    '''
    secondary_group = cmds.group(empty=True, world=True)
    cmds.parent(text, secondary_group)
    cmds.parent(secondary_group, group)
    cmds.setAttr(secondary_group + ".translateZ", -1)

    # mutliply out of focal
    multiply1 = cmds.createNode('multiplyDivide')
    cmds.setAttr(multiply1 + '.operation', 2)
    cmds.setAttr(multiply1 + '.input1.input1X', REFERENCE_FOCAL)
    cmds.connectAttr(camera + '.focalLength', multiply1 + '.input2.input2X')

    # multiply to compute film ratio
    multiply2 = cmds.createNode('multiplyDivide')
    cmds.setAttr(multiply2 + '.operation', 2)
    outplug = camera + '.cameraAperture.horizontalFilmAperture'
    inplug = multiply2 + '.input1.input1X'
    cmds.connectAttr(outplug, inplug)
    outplug = camera + '.cameraAperture.verticalFilmAperture'
    inplug = multiply2 + '.input2.input2X'
    cmds.connectAttr(outplug, inplug)

    # normalize ratio
    multiply3 = cmds.createNode('multiplyDivide')
    cmds.setAttr(multiply3 + '.operation', 2)
    outplug = multiply2 + '.output.outputX'
    inplug = multiply3 + '.input1.input1X'
    cmds.connectAttr(outplug, inplug)
    cmds.setAttr(multiply3 + '.input2.input2X', 1.5)

    # divid focal and ratio
    multiply4 = cmds.createNode('multiplyDivide')
    cmds.setAttr(multiply4 + '.operation', 2)
    outplug = multiply3 + '.output.outputX'
    inplug = multiply4 + '.input1.input1X'
    cmds.connectAttr(outplug, inplug)
    outplug = multiply1 + '.output.outputX'
    inplug = multiply4 + '.input2.input2X'
    cmds.connectAttr(outplug, inplug)

    # connect to text scale
    for axe in ['X', 'Y', 'Z']:
        outplug = multiply4 + '.output.outputX'
        cmds.connectAttr(outplug, secondary_group + '.scale.scale' + axe)


def check_type_plugin():
    if cmds.pluginInfo("Type", loaded=True, query=True):
        return
    cmds.loadPlugin("Type")


def constrain_group_to_camera(group, camera):
    ''' this function align the main group text with the given camera. And
    constrain the group to it in translate and rotate.
    '''
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
    # the nodeType "type" only support text as hexadecimal data
    text = string_to_hexadecimal(text)
    cmds.setAttr(typenode + '.textInput', text, type="string")
    cmds.setAttr(typenode + '.currentFont', "Arial", type="string")
    cmds.connectAttr(typenode +".outputMesh", mesh + '.inMesh')
    apply_text_shading(mesh)
    return mesh


def apply_text_shading(mesh):
    """ Create and apply a standard white lambert with incendescence to 1.0
    """
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
