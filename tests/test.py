
import sys
import os
home = os.path.expanduser("~")
sys.path.append(os.path.realpath('{}/DEV/ncachemanager'.format(home)))

from maya import cmds, mel
from PySide2 import QtCore
from ncachemanager.ui import nodetable, qtutils, comparator
from ncachemanager.versioning import list_available_cacheversions
from ncachemanager.manager import create_and_record_cacheversion


def create_ncloth_test_scene():
    cmds.file(new=True, force=True)
    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', -3, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', -3, 0, -1)

    cmds.select([sphere_1, sphere_2])
    mel.eval('createNCloth 0')

    cmds.select([sphere_1 + ".vtx[381]", sphere_2 + ".vtx[381]"])
    dc = mel.eval('createNConstraint("transform", "")')

    cmds.select([sphere_1 + ".vtx[53:70]", sphere_2 + ".vtx[0]"])
    dc = mel.eval('createNConstraint("pointToPoint", "")')
    cmds.select([sphere_1, sphere_2 + ".vtx[35:50]"])
    dc = mel.eval('createNConstraint("pointToSurface", "")')

    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', 4, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', 4, 0, -1)

    cmds.select([sphere_1, sphere_2])
    mel.eval('createNCloth 0')

    cmds.select([sphere_1])
    dc = mel.eval('createNConstraint("transform", "")')

    cmds.select([sphere_1, sphere_2 + ".vtx[381]"])
    dc = mel.eval('createNConstraint("pointToSurface", "")')


workspace = home + "/ncachemanager_tests"
if not os.path.exists(workspace):
    os.makedirs(workspace)

create_ncloth_test_scene()
version = create_and_record_cacheversion(workspace, 1, 50)

view = nodetable.DynamicNodesTableWidget(qtutils.get_maya_windows())
view.set_workspace(workspace)
view.show()

view2 = comparator.ComparisonWidget('nClothShape2', version)
view2.show()
