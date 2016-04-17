from pyvmmonitor_core import overrides
from pyvmmonitor_core.callback import Callback
from pyvmmonitor_qt.qt import QtCore
from pyvmmonitor_qt.qt.QtCore import Qt
from pyvmmonitor_qt.qt.QtGui import QGraphicsEllipseItem, QColor, QPen, QBrush


def set_graphics_item_pen(item, pen=None):
    if pen is None:
        pen = QPen(QColor(Qt.black))
    item.setPen(pen)


def set_graphics_item_brush(item, fill_color=None, alpha=255):
    if fill_color is None:
        fill_color = QColor(Qt.white)
    fill_color.setAlpha(alpha)
    brush = QBrush(fill_color)
    item.setBrush(brush)


def set_graphics_item_colors(item, pen=None, fill_color=None, alpha=255):
    set_graphics_item_pen(item, pen)
    set_graphics_item_brush(item, fill_color, alpha)


class _CustomGraphicsEllipseItem(QGraphicsEllipseItem):

    def __init__(self, parent_item, center, radius_in_px, pen, fill_color, alpha):
        QGraphicsEllipseItem.__init__(self, parent_item)
        self._center = center
        self._radius_in_px = radius_in_px

        self._last_radius = None
        self._last_center = None

        self._custom_hover = False
        self._hover_pen = None
        self._hover_fill_color = None
        self._hover_alpha = None
        self._hover_radius_in_px = None

        self._regular_pen = pen
        self._regular_fill_color = fill_color
        self._regular_alpha = alpha
        self._regular_radius_in_px = radius_in_px
        self.on_enter_hover = Callback()
        self.on_leave_hover = Callback()

        self._update(radius_in_px)
        set_graphics_item_colors(self, pen, fill_color, alpha)

    def set_radius_in_px(self, radius_in_px):
        self._radius_in_px = radius_in_px

    def _update(self, radius):
        center = self._center

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
            radius = calculate_size_for_value_in_px(transform, self._radius_in_px)
            self._update(radius)

        return QGraphicsEllipseItem.paint(self, painter, option, widget)

    def configure_hover(
            self,
            hover_pen,
            hover_fill_color=None,
            hover_alpha=255,
            hover_radius_in_px=None):
        self._custom_hover = True
        self._hover_pen = hover_pen
        self._hover_fill_color = hover_fill_color
        self._hover_alpha = hover_alpha
        self._hover_radius_in_px = hover_radius_in_px
        self.setAcceptHoverEvents(True)

    def unconfigure_hover(self):
        self._custom_hover = False
        self.setAcceptHoverEvents(False)
        # Restore pre-hover values
        self._radius_in_px = self._regular_radius_in_px
        set_graphics_item_colors(
            self,
            self._regular_pen,
            self._regular_fill_color,
            self._regular_alpha)

    def hoverEnterEvent(self, event):
        if self._custom_hover:
            if self._hover_radius_in_px is not None:
                self._radius_in_px = self._hover_radius_in_px
            set_graphics_item_colors(
                self,
                self._hover_pen,
                self._hover_fill_color,
                self._hover_alpha)
            self.on_enter_hover(self)
        return QGraphicsEllipseItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        if self._custom_hover:
            self._radius_in_px = self._regular_radius_in_px
            set_graphics_item_colors(
                self,
                self._regular_pen,
                self._regular_fill_color,
                self._regular_alpha)
            self.on_leave_hover(self)
        return QGraphicsEllipseItem.hoverLeaveEvent(self, event)


def create_fixed_pixels_graphics_item_circle(
        center, radius_in_px, pen=None, fill_color=None, parent_item=None, alpha=200):
    circle = _CustomGraphicsEllipseItem(parent_item, center, radius_in_px, pen, fill_color, alpha)
    return circle


def calculate_size_for_value_in_px(transform, value_in_px):
    p0 = transform.map(0.0, 0.0)
    p1 = transform.map(1.0, 0.0)

    size = 1.0 / (p1[0] - p0[0])
    size *= value_in_px

    return size
