'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
from __future__ import division

import logging

from pyvmmonitor_core import abstract, overrides
from pyvmmonitor_core.callback import Callback
from pyvmmonitor_core.props import PropsObject
from pyvmmonitor_qt.qt.QtCore import Qt
from pyvmmonitor_qt.qt.QtGui import QColor
from pyvmmonitor_qt.qt.QtWidgets import QSizePolicy, QWidget
from pyvmmonitor_qt.qt_app import obtain_qapp
from pyvmmonitor_qt.qt_linked_edition import (does_expected_data_change,
                                              does_expected_ui_change,
                                              skip_on_expected_data_change,
                                              skip_on_expected_ui_change)
from pyvmmonitor_qt.qt_pixmap_widget import QPixmapWidget

logger = logging.getLogger(__name__)

WIDTH_LABEL = 30
WIDTH_VALUE = 70


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
        self._label.setFixedWidth(WIDTH_LABEL)

        self._limits = limits

        self._slider = QGradientSlider(self)
        self._slider.min_value = limits[0]
        self._slider.max_value = limits[1]
        self._slider.on_value.register(self._on_gradient_value_changed)

        self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._slider.setFixedHeight(20)

        self._spin_box = QSpinBox(self)
        self._spin_box.setFixedWidth(WIDTH_VALUE)
        self._spin_box.setMinimum(limits[0])
        self._spin_box.setMaximum(limits[1])
        self._spin_box.valueChanged.connect(self._on_spin_value_changed)

        self._layout.addWidget(self._label)
        self._layout.addWidget(self._slider)
        self._layout.addWidget(self._spin_box)

        self.set_gradient_stops(gradient_stops)

    @property
    def slider(self):
        return self._slider

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


class _LabelAndHex(QWidget):

    def __init__(self, parent, text, model):
        from pyvmmonitor_qt.qt.QtWidgets import QLabel
        from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
        from pyvmmonitor_qt.qt_utils import add_expanding_spacer_to_layout
        from pyvmmonitor_qt.qt.QtWidgets import QLineEdit
        QWidget.__init__(self, parent)
        self._in_expected_ui_change = 0
        self._in_expected_data_change = 0
        self._model = model

        self.on_value_changed = Callback()

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        self._label = QLabel(self)
        self._label.setText(text)
        self._label.setFixedWidth(WIDTH_LABEL)

        self._line_edit = QLineEdit(self)
        self._line_edit.textChanged.connect(self._on_line_edit_changed)
        self._line_edit.setFixedWidth(WIDTH_VALUE)

        self._layout.addWidget(self._label)
        add_expanding_spacer_to_layout(self._layout)
        self._layout.addWidget(self._line_edit)
        self._model.register_modified(self._on_model_changed)
        self._update_line_edit()

    def _on_model_changed(self, obj, attrs):
        if 'color' in attrs:
            self._update_line_edit()

    @does_expected_ui_change
    @skip_on_expected_data_change
    def _update_line_edit(self):
        color = self._model.color
        self._line_edit.setText(color.name())
        self._line_edit.setStyleSheet("")

    @skip_on_expected_ui_change
    @does_expected_data_change
    def _on_line_edit_changed(self, value):
        color = QColor()
        color.setNamedColor(value)
        if not color.isValid():
            color.setNamedColor('#' + value)
        if color.isValid():
            self._model.color = color
            self._line_edit.setStyleSheet("")
        else:
            self._line_edit.setStyleSheet("QLineEdit { background: #D30000; color: white;}")


class _BaseColorsWidget(QWidget):

    def __init__(self, parent, model):
        from pyvmmonitor_qt.qt.QtWidgets import QVBoxLayout
        QWidget.__init__(self, parent)
        self._in_expected_ui_change = 0
        self._in_expected_data_change = 0
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        assert model is not None
        self._model = model

        self._create_label_widgets()

        self._widget_0.on_value_changed.register(self._update_w0)
        self._layout.addWidget(self._widget_0)

        if hasattr(self, '_widget_1'):
            self._widget_1.on_value_changed.register(self._update_w1)
            self._layout.addWidget(self._widget_1)

        if hasattr(self, '_widget_2'):
            self._widget_2.on_value_changed.register(self._update_w2)
            self._layout.addWidget(self._widget_2)

        if hasattr(self, '_widget_3'):
            self._widget_3.on_value_changed.register(self._update_w3)
            self._layout.addWidget(self._widget_3)

        self._update_widgets()
        model.register_modified(self._on_model_changed)

    @abstract
    def _create_label_widgets(self):
        pass

    @property
    def model(self):
        return self._model

    @skip_on_expected_ui_change
    @does_expected_data_change
    def _update_from_widget(self, v, index):
        assert 0 <= v <= 1
        color = self._model.color
        old_values = self._get_color_params(color)
        if old_values[index] != v:
            new_values = list(old_values)
            new_values[index] = v
            color = self._create_color_from_params(new_values)
            self._model.color = color

    @skip_on_expected_ui_change
    @does_expected_data_change
    def _update_w0(self, v):
        self._update_from_widget(v, 0)

    @skip_on_expected_ui_change
    @does_expected_data_change
    def _update_w1(self, v):
        self._update_from_widget(v, 1)

    @skip_on_expected_ui_change
    @does_expected_data_change
    def _update_w2(self, v):
        self._update_from_widget(v, 2)

    @skip_on_expected_ui_change
    @does_expected_data_change
    def _update_w3(self, v):
        self._update_from_widget(v, 3)

    def _on_model_changed(self, obj, attrs):
        if 'color' in attrs:
            self._update_widgets()

    @does_expected_ui_change
    def _update_widgets(self):
        color = self._model.color
        params = self._get_color_params(color)

        for i, param in enumerate(params):
            getattr(self, '_widget_%s' % (i,)).set_normalized_value(param)

        self.update()


