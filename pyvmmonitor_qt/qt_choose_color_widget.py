from __future__ import division

import logging

from pyvmmonitor_core import overrides
from pyvmmonitor_qt.qt.QtWidgets import QWidget
from pyvmmonitor_qt.qt_app import obtain_qapp
from pyvmmonitor_qt.qt_pixmap_widget import QPixmapWidget

logger = logging.getLogger(__name__)


class _ColorWheelWidget(QPixmapWidget):

    def __init__(self, *args, **kwargs):
        from pyvmmonitor_core.callback import Callback
        super().__init__(*args, **kwargs)

        # Called with on_hue_saturation_selected(hue, saturation)
        # 0 <= hue <= 1
        # 0 <= saturation <= 1
        self.on_hue_saturation_selected = Callback()
        self._last_pos = None
        self._color = None

    @property
    def _wheel_size(self):
        return self._w - int(self._pointer_size * 1.3)

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

    @property
    def _pointer_size(self):
        pointer_size = int(self._w * .03) + 1
        if pointer_size % 2 == 0:
            pointer_size += 1
        return pointer_size

    @overrides(QPixmapWidget.paintEvent)
    def paintEvent(self, ev):
        from pyvmmonitor_qt.qt_utils import painter_on
        from pyvmmonitor_qt.qt.QtCore import Qt
        from pyvmmonitor_core import math_utils
        import math

        QPixmapWidget.paintEvent(self, ev)
        color = self._color
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
        from pyvmmonitor_qt.qt.QtCore import Qt
        from pyvmmonitor_qt.qt_utils import painter_on
        from pyvmmonitor_qt.qt.QtGui import QColor
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
        from pyvmmonitor_qt.qt.QtCore import Qt
        from pyvmmonitor_qt.qt.QtGui import QColor
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
        self.on_hue_saturation_selected(hue, saturation)


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


class ChooseColorWidget(QWidget):

    def __init__(self, *args, **kwargs):
        from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
        from pyvmmonitor_qt.qt.QtCore import QSize
        super(ChooseColorWidget, self).__init__(*args, **kwargs)

        self._selected_color_widget = _SelectedColorWidget(self)
        self._selected_color_widget.setFixedWidth(42)

        self._color_wheel_widget = _ColorWheelWidget(self)
        self._color_wheel_widget.setFixedSize(QSize(200, 200))

        layout = QHBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(self._selected_color_widget)
        layout.addWidget(self._color_wheel_widget)

        self._color_wheel_widget.on_hue_saturation_selected.register(
            self._on_hue_saturation_selected)

    def _on_hue_saturation_selected(self, hue, saturation):
        from pyvmmonitor_qt.qt.QtGui import QColor
        color = QColor.fromHsvF(hue, saturation, 1.0)
        self.set_color(color)

    @property
    def color_wheel_widget(self):
        return self._color_wheel_widget

    def set_color(self, qcolor):
        self._color = qcolor
        self._selected_color_widget.color = qcolor
        self._color_wheel_widget.color = qcolor


if __name__ == '__main__':
    qapp = obtain_qapp()
    w = _SelectedColorWidget()
    w.show()
    qapp.exec_()
