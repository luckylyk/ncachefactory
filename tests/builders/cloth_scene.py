

import sys
import os
home = os.path.expanduser("~")
sys.path.append(r"D:\Works\Python\GitHub\ncachefactory")
from maya import cmds, mel
for key in sys.modules.keys():
    if 'ncachefactory' in key:
        print key
        del sys.modules[key]


def built_ncloth_test_scene(with_namespace=True):
    cmds.file(new=True, force=True)

    if with_namespace is True:
        cmds.namespace(add='namespaceTest')
        cmds.namespace(set='namespaceTest')

    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', -3, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', -3, 0, -1)

    cmds.select([sphere_1, sphere_2])
    ncloth = mel.eval('createNCloth 0')
    cmds.connectAttr(ncloth[0] + ".depthSort", ncloth[0] + ".isDynamic")

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

    nucleus = cmds.ls(type="nucleus")[0]
    cmds.setAttr(nucleus + '.startFrame', 10)
    cmds.playbackOptions(minTime=10)


if __name__ == "__main__":
    create_ncloth_test_scene()
    import ncachefactory
    ncachefactory.launch()