from __future__ import division

import logging

from pyvmmonitor_qt.qt.QtWidgets import QWidget
from pyvmmonitor_qt.qt_app import obtain_qapp

logger = logging.getLogger(__name__)


class _ColorWheelWidget(QWidget):

    def __init__(self, *args, **kwargs):
        from pyvmmonitor_core.callback import Callback
        super().__init__(*args, **kwargs)

        self._pixmap = None
        # Called with on_hue_saturation_selected(hue, saturation)
        # 0 <= hue <= 1
        # 0 <= saturation <= 1
        self.on_hue_saturation_selected = Callback()

    def paintEvent(self, *args, **kwargs):
        from pyvmmonitor_qt.qt_utils import painter_on
        if self._pixmap is None or (
                self._pixmap.width(), self._pixmap.height()) != (self._w, self._h):
            self._create_pixmap()

        with painter_on(self, False) as painter:
            painter.drawPixmap(0, 0, self._pixmap)
        return

    @property
    def _w(self):
        return self.width()

    @property
    def _h(self):
        return self.height()

    @property
    def _center(self):
        return self.width() / 2, self.height() / 2

    def _create_pixmap(self):
        hue_pixmap = self._create_hue_pixmap()
        self._pixmap = self._lighten_with_alpha(hue_pixmap)

    def _lighten_with_alpha(self, hue_pixmap):
        from pyvmmonitor_qt.qt.QtGui import QPixmap
        from pyvmmonitor_qt.qt.QtCore import Qt
        from pyvmmonitor_qt.qt_utils import painter_on
        from pyvmmonitor_qt.qt.QtGui import QColor
        from pyvmmonitor_qt.qt.QtGui import QRadialGradient
        from pyvmmonitor_qt.qt.QtGui import QBrush

        # Create a gradient to lighten up the center
        alpha_channel_pixmap = QPixmap(self._w, self._h)
        alpha_channel_pixmap.fill(Qt.transparent)
        radius = (self._w / 2) - 4
        rg = QRadialGradient(self._w / 2, self._h / 2, radius, self._w / 2, self._h / 2)

        delta = 0.1
        v = 0.0
        for _ in range(10):
            v += delta
            rg.setColorAt(v, QColor.fromHsvF(0, 0, 1.0, 1.0 - v))

        with painter_on(alpha_channel_pixmap, True) as painter:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(rg))
            painter.drawEllipse(0, 0, self._w, self._h)

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
        w, h = self._w, self._h

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)

        degrees = 360
        gradient = QConicalGradient(w / 2, h / 2, degrees)
        for _stop in range(stops):
            v += delta
            # we do 1.0 - v to have blue on top (just a matter of taste really).
            color = QColor.fromHsvF(1.0 - v, 1.0, 1.0)
            gradient.setColorAt(v, color)

        with painter_on(pixmap, True) as painter:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(0, 0, w, h)

        return pixmap

    def saturation_from_point(self, x, y):
        from pyvmmonitor_core.math_utils import calculate_distance
        point = x, y
        w, h = self._w, self._h
        center = self._center

        distance = calculate_distance(center, point)
        if distance == 0.0:
            return 0.0
        if w != h:
            logger.warn('Hue may be wrong when w (%s) != h (%s)' % (w, h))

        max_distance = w / 2
        if distance >= max_distance:
            return 1.0
        return distance / max_distance

    def hue_from_point(self, x, y):
        from pyvmmonitor_core import math_utils
        import math
        point = x, y
        angle = math_utils.calc_angle_in_radians(self._center, point)
        degrees = math_utils.radians_to_0_360_degrees(angle)
        return degrees / 360.

    def mousePressEvent(self, ev):
        from pyvmmonitor_qt.qt.QtCore import Qt
        if ev.button() == Qt.LeftButton:
            pos = ev.pos()
            saturation = self.saturation_from_point(pos.x(), pos.y())
            hue = self.hue_from_point(pos.x(), pos.y())
            self.on_hue_saturation_selected(hue, saturation)
        return QWidget.mousePressEvent(self, ev)


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
                w = self.width() - 2
                painter.drawRoundedRect(0, 0, w, w, radius, radius)
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
        print('update', hue, saturation)
        from pyvmmonitor_qt.qt.QtGui import QColor
        color = QColor.fromHsvF(hue, saturation, 1.0)
        self._selected_color_widget.color = color

    @property
    def color_wheel_widget(self):
        return self._color_wheel_widget

if __name__ == '__main__':
    qapp = obtain_qapp()
    w = _SelectedColorWidget()
    w.show()
    qapp.exec_()
