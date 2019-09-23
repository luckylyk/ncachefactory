from maya import cmds
import maya.api.OpenMaya as om2

from ncachemanager.ncloth import (
    find_input_mesh_dagpath, find_output_mesh_dagpath)
from ncachemanager.mesh import (
    set_mesh_color, get_mesh_color, is_mesh_visible,
    switch_meshes_visibilities)
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
        return cmds.getAttr(self.name + '.solverDisplay')

    def set_visible(self, state):
        return cmds.setAttr(self.name + '.solverDisplay', state)


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
        self._in_mesh = None
        self._out_mesh = None
        self._current_mesh = None

    def reset_connections(self):
        self._in_mesh = None
        self._out_mesh = None
        self._current_mesh = None
        self._color = None

    @property
    def in_mesh(self):
        # This property is an evaluation fix for maya 2019
        # Maya 2019 need time to create his connections to in and out mesh
        # When the ClothNode object is create during the maya ncloth node
        # creation call back process, connections to inmesh are not done
        # yet when the __init__ is triggered. This delay the assignement.
        if self._in_mesh is not None:
            return self._in_mesh
        try:
            self._in_mesh = find_input_mesh_dagpath(self.name)
            return self._in_mesh
        except:
            return None

    @property
    def current_mesh(self):
        if self._current_mesh is not None:
            return self._current_mesh
        if is_mesh_visible(self.out_mesh.name()):
            self._current_mesh = self.out_mesh
        else:
            self._current_mesh = self.in_mesh
        return self._current_mesh

    @property
    def out_mesh(self):
        # This property is an evaluation fix for maya 2019
        # Maya 2019 need time to create his connections to in and out mesh
        # When the ClothNode object is create during the maya ncloth node
        # creation call back process, connections to inmesh are not done
        # yet when the __init__ is triggered. This delay the assignement.
        if self._out_mesh is not None:
            return self._out_mesh
        try:
            self._out_mesh = find_output_mesh_dagpath(self.name)
            return self._out_mesh
        except:
            return None

    @property
    def color(self):
        if self._color is None:
            self._color = get_mesh_color(self.current_mesh.name())
        return self._color

    def set_color(self, red, green, blue):
        set_mesh_color(self.current_mesh.name(), red, green, blue)
        self._color = red, green, blue

    @property
    def visible(self):
        if self.out_mesh is None:
            return False
        return is_mesh_visible(self.out_mesh.name())

    def set_visible(self, state):
        if not self.out_mesh or not self.in_mesh:
            return
        mesh_to_show = self.out_mesh if state else self.in_mesh
        mesh_to_hide = self.in_mesh if state else self.out_mesh
        switch_meshes_visibilities(mesh_to_show.name(), mesh_to_hide.name())
        self._current_mesh = None
        self._color = None


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