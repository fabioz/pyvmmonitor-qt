# License: LGPL
#
# Copyright: Brainwy Software

import pytest

from pyvmmonitor_qt import qt_utils
from pyvmmonitor_qt.qt.QtGui import QTreeView
from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView, TreeNode


def test_tree_view(qtapi):
    tree = QTreeView()
    tree = PythonicQTreeView(tree)

    tree.tree.show()

    tree.columns = ['col1', 'col2']
    qtapi.add_widget(tree.tree)

    # Usual API to use
    tree['a'] = [10, 20]
    tree['a.b'] = [20, 30]
    tree['a.c'] = ['30']
    tree['a.b.c'] = ['30', 40]

    assert qt_utils.list_wiget_item_captions(tree.tree, cols=(0, 1)) == [
        ['10', '20'], ['+20', '+30'], ['++30', '++40'], ['+30', '+']]

    tree['a'].expand()
    tree['a'].check(True)

    node = TreeNode([1, 2])
    assert not node.is_expanded()
    with pytest.raises(RuntimeError):
        node.expand(True)
    assert not node.is_expanded()  # We can only expand after it's added to the tree
    with pytest.raises(RuntimeError):
        node.check(True)
    assert not node.is_checked()

    tree['a.d'] = node
    node.expand()
    node.check()
    assert node.is_expanded()
    assert node.is_checked()
    tree['a.d.c'] = [2, 4]
    tree['a.d.c'].expand()
    assert tree['a.d.c'].is_expanded()

    assert node.is_expanded()
    assert node.is_checked()
    assert not node.is_checked(1)

    qt_utils.process_events()
    assert node.is_expanded()
    assert node.is_checked()
    assert not node.is_checked(1)


def test_iter_nodes(qtapi):
    tree = QTreeView()
    tree = PythonicQTreeView(tree)

    tree.tree.show()

    tree['a'] = 10
    tree['b'] = 20
    tree['a.b'] = 30
    tree['a.b.c'] = 40
    tree['a.b.d'] = 41

    contents = []
    for node in tree.iternodes('a'):
        contents.append(node.obj_id)

    assert '\n'.join(sorted(contents)) == '''a.b
a.b.c
a.b.d'''

    del tree['a.b']

    assert len(list(tree.iternodes('a'))) == 0


def test_tree_view_expand_remove(qtapi):
    tree = QTreeView()
    tree = PythonicQTreeView(tree)

    tree.tree.show()

    tree.columns = ['col1', 'col2']
    qtapi.add_widget(tree.tree)
    tree['a'] = [10, 20]
    tree['a'].expand()
    assert qt_utils.count_items(tree.tree) == 1
    del tree['a']
    assert qt_utils.count_items(tree.tree) == 0


def test_hierarchy_different_from_ids(qtapi):
    tree = QTreeView()
    tree = PythonicQTreeView(tree)

    tree.tree.show()

    tree.columns = ['col1', 'col2']
    qtapi.add_widget(tree.tree)
    tree['a'] = [10, 20]
    tree.add_node('a', 'a.b.c.d', [1, 2])

    contents = []
    for node in tree.iternodes('a'):
        contents.append(node.obj_id)
    assert ''.join(contents) == 'a.b.c.d'

    assert qt_utils.count_items(tree.tree) == 2
    assert len(tree) == 2
    del tree['a']
    assert qt_utils.count_items(tree.tree) == 0
