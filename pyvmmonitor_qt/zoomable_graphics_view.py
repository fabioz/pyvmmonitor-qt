# License: LGPL
#
# Copyright: Brainwy Software

import enum

from pyvmmonitor_qt.qt.QtCore import Qt
from pyvmmonitor_qt.qt.QtWidgets import QGraphicsView
from pyvmmonitor_qt.qt_utils import handle_exception_in_method


class BackgroundMode(enum.Enum):

    WIDGET_BACKGROUND = 0
    TILED_TRANSPARENT_BACKGROUND = 1


class ZoomableGraphicsView(QGraphicsView):
    '''
    A graphics view which provides zooming by default.

    Other properties:
        - OpenGL enabled if available
        - Antialiased by default.
        - Keeps center on resize.
        - Subclasses can specify a different background mode based on BackgroundMode.

    Some notes:

    - The view has 0,0 at the top-left corner.
    '''

    ANCHOR_CENTER = 'anchor_center'
    ANCHOR_MOUSE = 'anchor_mouse'

    BACKGROUND_MODE = BackgroundMode.TILED_TRANSPARENT_BACKGROUND

    def __init__(self, *args, **kwargs):
        from pyvmmonitor_qt.qt.QtWidgets import QGraphicsScene
        from pyvmmonitor_core.callback import Callback
        self.on_zoom = Callback()
        self._old_size = None

        scene = QGraphicsScene()
        QGraphicsView.__init__(self, scene, *args, **kwargs)
        self._scene = scene

        qglwidget = None
        from pyvmmonitor_qt.qt.QtOpenGL import is_good_opengl_version, create_gl_widget
        if is_good_opengl_version():
            qglwidget = create_gl_widget()
            self.setViewport(qglwidget)

        from pyvmmonitor_qt.qt_utils import set_painter_antialiased
        set_painter_antialiased(self, True, qglwidget)

        self._background_painter = BackgroundPainter(self.BACKGROUND_MODE)

        # self.setMouseTracking(True) -- enable if we want to receive mouse events
        # even without a click

        # Could be used to disable scroll bars
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    ZOOM_LEVELS = (0.05, 0.1, 0.175, 0.25, 0.375, 0.5, 0.75, 1.0,
                   1.25, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0, 15.0,
                   20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0,
                   125.0, 150.0, 175.0, 200.0, 300.0)

    @handle_exception_in_method
    def drawBackground(self, painter, rect):
        self._background_painter.paint(self, painter, rect)

    @property
    def curr_zoom(self):
        return self.transform().m11()

    def zoom_out(self, anchor=ANCHOR_CENTER):
        self.zoom_to(self.next_zoom_level(self.curr_zoom, 'out'), anchor)

    def zoom_in(self, anchor=ANCHOR_CENTER):
        self.zoom_to(self.next_zoom_level(self.curr_zoom, 'in'), anchor)

    def zoom_to(self, zoom, anchor=ANCHOR_CENTER):
        factor = zoom / self.curr_zoom
        if anchor == self.ANCHOR_MOUSE:
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        else:
            self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.scale(factor, factor)
        self.on_zoom(self.transform())

    @classmethod
    def next_zoom_level(cls, curr_zoom, mode):
        import bisect

        i = bisect.bisect_left(cls.ZOOM_LEVELS, curr_zoom)

        if i < 0:
            return cls.ZOOM_LEVELS[0]
        elif i >= len(cls.ZOOM_LEVELS):
            return cls.ZOOM_LEVELS[-1]

        next_zoom = cls.ZOOM_LEVELS[i]
        if mode == 'in':
            while next_zoom <= curr_zoom:
                i += 1
                if i >= len(cls.ZOOM_LEVELS):
                    return next_zoom  # Can't zoom in anymore
                next_zoom = cls.ZOOM_LEVELS[i]
        else:
            while next_zoom >= curr_zoom:
                i -= 1
                if i < 0:
                    return next_zoom  # Can't zoom out anymore
                next_zoom = cls.ZOOM_LEVELS[i]
        return next_zoom

    def fit(self):
        rect = self.sceneRect()
        x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
        self.fitInView(x, y, width, height, Qt.KeepAspectRatio)
        self.on_zoom(self.transform())

    def get_scene(self):
        return self._scene

    @handle_exception_in_method
    def wheelEvent(self, event, anchor=ANCHOR_MOUSE):
        if event.delta() < 0:
            self.zoom_out(anchor)
        else:
            self.zoom_in(anchor)

    @handle_exception_in_method
    def keyPressEvent(self, event):
        # Note: as we have scroll, left, right, up, down are already covered.
        if event.key() == Qt.Key_Plus:
            self.zoom_in()

        elif event.key() == Qt.Key_Minus:
            self.zoom_out()

        else:
            return QGraphicsView.keyPressEvent(self, event)

    def get_center(self):
        size = self.size()
        curr_center = self.mapToScene(size.width() / 2.0, size.height() / 2.0)
        return curr_center.x(), curr_center.y()

    def get_scene_visible_rect(self):
        size = self.size()
        w_and_h = self.mapToScene(size.width(), size.height())
        w_and_h.x(), w_and_h.y()

        x_and_y = self.mapToScene(0.0, 0.0)
        return x_and_y.x(), x_and_y.y(), w_and_h.x(), w_and_h.y()

    @handle_exception_in_method
    def resizeEvent(self, event):
        event_size = event.size()
        new_size = event_size.width(), event_size.height()
        if self._old_size is not None:
            old_size = self._old_size
            # Get the center before and after
            c0 = self.mapToScene(old_size[0] / 2.0, old_size[1] / 2.0)
            c1 = self.mapToScene(new_size[0] / 2.0, new_size[1] / 2.0)

            diff_x = c1.x() - c0.x()
            diff_y = c1.y() - c0.y()
            # And translate so that the current center is kept
            self.translate(diff_x, diff_y)

        self._old_size = new_size

        return QGraphicsView.resizeEvent(self, event)


