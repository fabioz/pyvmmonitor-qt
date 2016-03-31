# License: LGPL
#
# Copyright: Brainwy Software
'''
This module provides a Pythonic API to a QTreeView using a QStandardItemModel.

Nodes always have an id (which is used to access the node in a fast way and by
default, ids identify the hierarchy based on dots -- although it's also possible
to create an hierarchy which is not dot-based by using `add_node` directly).

To use:

    tree = QTreeView()
    tree = PythonicQTreeView(tree)

    tree.columns = ['col1', 'col2']

    # Create a tree node with the underlying data (by default, we convert
    # the data to unicode to show in the tree).
    tree['a'] = [10, 20]

    # When using __setitem__, we create the hierarchy based on dots, so, the
    # statement below creates 'a.b' as a child of 'a'.
    tree['a.b'] = ['30']

    # The node can be expanded
    tree['a'].expand()
    tree['a'].expand(False)

    # And checked
    tree['a'].check(True) # Default is column 0
    tree['a'].check(False, col=1)

    # Check whether it's checked
    tree['a'].is_checked() # Default is column 0

    # Note: iteration order among siblings is not guaranteed!
    for node in tree.iternodes('a'):
        print(node.obj_id, node.data)

    del tree['a']
'''

from __future__ import unicode_literals

from pyvmmonitor_core import thread_utils, compat
from pyvmmonitor_qt.qt.QtCore import Qt
from pyvmmonitor_qt.qt.QtGui import QStandardItemModel, QStandardItem


class _CustomModel(QStandardItemModel):
    pass


class TreeNode(object):

    def __init__(self, data):
        self.data = data
        self.tree = None
        self.obj_id = None
        self._items = None
        self._state = None
        self._children = set()

    def _as_str(self, obj):
        if obj.__class__ == compat.unicode:
            return obj
        if obj.__class__ == compat.bytes:
            return compat.as_unicode(obj)

        return compat.unicode(obj)

    def _attach_to_tree(self, tree, obj_id):
        assert self.tree is None
        assert self.obj_id is None
        self.tree = tree
        self.obj_id = obj_id
        return self._create_items()

    def _append_row(self, node):
        self._children.add(node)
        self._items[0].appendRow(node._items)

    def _detach(self, parent_node, parent_item):
        assert not self._children, \
            'The children of this node must be removed before this node itself.'

        if parent_node is not None:
            parent_node._children.remove(self)

        parent_item.removeRow(self._items[0].row())
        self.tree = None
        self._items = None

    def _create_items(self):
        if self._items is None:
            data = self.data
            if not isinstance(data, (list, tuple)):
                data = (data,)
            self._items = [QStandardItem(self._as_str(x)) for x in data]

            assert len(self._items) > 0

            state = self._state
            if state is not None:
                self._state = None
                for (meth, col), args in compat.iteritems(state):
                    if col is not None:
                        getattr(self, meth)(*(args + (col,)))
                    else:
                        getattr(self, meth)(*args)

        return self._items

    def expand(self, b=True):
        if self._items is None:
            raise RuntimeError('Can only expand a node after it is added to the tree.')

        self.tree.tree.expand(self._items[0].index())

    def _expand(self, b):
        if self.tree is not None and self._items:
            self.tree.tree.expand(self._items[0].index())

    def is_expanded(self):
        if self._items is None:
            return False

        return self.tree.tree.isExpanded(self._items[0].index())

    def check(self, b=True, col=0):
        if self._items is None:
            raise RuntimeError('Can only check a node after it is added to the tree.')

        item = self._items[col]
        item.setCheckable(True)
        if b:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

    def is_checked(self, col=0):
        if self._items is None:
            return False

        return self._items[col].checkState() == Qt.Checked

    def set_foreground_brush(self, brush, col=-1):
        if col == -1:
            items = self._items
        else:
            items = [self._items[col]]

        for item in items:
            item.setData(brush, Qt.ForegroundRole)

    def get_foreground_brush(self, col):
        return self._items[col].data(Qt.ForegroundRole)

    def set_background_brush(self, brush, col=-1):
        if col == -1:
            items = self._items
        else:
            items = [self._items[col]]

        for item in items:
            item.setData(brush, Qt.BackgroundRole)

    def get_background_brush(self, col):
        return self._items[col].data(Qt.BackgroundRole)


class PythonicQTreeView(object):

    def __init__(self, tree):
        self.tree = tree
        model = self._model = _CustomModel(tree)
        tree.setModel(model)
        self._fast = {}
        self._root_items = set()

    def clear(self):
        while self._root_items:
            del self[compat.next(iter(self._root_items)).obj_id]

    @property
    def columns(self):
        ret = []
        for i in compat.xrange(self._model.columnCount()):
            item = self._model.horizontalHeaderItem(i)
            ret.append(item.text())
        return ret

    @columns.setter
    def columns(self, col_titles):
        self._model.setHorizontalHeaderLabels(col_titles)
        self._model.setColumnCount(len(col_titles))

    def __setitem__(self, obj_id, node):
        try:
            i = obj_id.rindex('.')
        except ValueError:
            parent_node = None
        else:
            parent_node = self._fast[obj_id[:i]]

        self.add_node(parent_node, obj_id, node)

    def add_node(self, parent_node, obj_id, node):
        if isinstance(parent_node, compat.unicode):
            parent_node = self._fast[parent_node]

        if not isinstance(node, TreeNode):
            node = TreeNode(node)

        assert thread_utils.is_in_main_thread()
        assert obj_id not in self._fast
        if parent_node is None:
            items = node._attach_to_tree(self, obj_id)
            self._model.appendRow(items)
            self._root_items.add(node)
        else:
            items = node._attach_to_tree(self, obj_id)
            parent_node._append_row(node)

        node._parent = parent_node
        self._fast[obj_id] = node
        return node

    def __getitem__(self, obj_id):
        return self._fast[obj_id]

    def __delitem__(self, obj_id):
        node = self._fast[obj_id]

        while node._children:
            child_node = compat.next(iter(node._children))
            del self[child_node.obj_id]

        self._root_items.discard(node)
        del self._fast[obj_id]

        parent_node = node._parent
        if parent_node is None:
            parent_item = self._model
        else:
            parent_item = parent_node._items[0]
        node._detach(parent_node, parent_item)

    def iternodes(self, parent_node=None, recursive=True):
        '''
        Iters children nodes of the given parent node. Note that the iteration
        order among siblings is not guaranteed.
        '''
        if parent_node is None:
            children = self._root_items
        else:
            if isinstance(parent_node, compat.unicode):
                parent_node = self._fast[parent_node]
            children = parent_node._children

        for child in children:
            yield child

            if recursive:
                for data in self._iternodes_recursive(child):
                    yield data

    def _iternodes_recursive(self, parent_node):
        for child in parent_node._children:
            yield child

            for data in self._iternodes_recursive(child):
                yield data

    def __len__(self):
        # Len of tree is the total number of nodes in the tree
        return len(self._fast)
