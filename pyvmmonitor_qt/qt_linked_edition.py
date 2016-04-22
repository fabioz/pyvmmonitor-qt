from pyvmmonitor_core import abstract
from pyvmmonitor_core.weak_utils import WeakList
from pyvmmonitor_qt import compat, qt_utils
from pyvmmonitor_qt.qt.QtGui import QSpinBox, QComboBox
from pyvmmonitor_qt.qt_event_loop import NextEventLoopUpdater


class _Base(object):

    def __init__(self, link_to_attribute):
        self._link_to_attribute = link_to_attribute
        self.data = WeakList()
        self._updater = NextEventLoopUpdater(self.update_ui)

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

    def _on_data_changed(self, obj, attrs):
        if self._link_to_attribute in attrs:
            self._updater.invalidate()

    def dispose(self):
        self._unlink()

        if self.qwidget is not None:
            if qt_utils.is_qobject_alive(self.qwidget):
                self.qwidget.deleteLater()

        self.data = None
        self.qwidget = None
        if self._updater is not None:
            self._updater.dispose()

        self._updater = None


class SpinBox(_Base):

    def __init__(self, parent_widget, link_to_attribute):
        '''
        :param QWidget parent_widget:
        :param str link_to_attribute:
        '''
        _Base.__init__(self, link_to_attribute)
        self.qwidget = QSpinBox(parent_widget)

        self.qwidget.valueChanged.connect(self.on_value_changed)
        self._link_to_attribute = link_to_attribute

    def _on_update_ui(self):
        for data in self.data:
            self.qwidget.setValue(getattr(data, self._link_to_attribute))
            return

    def on_value_changed(self, value):
        for obj in self.data:
            setattr(obj, self._link_to_attribute, value)

    def value(self):
        return self.qwidget.value()

    def set_value(self, value):
        return self.qwidget.setValue(value)


class Combo(_Base):

    def __init__(self, parent_widget, link_to_attribute, caption_to_internal_value):
        '''
        :param QWidget parent_widget:
        :param str link_to_attribute:
        :param OrderedDict caption_to_internal_value:
        '''
        _Base.__init__(self, link_to_attribute)
        self._link_to_attribute = link_to_attribute
        qwidget = self.qwidget = QComboBox(parent_widget)
        self._caption_to_index = {}
        for i, caption in enumerate(compat.iterkeys(caption_to_internal_value)):
            qwidget.addItem(caption)
            self._caption_to_index[caption] = i

        qwidget.currentIndexChanged.connect(self.on_value_changed)
        self.caption_to_internal_value = caption_to_internal_value

    def _on_update_ui(self):
        for data in self.data:
            internal_value = getattr(data, self._link_to_attribute)
            for caption, val in compat.iteritems(self.caption_to_internal_value):
                if val == internal_value:
                    self.qwidget.setCurrentIndex(self._caption_to_index[caption])
            return

    def on_value_changed(self, index):
        current_text = self.qwidget.currentText()
        try:
            value = self.caption_to_internal_value[current_text]
        except KeyError:
            pass
        else:
            for obj in self.data:
                setattr(obj, self._link_to_attribute, value)

    def current_text(self):
        return self.qwidget.currentText()

    def set_current_text(self, text):
        i = self.qwidget.findText(text)
        if i >= 0:
            self.qwidget.setCurrentIndex(i)
