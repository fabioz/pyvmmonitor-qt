import functools

from pyvmmonitor_core import abstract, overrides
from pyvmmonitor_core.weak_utils import WeakList
from pyvmmonitor_qt import compat, qt_utils
from pyvmmonitor_qt.qt.QtCore import QObject
from pyvmmonitor_qt.qt.QtWidgets import QSpinBox, QComboBox, QDoubleSpinBox
from pyvmmonitor_qt.qt_event_loop import NextEventLoopUpdater


def _does_expected_ui_change(func):
    @functools.wraps(func)
    def _expected_change(self, *args, **kwargs):
        self._in_expected_ui_change += 1
        try:
            func(self, *args, **kwargs)
        finally:
            self._in_expected_ui_change -= 1

    return _expected_change


def _skip_on_expected_ui_change(func):
    @functools.wraps(func)
    def _skip_on_change(self, *args, **kwargs):
        if self._in_expected_ui_change:
            return
        func(self, *args, **kwargs)

    return _skip_on_change


def _does_expected_data_change(func):
    @functools.wraps(func)
    def _expected_change(self, *args, **kwargs):
        self._in_expected_data_change += 1
        try:
            func(self, *args, **kwargs)
        finally:
            self._in_expected_data_change -= 1

    return _expected_change


def _skip_on_expected_data_change(func):
    @functools.wraps(func)
    def _skip_on_change(self, *args, **kwargs):
        if self._in_expected_data_change:
            return
        func(self, *args, **kwargs)

    return _skip_on_change


class BaseLinkedEdition(object):

    __slots__ = [
        '__weakref__',
        '_in_expected_ui_change',
        '_in_expected_data_change',
        '_link_to_attribute',
        'data',
        '_updater',
        'qwidget']

    def __init__(self, link_to_attribute):
        self._in_expected_ui_change = 0
        self._in_expected_data_change = 0
        self._link_to_attribute = link_to_attribute
        self.data = WeakList()
        self._updater = NextEventLoopUpdater(self.update_ui)

    @_does_expected_ui_change
    def update_ui(self):
        if self.qwidget is not None:
            if not qt_utils.is_qobject_alive(self.qwidget):
                self.dispose()
                return

            self._on_update_ui()

    @abstract
    def _on_update_ui(self):
        pass

    def set_data(self, lst):
        self._unlink()
        self.data = WeakList(lst)
        for d in lst:
            d.register_modified(self._on_data_changed)
        self.update_ui()

    def _unlink(self):
        if self.data:
            for d in self.data:
                d.unregister_modified(self._on_data_changed)

    @_skip_on_expected_data_change
    def _on_data_changed(self, obj, attrs):
        if self._link_to_attribute in attrs:
            self._updater.invalidate()

    @_does_expected_data_change
    def _set_attr(self, value):
        for obj in self.data:
            try:
                setattr(obj, self._link_to_attribute, value)
            except Exception:
                raise AttributeError('Unable to set: %s' % (self._link_to_attribute))

    def dispose(self):
        self._unlink()

        if self.qwidget is not None and qt_utils.is_qobject_alive(self.qwidget):
            self.qwidget.deleteLater()

        self.data = None
        self.qwidget = None
        if self._updater is not None:
            self._updater.dispose()

        self._updater = None


class _IntEditionEventFilter(QObject):

    def __init__(self, int_edition):
        import weakref
        QObject.__init__(self)
        self._int_edition = weakref.ref(int_edition)

    def eventFilter(self, obj, event):
        from pyvmmonitor_qt.qt.QtCore import QEvent
        from pyvmmonitor_qt.qt.QtCore import Qt
        if event.type() == QEvent.KeyPress:
            int_edition = self._int_edition()
            if int_edition is not None:
                if event.key() == Qt.Key_Up:
                    int_edition.decrement_one()

                elif event.key() == Qt.Key_PageUp:
                    int_edition.decrement_multi()

                elif event.key() == Qt.Key_Down:
                    int_edition.increment_one()

                elif event.key() == Qt.Key_PageDown:
                    int_edition.increment_multi()

        return QObject.eventFilter(self, obj, event)


