from maya import cmds
import maya.api.OpenMaya as om2

from ncachemanager.ncloth import (
    get_clothnode_color, set_clothnode_color, switch_visibility,
    find_input_mesh_dagpath, find_output_mesh_dagpath, is_mesh_visible)
from ncachemanager.attributes import (
    ensure_node_has_ncachemanager_tags, FILTERED_FOR_NCACHEMANAGER)


class DynamicNode(object):
    """this object is a model for the DynamicNodeTableView and his delegate.
    It's linked to a maya node and contain method and properties needed for
    the table view"""
    ENABLE_ATTRIBUTE = None
    TYPE = None
    ICONS = {'on': None, 'off': None, 'visible': None, 'hidden': None}

    def __init__(self, nodename):
        if cmds.nodeType(nodename) != self.TYPE:
            raise ValueError('wrong node type, {} excepted'.format(self.TYPE))
        ensure_node_has_ncachemanager_tags(nodename)
        dependnode = om2.MSelectionList().add(nodename).getDependNode(0)
        self._dagnode = om2.MFnDagNode(dependnode)
        self._color = None

    @property
    def name(self):
        return self._dagnode.name()

    @property
    def parent(self):
        return cmds.listRelatives(self.name, parent=True)[0].split(':')[-1]

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

    @property
    def filtered(self):
        return cmds.getAttr(self.name + '.' + FILTERED_FOR_NCACHEMANAGER)

    def set_filtered(self, state):
        cmds.setAttr(self.name + '.' + FILTERED_FOR_NCACHEMANAGER, state)


class HairNode(DynamicNode):
    ENABLE_ATTRIBUTE = 'simulationMethod'
    TYPE = "hairSystem"
    ICONS = {
        'on': 'hairsystem.png',
        'off': 'hairsystem_off.png',
        'visible': 'visibility.png',
        'hidden': 'visibility_off.png'}

    @property
    def color(self):
        return cmds.getAttr(self.name + '.displayColor')[0]

    def set_color(self, red, green, blue):
        cmds.setAttr(self.name + '.displayColor', red, green, blue)

    @property
    def visible(self):
        return cmds.getAttr(self.name, '.solverDisplay')

    def set_visible(self, state):
        return cmds.setAttr(self.name, '.solverDisplay', state)


class ClothNode(DynamicNode):
    ENABLE_ATTRIBUTE = 'isDynamic'
    TYPE = "nCloth"
    ICONS = {
        'on': 'ncloth.png',
        'off': 'ncloth_off.png',
        'visible': 'current.png',
        'hidden': 'input.png'}

    def __init__(self, nodename):
        super(ClothNode, self).__init__(nodename)
        self._color = None
        self._in_mesh = find_input_mesh_dagpath(nodename)
        self._out_mesh = find_output_mesh_dagpath(nodename)

    @property
    def color(self):
        if self._color is None:
            self._color = get_clothnode_color(self.name)
        return self._color

    def set_color(self, red, green, blue):
        set_clothnode_color(self.name, red, green, blue)
        self._color = red, green, blue

    @property
    def visible(self):
        return is_mesh_visible(self._out_mesh.name())

    def set_visible(self, state):
        mesh_to_show = self._out_mesh if state else self._in_mesh
        mesh_to_hide = self._in_mesh if state else self._out_mesh
        switch_visibility(mesh_to_show.name(), mesh_to_hide.name())


def list_dynamic_nodes():
    return [
        create_dynamic_node(n) for n in cmds.ls(type=('hairSystem', 'nCloth'))]


def filtered_dynamic_nodes():
    return [n for n in list_dynamic_nodes() if not n.filtered]


def create_dynamic_node(nodename):
    if cmds.nodeType(nodename) == 'hairSystem':
        return HairNode(nodename)
    if cmds.nodeType(nodename) == 'nCloth':
        return ClothNode(nodename)
    cmds.warning(nodename + ' is not a dynamic node')