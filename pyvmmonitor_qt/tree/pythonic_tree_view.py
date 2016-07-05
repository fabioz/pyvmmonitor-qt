# License: LGPL
#
# Copyright: Brainwy Software
'''
This module provides a Pythonic API to a QTreeView using a QStandardItemModel.

Nodes always have an id (which is used to access the node in a fast way and by
default, ids identify the hierarchy based on dots in the id -- although it's
also possible to create an hierarchy which is not dot-based by using `add_node`
directly).

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

from contextlib import contextmanager

from pyvmmonitor_core import thread_utils, compat
from pyvmmonitor_qt import qt_utils
from pyvmmonitor_qt.qt.QtCore import Qt
from pyvmmonitor_qt.qt.QtGui import QStandardItemModel, QStandardItem

_SORT_KEY_ROLE = Qt.UserRole + 9


class _CustomModel(QStandardItemModel):
    pass


class TreeNode(object):

    def __init__(self, data):
        self._items = None
        self.data = data
        self.tree = None
        self.obj_id = None
        self._children = set()
        self._sort_key = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        if not isinstance(data, (list, tuple)):
            data = (data,)

        self._data = data
        if self._items is not None:
            for item, d in compat.izip(self._items, data):
                item.setData(self._as_str(d), Qt.DisplayRole)

    @property
    def sort_key(self):
        return self._sort_key

    @sort_key.setter
    def sort_key(self, sort_key):
        self._sort_key = sort_key
        if self._items is not None:
            for item in self._items:
                item.setData(sort_key, _SORT_KEY_ROLE)

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

        self._items[0].setData(None)
        parent_item.removeRow(self._items[0].row())
        self.tree = None
        self._items = None

    def _create_items(self):
        if self._items is None:
            data = self.data
            items = []
            for x in data:
                item = QStandardItem(self._as_str(x))

                # Always define a sort key role (even if we don't use it).
                sort_role = self._sort_key if self._sort_key is not None else self.obj_id
                item.setData(sort_role, _SORT_KEY_ROLE)

                items.append(item)

            self._items = items

            assert len(self._items) > 0
            self._items[0].setData(self)

        return self._items

    def expand(self, b=True):
        if self._items is None:
            raise RuntimeError('Can only expand a node after it is added to the tree.')

        index = self._get_sort_model_index(col=0)
        self.tree.tree.expand(index)

    def _expand(self, b):
        if self.tree is not None and self._items:
            index = self._get_sort_model_index(col=0)
            self.tree.tree.expand(index)

    def is_expanded(self):
        if self._items is None:
            return False

        index = self._get_sort_model_index(col=0)
        return self.tree.tree.isExpanded(index)

    def _get_sort_model_index(self, col=0):
        return self.tree._sort_model.mapFromSource(self._items[col].index())

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
        from pyvmmonitor_qt.qt.QtGui import QAbstractItemView

        self.tree = tree
        model = self._model = _CustomModel(tree)
        tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        from pyvmmonitor_qt.qt.QtGui import QSortFilterProxyModel

        self._sort_model = QSortFilterProxyModel()
        self._sort_model.setSourceModel(model)

        tree.setModel(self._sort_model)
        self._fast = {}
        self._root_items = set()

    def list_item_captions(self, prefix='', cols=(0,), only_show_expanded=False):
        return qt_utils.list_wiget_item_captions(
            self.tree,
            parent_index=None,
            prefix=prefix,
            cols=cols,
            only_show_expanded=only_show_expanded
        )

    @property
    def sort_strategy(self):
        sort_role = self._sort_model.sortRole()
        if sort_role == _SORT_KEY_ROLE:
            return 'sort_key'
        if sort_role == Qt.DisplayRole:
            return 'display'
        return sort_role

    @sort_strategy.setter
    def sort_strategy(self, sort_strategy):
        if sort_strategy == 'sort_key':
            self._sort_model.setSortRole(_SORT_KEY_ROLE)
        elif sort_strategy == 'display':
            self._sort_model.setSortRole(Qt.DisplayRole)
        else:
            self._sort_model.setSortRole(sort_strategy)

    @property
    def sorting_enabled(self):
        return self.tree.isSortingEnabled()

    @sorting_enabled.setter
    def sorting_enabled(self, enable):
        self.tree.setSortingEnabled(enable)
        if enable:
            self._sort_model.setDynamicSortFilter(True)
            self._sort_model.sort(0, Qt.AscendingOrder)
        else:
            self._sort_model.setDynamicSortFilter(False)

    @contextmanager
    def batch_changes(self):
        '''
        Context manager to be used when multiple changes are going to be done at once.
        Can disable features from the tree while in the context.

        I.e.:
            with tree.batch_changes():
                tree['x'] = '20'
        '''
        if self.tree.isSortingEnabled():
            self.sorting_enabled = False
            try:
                yield
            finally:
                self.sorting_enabled = True
        else:
            yield

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

    def get_selection(self):
        assert thread_utils.is_in_main_thread()
        new_selection = []
        selected_indexes = self.tree.selectedIndexes()

        sort_model = self._sort_model
        model = self._model  # : :type model: QStandardItemModel

        if selected_indexes:
            for i in selected_indexes:
                i = sort_model.mapToSource(i)
                item = model.itemFromIndex(i)
                node = item.data()
                if node is not None:
                    obj_id = node.obj_id
                    new_selection.append(obj_id)
        return new_selection

    def set_selection(self, obj_ids, clear_selection=True):
        from pyvmmonitor_qt.qt import QtGui
        from pyvmmonitor_qt.qt.QtCore import QModelIndex

        assert thread_utils.is_in_main_thread()
        selection_model = self.tree.selectionModel()

        selection = None
        for obj_id in obj_ids:

            item = self._fast.get(obj_id)
            if item is not None:
                index = item._items[0].index()
                if index is not None:
                    index = self._sort_model.mapFromSource(index)
                    if selection is None:
                        selection = QtGui.QItemSelection(index, index)
                    else:
                        selection.select(index, index)

        if selection:
            if not clear_selection:
                selection_model.select(
                    selection,
                    QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Rows)
            else:
                selection_model.select(
                    selection,
                    QtGui.QItemSelectionModel.ClearAndSelect | QtGui.QItemSelectionModel.Current |
                    QtGui.QItemSelectionModel.Rows)
        else:
            if clear_selection:
                selection_model.select(QModelIndex(), QtGui.QItemSelectionModel.Clear)
