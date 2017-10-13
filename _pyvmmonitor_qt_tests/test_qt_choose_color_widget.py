'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
import pytest

from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


@pytest.yield_fixture
def hsv_widget():
    from pyvmmonitor_qt.qt_choose_color_widget import HSVWidget
    from pyvmmonitor_qt.qt_choose_color_widget import ChooseColorModel
    hsvwidget = HSVWidget(parent=None, model=ChooseColorModel())
    hsvwidget.show()
    yield hsvwidget
    hsvwidget.deleteLater()
    hsvwidget = None
    from pyvmmonitor_qt.qt_event_loop import process_events
    process_events(collect=True)


def test_hsv_widget(qtapi, hsv_widget):
    from pyvmmonitor_qt.qt.QtGui import QColor
    assert hsv_widget.model is not None

    hsv_widget.model.color = QColor.fromHsvF(0.5, 0.5, 0.5)
    assert hsv_widget._hue_widget._slider.value == 360 * .5

    hsv_widget.model.color = QColor.fromHsvF(0.1, 0.5, 0.5)
    assert hsv_widget._hue_widget._slider.value == 360 * .1

    hsv_widget._hue_widget._slider.value = 360 * .4
    assert hsv_widget.model.color == QColor.fromHsvF(0.4, 0.5, 0.5)


@pytest.yield_fixture
def rgb_widget():
    from pyvmmonitor_qt.qt_choose_color_widget import RGBWidget
    from pyvmmonitor_qt.qt_choose_color_widget import ChooseColorModel
    rgbwidget = RGBWidget(parent=None, model=ChooseColorModel())
    rgbwidget.show()
    yield rgbwidget
    rgbwidget.deleteLater()
    rgbwidget = None
    from pyvmmonitor_qt.qt_event_loop import process_events
    process_events(collect=True)


@pytest.yield_fixture
def opacity_widget():
    from pyvmmonitor_qt.qt_choose_color_widget import ChooseColorModel
    from pyvmmonitor_qt.qt_choose_color_widget import _OpacityWidget
    widget = _OpacityWidget(parent=None, model=ChooseColorModel())
    widget.show()
    yield widget
    widget.deleteLater()
    widget = None
    from pyvmmonitor_qt.qt_event_loop import process_events
    process_events(collect=True)


def test_rgb_widget(qtapi, rgb_widget):
    from pyvmmonitor_qt.qt.QtGui import QColor
    assert rgb_widget.model is not None

    color = rgb_widget.model.color = QColor.fromRgbF(0.5, 0.5, 0.5)
    # Note: qt doesn't really store the original float for the later redF (it's re-normalized
    # based on 0-255.
    assert rgb_widget._r_widget._slider.value == 255 * color.redF()

    color = rgb_widget.model.color = QColor.fromRgbF(0.1, 0.5, 0.5)
    assert rgb_widget._r_widget._slider.value == 255 * color.redF()

    rgb_widget._r_widget._slider.value = 255 * .4
    assert rgb_widget.model.color == QColor.fromRgbF(0.4, 0.5, 0.5)


def test_opacity_widget(qtapi, opacity_widget):
    from pyvmmonitor_qt.qt.QtGui import QColor
    assert opacity_widget.model is not None
    color = opacity_widget.model.color = QColor.fromRgb(100, 90, 80)
    assert opacity_widget.model.opacity == 0
    opacity_widget.model.opacity = 150
    assert opacity_widget._widget_0._slider.value == 150


@pytest.yield_fixture
def choose_color_widget():
    from pyvmmonitor_qt.qt_choose_color_widget import ChooseColorModel
    from pyvmmonitor_qt.qt_choose_color_widget import ChooseColorWidget
    from pyvmmonitor_qt.qt_event_loop import process_events
    choose_color_widget = ChooseColorWidget(parent=None, model=ChooseColorModel())
    choose_color_widget.show()
    yield choose_color_widget
    choose_color_widget.deleteLater()
    choose_color_widget = None
    process_events(collect=True)


def test_choose_color_widget(qtapi, choose_color_widget):
    from pyvmmonitor_qt.qt_event_loop import process_events
    from pyvmmonitor_qt.qt.QtGui import QColor

    process_events()
    color_wheel_widget = choose_color_widget.color_wheel_widget
    choose_color_widget.color_wheel_widget.repaint()
    pixmap_size = choose_color_widget.color_wheel_widget._pixmap.size()

    # Just checking that the color wheel was built on paint
    assert pixmap_size.width() > 30
    assert pixmap_size.height() > 30
    assert color_wheel_widget.width() > pixmap_size.width()
    assert color_wheel_widget.height() > pixmap_size.height()

    center = color_wheel_widget._center

    assert color_wheel_widget.saturation_from_point(center[0], center[1]) == 0.0
    assert color_wheel_widget.saturation_from_point(pixmap_size.width(), 0.0) == 1.0

    choose_color_widget.model.color = QColor.fromCmykF(
        0.000000, 0.000000, 0.000000, 0.000000, 1.000000)

