from maya import cmds
import maya.api.OpenMaya as om2

class DynamicNode(object):
    """this object is a model for the DynamicNodeTableView and his delegate.
    It's linked to a maya node and contain method and properties needed for
    the table view"""
    ENABLE_ATTRIBUTE = None
    TYPE = None
    ICONS = {'on': None, 'off': None}

    def __init__(self, nodename):
        if cmds.nodeType(nodename) != self.TYPE:
            raise ValueError('wrong node type, {} excepted'.format(self.TYPE))
        dependnode = om2.MSelectionList().add(nodename).getDependNode(0)
        self._dagnode = om2.MFnDagNode(dependnode)
        self._color = None

    @property
    def name(self):
        return self._dagnode.name()

    @property
    def parent(self):
        return cmds.listRelatives(self.name, parent=True)

    @property
    def is_cached(self):
        return bool(cmds.listConnections(self.name + '.playFromCache'))

    @property
    def cache_nodetype(self):
        if not self.is_cached:
            return None
        connections = cmds.listConnections(self.name + '.playFromCache')
        if not connections:
            return None
        return cmds.nodeType(connections[0])

    @property
    def enable(self):
        return cmds.getAttr(self.name + '.' + self.ENABLE_ATTRIBUTE)

    def switch(self):
        value = not self.enable
        cmds.setAttr(self.name + '.' + self.ENABLE_ATTRIBUTE, value)


class HairNode(DynamicNode):
    ENABLE_ATTRIBUTE = 'simulationMethod'
    TYPE = "hairSystem"
    ICONS = {'on': 'hairsystem.png', 'off': 'hairsystem_off.png'}

    @property
    def color(self):
        return cmds.getAttr(self.name + '.displayColor')[0]

    def set_color(self, red, green, blue):
        cmds.setAttr(self.name + '.displayColor', red, green, blue)


class ClothNode(DynamicNode):
    ENABLE_ATTRIBUTE = 'isDynamic'
    TYPE = "nCloth"
    ICONS = {'on': 'ncloth.png', 'off': 'ncloth_off.png'}

    def __init__(self, nodename):
        super(ClothNode, self).__init__(nodename)
        self._color = None

    @property
    def color(self):
        if self._color is None:
            self._color = get_clothnode_color(self.name)
        return self._color

    def set_color(self, red, green, blue):
        set_clothnode_color(self.name, red, green, blue)
        self._color = red, green, blue


def list_dynamic_nodes():
    return [
        create_dynamic_node(n) for n in cmds.ls(type=('hairSystem', 'nCloth'))]


def create_dynamic_node(nodename):
    if cmds.nodeType(nodename) == 'hairSystem':
        return HairNode(nodename)
    if cmds.nodeType(nodename) == 'nCloth':
        return ClothNode(nodename)
    cmds.warning(nodename + ' is not a dynamic node')


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

