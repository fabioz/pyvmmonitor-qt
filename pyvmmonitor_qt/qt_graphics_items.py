from pyvmmonitor_core import overrides
from pyvmmonitor_core.callback import Callback
from pyvmmonitor_core.weak_utils import get_weakref
from pyvmmonitor_qt.qt import QtCore
from pyvmmonitor_qt.qt.QtCore import Qt, QRectF
from pyvmmonitor_qt.qt.QtGui import QGraphicsEllipseItem, QColor, QPen, QBrush
from pyvmmonitor_qt.qt.QtGui import QGraphicsRectItem
from pyvmmonitor_qt.qt_event_loop import execute_on_next_event_loop


def create_graphics_item_rect(rect, fill_color=None, alpha=255, pen=None, parent=None):
    if isinstance(rect, (list, tuple)):
        rect = QRectF(*rect)
    rect_item = QGraphicsRectItem(rect, parent)
    set_graphics_item_pen(rect_item, pen)
    set_graphics_item_brush(rect_item, fill_color, alpha)
    return rect_item


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

    def __init__(
            self,
            parent_item,
            center,
            radius_in_px,
            pen,
            fill_color,
            alpha,
            pixels_displacement=(0, 0),
            graphics_widget=None):
        QGraphicsEllipseItem.__init__(self, parent_item)
        self._center = center
        self._radius_in_px = radius_in_px
        self._pixels_displacement = pixels_displacement

        self._last_radius = None
        self._last_center = None
        self._last_pixels_displacement = None
        self._last_transform = None

        self._custom_hover = False
        self._hover_pen = None
        self._hover_fill_color = None
        self._hover_alpha = None
        self._hover_radius_in_px = None

        self._regular_pen = pen
        self._regular_fill_color = fill_color
        self._regular_alpha = alpha
        self._regular_radius_in_px = radius_in_px

        # May be changed for a function and if True is returned, the mouse press
        # is accepted.
        self.accept_mouse_press = lambda event: False

        self.on_enter_hover = Callback()
        self.on_leave_hover = Callback()

        self.on_mouse_press = Callback()
        self.on_mouse_move = Callback()
        self.on_mouse_release = Callback()

        set_graphics_item_colors(self, pen, fill_color, alpha)

        assert graphics_widget is not None
        self._graphics_widget = get_weakref(graphics_widget)

        # Needed to set the real position in pixels for the radius and pixels displacement.
        self._update_with_graphics_widget()

    def mousePressEvent(self, event):
        if self.accept_mouse_press(event):
            event.accept()
            self.on_mouse_press(self, event)

    def mouseMoveEvent(self, event):
        event.accept()
        self.on_mouse_move(self, event)

    def mouseReleaseEvent(self, event):
        event.accept()
        self.on_mouse_release(self, event)

    def set_radius_in_px(self, radius_in_px):
        self._radius_in_px = radius_in_px
        self._update_with_graphics_widget()

    def get_radius_in_px(self):
        return self._radius_in_px

    def set_center(self, center):
        self._center = center
        self._update_with_graphics_widget()

    def set_pixels_displacement(self, pixels_displacement):
        self._pixels_displacement = pixels_displacement
        self._update_with_graphics_widget()

    def get_pixels_displacement(self):
        return self._pixels_displacement

    def get_center(self):
        return self._center

    def _update_with_graphics_widget(self):
        g = self._graphics_widget()
        if g is not None:
            self._update_info(g)

    def _update(self, radius, pixels_displacement, transform):
        center = self._center

        if radius != self._last_radius or center != self._last_center or \
                pixels_displacement != self._last_pixels_displacement or \
                transform != self._last_transform:
            self._last_radius = radius
            self._last_center = center
            self._last_pixels_displacement = pixels_displacement
            self._last_transform = transform
            self.setRect(
                QtCore.QRectF(
                    center[0] - radius + pixels_displacement[0],
                    center[1] - radius + pixels_displacement[1],
                    2. * radius,
                    2. * radius))

    def _update_info(self, graphics_widget):
        transform = graphics_widget.transform()
        pixels_displacement = self._pixels_displacement
        if pixels_displacement != (0, 0):
            pixels_displacement = (
                calculate_size_for_value_in_px(transform, pixels_displacement[0]),
                calculate_size_for_value_in_px(transform, pixels_displacement[1]),
            )

        radius = calculate_size_for_value_in_px(transform, self._radius_in_px)
        self._update(radius, pixels_displacement, transform)

    @overrides(QGraphicsEllipseItem.paint)
    def paint(self, painter, option, widget=None):
        g = self._graphics_widget()
        if g is not None:
            transform = g.transform()
            if transform != self._last_transform:
                # Note: updating on paint doesn't work well (bug was: when item goes out of the
                # window and then back, it is no longer shown).
                # So, always ask to update on next event.
                execute_on_next_event_loop(self._update_with_graphics_widget)

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
        center,
        radius_in_px,
        pen=None,
        fill_color=None,
        parent_item=None,
        alpha=200,
        pixels_displacement=(0, 0),
        graphics_widget=None):
    '''
    :param pixels_displacement:
        A tuple (x, y) with pixels coordinates with a translation to be
        applied to sum with the center passed to calculate the actual center (useful when it's
        some item which is anchored in another item based on some distance in pixels).
    '''
    circle = _CustomGraphicsEllipseItem(
        parent_item,
        center,
        radius_in_px,
        pen,
        fill_color,
        alpha,
        pixels_displacement,
        graphics_widget)
    return circle


def calculate_size_for_value_in_px(transform, value_in_px):
    p0 = transform.map(0.0, 0.0)
    p1 = transform.map(1.0, 0.0)

    size = 1.0 / (p1[0] - p0[0])
    size *= value_in_px

    return size
