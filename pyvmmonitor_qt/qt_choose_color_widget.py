'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
from __future__ import division

import functools
import logging

from pyvmmonitor_core import overrides
from pyvmmonitor_core.callback import Callback
from pyvmmonitor_core.props import PropsObject
from pyvmmonitor_qt.qt.QtCore import Qt
from pyvmmonitor_qt.qt.QtGui import QColor
from pyvmmonitor_qt.qt.QtWidgets import QSizePolicy, QWidget
from pyvmmonitor_qt.qt_app import obtain_qapp
from pyvmmonitor_qt.qt_pixmap_widget import QPixmapWidget

logger = logging.getLogger(__name__)


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


class _LabelGradientAndInt(QWidget):

    def __init__(self, parent, text, gradient_stops=None, limits=(0, 100)):
        from pyvmmonitor_qt.qt.QtWidgets import QLabel
        from pyvmmonitor_qt.qt_gradient_slider import QGradientSlider
        from pyvmmonitor_qt.qt.QtWidgets import QSpinBox
        from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
        QWidget.__init__(self, parent)

        self.on_value_changed = Callback()

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        self._label = QLabel(self)
        self._label.setText(text)
        self._label.setFixedWidth(30)

        self._limits = limits

        self._slider = QGradientSlider(self)
        self._slider.min_value = limits[0]
        self._slider.max_value = limits[1]
        self._slider.on_value.register(self._on_gradient_value_changed)

        self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._slider.setFixedHeight(20)

        self._spin_box = QSpinBox(self)
        self._spin_box.setMinimum(limits[0])
        self._spin_box.setMaximum(limits[1])
        self._spin_box.valueChanged.connect(self._on_spin_value_changed)

        self._layout.addWidget(self._label)
        self._layout.addWidget(self._slider)
        self._layout.addWidget(self._spin_box)

        self.set_gradient_stops(gradient_stops)

    def set_gradient_stops(self, gradient_stops):
        if gradient_stops is not None:
            self._slider.set_gradient_stops(gradient_stops)

    def set_normalized_value(self, v):
        self._slider.normalized_value = v
        not_normalized = round(self._slider.value)  # Round to nearest int
        self._spin_box.setValue(not_normalized)

    def _on_gradient_value_changed(self, slider, value):
        self.on_value_changed(self._normalize(value))

    def _on_spin_value_changed(self, value):
        self.on_value_changed(self._normalize(value))

    def _normalize(self, value):
        limits = self._limits
        return (value - limits[0]) / float(limits[1] - limits[0])


class HSVWidget(QWidget):

    def __init__(self, parent, model):
        from pyvmmonitor_qt.qt.QtWidgets import QVBoxLayout
        QWidget.__init__(self, parent)
        self._in_expected_ui_change = 0

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        assert model is not None
        self._model = model

        hue_colors = [
            (hue / 360., QColor.fromHsvF(hue / 360., 1.0, 1.0)) for hue in range(0, 360, 10)]
        self._hue_widget = _LabelGradientAndInt(self, 'H', hue_colors, (0, 360))
        self._sat_widget = _LabelGradientAndInt(self, 'S')
        self._v_widget = _LabelGradientAndInt(self, 'V')

        self._hue_widget.on_value_changed.register(self._update_hue)
        self._sat_widget.on_value_changed.register(self._update_sat)
        self._v_widget.on_value_changed.register(self._update_v)

        self._layout.addWidget(self._hue_widget)
        self._layout.addWidget(self._sat_widget)
        self._layout.addWidget(self._v_widget)

        self._update_widgets()
        model.register_modified(self._on_model_changed)

    @property
    def model(self):
        return self._model

    def _update_hue(self, h):
        assert 0 <= h <= 1
        color = self._model.color
        old_h, s, v = color.hueF(), color.saturationF(), color.valueF()
        if old_h != h:
            color = QColor.fromHsvF(h, s, v)
            self._model.color = color

    def _update_sat(self, s):
        assert 0 <= s <= 1
        color = self._model.color
        h, old_s, v = color.hueF(), color.saturationF(), color.valueF()
        if old_s != s:
            color = QColor.fromHsvF(h, s, v)
            self._model.color = color

    def _update_v(self, v):
        assert 0 <= v <= 1
        color = self._model.color
        h, s, old_v = color.hueF(), color.saturationF(), color.valueF()
        if old_v != v:
            color = QColor.fromHsvF(h, s, v)
            self._model.color = color

    @_skip_on_expected_ui_change
    def _on_model_changed(self, obj, attrs):
        if 'color' in attrs:
            self._update_widgets()

    @_does_expected_ui_change
    def _update_widgets(self):
        color = self._model.color
        h, s, v = color.hueF(), color.saturationF(), color.valueF()
        self._sat_widget.set_gradient_stops(
            [(x / 100, QColor.fromHsvF(h, x / 100., v)) for x in range(100)])
        self._v_widget.set_gradient_stops(
            [(x / 100, QColor.fromHsvF(h, s, x / 100.)) for x in range(100)])

        self._hue_widget.set_normalized_value(h)
        self._sat_widget.set_normalized_value(s)
        self._v_widget.set_normalized_value(v)

        self.update()


