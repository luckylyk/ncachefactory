

import sys
import os
home = os.path.expanduser("~")
sys.path.append(os.path.realpath('{}/DEV/ncachemanager'.format(home)))

for key in sys.modules.keys():
    if 'ncachemanager' in key:
        print key
        del sys.modules[key]

from maya import cmds, mel
from PySide2 import QtCore
from ncachemanager import nodetable, qtutils, comparator, main
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
