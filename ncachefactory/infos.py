
import datetime
import subprocess

from maya import cmds
from PySide2 import QtWidgets, QtCore

from ncachefactory.versioning import (
    filter_cacheversions_containing_nodes, cacheversion_contains_node)
from ncachefactory.cachemanager import (
    filter_connected_cacheversions, connect_cacheversion, apply_settings,
    plug_cacheversion_to_inputmesh, plug_cacheversion_to_restshape,
    recover_original_inputmesh)
from ncachefactory.optionvars import MEDIAPLAYER_PATH_OPTIONVAR
from ncachefactory.qtutils import get_icon
from ncachefactory.attributes import set_pervertex_maps


class WorkspaceCacheversionsExplorer(QtWidgets.QWidget):
    cacheApplied = QtCore.Signal()
    infosModified = QtCore.Signal()

    def __init__(self, parent=None):
        super(WorkspaceCacheversionsExplorer, self).__init__(parent)
        self.setFixedHeight(420)
        self.cacheversion = None
        self.nodes = None

        minpolicy = QtWidgets.QSizePolicy()
        minpolicy.setHorizontalPolicy(QtWidgets.QSizePolicy.Minimum)
        maxpolicy = QtWidgets.QSizePolicy()
        maxpolicy.setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)
        self.version_label = QtWidgets.QLabel("Version: ")
        self.version_label.setSizePolicy(minpolicy)
        self.version_selector_model = CacheversionsListModel()
        self.version_selector = QtWidgets.QComboBox()
        self.version_selector.setSizePolicy(maxpolicy)
        self.version_selector.setModel(self.version_selector_model)
        self.version_selector.currentIndexChanged.connect(self._call_index_changed)
        self.version_toolbal = CacheversionToolbar()
        self.version_toolbal.setSizePolicy(minpolicy)
        self.version_layout = QtWidgets.QHBoxLayout()
        self.version_layout.setContentsMargins(0, 0, 0, 0)
        self.version_layout.addWidget(self.version_label)
        self.version_layout.addWidget(self.version_selector)
        self.version_layout.addWidget(self.version_toolbal)

        self.groupbox_infos = QtWidgets.QGroupBox()
        self.cacheversion_infos = CacheversionInfosWidget()
        self.cacheversion_infos.infosModified.connect(self.infosModified.emit)
        self.layout_cacheversion = QtWidgets.QVBoxLayout(self.groupbox_infos)
        self.layout_cacheversion.setContentsMargins(0, 0, 0, 0)
        self.layout_cacheversion.addWidget(self.cacheversion_infos)

        self.connect_cache = QtWidgets.QPushButton("connect cache")
        self.connect_cache.released.connect(self._call_connect_cache)
        self.blend_cache = QtWidgets.QPushButton("blend cache")
        self.blend_cache.released.connect(self._call_blend_cache)
        self.connect_layout = QtWidgets.QHBoxLayout()
        self.connect_layout.setContentsMargins(0, 0, 0, 0)
        self.connect_layout.addWidget(self.connect_cache)
        self.connect_layout.addWidget(self.blend_cache)

        self.plug_input = QtWidgets.QPushButton("plug as input shape")
        self.plug_input.released.connect(self._call_plug_input)
        self.plug_rest = QtWidgets.QPushButton("plug as rest shape")
        self.plug_rest.released.connect(self._call_plug_rest)
        self.connect_layout2 = QtWidgets.QHBoxLayout()
        self.connect_layout2.setContentsMargins(0, 0, 0, 0)
        self.connect_layout2.addWidget(self.plug_input)
        self.connect_layout2.addWidget(self.plug_rest)

        text = "recover original input"
        self.recover_input = QtWidgets.QPushButton(text)
        self.recover_input.released.connect(self._call_recover_input)

        self.apply_settings = QtWidgets.QPushButton("apply settings")
        self.apply_settings.released.connect(self._call_apply_settings)
        self.blend_attributes = QtWidgets.QPushButton("%")
        self.blend_attributes.setFixedWidth(25)
        self.apply_maps = QtWidgets.QPushButton("apply maps")
        self.apply_maps.released.connect(self._call_apply_maps)
        self.attributes_layout = QtWidgets.QHBoxLayout()
        self.attributes_layout.setContentsMargins(0, 0, 0, 0)
        self.attributes_layout.setSpacing(0)
        self.attributes_layout.addWidget(self.apply_settings)
        self.attributes_layout.addSpacing(1)
        self.attributes_layout.addWidget(self.blend_attributes)
        self.attributes_layout.addSpacing(4)
        self.attributes_layout.addWidget(self.apply_maps)

        self.show_playblasts = QtWidgets.QPushButton("show playblasts")
        self.show_playblasts.released.connect(self._call_show_playblasts)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(4)
        self.layout.addLayout(self.version_layout)
        self.layout.addWidget(self.groupbox_infos)
        self.layout.addLayout(self.connect_layout)
        self.layout.addLayout(self.connect_layout2)
        self.layout.addWidget(self.recover_input)
        self.layout.addLayout(self.attributes_layout)
        self.layout.addWidget(self.show_playblasts)
        self.setEnabled(False)

    def update_ui_states(self):
        contains_clothnodes = bool(cmds.ls(self.nodes, type='nCloth'))
        self.plug_input.setEnabled(contains_clothnodes)
        self.plug_rest.setEnabled(contains_clothnodes)
        self.recover_input.setEnabled(contains_clothnodes)
        self.apply_maps.setEnabled(contains_clothnodes)
        if self.cacheversion is not None:
            playblasts_available = bool(self.cacheversion.infos['playblasts'])
            self.show_playblasts.setEnabled(playblasts_available)
        else:
            self.show_playblasts.setEnabled(False)

    def set_nodes_and_cacheversions(self, nodes=None, cacheversions=None):
        self.nodes = nodes
        if cacheversions is None or nodes is None:
            self.setEnabled(False)
            self.cacheversion_infos.set_cacheversion(None)
            return
        self.setEnabled(True)
        self.version_selector_model.set_cacheversions(
            filter_cacheversions_containing_nodes(nodes, cacheversions))
        cacheversions = filter_connected_cacheversions(nodes[0], cacheversions)
        if not cacheversions:
            self.version_selector.setCurrentIndex(0)
            return
        index = self.version_selector_model.cacheversions.index(cacheversions[0])
        self.version_selector.setCurrentIndex(index)
        self.update_ui_states()

    def _call_index_changed(self, index):
        if not self.version_selector_model.cacheversions:
            self.cacheversion = None
            self.cacheversion_infos.set_cacheversion(None)
            return
        self.cacheversion = self.version_selector_model.cacheversions[index]
        self.cacheversion_infos.set_cacheversion(self.cacheversion)
        self.update_ui_states()

    def get_connectable_nodes(self):
        nodes = []
        for node in self.nodes:
            if not cacheversion_contains_node(node, self.cacheversion):
                msg = '{} is not cached in version: {}. Skip connection'
                cmds.warning(msg.format(node, self.cacheversion.infos['name']))
                continue
            nodes.append(node)
        return nodes

    def _call_connect_cache(self):
        nodes = self.get_connectable_nodes()
        connect_cacheversion(self.cacheversion, nodes=nodes, behavior=0)

    def _call_blend_cache(self):
        nodes = self.get_connectable_nodes()
        connect_cacheversion(self.cacheversion, nodes=nodes, behavior=2)

    def _call_plug_input(self):
        nodes = cmds.ls(self.nodes, type='nCloth')
        plug_cacheversion_to_inputmesh(self.cacheversion, nodes)

    def _call_plug_rest(self):
        nodes = cmds.ls(self.nodes, type='nCloth')
        plug_cacheversion_to_restshape(self.cacheversion, nodes)

    def _call_recover_input(self):
        nodes = cmds.ls(self.nodes, type='nCloth')
        recover_original_inputmesh(nodes)

    def _call_apply_settings(self):
        apply_settings(self.cacheversion, self.nodes)

    def _call_apply_maps(self):
        nodes = cmds.ls(self.nodes, type='nCloth')
        set_pervertex_maps(self.nodes, self.cacheversion.directory)

    def _call_show_playblasts(self):
        mediaplayer = cmds.optionVar(query=MEDIAPLAYER_PATH_OPTIONVAR)
        if not mediaplayer:
            return
        playblasts = self.cacheversion.infos['playblasts']
        if not playblasts:
            return
        arguments = [mediaplayer] + self.cacheversion.infos['playblasts']
        subprocess.Popen(arguments)


class CacheversionsListModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
        super(CacheversionsListModel, self).__init__(parent)
        self.cacheversions = []

    def rowCount(self, *unused_signal_args):
        return len(self.cacheversions)

    def set_cacheversions(self, cacheversions):
        self.layoutAboutToBeChanged.emit()
        self.cacheversions = cacheversions
        self.layoutChanged.emit()

    def data(self, index, role):
        if not index.isValid():
            return
        if role == QtCore.Qt.DisplayRole:
            return self.cacheversions[index.row()].infos['name']


class CacheversionInfosWidget(QtWidgets.QWidget):
    infosModified = QtCore.Signal()

    def __init__(self, parent=None):
        super(CacheversionInfosWidget, self).__init__(parent)

        self.cacheversion = None
        self.name = QtWidgets.QLineEdit()
        self.name.setEnabled(False)
        self.name.textEdited.connect(self._call_name_changed)
        self.comment = QtWidgets.QTextEdit()
        self.comment.setFixedHeight(50)
        self.comment.setEnabled(False)
        self.comment.textChanged.connect(self._call_comment_changed)
        self.nodes_table_model = NodeInfosTableModel()
        self.nodes_table_view = NodeInfosTableView()
        self.nodes_table_view.setModel(self.nodes_table_model)

        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.addRow("name", self.name)
        self.form_layout.addRow("comment", self.comment)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.nodes_table_view)

    def set_cacheversion(self, cacheversion):
        self.blockSignals(True)
        self.cacheversion = cacheversion
        self.nodes_table_model.set_cacheversion(cacheversion)
        self.name.setEnabled(bool(cacheversion))
        self.comment.setEnabled(bool(cacheversion))
        if cacheversion is None:
            self.name.setText("")
            self.comment.setText("")
            return
        self.name.setText(cacheversion.name)
        self.comment.setText(cacheversion.infos["comment"])
        self.nodes_table_view.update_header()
        self.blockSignals(False)

    def _call_name_changed(self, text):
        if self.cacheversion is None:
            return
        self.cacheversion.set_name(text)
        self.infosModified.emit()

    def _call_comment_changed(self, *unused_signal_args):
        if self.cacheversion is None:
            return
        self.cacheversion.set_comment(self.comment.toHtml())


class NodeInfosTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(NodeInfosTableView, self).__init__(parent)
        self.configure()

    def configure(self):
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        scrollmode = QtWidgets.QAbstractItemView.ScrollPerPixel
        self.setVerticalScrollMode(scrollmode)
        self.setHorizontalScrollMode(scrollmode)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(mode)
        self.horizontalHeader().setSectionResizeMode(mode)
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    def update_header(self):
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.horizontalHeader().setSectionResizeMode(mode)


class NodeInfosTableModel(QtCore.QAbstractTableModel):
    HEADERS = "Node", "Range", "Namespace", "Time spent"

    def __init__(self, parent=None):
        super(NodeInfosTableModel, self).__init__(parent)
        self.infos = None
        self.nodes = None

    def columnCount(self, _):
        return len(self.HEADERS)

    def rowCount(self, _):
        if self.nodes is None:
            return 0
        return len(self.nodes)

    def set_cacheversion(self, cacheversion):
        self.layoutAboutToBeChanged.emit()
        if cacheversion is None:
            self.infos = None
            self.nodes = None
            self.layoutChanged.emit()
            return
        self.infos = cacheversion.infos
        self.nodes = sorted([n for n in self.infos['nodes']])
        self.layoutChanged.emit()

    def sort(self, column, order):
        if column != 2:
            return
        reverse_ = order == QtCore.Qt.AscendingOrder
        self.layoutAboutToBeChanged.emit()
        self.nodes = sorted(self.nodes, reverse=reverse_)
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        node = self.nodes[row]
        if role == QtCore.Qt.DisplayRole:
            if col == 0:
                return node
            if col == 1:
                frames = self.infos['nodes'][node]['range']
                return ", ".join([str(f) for f in frames])
            if col == 2:
                return self.infos['nodes'][node]['namespace'] or 'None'
            if col == 3:
                seconds = self.infos['nodes'][node]['timespent']
                delta = datetime.timedelta(seconds=seconds)
                return str(delta)

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter


class CacheversionToolbar(QtWidgets.QToolBar):

    def __init__(self, parent=None):
        super(CacheversionToolbar, self).__init__(parent)
        self.setIconSize(QtCore.QSize(15, 15))
        self.filter = QtWidgets.QAction(get_icon('filter.png'), '', self)
        self.filter.setToolTip('filter versions available for selected nodes')
        self.filter.setCheckable(True)
        self.sort = QtWidgets.QAction(get_icon('sort.png'), '', self)
        self.sort.setToolTip('sort version by')

        self.sort_menu = QtWidgets.QMenu()
        self.sort_menu.addAction('name')
        self.sort_menu.addAction('last modification')
        self.sort_menu.addAction('creation date')
        self.sort.setMenu(self.sort_menu)

        self.addAction(self.filter)
        self.addAction(self.sort)
