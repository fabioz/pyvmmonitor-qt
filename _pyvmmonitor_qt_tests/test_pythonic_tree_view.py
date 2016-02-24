from pyvmmonitor_qt.qt.QtGui import QTreeView
from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView


def test_tree_view(qtapi):
    tree = QTreeView()
    tree = PythonicQTreeView(tree)