class IntEdition(BaseLinkedEdition):

    __slots__ = ['_event_filter']

    def __init__(self, parent_widget, link_to_attribute):
        '''
        :param QWidget parent_widget:
        :param str link_to_attribute:
        '''
        from pyvmmonitor_qt.qt.QtWidgets import QLineEdit
        BaseLinkedEdition.__init__(self, link_to_attribute)
        self.qwidget = QLineEdit(parent_widget)

        self.qwidget.textChanged.connect(self._on_text_changed)
        self._link_to_attribute = link_to_attribute
        self._event_filter = _IntEditionEventFilter(self)
        self.qwidget.installEventFilter(self._event_filter)

    @overrides(BaseLinkedEdition.dispose)
    def dispose(self):
        if self.qwidget is not None and qt_utils.is_qobject_alive(self.qwidget):
            self.qwidget.removeEventFilter(self._event_filter)

        BaseLinkedEdition.dispose(self)

    @overrides(BaseLinkedEdition._on_update_ui)
    def _on_update_ui(self):
        for data in self.data:
            self.qwidget.setText(str(getattr(data, self._link_to_attribute)))
            return

    @_skip_on_expected_ui_change
    def _on_text_changed(self, value):
        try:
            value = int(value)
        except ValueError:
            return

        self._set_attr(value)

    @_does_expected_data_change
    def _apply_delta(self, delta):
        for obj in self.data:
            setattr(obj, self._link_to_attribute, getattr(obj, self._link_to_attribute) + delta)

    def increment_multi(self):
        self._apply_delta(10)

    def increment_one(self):
        self._apply_delta(1)

    def decrement_multi(self):
        self._apply_delta(-10)

    def decrement_one(self):
        self._apply_delta(-1)


class SpinBox(BaseLinkedEdition):

    __slots__ = []

    def __init__(self, parent_widget, link_to_attribute):
        '''
        :param QWidget parent_widget:
        :param str link_to_attribute:
        '''
        BaseLinkedEdition.__init__(self, link_to_attribute)
        self.qwidget = self._get_widget_class()(parent_widget)

        self.qwidget.valueChanged.connect(self._on_text_changed)
        self._link_to_attribute = link_to_attribute

    def _get_widget_class(self):
        return QSpinBox

    @overrides(BaseLinkedEdition._on_update_ui)
    def _on_update_ui(self):
        for data in self.data:
            self.qwidget.setValue(getattr(data, self._link_to_attribute))
            return

    @_skip_on_expected_ui_change
    def _on_text_changed(self, value):
        for obj in self.data:
            setattr(obj, self._link_to_attribute, value)

    def get_value(self):
        return self.qwidget.value()

    def set_value(self, value):
        return self.qwidget.setValue(value)

    value = property(get_value, set_value)


class DoubleSpinBox(SpinBox):

    __slots__ = []

    def _get_widget_class(self):
        return QDoubleSpinBox

    def set_value_range(self, value_range):
        self.qwidget.setRange(*value_range)

    def set_step(self, step_value):
        self.qwidget.setSingleStep(step_value)


class Combo(BaseLinkedEdition):

    __slots__ = ['caption_to_internal_value', '_caption_to_index']

    def __init__(self, parent_widget, link_to_attribute, caption_to_internal_value):
        '''
        :param QWidget parent_widget:
        :param str link_to_attribute:
        :param OrderedDict caption_to_internal_value:
        '''
        BaseLinkedEdition.__init__(self, link_to_attribute)
        self._link_to_attribute = link_to_attribute
        qwidget = self.qwidget = QComboBox(parent_widget)
        self._caption_to_index = {}
        for i, caption in enumerate(compat.iterkeys(caption_to_internal_value)):
            qwidget.addItem(caption)
            self._caption_to_index[caption] = i

        qwidget.currentIndexChanged.connect(self._on_index_changed)
        self.caption_to_internal_value = caption_to_internal_value

    @overrides(BaseLinkedEdition._on_update_ui)
    def _on_update_ui(self):
        for data in self.data:
            internal_value = getattr(data, self._link_to_attribute)
            for caption, val in compat.iteritems(self.caption_to_internal_value):
                if val == internal_value:
                    self.qwidget.setCurrentIndex(self._caption_to_index[caption])
                    return True

        return False

    @_skip_on_expected_ui_change
    def _on_index_changed(self, index):
        current_text = self.qwidget.currentText()
        try:
            value = self.caption_to_internal_value[current_text]
        except KeyError:
            pass
        else:
            self._set_attr(value)

    def get_current_text(self):
        return self.qwidget.currentText()

    def set_current_text(self, text):
        i = self.qwidget.findText(text)
        if i >= 0:
            self.qwidget.setCurrentIndex(i)

    current_text = property(get_current_text, set_current_text)


