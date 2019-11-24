
import os
import json
import xml.etree.ElementTree
from maya import cmds
from ncachefactory.ncache import DYNAMIC_NODES


FILTERED_FOR_NCACHEMANAGER = 'isFilteredForNCacheManager'
ORIGINAL_INPUTSHAPE_ATTRIBUTE = 'originalInputShape'
TAGS = [
    {
        'longName': FILTERED_FOR_NCACHEMANAGER,
        'attributeType': 'bool',
        'defaultValue': False
    },
    {
        'longName': ORIGINAL_INPUTSHAPE_ATTRIBUTE,
        'attributeType': 'message',
    }
]

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
SUPPORTED_TYPES = (
    u'Int32Array',
    u'None',
    u'TdataCompound',
    u'bool',
    u'byte',
    u'double',
    u'double3',
    u'doubleArray',
    u'doubleLinear',
    u'enum',
    u'float',
    u'float3',
    u'floatAngle',
    u'long',
    u'long3',
    u'matrix',
    u'message',
    u'short',
    u'string',
    u'time',
    u'vectorArray')


def save_pervertex_maps(nodes=None, directory=''):
    nodes = nodes if nodes is not None else cmds.ls(type=DYNAMIC_NODES)
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
    nodes = nodes if nodes is not None else cmds.ls(type=DYNAMIC_NODES)
    filename = os.path.join(directory, PERVERTEX_FILE)
    with open(filename, 'r') as f:
        attributes = json.load(f)
    for node in nodes:
        for attribute, values in attributes[node].items():
            if values is None:
                continue
            cmds.setAttr(node + '.' + attribute, values, type='doubleArray')


def to_maya_value(string):
    if string.isdigit():
        return int(string)
    if '.' in string or ',' in string:
        if string.replace(',', '').replace('.', '').isdigit():
            return float(string)
    return string


def extract_xml_attributes(xml_file):
    tree = xml.etree.ElementTree.parse(xml_file).getroot()
    attributes = [element.text.split("=") for element in tree.findall('extra')]
    return {a[0]: to_maya_value(a[1]) for a in attributes if len(a) == 2}


def clean_namespaces_in_attributes_dict(attributes):
    for key in attributes:
        attributes[key.split(":")[-1]] = attributes.pop(key)
    return attributes


def list_node_attributes_values(node):
    attributes = {}
    for attribute in cmds.listAttr(node):
        try:
            plug = node + '.' + attribute
            attribute_type = cmds.getAttr(plug, type=True)
            if attribute_type is None or attribute_type not in SUPPORTED_TYPES:
                continue
            value = cmds.getAttr(plug)
            attributes[plug] = value
        # RuntimeError is not a numerical attribute
        except RuntimeError:
            pass
        # Value Error is a compount or subattribute
        except ValueError:
            pass
        # TypeError this is a WTF bug which happen sometime in maya. My raise
        # an error on the getAttr(plug, type=True) which says that True is not
        # a boolean. Ole !
        except TypeError:
            pass
    return attributes


def ensure_node_has_ncachemanager_tags(node):
    for tag in TAGS:
        if not cmds.attributeQuery(tag['longName'], node=node, exists=True):
            cmds.addAttr(node, **tag)


def list_wedgable_attributes(node):
    attributes = []
    for attribute in cmds.listAttr(node):
        plug = node + "." + attribute
        if plug.count(".") > 1:
            continue
        if cmds.getAttr(plug, type=True) not in ["double", "float", "int"]:
            continue
        attributes.append(attribute)
    return sorted(attributes)


def list_channelbox_highlited_plugs():
    '''this function inspect the maya ui and return all the selected plugs in
    the channelbox.'''
    plugs = set()
    channelbox = "mainChannelBox"
    kwargs = (
        ('selectedMainAttributes', 'mainObjectList'),
        ('selectedShapeAttributes', 'shapeObjectList'),
        ('selectedHistoryAttributes', 'historyObjectList'),
        ('selectedOutputAttributes', 'outputObjectList'))
    for kwattr, kwnode in kwargs:
        attributes = cmds.channelBox(channelbox, query=True, **{kwattr: True})
        nodes = cmds.channelBox(channelbox, query=True, **{kwnode: True})
        if attributes is None:
            continue
        for node in nodes:
            for attribute in attributes:
                plugs.add(node + '.' + attribute)
    return list(plugs)
