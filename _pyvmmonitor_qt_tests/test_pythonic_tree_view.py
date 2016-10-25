# License: LGPL
#
# Copyright: Brainwy Software

import pytest

from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


def test_tree_view(qtapi):
    from pyvmmonitor_qt import qt_utils
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
    from pyvmmonitor_qt.tree.pythonic_tree_view import TreeNode

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

    from pyvmmonitor_qt.qt_event_loop import process_events
    process_events()
    assert node.is_expanded()
    assert node.is_checked()
    assert not node.is_checked(1)


def test_iter_nodes(qtapi):
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    tree = QTreeView()
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
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
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    tree = QTreeView()
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
    tree = PythonicQTreeView(tree)

    tree.tree.show()

    tree.columns = ['col1', 'col2']
    qtapi.add_widget(tree.tree)
    tree['a'] = [10, 20]
    tree['a'].expand()
    from pyvmmonitor_qt.qt_utils import count_items
    assert count_items(tree.tree) == 1
    del tree['a']
    assert count_items(tree.tree) == 0


def test_hierarchy_different_from_ids(qtapi):
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    tree = QTreeView()
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
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

    from pyvmmonitor_qt.qt_utils import count_items
    assert count_items(tree.tree) == 2
    assert len(tree) == 2
    del tree['a']
    assert count_items(tree.tree) == 0


def test_clear(qtapi):
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    tree = QTreeView()
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
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

    from pyvmmonitor_qt import qt_utils
    assert qt_utils.count_items(tree.tree) == 2
    tree.clear()
    assert qt_utils.count_items(tree.tree) == 0
    tree['a'] = [10, 20]
    tree.add_node('a', 'a.b.c.d', [1, 2])
    assert qt_utils.count_items(tree.tree) == 2


def test_color(qtapi):
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    tree = QTreeView()
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
    tree = PythonicQTreeView(tree)
    tree.tree.show()
    tree['a'] = [10, 20]
    from pyvmmonitor_qt.qt.QtGui import QBrush
    from pyvmmonitor_qt.qt.QtGui import QColor
    from pyvmmonitor_qt.qt.QtCore import Qt
    tree['a'].set_foreground_brush(QBrush(QColor(Qt.red)))

    assert tree['a'].get_foreground_brush(0).color() == QColor(Qt.red)

    tree['a'].set_background_brush(QBrush(QColor(Qt.gray)))

    assert tree['a'].get_background_brush(0).color() == QColor(Qt.gray)


def test_selection(qtapi):
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    tree = QTreeView()
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
    tree = PythonicQTreeView(tree)

    tree.tree.show()

    tree.columns = ['col1', 'col2']
    qtapi.add_widget(tree.tree)
    tree['a'] = [10, 20]
    tree.add_node('a', 'a.b.c.d', [1, 2])

    tree.set_selection(['a.b.c.d'])
    assert tree.get_selection() == ['a.b.c.d']

    tree.set_selection(['a', 'a.b.c.d'])
    assert tree.get_selection() == ['a', 'a.b.c.d']


def test_sort_order(qtapi):
    '''
    By default there's no sorting (it's kept by insertion order), but it's possible to turn on the
    sorting to be used and set the sort key.
    '''
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    tree = QTreeView()
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
    tree = PythonicQTreeView(tree)

    tree.tree.show()

    tree['a'] = 'a'
    tree['c'] = 'c'
    tree['b'] = 'b'
    assert tree.list_item_captions() == 'a c b'.split()

    tree.sorting_enabled = True

    assert tree.list_item_captions() == 'a b c'.split()

    tree['d'] = 'a'
    assert tree.list_item_captions() == 'a a b c'.split()

    tree.sorting_enabled = False

    tree['e'] = 'b'
    assert tree.list_item_captions() == 'a a b c b'.split()

    tree.sorting_enabled = True

    assert tree.list_item_captions() == 'a a b b c'.split()

    with tree.batch_changes():
        tree['f'] = 'b'
        tree['g'] = 'a'
        assert not tree.sorting_enabled

    assert tree.list_item_captions() == 'a a a b b b c'.split()

    for node in tree.iternodes():
        # Reverse sort order
        node.sort_key = ord('z') - ord(node.data[0])

    # for node in sorted(tree.iternodes(), key=lambda node: node.sort_key):
    #     print(node.obj_id, node.data, node.sort_key)

    tree.sort_strategy = 'sort_key'
    assert tree.list_item_captions() == list(reversed('a a a b b b c'.split()))

    tree.sort_strategy = 'display'
    assert tree.list_item_captions() == 'a a a b b b c'.split()

    # Now, let's change the caption and make sure it's still Ok.
    tree['g'].data = 'g'

    assert tree.list_item_captions() == 'a a b b b c g'.split()


def test_icon(qtapi):
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView

    # Example on how to deal with a mouse click.
    class MyQTreeView(QTreeView):

        def mousePressEvent(self, ev):
            index = self.indexAt(ev.pos())
            if index.isValid():
                # print('col', col, 'col_width', col_width, 'col_viewport_pos', col_viewport_pos)
                # print('relative', relative_x)
                if index.column() == 1:
                    col = self.columnAt(ev.pos().x())
                    col_width = self.columnWidth(col)
                    col_viewport_pos = self.columnViewportPosition(col)
                    relative_x = ev.pos().x() - col_viewport_pos

                    node = tree.node_from_index(index)
                    print(node.__class__, relative_x, col_width)
                    ev.setAccepted(True)
                    return
            return QTreeView.mousePressEvent(self, ev)

    tree = MyQTreeView()
    tree = PythonicQTreeView(tree)
    tree.columns = ['Caption', 'Action']
    tree.tree.show()

    tree['a'] = ('a', '')
    tree['c'] = ('c', '')
    tree['b'] = ('b', '')

    from pyvmmonitor_qt.qt.QtGui import QPixmap
    pixmap = QPixmap(30, 30)
    from pyvmmonitor_qt.qt.QtCore import Qt
    pixmap.fill(Qt.red)

    # Should show a red square for column 1
    tree['a'].set_item_role(Qt.DecorationRole, 1, pixmap)

    # __eq__ works properly for QImage but not QPixmap.
    assert tree['a'].item_role(Qt.DecorationRole, 1).toImage() == pixmap.toImage()


def test_custom_widget(qtapi):
    from pyvmmonitor_qt.qt.QtWidgets import QTreeView
    tree = QTreeView()
    from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView
    tree = PythonicQTreeView(tree)
    tree.columns = ['Caption', 'Action']
    tree.tree.show()

    tree['a'] = ('a', '')
    tree['c'] = ('c', '')
    tree['b'] = ('b', '')

    from pyvmmonitor_qt.qt.QtGui import QPixmap
    from pyvmmonitor_qt.qt.QtWidgets import QPushButton
    from pyvmmonitor_qt.qt.QtCore import Qt

    bt = QPushButton(None)
    icon = QPixmap(20, 20)
    icon.fill(Qt.red)
    from pyvmmonitor_qt.qt.QtGui import QIcon
    bt.setIcon(QIcon(icon))
    bt.setAutoFillBackground(True)

    # Should show a button at column 1
    tree['a'].set_item_custom_widget(1, bt)
    assert tree['a'].item_custom_widget(1) == bt
