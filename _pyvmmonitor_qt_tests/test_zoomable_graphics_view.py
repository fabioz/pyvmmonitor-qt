'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
import pytest

from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


@pytest.fixture
def view(qtapi):
    from pyvmmonitor_qt.zoomable_graphics_view import ZoomableGraphicsView
    view = ZoomableGraphicsView()
    view.show()
    yield view
    view.hide()
    view.deleteLater()
    view = None


def test_next_zoom_level():
    from pyvmmonitor_qt.zoomable_graphics_view import ZoomableGraphicsView
    assert ZoomableGraphicsView.next_zoom_level(12, mode='in') == 15
    assert ZoomableGraphicsView.next_zoom_level(12, mode='out') == 10

    assert ZoomableGraphicsView.next_zoom_level(0.01, mode='in') == 0.05
    assert ZoomableGraphicsView.next_zoom_level(0.01, mode='out') == 0.05

    assert ZoomableGraphicsView.next_zoom_level(60000, mode='in') == 300
    assert ZoomableGraphicsView.next_zoom_level(60000, mode='out') == 300


def test_svg(qtapi, view):

    from pyvmmonitor_qt.qt_graphics_items import (
        create_graphics_item_rect, create_fixed_pixels_graphics_item_svg)
    from pyvmmonitor_qt.qt.QtSvg import QSvgRenderer

    item = create_graphics_item_rect((0, 0, 76, 76))
    view.scene().addItem(item)

    svg_renderer = QSvgRenderer(':appbar.cursor.move.svg')

    item = create_fixed_pixels_graphics_item_svg(
        (0, 0),
        50,
        pixels_displacement=(0, 0),
        graphics_widget=view,
        svg_renderer=svg_renderer,
    )
    item.set_base_scale(1 / 76)
    view.scene().addItem(item)

#    qtapi.d()


def test_zoom_on_wheel(qtapi, view):
    from pyvmmonitor_qt.qt.QtWidgets import QGraphicsLineItem
    from pyvmmonitor_qt.qt.QtGui import QColor
    from pyvmmonitor_qt.qt.QtGui import QPen
    from pyvmmonitor_qt.qt.QtCore import Qt

    item = QGraphicsLineItem(0, 0, 10, 10)
    item.setPen(QPen(QColor(Qt.red)))
    view.scene().addItem(item)
