'''
This module provides a Pythonic API to a QTreeView using a QStandardItemModel.
'''

from __future__ import unicode_literals

from pyvmmonitor_core import thread_utils, compat
from pyvmmonitor_qt.qt.QtGui import QStandardItemModel, QStandardItem


class _CustomModel(QStandardItemModel):
    pass


class _NodeFacade(object):

    def __init__(self, tree, obj_id):
        self.tree = tree
        self.obj_id = obj_id

    def expand(self, b=True):
        items = self.tree._fast[self.obj_id]
        self.tree.tree.expand(items.index())


class PythonicQTreeView(object):

    def __init__(self, tree):
        self.tree = tree
        model = self._model = _CustomModel(tree)
        tree.setModel(model)
        self._fast = {}

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

    def __setitem__(self, obj_id, lst):
        assert thread_utils.is_in_main_thread()
        assert obj_id not in self._fast
        assert len(lst) > 0

        try:
            i = obj_id.rindex('.')
        except ValueError:
            parent_item = self._model
        else:
            parent_item = self._fast[obj_id[:i]]

        items = [QStandardItem(self._as_str(x)) for x in lst]
        parent_item.appendRow(items)
        self._fast[obj_id] = items[0]  # We only store col0

    def __getitem__(self, obj_id):
        return _NodeFacade(self, obj_id)

    def _as_str(self, obj):
        if obj.__class__ == compat.unicode:
            return obj
        if obj.__class__ == compat.bytes:
            return compat.as_unicode(obj)

        return compat.unicode(obj)

    def expand(self, obj_id):
        pass
