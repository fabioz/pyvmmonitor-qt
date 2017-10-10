'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
from contextlib import contextmanager

from PySide.QtSvg import QGraphicsSvgItem

from pyvmmonitor_core import overrides
from pyvmmonitor_core.callback import Callback
from pyvmmonitor_core.weak_utils import get_weakref
from pyvmmonitor_qt.qt import QtCore
from pyvmmonitor_qt.qt.QtCore import QPointF, QRectF, Qt
from pyvmmonitor_qt.qt.QtGui import QBrush, QColor, QPen
from pyvmmonitor_qt.qt.QtWidgets import (QGraphicsEllipseItem,
                                         QGraphicsPathItem, QGraphicsRectItem)
from pyvmmonitor_qt.qt_event_loop import execute_on_next_event_loop
from pyvmmonitor_qt.qt_transform import calculate_size_for_value_in_px


def create_graphics_item_rect(rect, fill_color=None, alpha=255, pen=None, parent=None):
    '''
    :param alpha: 255 means opaque, 0 means transparent.
    '''
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
    '''
    :param alpha: 255 means opaque, 0 means transparent.
    '''
    if fill_color is None:
        fill_color = QColor(Qt.white)
    fill_color.setAlpha(alpha)
    brush = QBrush(fill_color)
    item.setBrush(brush)


def set_graphics_item_colors(item, pen=None, fill_color=None, alpha=255):
    set_graphics_item_pen(item, pen)
    set_graphics_item_brush(item, fill_color, alpha)

# ==================================================================================================
#
# Using some free-functions to avoid inheritance with the QGraphicsItems (just expecting self to
# be passed as the first argument).
#
# In the end, the user still has to write the forwarding methods, but this keeps things more
# explicit as multiple inheritance with Qt can become a can of worms (this may be true with any
# multiple inheritance, but it can be particularly nasty with Qt in the mix).
#
# ==================================================================================================


def _init_item(
        item,
        center,
        radius_in_px,
        pen,
        fill_color,
        alpha,
        pixels_displacement=(0, 0),
        graphics_widget=None):
    '''
    :param alpha: 255 means opaque, 0 means transparent.
    '''

    item._center = center
    item._radius_in_px = radius_in_px
    item._pixels_displacement = pixels_displacement

    item._last_radius = None
    item._last_center = None
    item._last_pixels_displacement = None
    item._last_transform = None

    item._custom_hover = False
    item._hover_pen = None
    item._hover_fill_color = None
    item._hover_alpha = None
    item._hover_radius_in_px = None

    item._regular_pen = pen
    item._regular_fill_color = fill_color
    item._regular_alpha = alpha
    item._regular_radius_in_px = radius_in_px

    # May be changed for a function and if True is returned, the mouse press
    # is accepted.
    item.accept_mouse_press = lambda event: False

    item.on_enter_hover = Callback()
    item.on_leave_hover = Callback()

    item.on_mouse_press = Callback()
    item.on_mouse_move = Callback()
    item.on_mouse_release = Callback()

    item._delay_update = 0

    if hasattr(item, 'setPen'):
        set_graphics_item_colors(item, pen, fill_color, alpha)

    assert graphics_widget is not None
    item._graphics_widget = get_weakref(graphics_widget)

    # Needed to set the real position in pixels for the radius and pixels displacement.
    item._update_with_graphics_widget()


def _mouse_press_event_item(item, event):
    if item.accept_mouse_press(event):
        event.accept()
        item.on_mouse_press(item, event)


def _mouse_move_event_item(item, event):
    event.accept()
    item.on_mouse_move(item, event)


def _mouse_release_event_item(item, event):
    event.accept()
    item.on_mouse_release(item, event)


def _set_radius_in_px_item(item, radius_in_px):
    force = item._radius_in_px != radius_in_px
    item._radius_in_px = radius_in_px
    item._update_with_graphics_widget(force=force)


def _set_center_item(item, center):
    force = item._center != center
    item._center = center
    item._update_with_graphics_widget(force=force)


def _set_pixels_displacement_item(item, pixels_displacement):
    force = item._pixels_displacement != pixels_displacement
    item._pixels_displacement = pixels_displacement
    item._update_with_graphics_widget(force=force)


