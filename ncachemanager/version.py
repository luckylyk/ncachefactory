"""
This module is the cache manager file system librairies.
It provide utils and constants of the file system cache management

The module respect a nomenclature:
    version: a folder containing all file of a cache:
        - the maya .mcx: the cache datas
        - the maya .xml: the setting used
        - the infos.json: json contain interesting information (range, nodes)
    workspace: a folder containing lot of versions

example of an infos.json structure
DEFAULT_INFOS = {
    'name': 'cache manager cache',
    'comment': 'comme ci comme ca',
    'nodes': {
        'nodename_1': {
            'range': (100, 150)}},
        'nodename_2': {
            'namespace': 'scene_saved_00'}}}
"""

import os
import json
import shutil

INFOS_FILENAME = 'infos.json'
VERSION_FOLDERNAME = 'version_{}'
WORKSPACE_FOLDERNAME = 'caches'


class CacheVersion(object):
    def __init__(self, directory):
        self.directory = directory.replace("\\", "/")
        if not os.path.exists(os.path.join(self.directory, INFOS_FILENAME)):
            raise ValueError('Invalid version directory')

        self.xml_files = self._get_xml_files()
        self.mcx_files = self._get_mcx_files()
        self.infos = self._load_infos()

    def _load_infos(self):
        with open(os.path.join(self.directory, INFOS_FILENAME), 'r') as f:
            return json.load(f)

    def save_infos(self):
        with open(os.path.join(self.directory, INFOS_FILENAME), 'w') as f:
            return json.dump(self.infos, f, indent=2)

    def _get_mcx_files(self):
        return [
            os.path.join(self.directory, f) for f in os.listdir(self.directory)
            if f.endswith('.mcx')]

    def _get_xml_files(self):
        return [
            os.path.join(self.directory, f) for f in os.listdir(self.directory)
            if f.endswith('.xml')]

    def set_range(self, nodes=None, start_frame=None, end_frame=None):
        assert start_frame or end_frame
        nodes = nodes or self.infos['nodes']
        if nodes:
            for node in nodes:
                # if only one value is modified, the other one is kept
                start = start_frame or self.infos['nodes'][node]['range'][0]
                end = end_frame or self.infos['nodes'][node]['range'][1]
                self.infos['nodes'][node]['range'] = start, end
        self.save_infos()

    def set_timespent(self, nodes=None, seconds=0):
        nodes = nodes or self.infos['nodes']
        if nodes:
            for node in nodes:
                self.infos['nodes'][node]['time spent'] = seconds
        self.save_infos()

    def set_comment(self, comment):
        self.infos['comment'] = comment
        self.save_infos()

    def set_name(self, name):
        self.infos['name'] = name
        self.save_infos()

    @property
    def name(self):
        return self.infos['name']

    @property
    def files(self):
        return self.xml_files + self.mcx_files 

    def __eq__(self, cacheversion):
        assert isinstance(cacheversion, CacheVersion)
        return cacheversion.directory == self.directory



def list_available_cacheversion_directories(workspace):
    versions = [
        os.path.join(workspace, folder)
        for folder in os.listdir(os.path.join(workspace))
        if os.path.exists(os.path.join(workspace, folder, INFOS_FILENAME))]
    return sorted(versions, key=lambda x: os.stat(x).st_ctime)


def list_available_cacheversions(workspace):
    return [
        CacheVersion(p)
        for p in list_available_cacheversion_directories(workspace)]


def get_new_cacheversion_directory(workspace):
    increment = 0
    cacheversion_directory = os.path.join(
        workspace, VERSION_FOLDERNAME.format(str(increment).zfill(3)))

    while os.path.exists(cacheversion_directory):
        increment += 1
        cacheversion_directory = os.path.join(
            workspace, VERSION_FOLDERNAME.format(str(increment).zfill(3)))

    return cacheversion_directory.replace("\\", "/")


def create_cacheversion(
        workspace=None, name=None, comment=None, nodes=None,
        start_frame=0, end_frame=0, timespent=None):

    directory = get_new_cacheversion_directory(workspace)
    os.makedirs(directory)

    nodes_infos = {}
    for node in nodes:
        namespace, nodename = split_namespace_nodename(node)
        if nodename in nodes_infos:
            raise KeyError("{} is not unique")
        nodes_infos[nodename] = {
            'range': (start_frame, end_frame),
            'namespace': namespace,
            'time spent': timespent}

    infos = dict(
        name=name, comment=comment, nodes=nodes_infos,
        start_frame=0, end_frame=0)

    infos_filepath = os.path.join(directory, INFOS_FILENAME)
    with open(infos_filepath, 'w') as infos_file:
        json.dump(infos, infos_file, indent=2, sort_keys=True)

    return CacheVersion(directory)


def list_nodes_in_cacheversions(versions):
    return list(set([version.infos['nodes'].keys() for version in versions]))


def version_contains_node(version, node, same_namespace=False):
    namespace, nodename = split_namespace_nodename(node)
    if not same_namespace:
        return nodename in version.infos['nodes']

    if nodename not in version.infos['nodes']:
        return False
    return version.infos['nodes'][nodename]['namespace'] == namespace


def split_namespace_nodename(node):
    names = node.split(":")
    if len(names) > 1:
        return names[0], names[1]
    return None, names[0]


def find_file_match(node, cacheversion, extention='mcx'):
    _, nodename = split_namespace_nodename(node)
    filename = nodename + '.' + extention
    cached_namespace = cacheversion.infos["nodes"][nodename]["namespace"]
    if cached_namespace:
        filename = cached_namespace + '_' + filename
    for cacheversion_filename in cacheversion.files:
        if filename == os.path.basename(cacheversion_filename):
            return cacheversion_filename



def ensure_workspace_exists(workspace):
    if is_workspace_folder(workspace):
        return workspace
    return create_workspace_folder(workspace)


def create_workspace_folder(directory):
    directory = os.path.join(directory, WORKSPACE_FOLDERNAME)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def is_workspace_folder(directory):
    return os.path.basename(directory) == WORKSPACE_FOLDERNAME


def clear_cacheversion_content(cacheversion):
    shutil.rmtree(cacheversion.directory)


if __name__ == "__main__":
    workspace_ = 'c:/test/cache/'
    cacheversion_ = create_cacheversion(
        workspace=workspace_,
        name="Cache",
        comment="salut",
        nodes=['truc'],
        start_frame=1.0,
        end_frame=150.0,
        timespent=1253)

    cacheversion_.set_range(start_frame=1.0, end_frame=100.0)