class SelectSingleIntCombo(Combo):

    __slots__ = []

    def __init__(
            self,
            parent_widget,
            link_to_attribute,
            values=(1, 3, 7, 14, 21),
            accept_custom_int=True):
        from collections import OrderedDict
        from pyvmmonitor_core.compat import unicode

        caption_to_internal_value = OrderedDict()
        for v in values:
            caption_to_internal_value[unicode(v)] = v

        Combo.__init__(self, parent_widget, link_to_attribute, caption_to_internal_value)
        if accept_custom_int:
            self.qwidget.setEditable(True)
            self.qwidget.editTextChanged.connect(self._edit_text_changed)

    @_skip_on_expected_ui_change
    def _edit_text_changed(self, text):
        try:
            value = int(text)
        except ValueError:
            return  # Invalid text... should we make it red to signal?

        self._set_attr(value)

        self._in_expected_ui_change += 1
        try:
            self._update_index()
            self.qwidget.setEditText(text)
        finally:
            self._in_expected_ui_change -= 1

    def _update_index(self):
        last_index = None
        for data in self.data:
            internal_value = getattr(data, self._link_to_attribute)
            for i, (caption, val) in enumerate(compat.iteritems(self.caption_to_internal_value)):
                if val == internal_value:
                    self.qwidget.setCurrentIndex(self._caption_to_index[caption])
                    return True
                if last_index is None:
                    if val > internal_value:
                        last_index = i - 1

        if last_index is None:
            last_index = self.qwidget.count() - 1

        if last_index < 0:
            last_index = 0

        self.qwidget.setCurrentIndex(last_index)

    @overrides(BaseLinkedEdition._on_update_ui)
    def _on_update_ui(self):
        self._update_index()
        from pyvmmonitor_core.compat import unicode
        for data in self.data:
            internal_value = getattr(data, self._link_to_attribute)
            self.qwidget.setEditText(unicode(internal_value))


class FontFamily(BaseLinkedEdition):

    __slots__ = []

    def __init__(self, parent_widget, link_to_attribute):
        '''
        :param QWidget parent_widget:
        :param str link_to_attribute:
        '''
        from pyvmmonitor_qt.qt.QtWidgets import QFontComboBox
        BaseLinkedEdition.__init__(self, link_to_attribute)
        qwidget = self.qwidget = QFontComboBox(parent_widget)
        qwidget.currentFontChanged.connect(self._on_font_changed)

    def _get_qfont(self, font_family):
        from pyvmmonitor_qt.qt.QtGui import QFont
        import sys
        font = QFont(font_family)
        if not font.exactMatch():
            sys.stderr.write(
                'Note: unable to find exact match for requested font: '
                '%s' % (font_family,))
        return font

    @overrides(BaseLinkedEdition._on_update_ui)
    def _on_update_ui(self):
        for data in self.data:
            internal_value = getattr(data, self._link_to_attribute)
            self.qwidget.setCurrentFont(self._get_qfont(internal_value))
            return True

        return False

    @_skip_on_expected_ui_change
    def _on_font_changed(self, font):
        font_family = font.family()
        self._set_attr(font_family)

    def get_current_font_family(self):
        return self.qwidget.currentFont().family()

    def set_current_font_family(self, font_family):
        self.qwidget.setCurrentFont(self._get_qfont(font_family))

    current_font_family = property(get_current_font_family, set_current_font_family)


class MultiLineText(BaseLinkedEdition):

    __slots__ = []

    def __init__(self, parent_widget, link_to_attribute):
        from pyvmmonitor_qt.qt.QtWidgets import QPlainTextEdit
        BaseLinkedEdition.__init__(self, link_to_attribute)
        qwidget = self.qwidget = QPlainTextEdit(parent_widget)
        qwidget.textChanged.connect(self._on_text_changed)

    @overrides(BaseLinkedEdition._on_update_ui)
    def _on_update_ui(self):
        for obj in self.data:
            self.qwidget.setPlainText(getattr(obj, self._link_to_attribute))
            return

    @_skip_on_expected_ui_change
    def _on_text_changed(self):
        text = self.qwidget.toPlainText()
        self._set_attr(text)
