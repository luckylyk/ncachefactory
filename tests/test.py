
from maya import cmds, mel
from PySide2 import QtCore
from ncachemanager.ui import table
from ncachemanager.nodes import ClothNode, HairNode
from ncachemanager.verisons import list_available_cacheversions

nodes = (
    [ClothNode(node) for node in cmds.ls('nCloth')] +
    [HairNode(node) for node in cmds.ls('hairSystem')])
versions = list_available_cacheversions(r"C:\test\chrfx\caches")
model = table.DynamicNodeTableModel()
model.set_nodes(nodes)
model.set_cacheversions(versions)

view = table.DynamicNodeTableView()
view.set_model(model)
view.setWindowFlags(QtCore.Qt.Window)
view.show()

def create_ncloth_test_scene():
    cmds.file(new=True, force=True)
    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', -3, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', -3, 0, -1)

    cmds.select([sphere_1, sphere_2])
    mel.eval('createNCloth 0')

    cmds.select([sphere_1 + ".vtx[381]", sphere_2 + ".vtx[381]"])
    dc = mel.eval('createNConstraint("transform")')
    dc.set_color(215, 25, 125)

    cmds.select([sphere_1 + ".vtx[53:70]", sphere_2 + ".vtx[0]"])
    dc = mel.eval('createNConstraint("pointToPoint")')
    dc.set_color(255, 0, 0)

    cmds.select([sphere_1, sphere_2 + ".vtx[35:50]"])
    dc = mel.eval('createNConstraint("pointToSurface")')
    dc.set_color(0, 125, 125)

    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', 4, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', 4, 0, -1)

    cmds.select([sphere_1, sphere_2])
    mel.eval('createNCloth 0')

    cmds.select([sphere_1])
    dc = mel.eval('createNConstraint("transform")')
    dc.set_color(0, 125, 125)

    cmds.select([sphere_1, sphere_2 + ".vtx[381]"])
    dc = mel.eval('createNConstraint("pointToSurface")')
    dc.set_color(0, 125, 125)