class _ColorWheelWidget(QPixmapWidget):

    def __init__(self, parent, model):
        super().__init__(parent)
        self._model = model

        self._last_pos = None
        self._model.register_modified(self._on_model_changed)

    @property
    def _wheel_size(self):
        return self._w - int(self._pointer_size * 1.3)

    def _on_model_changed(self, obj, attrs):
        if 'color' in attrs:
            self.update()

    @property
    def color(self):
        raise AssertionError('deprecated')

    @color.setter
    def color(self, color):
        raise AssertionError('deprecated')

    @property
    def _pointer_size(self):
        pointer_size = int(self._w * .03) + 1
        if pointer_size % 2 == 0:
            pointer_size += 1
        return pointer_size

    @overrides(QPixmapWidget.paintEvent)
    def paintEvent(self, ev):
        from pyvmmonitor_qt.qt_utils import painter_on
        from pyvmmonitor_core import math_utils
        import math

        QPixmapWidget.paintEvent(self, ev)
        color = self._model.color
        if color is None or self._pixmap is None:
            return

        # After the pixmap is drawn, draw the selected hue/saturation.
        hue, saturation = color.hsvHueF(), color.hsvSaturationF()
        size = self._pixmap.width()
        center = self._center
        degrees = hue * 360
        distance = saturation * (size / 2)

        pointer_size = self._pointer_size
        delta = pointer_size / 2

        pt = math_utils.create_point(center, math.radians(degrees), distance)
        rect = pt[0] - delta, pt[1] - delta, pointer_size, pointer_size
        rect2 = rect[0] - 1, rect[1] - 1, rect[2] + 2, rect[3] + 2

        with painter_on(self, True) as painter:
            painter.setPen(Qt.white)
            painter.drawEllipse(*rect)
            painter.setPen(Qt.black)
            painter.drawEllipse(*rect2)

    @overrides(QPixmapWidget._create_pixmap)
    def _create_pixmap(self):
        hue_pixmap = self._create_hue_pixmap()
        return self._lighten_with_alpha(hue_pixmap)

    def _lighten_with_alpha(self, hue_pixmap):
        from pyvmmonitor_qt.qt.QtGui import QPixmap
        from pyvmmonitor_qt.qt_utils import painter_on
        from pyvmmonitor_qt.qt.QtGui import QRadialGradient
        from pyvmmonitor_qt.qt.QtGui import QBrush

        size = self._wheel_size

        # Create a gradient to lighten up the center
        alpha_channel_pixmap = QPixmap(size, size)
        alpha_channel_pixmap.fill(Qt.transparent)
        radius = (size / 2) - 4
        rg = QRadialGradient(size / 2, size / 2, radius, size / 2, size / 2)

        delta = 0.1
        v = 0.0
        for _ in range(10):
            v += delta
            rg.setColorAt(v, QColor.fromHsvF(0, 0, 1.0, 1.0 - v))

        with painter_on(alpha_channel_pixmap, True) as painter:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(rg))
            painter.drawEllipse(0, 0, size, size)

        with painter_on(hue_pixmap, True) as painter:
            # Draw the alpha channel pixmap on top of the hue.
            painter.drawPixmap(0, 0, alpha_channel_pixmap)

        return hue_pixmap

    def _create_hue_pixmap(self):
        '''
        Create a simple hue pixmap where we change the hue in a conical gradient.
        '''
        from pyvmmonitor_qt.qt.QtGui import QPixmap
        from pyvmmonitor_qt.qt.QtGui import QBrush
        from pyvmmonitor_qt.qt_utils import painter_on
        from pyvmmonitor_qt.qt.QtGui import QConicalGradient

        stops = 360
        delta = 1.0 / stops
        v = 0.0
        size = self._wheel_size

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        degrees = 360
        gradient = QConicalGradient(size / 2, size / 2, degrees)
        for _stop in range(stops):
            v += delta
            # we do 1.0 - v to have blue on top (just a matter of taste really).
            color = QColor.fromHsvF(1.0 - v, 1.0, 1.0)
            gradient.setColorAt(v, color)

        with painter_on(pixmap, True) as painter:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(0, 0, size, size)

        return pixmap

    def saturation_from_point(self, x, y):
        from pyvmmonitor_core.math_utils import calculate_distance
        point = x, y
        size = self._wheel_size
        center = self._center

        distance = calculate_distance(center, point)
        if distance == 0.0:
            return 0.0

        max_distance = size / 2
        if distance >= max_distance:
            return 1.0
        return distance / max_distance

    def hue_from_point(self, x, y):
        from pyvmmonitor_core import math_utils
        point = x, y
        angle = math_utils.calc_angle_in_radians(self._center, point)
        degrees = math_utils.radians_to_0_360_degrees(angle)
        return degrees / 360.

    @overrides(QPixmapWidget._on_mouse_pos)
    def _on_mouse_pos(self, pos):
        self._last_pos = pos
        saturation = self.saturation_from_point(*pos)
        hue = self.hue_from_point(*pos)

        # Update the model for the new saturation / hue.
        value = self._model.color.valueF()
        color = QColor.fromHsvF(hue, saturation, value)
        self._model.color = color


