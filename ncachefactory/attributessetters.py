from PySide2 import QtWidgets, QtCore
from ncachefactory.versioning import find_file_match, extract_xml_attributes
from ncachefactory.attributes import (
    set_pervertex_maps, PERVERTEX_ATTRIBUTES, apply_attibutes_dict)


MAP_TRANSFER_WINDOW = "Dynamic maps transfer tool"
ATTRIBUTES_TRANSFER_WINDOW = "Attribute transfer from version"


class AttributesTransferWindow(QtWidgets.QWidget):
    HEADER_LABELS = ["plug", "value"]

    def __init__(self, cacheversion, nodes=None, parent=None):
        super(AttributesTransferWindow, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(ATTRIBUTES_TRANSFER_WINDOW)
        self.cacheversion = cacheversion
        self.datas = self._gather_attributes_datas(nodes)
        selectionmode = QtWidgets.QAbstractItemView.ExtendedSelection
        self.nodelist = QtWidgets.QListWidget()
        self.nodelist.addItems(sorted(self.datas.keys()))
        self.nodelist.itemSelectionChanged.connect(self._selection_changed)
        self.nodelist.setSelectionMode(selectionmode)

        self.attributestable = QtWidgets.QTableWidget()
        self.attributestable.setColumnCount(2)
        self.attributestable.setSelectionMode(selectionmode)
        behavior = QtWidgets.QAbstractItemView.SelectRows
        self.attributestable.setSelectionBehavior(behavior)
        self.attributestable.verticalHeader().hide()
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.attributestable.verticalHeader().setSectionResizeMode(mode)
        self.attributestable.horizontalHeader().setSectionResizeMode(mode)
        self.attributestable.horizontalHeader().setStretchLastSection(True)
        self.attributestable.setShowGrid(False)
        self.attributestable.setWordWrap(False)
        self.attributestable.setAlternatingRowColors(True)
        self.attributestable.setHorizontalHeaderLabels(self.HEADER_LABELS)

        self.apply_all = QtWidgets.QPushButton("Apply all settings")
        self.apply_all.released.connect(self._call_apply_all)
        text = "Apply all settings on selected nodes"
        self.apply_all_on_selected_nodes = QtWidgets.QPushButton(text)
        method = self._call_apply_on_nodes_selected
        self.apply_all_on_selected_nodes.released.connect(method)
        text = "Apply selected settings"
        self.apply_attributes_selected = QtWidgets.QPushButton(text)
        method = self._call_apply_attributes_selected
        self.apply_attributes_selected.released.connect(method)
        self.sliderlabel = QtWidgets.QLabel("Blend with scene: ")
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMaximum(100)
        self.slider.setMinimum(0)
        self.slider.setSliderPosition(100)
        self.slider.setSingleStep(1)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.apply_all)
        self.button_layout.addWidget(self.apply_all_on_selected_nodes)
        self.button_layout.addWidget(self.apply_attributes_selected)
        self.button_layout.addWidget(self.sliderlabel)
        self.button_layout.addWidget(self.slider)
        self.button_layout.addStretch(1)

        self.splitter = QtWidgets.QSplitter()
        self.splitter.addWidget(self.nodelist)
        self.splitter.addWidget(self.attributestable)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.splitter)
        self.layout.addLayout(self.button_layout)

    def _selection_changed(self):
        self.attributestable.clear()
        nodes = [item.text() for item in self.nodelist.selectedItems()]
        datas = sorted([tpl for node in nodes for tpl in self.datas[node]])
        self.attributestable.setRowCount(len(datas))
        for i, (attribute, value) in enumerate(datas):
            attribute_item = QtWidgets.QTableWidgetItem(attribute)
            attribute_item.plug = attribute
            attribute_item.value = value
            value_item = QtWidgets.QTableWidgetItem(str(value))
            self.attributestable.setItem(i, 0, attribute_item)
            self.attributestable.setItem(i, 1, value_item)
        self.attributestable.setHorizontalHeaderLabels(self.HEADER_LABELS)

    def _gather_attributes_datas(self, nodes):
        attributes = {}
        for node in nodes:
            xml = find_file_match(node, self.cacheversion, extension='xml')
            attributes.update(extract_xml_attributes(xml))

        nodes = set([key.split(".")[0] for key in attributes.keys()])
        datas = {node: [] for node in nodes}
        for attribute, value in attributes.items():
            key = attribute.split(".")[0]
            datas[key].append([attribute, value])

        return datas

    def _call_apply_all(self):
        attributes = {}
        for _, data in self.datas.items():
            attributes.update(data)
        blend = self.slider.value() / 100.0
        apply_attibutes_dict(attributes, blend=blend)

    def _call_apply_on_nodes_selected(self):
        attributes = {}
        nodes = [item.text() for item in self.nodelist.selectedItems()]
        for node, data in self.datas.items():
            if node in nodes:
                attributes.update(data)
        blend = self.slider.value() / 100.0
        apply_attibutes_dict(attributes, blend=blend)

    def _call_apply_attributes_selected(self):
        attributes = {
            item.plug: item.value
            for item in self.attributestable.selectedItems()
            if item.column() == 0}
        blend = self.slider.value() / 100.0
        apply_attibutes_dict(attributes, blend=blend)


class DynamicMapTransferWindow(QtWidgets.QWidget):
    def __init__(self, cacheversion, nodes=None, parent=None):
        super(DynamicMapTransferWindow, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(MAP_TRANSFER_WINDOW)
        self.cacheversion = cacheversion
        self.nodelist = QtWidgets.QListWidget()
        self.nodelist.addItems(nodes)
        selectionmode = QtWidgets.QAbstractItemView.ExtendedSelection
        self.nodelist.setSelectionMode(selectionmode)
        self.maplist = QtWidgets.QListWidget()
        self.maplist.addItems(PERVERTEX_ATTRIBUTES)
        self.maplist.setSelectionMode(selectionmode)

        self.apply_all = QtWidgets.QPushButton("Apply all maps")
        self.apply_all.released.connect(self._call_apply_all)
        self.apply_all_on_selection = QtWidgets.QPushButton("Apply maps on selection")
        self.apply_all_on_selection.released.connect(self._call_apply_on_selection)
        self.apply_selected_maps = QtWidgets.QPushButton("Apply selected maps")
        self.apply_selected_maps.released.connect(self._call_apply_selected_maps)

        self.button_layout = QtWidgets.QVBoxLayout()
        self.button_layout.addWidget(self.apply_all)
        self.button_layout.addWidget(self.apply_all_on_selection)
        self.button_layout.addWidget(self.apply_selected_maps)
        self.button_layout.addStretch(1)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.nodelist)
        self.layout.addWidget(self.maplist)
        self.layout.addLayout(self.button_layout)

    def _call_apply_all(self):
        set_pervertex_maps(directory=self.cacheversion.directory)

    def _call_apply_on_selection(self):
        nodes = [item.text() for item in self.nodelist.selectedItems()]
        set_pervertex_maps(nodes=nodes, directory=self.cacheversion.directory)

    def _call_apply_selected_maps(self):
        nodes = [item.text() for item in self.nodelist.selectedItems()]
        maps = [item.text() for item in self.maplist.selectedItems()]
        set_pervertex_maps(
            nodes=nodes,
            directory=self.cacheversion.directory,
            maps=maps)