

import sys
import os
home = os.path.expanduser("~")
sys.path.append(r"D:\Works\Python\GitHub\ncachemanager")
from maya import cmds, mel
for key in sys.modules.keys():
    if 'ncachemanager' in key:
        print key
        del sys.modules[key]


def create_ncloth_test_scene():
    cmds.file(new=True, force=True)
    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', -3, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', -3, 0, -1)

    cmds.select([sphere_1, sphere_2])
    mel.eval('createNCloth 0')

    cmds.select([sphere_1 + ".vtx[381]", sphere_2 + ".vtx[381]"])
    mel.eval('createNConstraint("transform", "")')

    cmds.select([sphere_1 + ".vtx[53:70]", sphere_2 + ".vtx[0]"])
    mel.eval('createNConstraint("pointToPoint", "")')
    cmds.select([sphere_1, sphere_2 + ".vtx[35:50]"])
    mel.eval('createNConstraint("pointToSurface", "")')

    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', 4, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', 4, 0, -1)

    cmds.select([sphere_1, sphere_2])
    mel.eval('createNCloth 0')

    cmds.select([sphere_1])
    mel.eval('createNConstraint("transform", "")')

    cmds.select([sphere_1, sphere_2 + ".vtx[381]"])
    mel.eval('createNConstraint("pointToSurface", "")')


create_ncloth_test_scene()


import ncachemanager
ncachemanager.launch()