class _SelectedColorWidget(QWidget):

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self._color = None

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        '''
        :param QColor color:
        '''
        self._color = color
        self.update()

    def paintEvent(self, ev):
        if self._color is not None:
            from pyvmmonitor_qt.qt_utils import painter_on
            with painter_on(self, False) as painter:
                radius = self.width() / 5
                painter.setBrush(self._color)
                size = self.width() - 2
                painter.drawRoundedRect(0, 0, size, size, radius, radius)
        else:
            super().paintEvent(ev)


class ChooseColorModel(PropsObject):

    PropsObject.declare_props(color=QColor(Qt.red))


class ChooseColorWidget(QWidget):

    def __init__(self, parent, model):
        '''
        :param parent:
        :param ChooseColorModel model:
        '''
        from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
        from pyvmmonitor_qt.qt.QtCore import QSize
        from pyvmmonitor_qt.qt.QtWidgets import QTabWidget
        from pyvmmonitor_qt.qt.QtWidgets import QLabel
        super(ChooseColorWidget, self).__init__(parent=parent)

        self._model = model

        self._selected_color_widget = _SelectedColorWidget(self)
        self._selected_color_widget.setFixedWidth(42)

        self._tab_widget = QTabWidget(self)

        self._color_wheel_widget = _ColorWheelWidget(self._tab_widget, self._model)
        self._color_wheel_widget.setFixedSize(QSize(200, 200))
        self._tab_widget.addTab(self._color_wheel_widget, 'Wheel')
        label = QLabel(self._tab_widget)
        self._tab_widget.addTab(label, 'HSV')

        layout = QHBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(self._selected_color_widget)
        layout.addWidget(self._tab_widget)

    @property
    def model(self):
        return self._model

    @property
    def color_wheel_widget(self):
        return self._color_wheel_widget

    def set_color(self, qcolor):
        raise AssertionError('deprecated')


if __name__ == '__main__':
    qapp = obtain_qapp()
    w = _SelectedColorWidget()
    w.show()
    qapp.exec_()
