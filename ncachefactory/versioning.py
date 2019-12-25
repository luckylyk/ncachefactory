"""
This module is the cache manager file system librairies.
It provide utils and constants of the file system cache management

The module respect a nomenclature:
    version: a folder containing all file of a cache:
        - the maya .mcc: the cache datas
        - the maya .xml: the setting used
        - the infos.json: json contain interesting information (range, nodes)
    workspace: a folder containing lot of versions

example of an infos.json structure
DEFAULT_INFOS = {
    'name': 'cache manager cache',
    'creation_time': 65000,
    'modification_time': 65252,
    'comment': 'comme ci comme ca',
    'playblasts': [],
    'nodes': {
        'nodename_1': {
            'range': (100, 150)}},
        'nodename_2': {
            'namespace': 'scene_saved_00'}}}
"""

import os
import json
import glob
import shutil
import time

INFOS_FILENAME = 'infos.json'
PLAYBLAST_FILENAME = 'playblast_{}.mp4'
VERSION_FOLDERNAME = 'version_{}'
WORKSPACE_FOLDERNAME = 'ncaches'
LOG_FILENAME = 'infos.log'


class CacheVersion(object):

    def __init__(self, directory):
        self.directory = directory.replace("\\", "/")
        self.infos_path = os.path.join(self.directory, INFOS_FILENAME)
        if not os.path.exists(self.infos_path):
            raise ValueError('Invalid version directory')
        self.infos = load_json(self.infos_path)

    def save_infos(self):
        save_json(self.infos_path, self.infos)

    def get_files(self, extension_filter=None):
        return [
            os.path.join(self.directory, f) for f in os.listdir(self.directory)
            if extension_filter is None or f.endswith('.' + extension_filter)]

    def get_available_playblast_filename(self):
        return get_available_playblast_filename(self.directory)

    def set_range(self, nodes=None, start_frame=None, end_frame=None):
        assert start_frame or end_frame
        nodes = nodes or self.infos['nodes']
        if not nodes:
            self.save_infos()
            return
        for node in nodes:
            # if only one value is modified, the other one is kept
            start = start_frame or self.infos['nodes'][node]['range'][0]
            end = end_frame or self.infos['nodes'][node]['range'][1]
            _, node = split_namespace_nodename(node)
            self.infos['nodes'][node]['range'] = start, end
        self.save_infos()

    def set_timespent(self, nodes=None, seconds=0):
        nodes = nodes or self.infos['nodes']
        if nodes:
            for node in nodes:
                _, node = split_namespace_nodename(node)
                self.infos['nodes'][node]['timespent'] = seconds
        self.save_infos()

    def add_playblast(self, playblast_filename):
        self.infos['playblasts'].append(playblast_filename)
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
    def workspace(self):
        return os.path.dirname(self.directory)

    def update(self):
        self.infos = load_json(self.infos_path)

    def update_modification_time(self):
        self.infos['modification_time'] = time.time()
        self.save_infos()

    def __eq__(self, cacheversion):
        assert isinstance(cacheversion, CacheVersion)
        return cacheversion.directory == self.directory

    def __ne__(self, cacheversion):
        assert isinstance(cacheversion, CacheVersion)
        return not self.__eq__(cacheversion)

    def __repr__(self):
        reprname = "CacheVersion | name={}, directory={}".format(
            self.infos["name"], self.directory)
        return reprname


def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def save_json(filename, data):
    with open(filename, 'w') as f:
        return json.dump(data, f, indent=2)


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
    name = directory[-3:] if name is None else name + '_' + directory[-3:]
    nodes_infos = {}
    for node in nodes:
        namespace, nodename = split_namespace_nodename(node)
        if nodename in nodes_infos:
            raise KeyError("{} is not unique")
        nodes_infos[nodename] = {
            'range': (start_frame, end_frame),
            'namespace': namespace,
            'timespent': timespent}
    time_ = time.time()
    infos = {
        'name': name,
        'creation_time': time_,
        'modification_time': time_,
        'comment': comment,
        'nodes': nodes_infos,
        'start_frame': start_frame,
        'end_frame': end_frame,
        'playblasts': []}

    infos_filepath = os.path.join(directory, INFOS_FILENAME)
    with open(infos_filepath, 'w') as infos_file:
        json.dump(infos, infos_file, indent=2, sort_keys=True)

    return CacheVersion(directory)


def list_nodes_in_cacheversions(cachversions):
    return list(set([v.infos['nodes'].keys() for v in cachversions]))


def cacheversion_contains_node(node, cacheversion, same_namespace=False):
    namespace, nodename = split_namespace_nodename(node)
    if same_namespace is False:
        return nodename in cacheversion.infos['nodes']
    if nodename not in cacheversion.infos['nodes']:
        return False
    return cacheversion.infos['nodes'][nodename]['namespace'] == namespace


def split_namespace_nodename(node):
    names = node.split(":")
    if len(names) == 2:
        return names[0], names[-1]
    elif len(names) >= 2:
        return ":".join(names[:-1]), names[-1]
    return None, names[0]


def find_file_match(node, cacheversion, extension='mcc'):
    _, nodename = split_namespace_nodename(node)
    filename = nodename + '.' + extension
    cached_namespace = cacheversion.infos["nodes"][nodename]["namespace"]
    if cached_namespace:
        filename = cached_namespace + '_' + filename
    for cacheversion_filename in cacheversion.get_files():
        if filename == os.path.basename(cacheversion_filename):
            return cacheversion_filename.replace("\\", "/")


def filter_cacheversions_containing_nodes(nodes, cacheversions):
    nodes = [split_namespace_nodename(node)[1] for node in nodes]
    filtered = set()
    for node in nodes:
        for cacheversion in cacheversions:
            if cacheversion_contains_node(node, cacheversion):
                filtered.add(cacheversion)
    return sorted(list(filtered), key=lambda x: x.name)


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


def get_available_playblast_filename(directory):
    i = 0
    filename = PLAYBLAST_FILENAME.format(str(i).zfill(4))
    while os.path.exists(os.path.join(directory, filename)):
        i += 1
        filename = PLAYBLAST_FILENAME.format(str(i).zfill(4))
    return os.path.join(directory, filename)


def move_playblast_to_cacheversion(source, cacheversion):
    destination = cacheversion.get_available_playblast_filename()
    os.rename(source, destination)
    cacheversion.add_playblast(destination)
    return destination


def get_log_filename(cacheversion):
    return os.path.join(cacheversion.directory, LOG_FILENAME)


def list_tmp_jpeg_under_cacheversion(cacheversion):
    jpegs = []
    directory = cacheversion.directory
    for _ in range(5):
        jpegs.extend(glob.glob(os.path.join(directory, "*.jpg")))
        directory = os.path.join(directory, "*")
    return sorted(jpegs)


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