def _update_with_graphics_widget_item(item, force=False):
    if item._delay_update:
        return

    g = item._graphics_widget()
    if g is not None:
        _update_info(item, g, force=force)


def _update(item, radius, pixels_displacement, transform, force=False):
    center = item._center

    if force or radius != item._last_radius or center != item._last_center or \
            pixels_displacement != item._last_pixels_displacement or \
            transform != item._last_transform:
        item._last_radius = radius
        item._last_center = center
        item._last_pixels_displacement = pixels_displacement
        item._last_transform = transform
        item.set_position(center, radius, pixels_displacement)


def _update_info(item, graphics_widget, force=False):
    transform = graphics_widget.transform()
    pixels_displacement = item._pixels_displacement
    if pixels_displacement != (0, 0):
        pixels_displacement = (
            calculate_size_for_value_in_px(transform, pixels_displacement[0]),
            calculate_size_for_value_in_px(transform, pixels_displacement[1]),
        )

    radius = calculate_size_for_value_in_px(transform, item._radius_in_px)
    _update(item, radius, pixels_displacement, transform, force=force)


def _before_paint_item(item, painter, widget):
    from pyvmmonitor_qt.qt_utils import set_painter_antialiased
    set_painter_antialiased(painter, True, widget)

    g = item._graphics_widget()
    if g is not None:
        transform = g.transform()
        if transform != item._last_transform:
            # Note: updating on paint doesn't work well (bug was: when item goes out of the
            # window and then back, it is no longer shown).
            # So, always ask to update on next event.
            execute_on_next_event_loop(item._update_with_graphics_widget)


def _configure_hover_item(
        item,
        hover_pen,
        hover_fill_color=None,
        hover_alpha=255,
        hover_radius_in_px=None):
    item._custom_hover = True
    item._hover_pen = hover_pen
    item._hover_fill_color = hover_fill_color
    item._hover_alpha = hover_alpha
    item._hover_radius_in_px = hover_radius_in_px
    item.setAcceptHoverEvents(True)


def _unconfigure_hover_item(item):
    item._custom_hover = False
    item.setAcceptHoverEvents(False)
    # Restore pre-hover values
    item._radius_in_px = item._regular_radius_in_px
    set_graphics_item_colors(
        item,
        item._regular_pen,
        item._regular_fill_color,
        item._regular_alpha)


def _before_hover_enter_event(item, event):
    if item._custom_hover:
        if item._hover_radius_in_px is not None:
            item._radius_in_px = item._hover_radius_in_px
            execute_on_next_event_loop(item._update_with_graphics_widget)

        set_graphics_item_colors(
            item,
            item._hover_pen,
            item._hover_fill_color,
            item._hover_alpha)
    item.on_enter_hover(item)


def _before_hover_leave_event(item, event):
    if item._custom_hover:
        if item._radius_in_px != item._regular_radius_in_px:
            item._radius_in_px = item._regular_radius_in_px
            execute_on_next_event_loop(item._update_with_graphics_widget)

        set_graphics_item_colors(
            item,
            item._regular_pen,
            item._regular_fill_color,
            item._regular_alpha)
    item.on_leave_hover(item)


