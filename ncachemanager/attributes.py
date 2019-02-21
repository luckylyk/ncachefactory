
import os
import json
from maya import cmds
from .cache import DYNAMIC_NODES


PERVERTEX_FILE = 'pervertexmaps.json'
PERVERTEX_ATTRIBUTE = [
    u'thicknessPerVertex',
    u'bouncePerVertex',
    u'frictionPerVertex',
    u'dampPerVertex',
    u'stickinessPerVertex',
    u'collideStrengthPerVertex',
    u'massPerVertex',
    u'fieldMagnitudePerVertex',
    u'stretchPerVertex',
    u'compressionPerVertex',
    u'bendPerVertex',
    u'bendAngleDropoffPerVertex',
    u'restitutionAnglePerVertex',
    u'rigidityPerVertex',
    u'deformPerVertex',
    u'inputAttractPerVertex',
    u'restLengthScalePerVertex',
    u'liftPerVertex',
    u'dragPerVertex',
    u'tangentialDragPerVertex',
    u'wrinklePerVertex']


def save_pervertex_maps(nodes=None, directory=''):
    nodes = nodes or cmds.ls(type=DYNAMIC_NODES)
    attributes = {}
    filename = os.path.join(directory, PERVERTEX_FILE)
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            attributes.update(json.load(f) or {})
    attributes.update({
        node.split(":")[-1]: {
            at: cmds.getAttr(node + '.' + at) for at in PERVERTEX_ATTRIBUTE}
        for node in nodes})
    with open(filename, 'w') as f:
        json.dump(attributes, f, indent=2, sort_keys=True)


def set_pervertex_maps(nodes=None, directory=''):
    nodes = nodes or cmds.ls(type=DYNAMIC_NODES)
    filename = os.path.join(directory, PERVERTEX_FILE)
    with open(filename, 'r') as f:
        attributes = json.load(f)
    for node in nodes:
        for attribute, values in attributes[node].items():
            cmds.setAttr(
                node + '.' + attribute, values, dataType='doubleArray')


