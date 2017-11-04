'''
License: LGPL

Copyright: Brainwy Software Ltda

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

from pyvmmonitor_core import compat, thread_utils
from pyvmmonitor_qt import qt_utils
from pyvmmonitor_qt.qt.QtCore import QSortFilterProxyModel, Qt
from pyvmmonitor_qt.qt.QtGui import QStandardItem, QStandardItemModel

_SORT_KEY_ROLE = Qt.UserRole + 9
_NODE_ROLE = Qt.UserRole + 21


class _CustomModel(QStandardItemModel):
    pass


class TreeNode(object):

    __slots__ = ['_items', '_data', 'tree', 'obj_id', '_children', '_sort_key', '_parent']

    def __init__(self, data):
        self._items = None

        # data is always a tuple so that each column can have a different data
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
        if isinstance(data, list):
            data = tuple(data)
        elif not isinstance(data, tuple):
            data = (data,)

        self._data = data
        if self._items is not None:
            for item, d in compat.izip(self._items, data):
                self._set_item_data(item, d)

    def _set_item_data(self, item, d):
        item.setData(self._as_str(d), Qt.DisplayRole)

    def _as_str(self, obj):
        if obj.__class__ == compat.unicode:
            return obj
        if obj.__class__ == compat.bytes:
            return compat.as_unicode(obj)

        return compat.unicode(obj)

    def set_item_role(self, role, column, data):
        if self._items is None:
            raise AssertionError(
                'This method can only be called when the item is attached to the tree.')
        self._items[column].setData(data, role)

    def item_role(self, role, column):
        if self._items is None:
            raise AssertionError(
                'This method can only be called when the item is attached to the tree.')
        return self._items[column].data(role)

    def set_item_custom_widget(self, column, widget):
        if self._items is None:
            raise AssertionError(
                'This method can only be called when the item is attached to the tree.')
        item = self._items[column]
        index = item.index()
        if not index.isValid():
            raise AssertionError(
                'This method can only be called when the item is attached to the tree.')
        self.tree.tree.setIndexWidget(
            self.tree._sort_model.mapFromSource(index), widget)

    def item_custom_widget(self, column):
        if self._items is None:
            raise AssertionError(
                'This method can only be called when the item is attached to the tree.')
        item = self._items[column]
        index = item.index()
        if not index.isValid():
            raise AssertionError(
                'This method can only be called when the item is attached to the tree.')
        return self.tree.tree.indexWidget(self.tree._sort_model.mapFromSource(index))

    @property
    def sort_key(self):
        return self._sort_key

    @sort_key.setter
    def sort_key(self, sort_key):
        self._sort_key = sort_key
        if self._items is not None:
            for item in self._items:
                item.setData(sort_key, _SORT_KEY_ROLE)

    def _attach_to_tree(self, tree, obj_id):
        assert self.tree is None
        assert self.obj_id is None
        self.tree = tree
        self.obj_id = obj_id
        return self._create_items()

    def _append_row(self, node, index=-1):
        self._children.add(node)
        if index == -1:
            self._items[0].appendRow(node._items)
        else:
            assert index >= 0
            self._items[0].insertRow(index, node._items)

    def _detach(self, parent_node, parent_item):
        assert not self._children, \
            'The children of this node must be removed before this node itself.'

        if parent_node is not None:
            parent_node._children.remove(self)

        for item in self._items:
            item.setData(None, _NODE_ROLE)
        parent_item.removeRow(self._items[0].row())
        self.tree = None
        self._items = None

    def _create_items(self):
        if self._items is None:
            data = self.data
            items = []
            for x in data:
                item = QStandardItem('')

                # Always define a sort key role (even if we don't use it).
                sort_role = self._sort_key if self._sort_key is not None else self.obj_id
                item.setData(sort_role, _SORT_KEY_ROLE)
                self._set_item_data(item, x)
                item.setData(self, _NODE_ROLE)

                items.append(item)

            self._items = items

            assert len(self._items) > 0

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


class FilterProxyModelCheckingChildren(QSortFilterProxyModel):

    def __init__(self, *args, **kwargs):
        QSortFilterProxyModel.__init__(self, *args, **kwargs)
        self._filter_text = ''

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        if self._filter_text in index.data(Qt.DisplayRole).lower():
            return True
        return False

    def set_filter_text(self, filter_text):
        self._filter_text = filter_text.lower()
        self.invalidateFilter()

    def get_filter_text(self):
        return self._filter_text


class PythonicQTreeView(object):

    __slots__ = [
        '__weakref__',
        '_sort_model',
        '_fast',
        '_root_items',
        'tree',
        '_model',
    ]

    def __init__(self, tree, editable=False):
        '''
        :param QTreeView tree:
        :param bool editable:
            Determines if the tree items should be editable.
        '''

        self.tree = tree
        model = self._model = _CustomModel(tree)
        from pyvmmonitor_qt.qt.QtWidgets import QAbstractItemView

        tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree.setSelectionBehavior(QAbstractItemView.SelectRows)

        self._sort_model = FilterProxyModelCheckingChildren()
        self._sort_model.setSourceModel(model)

        tree.setModel(self._sort_model)
        self._fast = {}
        self._root_items = set()
        if not editable:
            # Set all items not editable
            # Otherwise, it could be set individually with:
            # QStandardItem.setEditable(False)
            tree.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def list_item_captions(self, prefix='', cols=(0,), only_show_expanded=False):
        return qt_utils.list_wiget_item_captions(
            self.tree,
            parent_index=None,
            prefix=prefix,
            cols=cols,
            only_show_expanded=only_show_expanded
        )

    @property
    def filter_text(self):
        return self._sort_model.get_filter_text()

    @filter_text.setter
    def filter_text(self, filter_text):
        self._sort_model.set_filter_text(filter_text)

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
        with self.batch_changes():
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

    def add_node(self, parent_node, obj_id, node, index=-1):
        '''
        Adds a node to the tree below the passed parent.

        :param TreeNode|unicode|NoneType parent_node:
            If None is passed, it'll be added to the root, otherwise, it'll be added to
            the passed node (which can be passed directly or through its id).

        :param unicode obj_id:
            The id for this node.

        :param object|TreeNode node:
            Either the instanced TreeNode to be added or the data for which a TreeNode
            should be created.

        :param int index:
            The index at which the child node should be added.
        '''
        if isinstance(parent_node, compat.unicode):
            parent_node = self._fast[parent_node]

        if not isinstance(node, TreeNode):
            node = TreeNode(node)

        assert thread_utils.is_in_main_thread()
        assert obj_id not in self._fast
        if parent_node is None:
            items = node._attach_to_tree(self, obj_id)
            if index == -1:
                self._model.appendRow(items)
            else:
                assert index >= 0
                self._model.insertRow(index, items)
            self._root_items.add(node)
        else:
            items = node._attach_to_tree(self, obj_id)
            parent_node._append_row(node, index=index)

        node._parent = parent_node
        self._fast[obj_id] = node
        return node

    def node_from_index(self, index):
        '''
        :param QModelIndex index:
            The model index from qt

        :return QTreeNode:
            Return the PythonicQTreeView node (or None if not found).
        '''
        if not index.isValid():
            return None
        return index.data(_NODE_ROLE)

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

        if selected_indexes:
            nodes = set()
            for i in selected_indexes:
                node = i.data(_NODE_ROLE)
                if node not in nodes:
                    nodes.add(node)
                    if node is not None:
                        obj_id = node.obj_id
                        new_selection.append(obj_id)
        return new_selection

    def set_selection(self, obj_ids, clear_selection=True):
        from pyvmmonitor_qt.qt.QtCore import QModelIndex
        from pyvmmonitor_qt.qt.QtCore import QItemSelection
        from pyvmmonitor_qt.qt.QtCore import QItemSelectionModel

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
                        selection = QItemSelection(index, index)
                    else:
                        selection.select(index, index)

        if selection:
            if not clear_selection:
                selection_model.select(
                    selection,
                    QItemSelectionModel.Select | QItemSelectionModel.Rows)
            else:
                selection_model.select(
                    selection,
                    QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Current |
                    QItemSelectionModel.Rows)
        else:
            if clear_selection:
                selection_model.select(QModelIndex(), QItemSelectionModel.Clear)