# ==================================================================================================
# _CustomGraphicsSquareItem
# ==================================================================================================
class _CustomGraphicsSquareItem(QGraphicsRectItem):

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
        QGraphicsRectItem.__init__(self, parent_item)
        self._qimage = None
        self._rotation_in_radians = 0.0
        _init_item(
            self,
            center,
            radius_in_px,
            pen,
            fill_color,
            alpha,
            pixels_displacement,
            graphics_widget)

    @contextmanager
    def delayed_update(self):
        self._delay_update += 1
        yield
        self._delay_update -= 1
        if self._delay_update == 0:
            self._update_with_graphics_widget()

    def mousePressEvent(self, event):
        _mouse_press_event_item(self, event)

    def mouseMoveEvent(self, event):
        _mouse_move_event_item(self, event)

    def mouseReleaseEvent(self, event):
        _mouse_release_event_item(self, event)

    def set_radius_in_px(self, radius_in_px):
        _set_radius_in_px_item(self, radius_in_px)

    def get_radius_in_px(self):
        return self._radius_in_px

    def set_center(self, center):
        _set_center_item(self, center)

    def set_pixels_displacement(self, pixels_displacement):
        _set_pixels_displacement_item(self, pixels_displacement)

    def get_pixels_displacement(self):
        return self._pixels_displacement

    def get_center(self):
        return self._center

    def _update_with_graphics_widget(self, force=False):
        _update_with_graphics_widget_item(self, force=force)

    @overrides(QGraphicsRectItem.paint)
    def paint(self, painter, option, widget=None):
        _before_paint_item(self, painter, widget)

        r = self.rect()
        if self._qimage is not None:
            painter.drawImage(
                r,
                self._qimage,
                QRectF(0, 0, self._qimage.width(), self._qimage.height()))

        QGraphicsRectItem.paint(self, painter, option, widget)

    def configure_hover(
            self,
            hover_pen,
            hover_fill_color=None,
            hover_alpha=255,
            hover_radius_in_px=None):
        _configure_hover_item(self, hover_pen, hover_fill_color, hover_alpha, hover_radius_in_px)

    def unconfigure_hover(self):
        _unconfigure_hover_item(self)

    def hoverEnterEvent(self, event):
        _before_hover_enter_event(self, event)
        return QGraphicsRectItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        _before_hover_leave_event(self, event)
        return QGraphicsRectItem.hoverLeaveEvent(self, event)

    def set_qimage(self, qimage):
        self._qimage = qimage

    def set_position(self, center, radius, pixels_displacement):
        x = center[0] + pixels_displacement[0]
        y = center[1] + pixels_displacement[1]

        self.setRect(QtCore.QRectF(x, y, 2. * radius, 2. * radius))

        import math
        self.setTransformOriginPoint(QPointF(x, y))
        self.setRotation(math.degrees(self._rotation_in_radians))

    def set_rotation_in_radians(self, rotation_in_radians):
        force = self._rotation_in_radians != rotation_in_radians
        self._rotation_in_radians = rotation_in_radians
        self._update_with_graphics_widget(force=force)


# ==================================================================================================
# _CustomGraphicsSvgItem
# ==================================================================================================
class _CustomGraphicsSvgItem(QGraphicsSvgItem):

    def __init__(
        self,
        parent_item,
        origin_pos,
        radius_in_px,
        pen,
        fill_color,
        alpha,
        pixels_displacement=(0, 0),
        graphics_widget=None,
        svg_renderer=None
    ):
        QGraphicsSvgItem.__init__(self, parent_item)
        self._qimage = None
        self._rotation_in_radians = 0.0
        self._base_scale = 1.0
        self._pen = None
        self._brush = None

        _init_item(
            self,
            origin_pos,
            radius_in_px,
            pen,
            fill_color,
            alpha,
            pixels_displacement,
            graphics_widget)

        if svg_renderer is not None:
            self._renderer = svg_renderer
            self.setSharedRenderer(svg_renderer)

    @contextmanager
    def delayed_update(self):
        self._delay_update += 1
        yield
        self._delay_update -= 1
        if self._delay_update == 0:
            self._update_with_graphics_widget()

    def setPen(self, pen):
        self._pen = pen

    def setBrush(self, brush):
        self._brush = brush

    def pen(self):
        return self._pen

    def brush(self):
        return self._brush

    def mousePressEvent(self, event):
        _mouse_press_event_item(self, event)

    def mouseMoveEvent(self, event):
        _mouse_move_event_item(self, event)

    def mouseReleaseEvent(self, event):
        _mouse_release_event_item(self, event)

    def set_radius_in_px(self, radius_in_px):
        _set_radius_in_px_item(self, radius_in_px)

    def get_radius_in_px(self):
        return self._radius_in_px

    def set_origin_pos(self, origin_pos):
        _set_center_item(self, origin_pos)

    def set_pixels_displacement(self, pixels_displacement):
        _set_pixels_displacement_item(self, pixels_displacement)

    def get_pixels_displacement(self):
        return self._pixels_displacement

    def get_origin_pos(self):
        return self._center  # _center internally, but it's actually the origin position.

    # Keep the center API for external users (although it actually sets the origin pos).
    set_center = set_origin_pos
    get_center = get_origin_pos

    def _update_with_graphics_widget(self, force=False):
        _update_with_graphics_widget_item(self, force=force)

    def configure_hover(
            self,
            hover_pen,
            hover_fill_color=None,
            hover_alpha=255,
            hover_radius_in_px=None):
        _configure_hover_item(self, hover_pen, hover_fill_color, hover_alpha, hover_radius_in_px)

    def unconfigure_hover(self):
        _unconfigure_hover_item(self)

    @overrides(QGraphicsSvgItem.paint)
    def paint(self, painter, option, widget=None):
        _before_paint_item(self, painter, widget)

        renderer = self.renderer()
        size = renderer.defaultSize()
        if size is not None and size.width() > 0 and size.height() > 0:
            width, height = size.width(), size.height()
            if self._pen is not None:
                painter.setPen(self._pen)
                painter.drawRect(QRectF(0, 0, width, height))

            if self._brush is not None:
                painter.setBrush(self._brush)
                painter.fillRect(QRectF(0, 0, width, height), self._brush)

        # : :type painter: QPainter
        QGraphicsSvgItem.paint(self, painter, option, widget)

    def hoverEnterEvent(self, event):
        # Note: although we have no configure_hover, the user may still treat
        # item.on_enter_hover and on_leave_hover.
        _before_hover_enter_event(self, event)
        return QGraphicsSvgItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        _before_hover_leave_event(self, event)
        return QGraphicsSvgItem.hoverLeaveEvent(self, event)

    def set_qimage(self, qimage):
        self._qimage = qimage

    def set_position(self, origin_pos, radius, pixels_displacement):
        x = origin_pos[0] + pixels_displacement[0]
        y = origin_pos[1] + pixels_displacement[1]

        from pyvmmonitor_qt.qt.QtGui import QTransform
        transf = QTransform()
        transf.translate(x, y)
        transf.rotateRadians(self._rotation_in_radians)
        transf.scale(self._base_scale * (radius * 2), self._base_scale * (radius * 2))
        self.setTransform(transf)

    def set_base_scale(self, base_scale):
        force = self._base_scale != base_scale
        self._base_scale = base_scale
        self._update_with_graphics_widget(force=force)

    def set_rotation_in_radians(self, rotation_in_radians):
        force = self._rotation_in_radians != rotation_in_radians
        self._rotation_in_radians = rotation_in_radians
        self._update_with_graphics_widget(force=force)


