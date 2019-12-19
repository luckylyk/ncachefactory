from PySide2 import QtWidgets, QtCore
from ncachefactory.attributes import set_pervertex_maps, PERVERTEX_ATTRIBUTES


MAP_TRANSFER_WINDOW = "Dynamic maps transfer tool"


class DynamicMapTransferWindow(QtWidgets.QWidget):
    def __init__(self, cacheversion, nodes=None, parent=None):
        super(DynamicMapTransferWindow, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(MAP_TRANSFER_WINDOW)
        self.cacheversion = cacheversion
        self.nodelist = QtWidgets.QListWidget()
        self.nodelist.addItems(nodes)
        self.maplist = QtWidgets.QListWidget()
        self.maplist.addItems(PERVERTEX_ATTRIBUTES)

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