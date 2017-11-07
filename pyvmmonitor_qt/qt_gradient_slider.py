'''
License: LGPL

Copyright: Brainwy Software Ltda

To use:

slider = QGradientSlider()
slider.min_value = 0
slider.max_value = 100
slider.value = 10

def on_value_changed(slider, value):
    ...

slider.on_value.register(on_value_changed)

'''
from __future__ import division

import logging

from pyvmmonitor_core import overrides
from pyvmmonitor_core.props import PropsCustomProperty, PropsObject
from pyvmmonitor_qt.qt_pixmap_widget import QPixmapWidget

logger = logging.getLogger(__name__)


class _ValueCustomProp(PropsCustomProperty):

    def convert(self, obj, v):
        if v < obj.min_value:
            logger.warn(
                'Trying to set a value (%s) < min (%s) value in QGradientSlider (using min instead).' % (
                    v, obj.min_value))
            v = obj.min_value

        elif v > obj.max_value:
            logger.warn(
                'Trying to set a value (%s) > max (%s) value in QGradientSlider (using min instead).' % (
                    v, obj.max_value))
            v = obj.max_value

        return v


class _MinValueCustomProp(PropsCustomProperty):

    def convert(self, obj, val):
        if val > obj.max_value:
            raise ValueError('Cannot set min value (%s) > max value (%s).' % (val, obj.max_value))
        return val


class _MaxValueCustomProp(PropsCustomProperty):

    def convert(self, obj, val):
        if val < obj.min_value:
            raise ValueError('Cannot set min value (%s) > max value (%s).' % (val, obj.min_value))
        return val


class _QGradientSliderProps(PropsObject):
    PropsObject.declare_props(
        value=_ValueCustomProp(0),
        min_value=_MinValueCustomProp(0),
        max_value=_MaxValueCustomProp(100))


class QGradientSlider(QPixmapWidget):

    # Will delegate the setters/getters to our properties
    PropsObject.delegate_to_props('value', 'min_value', 'max_value')

    def __init__(self, *args, **kwargs):
        from pyvmmonitor_core.callback import Callback
        from pyvmmonitor_qt.qt.QtGui import QColor
        from pyvmmonitor_qt.qt.QtCore import Qt
        QPixmapWidget.__init__(self, *args, **kwargs)
        self._props = _QGradientSliderProps()
        self._props.register_modified(self._on_modified)
        self._triangle_path = None
        self._triangle_size = None
        # Called with on_value(self, value)
        self.on_value = Callback()

        gradient_stops = [
            (0, QColor(Qt.black)),
            (1, QColor(Qt.red)),
        ]
        self.set_gradient_stops(gradient_stops)

    def set_gradient_stops(self, gradient_stops):
        from pyvmmonitor_qt.qt.QtGui import QColor
        last_i = -1
        for i, val in gradient_stops:
            assert 0 <= i <= 1, 'Expected %s to be 0 < i < 1' % (i,)
            assert i > last_i
            assert val.__class__ == QColor
            i = last_i

        self._gradient_stops = gradient_stops
        self._last_widget_size = None  # Force to regenerate
        self._pixmap = None  # Force to regenerate
        self.update()

    @property
    def normalized_value(self):
        v = (self.value - self.min_value) / float(self.max_value - self.min_value)
        if v < 0:
            v = 0
        if v > 1:
            v = 1
        return v

    @normalized_value.setter
    def normalized_value(self, value):
        self.value = self.min_value + ((self.max_value - self.min_value) * value)

    def _on_modified(self, obj, attrs):
        if 'value' in attrs:
            new_val, _old_val = attrs['value']
            self.on_value(self, new_val)
        self.update()

    @overrides(QPixmapWidget._create_pixmap)
    def _create_pixmap(self):
        '''
        Creates a qpixmap with the gradient.
        '''
        from pyvmmonitor_qt.qt.QtGui import QLinearGradient
        from pyvmmonitor_qt.qt.QtCore import Qt
        from pyvmmonitor_qt.qt_utils import painter_on
        from pyvmmonitor_qt.qt.QtGui import QBrush
        from pyvmmonitor_qt import qt_painter_path
        from pyvmmonitor_qt.qt_pixmap_widget import create_tiled_pixmap
        w, h = self._w, self._h
        triangle_size = int(min(w, h) * .3)
        if triangle_size < 10:
            triangle_size = 10
        w *= .9
        h *= .9

        # pixmap = QPixmap(w, h)
        # Note: we could do the tiling only if there was actually some alpha.
        pixmap = create_tiled_pixmap(w, h, min(w, h) // 3)
        gradient = QLinearGradient(0, h // 2, w, h // 2)
        gradient.setStops(self._gradient_stops)
        with painter_on(pixmap, True) as painter:
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, w, h)

        self._triangle_path = qt_painter_path.create_equilateral_triangle_painter_path(
            triangle_size)
        self._triangle_size = triangle_size

        return pixmap

    @overrides(QPixmapWidget.paintEvent)
    def paintEvent(self, ev):
        from pyvmmonitor_qt.qt_utils import painter_on
        from pyvmmonitor_qt.qt.QtGui import QColor
        from pyvmmonitor_qt.qt.QtCore import Qt
        from pyvmmonitor_qt.qt.QtGui import QBrush

        QPixmapWidget.paintEvent(self, ev)
        pixmap = self._pixmap
        triangle_path = self._triangle_path
        pixmap_offset = self._pixmap_offset
        if pixmap is None or triangle_path is None or pixmap_offset is None:
            return

        # After painting, also show the value selected.
        with painter_on(self, True) as painter:
            painter.setPen(Qt.lightGray)

            translation = [pixmap_offset[0], pixmap_offset[1]]
            translation[1] += (pixmap.height() + 2)
            translation[0] += (self.normalized_value * pixmap.width())  # calculate the position
            translation[0] -= (self._triangle_size / 2)

            path = triangle_path.translated(translation[0], translation[1])
            painter.fillPath(path, QBrush(QColor(30, 30, 30)))
            painter.drawPath(path)

    def _on_mouse_pos(self, pos):
        value = self.value_from_point(*pos)
        self.value = value

    def value_from_point(self, x, y):
        pixmap = self._pixmap
        pixmap_offset = self._pixmap_offset
        if pixmap is None or pixmap_offset is None:
            # Unable to calculate anything, just return current value.
            return self.value

        x -= pixmap_offset[0]

        normalized = x / pixmap.width()
        if normalized < 0:
            normalized = 0
        if normalized > 1:
            normalized = 1
        return self.min_value + int((self.max_value - self.min_value) * normalized)