# ==================================================================================================
# _CustomGraphicsEllipseItem
# ==================================================================================================
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
        _init_item(
            self,
            center,
            radius_in_px,
            pen,
            fill_color,
            alpha,
            pixels_displacement,
            graphics_widget)

    @contextmanager
    def delayed_update(self):
        self._delay_update += 1
        yield
        self._delay_update -= 1
        if self._delay_update == 0:
            self._update_with_graphics_widget()

    def mousePressEvent(self, event):
        _mouse_press_event_item(self, event)

    def mouseMoveEvent(self, event):
        _mouse_move_event_item(self, event)

    def mouseReleaseEvent(self, event):
        _mouse_release_event_item(self, event)

    def set_radius_in_px(self, radius_in_px):
        _set_radius_in_px_item(self, radius_in_px)

    def get_radius_in_px(self):
        return self._radius_in_px

    def set_center(self, center):
        _set_center_item(self, center)

    def set_pixels_displacement(self, pixels_displacement):
        _set_pixels_displacement_item(self, pixels_displacement)

    def get_pixels_displacement(self):
        return self._pixels_displacement

    def get_center(self):
        return self._center

    def _update_with_graphics_widget(self, force=False):
        from pyvmmonitor_qt import qt_utils
        if not qt_utils.is_qobject_alive(self):
            return
        _update_with_graphics_widget_item(self, force=force)

    @overrides(QGraphicsEllipseItem.paint)
    def paint(self, painter, option, widget=None):
        _before_paint_item(self, painter, widget)

        QGraphicsEllipseItem.paint(self, painter, option, widget)

    def configure_hover(
            self,
            hover_pen,
            hover_fill_color=None,
            hover_alpha=255,
            hover_radius_in_px=None):
        _configure_hover_item(self, hover_pen, hover_fill_color, hover_alpha, hover_radius_in_px)

    def unconfigure_hover(self):
        _unconfigure_hover_item(self)

    def hoverEnterEvent(self, event):
        _before_hover_enter_event(self, event)
        return QGraphicsEllipseItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        _before_hover_leave_event(self, event)
        return QGraphicsEllipseItem.hoverLeaveEvent(self, event)

    def set_position(self, center, radius, pixels_displacement):
        self.setRect(
            QtCore.QRectF(
                center[0] - radius + pixels_displacement[0],
                center[1] - radius + pixels_displacement[1],
                2. * radius,
                2. * radius))


