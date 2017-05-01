from __future__ import unicode_literals, absolute_import
from pyvmmonitor_qt.qt.QtWidgets import QWidget


class ShortcutsConfigWidget(QWidget):

    def __init__(self, shortcuts_manager):
        '''
        :param IShortcutsManager shortcuts_manager:
        '''
        QWidget.__init__(self)
        from pyvmmonitor_qt.qt.QtWidgets import QTreeView
        self._shortcuts = QTreeView(self)

        from pyvmmonitor_qt.qt.QtWidgets import QVBoxLayout
        self._vlayout = QVBoxLayout(self)
        self._vlayout.addWidget(self._shortcuts)
        self.setLayout(self._vlayout)

        from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
        self._pythonic_tree = PythonicQTreeView(self._shortcuts)
        self._pythonic_tree.columns = ['Action', 'Shortcut']
