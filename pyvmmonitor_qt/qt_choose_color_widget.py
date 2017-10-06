from pyvmmonitor_qt.qt.QtWidgets import QWidget


class _ColorWheelWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._pixmap = None

    def paintEvent(self, *args, **kwargs):
        from pyvmmonitor_qt.qt.QtGui import QPainter
        if self._pixmap is None or (
                self._pixmap.width(), self._pixmap.height()) != (self._w, self._h):
            self._create_pixmap()

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pixmap)
        return

    @property
    def _w(self):
        return self.width()

    @property
    def _h(self):
        return self.height()

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


class ChooseColorWidget(QWidget):

    def __init__(self, *args, **kwargs):
        from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
        super(ChooseColorWidget, self).__init__(*args, **kwargs)
        self._color_wheel_widget = _ColorWheelWidget(self)
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self._color_wheel_widget)

    @property
    def color_wheel_widget(self):
        return self._color_wheel_widget