class HSVWidget(_BaseColorsWidget):

    def _create_label_widgets(self):
        hue_colors = [
            (hue / 360., QColor.fromHsvF(hue / 360., 1.0, 1.0)) for hue in range(361)]
        self._widget_0 = _LabelGradientAndInt(self, 'H', hue_colors, (0, 360))
        self._widget_0.slider.setObjectName('Hue')

        self._widget_1 = _LabelGradientAndInt(self, 'S')
        self._widget_1.slider.setObjectName('Saturation')

        self._widget_2 = _LabelGradientAndInt(self, 'V')
        self._widget_2.slider.setObjectName('Value')

    def _get_color_params(self, color):
        h, s, v = color.hueF(), color.saturationF(), color.valueF()
        if h <= -1.0:
            h = 0.0
        return h, s, v

    def _create_color_from_params(self, params):
        return QColor.fromHsvF(*params)

    @does_expected_ui_change
    def _update_widgets(self):
        _BaseColorsWidget._update_widgets(self)
        color = self._model.color
        h, s, v = self._get_color_params(color)
        self._widget_1.set_gradient_stops(
            [(x / 100, QColor.fromHsvF(h, x / 100., v)) for x in range(101)])
        self._widget_2.set_gradient_stops(
            [(x / 100, QColor.fromHsvF(h, s, x / 100.)) for x in range(101)])

    @property
    def _hue_widget(self):  # Just for testing
        return self._widget_0


class RGBWidget(_BaseColorsWidget):

    def __init__(self, parent, model):
        _BaseColorsWidget.__init__(self, parent, model)
        self._layout.addWidget(self._widget_hex)

    def _create_label_widgets(self):
        colors = None
        self._widget_0 = _LabelGradientAndInt(self, 'R', colors, (0, 255))
        self._widget_0.slider.setObjectName('Red')

        self._widget_1 = _LabelGradientAndInt(self, 'G', colors, (0, 255))
        self._widget_1.slider.setObjectName('Green')

        self._widget_2 = _LabelGradientAndInt(self, 'B', colors, (0, 255))
        self._widget_2.slider.setObjectName('Blue')

        self._widget_hex = _LabelAndHex(self, 'Hex', self._model)

    def _get_color_params(self, color):
        return color.redF(), color.greenF(), color.blueF()

    def _create_color_from_params(self, params):
        return QColor.fromRgbF(*params)

    @does_expected_ui_change
    def _update_widgets(self):
        _BaseColorsWidget._update_widgets(self)
        color = self._model.color
        r, g, b = self._get_color_params(color)
        self._widget_0.set_gradient_stops(
            [(x / 255, QColor.fromRgbF(x / 255., g, b)) for x in range(256)])

        self._widget_1.set_gradient_stops(
            [(x / 255, QColor.fromRgbF(r, x / 255., b)) for x in range(256)])

        self._widget_2.set_gradient_stops(
            [(x / 255, QColor.fromRgbF(r, g, x / 255.)) for x in range(256)])

    @property
    def _r_widget(self):  # Just for testing
        return self._widget_0


class _CMYKWidget(_BaseColorsWidget):

    def __init__(self, parent, model):
        _BaseColorsWidget.__init__(self, parent, model)
        self._layout.addWidget(self._widget_3)

    def _create_label_widgets(self):
        self._widget_0 = _LabelGradientAndInt(self, 'C')
        self._widget_0.slider.setObjectName('Cyan')

        self._widget_1 = _LabelGradientAndInt(self, 'M')
        self._widget_1.slider.setObjectName('Magenta')

        self._widget_2 = _LabelGradientAndInt(self, 'Y')
        self._widget_2.slider.setObjectName('Yellow')

        self._widget_3 = _LabelGradientAndInt(self, 'K')
        self._widget_3.slider.setObjectName('Black')

    def _get_color_params(self, color):
        '''
        :param QColor color:
        '''
        return color.cyanF(), color.magentaF(), color.yellowF(), color.blackF()

    def _create_color_from_params(self, params):
        return QColor.fromCmykF(*params)

    @does_expected_ui_change
    def _update_widgets(self):
        _BaseColorsWidget._update_widgets(self)
        color = self._model.color
        c, m, y, k = self._get_color_params(color)
        self._widget_0.set_gradient_stops(
            [(x / 100, QColor.fromCmykF(x / 100., m, y, k)) for x in range(101)])

        self._widget_1.set_gradient_stops(
            [(x / 100, QColor.fromCmykF(c, x / 100., y, k)) for x in range(101)])

        self._widget_2.set_gradient_stops(
            [(x / 100, QColor.fromCmykF(c, m, x / 100., k)) for x in range(101)])

        self._widget_3.set_gradient_stops(
            [(x / 100, QColor.fromCmykF(c, m, y, x / 100)) for x in range(101)])


