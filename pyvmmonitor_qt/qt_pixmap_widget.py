'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
from pyvmmonitor_core import overrides
from pyvmmonitor_qt.qt.QtWidgets import QWidget


class QPixmapWidget(QWidget):
    '''
    A widget which shows a pixmap. It may be set by using the pixmap property or
    by subclassing _create_pixmap() to set the _pixmap (delayed until painting).

    Note that an internal flag _regenerate_pixmap_on_resize is kept to signal if
    the pixmap should be regenerated on each resize (subclasses may want to change it).
    '''

    _regenerate_pixmap_on_resize = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pixmap = None
        self._last_widget_size = None

        # When the pixmap is drawn, this will hold the amount translated to print the pixmap
        # centered in the widget.
        self._pixmap_offset = (0, 0)

    @property
    def pixmap(self):
        return self._pixmap

    @pixmap.setter
    def pixmap(self, pixmap):
        self._pixmap = pixmap
        # If the user is setting it from the outside, don't regenerate when a different
        # size is detected.
        self._regenerate_pixmap_on_resize = False
        self.update()

    @overrides(QWidget.paintEvent)
    def paintEvent(self, ev):
        from pyvmmonitor_qt.qt_utils import painter_on
        pixmap = self._pixmap
        widget_size = self._w, self._h

        if pixmap is None or (
                self._regenerate_pixmap_on_resize and widget_size != self._last_widget_size):
            pixmap = self.force_create_pixmap()

            if pixmap is None:
                self._last_widget_size = None
                return

            pixmap_size = pixmap.width(), pixmap.height()
            self._last_widget_size = widget_size
        else:
            pixmap_size = pixmap.width(), pixmap.height()

        with painter_on(self, False) as painter:
            # Draws the pixmap centered in the widget.
            diff = int((widget_size[0] - pixmap_size[0]) / 2), \
                int((widget_size[1] - pixmap_size[1]) / 2)

            self._pixmap_offset = diff
            painter.drawPixmap(diff[0], diff[1], pixmap)

    def force_create_pixmap(self):
        pixmap = self._pixmap = self._create_pixmap()
        return pixmap

    def _create_pixmap(self):
        '''
        Subclasses can override to show a qpixmap (delayed until actually painting -- usually
        used when the pixmap relies on the size).
        '''

    @property
    def _w(self):
        return self.width()

    @property
    def _h(self):
        return self.height()

    @property
    def _center(self):
        return self.width() / 2, self.height() / 2

    def mousePressEvent(self, ev):
        from pyvmmonitor_qt.qt.QtCore import Qt
        if ev.button() == Qt.LeftButton:
            pos = ev.pos()
            pos = pos.x(), pos.y()
            self._on_mouse_pos(pos)
            return

        return QWidget.mousePressEvent(self, ev)

    def mouseMoveEvent(self, ev):
        if self._last_pos is not None:
            pos = ev.pos()
            pos = pos.x(), pos.y()
            self._last_pos = pos
            self._on_mouse_pos(pos)
            return

        return QWidget.mouseMoveEvent(self, ev)

    def mouseReleaseEvent(self, ev):
        self._last_pos = None
        return QWidget.mouseReleaseEvent(self, ev)

    def _on_mouse_pos(self, pos):
        '''
        Subclasses may overwrite to receive a mouse press or mouse move notification.
        :param tuple pos:
            Position (x,y) where the mouse was pressed (widget coordinates).
        '''
