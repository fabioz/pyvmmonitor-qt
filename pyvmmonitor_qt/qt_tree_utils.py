'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
import contextlib

from pyvmmonitor_core.nodes_tree import Node, NodesTree
from pyvmmonitor_core.weak_utils import get_weakref
from pyvmmonitor_qt import compat
from pyvmmonitor_qt.qt import QtCore


def _get_expanded_nodes_tree(
        widget,
        parent_index=None,
        parent_node=None,
        data=QtCore.Qt.DisplayRole):
    '''
    :return NodesTree:
        Returns a tree with the paths for the passed data.
    '''
    model = widget.model()
    if parent_index is None:
        parent_index = QtCore.QModelIndex()
    row_count = model.rowCount(parent_index)

    if parent_node is None:
        parent_node = NodesTree()

    for row in compat.xrange(row_count):
        index = model.index(row, 0, parent_index)
        if not widget.isExpanded(index):
            continue
        node = parent_node.add_child(Node(model.data(index, data)))
        _get_expanded_nodes_tree(widget, parent_index=index, parent_node=node)

    return parent_node


def _set_expanded_nodes_tree(
        widget,
        nodes_tree=None,
        parent_index=None,
        data=QtCore.Qt.DisplayRole):
    '''
    We have to find a tree subpath which matches the passed path (in nodes_tree) and expand it
    accordingly.

    :param NodesTree nodes_tree:
    '''
    if not nodes_tree.children:
        return True

    model = widget.model()
    if parent_index is None:
        parent_index = QtCore.QModelIndex()
    row_count = model.rowCount(parent_index)

    found = 0

    for row in compat.xrange(row_count):
        index = model.index(row, 0, parent_index)

        model_data = model.data(index, data)
        for node in nodes_tree.children:
            if node.data == model_data:
                # Ok, we have a match on this subtree (expand even if it means expanding
                # only partially).
                widget.setExpanded(index, True)

                # Ok, we have a possible match, let's go forward on this node
                if _set_expanded_nodes_tree(widget, nodes_tree=node, parent_index=index):
                    found += 1

    return found == len(nodes_tree.children)


def expanded_nodes_tree(widget, nodes_tree=None, data=QtCore.Qt.DisplayRole):
    if nodes_tree is not None:
        _set_expanded_nodes_tree(widget, nodes_tree=nodes_tree, data=data)
    else:
        return _get_expanded_nodes_tree(widget, data=data)


def scroll_pos(widget, val=None):
    vertical_scrollbar = widget.verticalScrollBar()
    if not val:
        return vertical_scrollbar.value()
    else:
        min_val = vertical_scrollbar.minimum()
        max_val = vertical_scrollbar.maximum()
        if min_val <= val <= max_val:
            vertical_scrollbar.setValue(val)
        else:
            weak = get_weakref(vertical_scrollbar)
            # We'll wait for the range to change to apply it (i.e.: if we're restoring the
            # contents of a widget, it may take a while until it actually receives a range).

            def _on_range_changed(self, *args, **kwargs):
                vertical_scrollbar = weak()  # Don't create a cycle
                if vertical_scrollbar is None:
                    return

                vertical_scrollbar.rangeChanged.disconnect(_on_range_changed)
                vertical_scrollbar.setValue(val)
            vertical_scrollbar.rangeChanged.connect(_on_range_changed)


@contextlib.contextmanager
def preserve_tree_expanded_nodes(widget):
    nodes_tree = expanded_nodes_tree(widget)
    yield
    expanded_nodes_tree(widget, nodes_tree)


@contextlib.contextmanager
def preserve_tree_scroll_pos(widget):
    '''
    Helper which will try to preserve the scroll pos of the tree.
    '''
    pos = scroll_pos(widget)
    yield
    scroll_pos(widget, pos)