class _OpacityWidget(_BaseColorsWidget):

    def _create_label_widgets(self):
        self._widget_0 = _LabelGradientAndInt(self, 'A', None, (0, 255))

    def _get_color_params(self, color):
        raise AssertionError('Should not be used')

    def _create_color_from_params(self, params):
        raise AssertionError('Should not be used')

    @does_expected_ui_change
    def _update_widgets(self):
        color = self._model.color
        r, g, b = color.redF(), color.greenF(), color.blueF()
        self._widget_0.set_gradient_stops(
            [(a / 255, QColor.fromRgbF(r, g, b, a / 255)) for a in range(256)])
        self._widget_0.set_normalized_value(self._model.opacity / 255.)

    @skip_on_expected_ui_change
    @does_expected_data_change
    def _update_from_widget(self, v, index):
        assert 0 <= v <= 1
        opacity = self._model.opacity
        new_opacity = int(v * 255)
        if new_opacity != opacity:
            self._model.opacity = new_opacity

    @overrides(_BaseColorsWidget._on_model_changed)
    def _on_model_changed(self, obj, attrs):
        if 'opacity' in attrs:
            self._update_widgets()


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

    def __init__(self, parent, model):
        QWidget.__init__(self, parent)
        self._model = model
        model.register_modified(self._on_modified)

    def _on_modified(self, obj, attrs):
        if 'color' in attrs:
            self.update()

    def paintEvent(self, ev):
        color = self._model.color
        from pyvmmonitor_qt.qt_utils import painter_on
        with painter_on(self, False) as painter:
            radius = self.width() / 5
            painter.setBrush(color)
            size = self.width() - 2
            painter.drawRoundedRect(0, 0, size, size, radius, radius)


class ChooseColorModel(PropsObject):

    PropsObject.declare_props(
        color=QColor(Qt.red),
        opacity=255,
    )


class ChooseColorWidget(QWidget):

    def __init__(self, parent, model):
        '''
        :param parent:
        :param ChooseColorModel model:
        '''
        from pyvmmonitor_qt.qt.QtCore import QSize
        from pyvmmonitor_qt.qt.QtWidgets import QTabWidget
        from pyvmmonitor_qt.qt_widget_builder import WidgetBuilder
        from pyvmmonitor_qt.qt.QtWidgets import QGridLayout
        super(ChooseColorWidget, self).__init__(parent=parent)

        self._model = model

        self._selected_color_widget = _SelectedColorWidget(self, model)
        self._selected_color_widget.setFixedWidth(42)

        self._tab_widget = QTabWidget(self)

        widget_builder = WidgetBuilder()
        widget_builder.create_widget(self._tab_widget)
        self._color_wheel_widget = widget_builder.add_widget(
            _ColorWheelWidget(self._tab_widget, model))
        self._color_wheel_widget.setFixedSize(QSize(200, 200))
        self._hsv_widget = widget_builder.add_widget(_OpacityWidget(widget_builder.widget, model))
        self._tab_widget.addTab(widget_builder.widget, 'Wheel')

        widget_builder = WidgetBuilder()
        widget_builder.create_widget(self._tab_widget)
        self._rgb_widget = widget_builder.add_widget(RGBWidget(widget_builder.widget, model))
        self._hsv_widget = widget_builder.add_widget(HSVWidget(widget_builder.widget, model))
        self._hsv_widget = widget_builder.add_widget(_OpacityWidget(widget_builder.widget, model))
        self._tab_widget.addTab(widget_builder.widget, 'RGB, HSV')

        widget_builder = WidgetBuilder()
        widget_builder.create_widget(self._tab_widget)
        self._cmyk_widget = widget_builder.add_widget(_CMYKWidget(self._tab_widget, model))
        widget_builder.create_spacer()
        self._tab_widget.addTab(widget_builder.widget, 'CMYK')

        layout = QGridLayout(self)
        self.setLayout(layout)

        layout.addWidget(self._selected_color_widget, 0, 0)
        layout.addWidget(self._tab_widget, 0, 1, 2)

    @property
    def model(self):
        return self._model

    @property
    def color_wheel_widget(self):
        return self._color_wheel_widget


if __name__ == '__main__':
    qapp = obtain_qapp()
    w = _SelectedColorWidget()
    w.show()
    qapp.exec_()