class BackgroundPainter(object):

    def __init__(self, background_mode):
        self._cache = None
        self._cache_key = None
        self.size = 10
        self.background_mode = background_mode

    def _calculate_background_pixmap(self, rect):
        from pyvmmonitor_qt.qt.QtGui import QPixmap, QBrush

        cache_key = rect.x(), rect.y(), rect.width(), rect.height()
        if self._cache_key == cache_key:
            return self._cache

        from pyvmmonitor_qt.qt_utils import painter_on
        size = self.size

        p = QPixmap(20, 20)
        with painter_on(p, antialias=False) as pix_painter:
            pix_painter.fillRect(0, 0, 20, 20, Qt.white)
            pix_painter.fillRect(0, 0, 10, 10, Qt.gray)
            pix_painter.fillRect(10, 10, 20, 20, Qt.gray)
            pix_painter.end()
            brush = QBrush(p)

        p2 = QPixmap(rect.width() + (size * 2), rect.height() + (size * 2))
        with painter_on(p2, antialias=False) as pix_painter:
            pix_painter.fillRect(
                0,
                0,
                rect.width() + (size * 2),
                rect.height() + (size * 2),
                brush)
        self._cache = p2
        self._cache_key = cache_key
        return p2

    def paint(self, graphics_view, painter, rect):
        from pyvmmonitor_qt.qt.QtCore import QRect
        curr_transform = painter.transform()

        palette = graphics_view.palette()

        scene_rect = graphics_view.sceneRect()

        painter.resetTransform()
        s = curr_transform.mapRect(scene_rect)
        # Clear the area
        painter.fillRect(
            0,
            0,
            graphics_view.width(),
            graphics_view.height(),
            palette.window().color())

        if self.background_mode == BackgroundMode.TILED_TRANSPARENT_BACKGROUND:
            viewport_rect = QRect(0, 0, graphics_view.width(), graphics_view.height())
            clip_rect = s.intersected(viewport_rect)
            painter.setClipRect(clip_rect)
            painter.fillRect(s, Qt.white)
            use_rect = clip_rect

            size = self.size
            p2 = self._calculate_background_pixmap(use_rect)
            painter.drawPixmap(
                use_rect.x() - ((size * 2) - ((s.x() - use_rect.x()) % (size * 2))),
                use_rect.y() - ((size * 2) - ((s.y() - use_rect.y()) % (size * 2))),
                p2.width(),
                p2.height(),
                p2)

# I thought that the code below would give the same results, but it seems it doesn't
#             painter.fillRect(
#                 use_rect.x() - ((size * 2) - ((s.x() - use_rect.x()) % (size * 2))),
#                 use_rect.y() - ((size * 2) - ((s.y() - use_rect.y()) % (size * 2))),
#                 use_rect.width() + (size * 2),
#                 use_rect.height() + (size * 2),
#                 brush
#             )

        # Restore the previous transform
        painter.setTransform(curr_transform, False)
