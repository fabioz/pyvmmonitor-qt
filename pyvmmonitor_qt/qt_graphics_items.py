from pyvmmonitor_core import overrides
from pyvmmonitor_qt.qt import QtCore
from pyvmmonitor_qt.qt.QtCore import Qt
from pyvmmonitor_qt.qt.QtGui import QGraphicsEllipseItem, QColor, QPen, QBrush


def set_graphics_item_pen(item, pen=None):
    if pen is None:
        pen = QPen(QColor(Qt.black))
    item.setPen(pen)


def set_graphics_item_colors(item, pen=None, fill_color=None, alpha=255):
    set_graphics_item_pen(item, pen)
    if fill_color is None:
        fill_color = QColor(Qt.white)
    fill_color.setAlpha(alpha)
    brush = QBrush(fill_color)
    item.setBrush(brush)


def create_graphics_item_circle(
        center, radius, pen=None, fill_color=None, parent_item=None, alpha=200):
    circle = QGraphicsEllipseItem(parent_item)
    circle.setRect(QtCore.QRectF(
        center[0] - radius, center[1] - radius, 2. * radius, 2. * radius))

    set_graphics_item_colors(circle, pen, fill_color, alpha)

    return circle


class _CustomGraphicsEllipseItem(QGraphicsEllipseItem):

    def __init__(self, parent_item, center, radius_in_px):
        QGraphicsEllipseItem.__init__(self, parent_item)
        self.center = center
        self.radius_in_px = radius_in_px

        self._last_radius = None
        self._last_center = None

        self._update(radius_in_px)

    def _update(self, radius):
        center = self.center

        if radius != self._last_radius or center != self._last_center:
            self._last_radius = radius
            self._last_center = center
            self.setRect(
                QtCore.QRectF(
                    center[0] - radius,
                    center[1] - radius,
                    2. * radius,
                    2. * radius))

    @overrides(QGraphicsEllipseItem.paint)
    def paint(self, painter, option, widget=None):
        if widget is not None:
            graphics_widget = widget.parent()
            transform = graphics_widget.transform()
            radius = calculate_size_for_value_in_px(transform, self.radius_in_px)
            self._update(radius)

        return QGraphicsEllipseItem.paint(self, painter, option, widget)


def create_fixed_pixels_graphics_item_circle(
        center, radius_in_px, pen=None, fill_color=None, parent_item=None, alpha=200):
    circle = _CustomGraphicsEllipseItem(parent_item, center, radius_in_px)
    set_graphics_item_colors(circle, pen, fill_color, alpha)
    return circle


def calculate_size_for_value_in_px(transform, value_in_px):
    p0 = transform.map(0.0, 0.0)
    p1 = transform.map(1.0, 0.0)

    size = 1.0 / (p1[0] - p0[0])
    size *= value_in_px

    return size
