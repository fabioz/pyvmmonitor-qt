#------------------------------------------------------------------------------
# Copyright (c) 2010, Enthought Inc
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD license.

#
# Author: Enthought Inc
# Description: <Enthought pyface code editor>
#------------------------------------------------------------------------------

import math

from pyvmmonitor_qt.qt import QtCore, QtGui, QtWidgets
from pyvmmonitor_qt.qt_utils import handle_exception_in_method, painter_on


class GutterWidget(QtWidgets.QWidget):

    min_width = 5
    background_color = QtGui.QColor(220, 220, 220)
    foreground_color = QtCore.Qt.black

    def sizeHint(self):
        return QtCore.QSize(self.min_width, 0)

    @handle_exception_in_method
    def paintEvent(self, event):
        """ Paint the line numbers.
        """
        with painter_on(self, antialias=True) as painter:
            painter.fillRect(event.rect(), QtCore.Qt.lightGray)

    @handle_exception_in_method
    def wheelEvent(self, event):
        """ Delegate mouse wheel events to parent for seamless scrolling.
        """
        self.parent().wheelEvent(event)


class StatusGutterWidget(GutterWidget):

    """ Draws status markers
    """

    def __init__(self, *args, **kw):
        super(StatusGutterWidget, self).__init__(*args, **kw)

        self.error_lines = []
        self.warn_lines = []
        self.info_lines = []

    @handle_exception_in_method
    def sizeHint(self):
        return QtCore.QSize(10, 0)

    @handle_exception_in_method
    def paintEvent(self, event):
        """ Paint the line numbers.
        """
        with painter_on(self, antialias=True) as painter:
            if self.background_color is not None:
                painter.fillRect(event.rect(), self.background_color)

            cw = self.parent()

            pixels_per_block = self.height() / float(cw.blockCount())

            for line in self.info_lines:
                painter.fillRect(QtCore.QRect(0, line * pixels_per_block, self.width(), 3),
                                 QtCore.Qt.green)

            for line in self.warn_lines:
                painter.fillRect(QtCore.QRect(0, line * pixels_per_block, self.width(), 3),
                                 QtCore.Qt.yellow)

            for line in self.error_lines:
                painter.fillRect(QtCore.QRect(0, line * pixels_per_block, self.width(), 3),
                                 QtCore.Qt.red)


class LineNumberWidget(GutterWidget):

    """ Draw line numbers.
    """

    min_char_width = 4

    @handle_exception_in_method
    def fontMetrics(self):
        # QWidget's fontMetrics method does not provide an up to date
        # font metrics, just one corresponding to the initial font
        return QtGui.QFontMetrics(self.font)

    def set_font(self, font):
        self.font = font

    def digits_width(self):
        nlines = max(1, self.parent().blockCount())
        ndigits = max(self.min_char_width,
                      int(math.floor(math.log10(nlines) + 1)))
        width = max(self.fontMetrics().boundingRect(u'0' * ndigits).width() + 3,
                    self.min_width)
        return width

    @handle_exception_in_method
    def sizeHint(self):
        return QtCore.QSize(self.digits_width(), 0)

    @handle_exception_in_method
    def paintEvent(self, event):
        """ Paint the line numbers.
        """
        with painter_on(self, antialias=True) as painter:
            painter.setFont(self.font)
            if self.background_color is not None:
                painter.fillRect(event.rect(), self.background_color)

            cw = self.parent()
            block = cw.firstVisibleBlock()
            blocknum = block.blockNumber()
            top = cw.blockBoundingGeometry(block).translated(
                cw.contentOffset()).top()
            bottom = top + int(cw.blockBoundingRect(block).height())

            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    painter.setPen(self.foreground_color)
                    painter.drawText(0, top, self.width() - 2,
                                     self.fontMetrics().height(),
                                     QtCore.Qt.AlignRight, str(blocknum + 1))
                block = block.next()
                top = bottom
                bottom = top + int(cw.blockBoundingRect(block).height())
                blocknum += 1
