from collections import OrderedDict
import sys

import pytest

from pyvmmonitor_core import compat
from pyvmmonitor_core.callback import Callback
from pyvmmonitor_qt import qt_linked_edition
from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport
from pyvmmonitor_qt.qt_event_loop import process_queue


def _make_property(key, default):

    def get_val(self):
        return self._props.get(key, default)

    def set_val(self, val):
        prev = self._props.get(key, default)
        self._props[key] = val
        if prev != val:
            self._on_modified_callback(self, {key: (val, prev)})

    return property(get_val, set_val)


class _PropsObject(object):

    @classmethod
    def declare_props(cls, **kwargs):
        frame = sys._getframe().f_back
        namespace = frame.f_locals

        for key, val in compat.iteritems(kwargs):
            namespace[key] = _make_property(key, val)

    def __init__(self):
        self._props = {}
        self._on_modified_callback = Callback()


class _Data(_PropsObject):

    _PropsObject.declare_props(val=10)

    def register_modified(self, on_modified):
        self._on_modified_callback.register(on_modified)

    def unregister_modified(self, on_modified):
        self._on_modified_callback.unregister(on_modified)


def test_combo_qt_linked_edition(qtapi):

    combo = qt_linked_edition.Combo(None, 'val', caption_to_internal_value=OrderedDict([
        ('Val 1', 1,),
        ('Val 10', 10,),
        ('Val 20', 20,),
    ]))

    combo.qwidget.show()
    data = _Data()
    combo.set_data([data])
    assert combo.current_text == 'Val 10'
    combo.set_current_text('Val 20')
    assert data.val == 20
    data.val = 1
    assert combo.current_text == 'Val 20'
    process_queue()
    assert combo.current_text == 'Val 1'

    with pytest.raises(AttributeError):
        combo.invalid_attribute = 20


def test_spin_box_qt_linked_edition(qtapi):

    spin = qt_linked_edition.SpinBox(None, 'val')

    spin.qwidget.show()
    data = _Data()
    spin.set_data([data])
    assert spin.value == 10
    spin.value = 20
    assert data.val == 20
    data.val = 1
    assert spin.value == 20
    process_queue()
    assert spin.value == 1

    with pytest.raises(AttributeError):
        spin.invalid_attribute = 20
