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

    _PropsObject.declare_props(val=10, font='Arial', text='Text')

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

    try:
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
    finally:
        combo.dispose()


def test_combo_values_qt_linked_edition(qtapi):

    from pyvmmonitor_core.compat import unicode
    combo = qt_linked_edition.SelectSingleIntCombo(None, 'val', values=[1, 3, 5])

    try:
        combo.qwidget.show()
        data = _Data()
        combo.set_data([data])

        assert combo.current_text == '10'
        assert combo.qwidget.currentIndex() == 2
        assert data.val == 10

        combo.qwidget.setEditText(unicode('4'))
        assert combo.qwidget.currentIndex() == 1
        assert combo.current_text == '4'
        assert data.val == 4

        combo.qwidget.setEditText(unicode('rara'))

        assert combo.qwidget.currentIndex() == 1
        assert combo.current_text == 'rara'
        assert data.val == 4

        combo.qwidget.setEditText(unicode('22'))
        assert combo.qwidget.currentIndex() == 2
        assert combo.current_text == '22'
        assert data.val == 22

        with pytest.raises(AttributeError):
            combo.invalid_attribute = 20
    finally:
        combo.dispose()


def test_spin_box_qt_linked_edition(qtapi):

    spin = qt_linked_edition.SpinBox(None, 'val')

    try:
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
    finally:
        spin.dispose()


def test_double_spin_box_qt_linked_edition(qtapi):

    spin = qt_linked_edition.DoubleSpinBox(None, 'val')
    spin.set_value_range((0, 50))

    try:
        spin.qwidget.show()
        data = _Data()
        spin.set_data([data])
        assert spin.value == 10
        spin.value = 20.5
        assert data.val == 20.5
        data.val = 1.2
        assert spin.value == 20.5
        process_queue()
        assert spin.value == 1.2

        with pytest.raises(AttributeError):
            spin.invalid_attribute = 20
    finally:
        spin.dispose()


def test_font_family_qt_linked_edition(qtapi):

    from pyvmmonitor_qt.qt_event_loop import process_events
    font_family = qt_linked_edition.FontFamily(None, 'font')
    try:
        font_family.qwidget.show()
        process_events()

        with pytest.raises(AttributeError):
            font_family.invalid_attribute = 20

        data = _Data()
        font_family.set_data([data])
        assert font_family.qwidget.currentFont().family() == 'Arial'

        data.font = 'Times'
        assert font_family.qwidget.currentFont().family() == 'Arial'
        process_queue()  # Only update when queue is processed
        assert font_family.qwidget.currentFont().family() == 'Times'

        font_family.set_current_font_family('Verdana')
        assert font_family.qwidget.currentFont().family() == 'Verdana'
    finally:
        font_family.dispose()


def test_int_edit_linked_edition(qtapi):
    from pyvmmonitor_qt.qt_event_loop import process_events
    int_edition = qt_linked_edition.IntEdition(None, 'val')
    try:
        int_edition.qwidget.show()
        process_events()

        with pytest.raises(AttributeError):
            int_edition.invalid_attribute = 20

        data = _Data()
        int_edition.set_data([data])
        assert int_edition.qwidget.text() == '10'

        data.val = 30
        assert int_edition.qwidget.text() == '10'
        process_queue()  # Only update when queue is processed
        assert int_edition.qwidget.text() == '30'

        int_edition.qwidget.setText('40')
        assert data.val == 40
    finally:
        int_edition.dispose()


def test_multi_line_edit_linked_edition(qtapi):
    from pyvmmonitor_qt.qt_event_loop import process_events
    edition = qt_linked_edition.MultiLineText(None, 'text')
    try:
        edition.qwidget.show()
        process_events()

        with pytest.raises(AttributeError):
            edition.invalid_attribute = 20

        data = _Data()
        edition.set_data([data])
        assert edition.qwidget.toPlainText() == 'Text'

        data.text = 'foo'
        assert edition.qwidget.toPlainText() == 'Text'
        process_queue()  # Only update when queue is processed
        assert edition.qwidget.toPlainText() == 'foo'

        changed = [0]

        def on_text_changed():
            changed[0] += 1

        edition.qwidget.textChanged.connect(on_text_changed)
        edition.qwidget.setPlainText('bar')
        process_events()
        assert changed[0] == 1
        assert data.text == 'bar'
    finally:
        edition.dispose()
