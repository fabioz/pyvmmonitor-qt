from pyvmmonitor_qt import qt_utils
from pyvmmonitor_qt.pytest_plugin import qtapi
from pyvmmonitor_qt.qt.QtGui import QTreeView
from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView


def test_tree_view(qtapi):
    tree = QTreeView()
    tree = PythonicQTreeView(tree)

    tree.columns = ['col1', 'col2']
    qtapi.add_widget(tree.tree)

    tree['a'] = [10, 20]
    tree['a.b'] = [20, 30]
    tree['a.c'] = ['30']
    tree['a.b.c'] = ['30', 40]

    assert qt_utils.list_wiget_item_captions(tree.tree, cols=(0, 1)) == [
        ['10', '20'], ['+20', '+30'], ['++30', '++40'], ['+30', '+']]

    tree['a'].expand()
    tree.tree.show()
#    qtapi.d()