# ==================================================================================================
# _CustomQGraphicsPathItem
# ==================================================================================================
class _CustomQGraphicsPathItem(QGraphicsPathItem):

    def __init__(
            self,
            parent_item,
            pen,
            fill_color,
            alpha,
            graphics_widget=None):
        QGraphicsPathItem.__init__(self, parent_item)
        _init_item(
            self,
            center=(0, 0),
            radius_in_px=0,
            pen=pen,
            fill_color=fill_color,
            alpha=alpha,
            pixels_displacement=(0, 0),
            graphics_widget=graphics_widget)

    @contextmanager
    def delayed_update(self):
        self._delay_update += 1
        yield
        self._delay_update -= 1
        if self._delay_update == 0:
            self._update_with_graphics_widget()

    def get_center(self):
        rect = self.path().controlPointRect()
        center = rect.center()
        return center.x(), center.y()

    def mousePressEvent(self, event):
        _mouse_press_event_item(self, event)

    def mouseMoveEvent(self, event):
        _mouse_move_event_item(self, event)

    def mouseReleaseEvent(self, event):
        _mouse_release_event_item(self, event)

    def _update_with_graphics_widget(self, force=False):
        # Nothing to actually update based on the graphics widget in this case.
        pass

    def configure_hover(
            self,
            hover_pen,
            hover_fill_color=None,
            hover_alpha=255):
        _configure_hover_item(
            self,
            hover_pen,
            hover_fill_color,
            hover_alpha,
            hover_radius_in_px=None)

    def unconfigure_hover(self):
        _unconfigure_hover_item(self)

    def hoverEnterEvent(self, event):
        _before_hover_enter_event(self, event)
        return QGraphicsPathItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        _before_hover_leave_event(self, event)
        return QGraphicsPathItem.hoverLeaveEvent(self, event)


# ==================================================================================================
# create_graphics_path_item
# ==================================================================================================
def create_graphics_path_item(
        parent_item=None,
        pen=None,
        fill_color=None,
        alpha=200,
        graphics_widget=None):
    '''
    This is a bit different from the other custom elements. It's main purpose is just giving us
    the callbacks related to the mouse (whereas the other elements created have a behavior where
    the representation is updated based on the zoom level).

    :param alpha: 255 means opaque, 0 means transparent.
    '''
    return _CustomQGraphicsPathItem(
        parent_item=parent_item,
        pen=pen,
        fill_color=fill_color,
        alpha=alpha,
        graphics_widget=graphics_widget)


# ==================================================================================================
# create_fixed_pixels_graphics_item_circle
# ==================================================================================================
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

    :param alpha: 255 means opaque, 0 means transparent.
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


# ==================================================================================================
# create_fixed_pixels_graphics_item_square
# ==================================================================================================
def create_fixed_pixels_graphics_item_square(
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

    :param alpha: 255 means opaque, 0 means transparent.
    '''
    circle = _CustomGraphicsSquareItem(
        parent_item,
        center,
        radius_in_px,
        pen,
        fill_color,
        alpha,
        pixels_displacement,
        graphics_widget)
    return circle


# ==================================================================================================
# create_fixed_pixels_graphics_item_svg
# ==================================================================================================
def create_fixed_pixels_graphics_item_svg(
        origin_pos,
        radius_in_px,
        pen=None,
        fill_color=None,
        parent_item=None,
        alpha=200,
        pixels_displacement=(0, 0),
        graphics_widget=None,
        svg_renderer=None):
    '''
    :param pixels_displacement:
        A tuple (x, y) with pixels coordinates with a translation to be applied to sum with the
        origin_pos passed to calculate the actual origin_pos (useful when it's some item which is
        anchored in another item based on some distance in pixels).

    :param alpha: 255 means opaque, 0 means transparent.
    '''
    circle = _CustomGraphicsSvgItem(
        parent_item,
        origin_pos,
        radius_in_px,
        pen,
        fill_color,
        alpha,
        pixels_displacement,
        graphics_widget,
        svg_renderer)
    return circle
