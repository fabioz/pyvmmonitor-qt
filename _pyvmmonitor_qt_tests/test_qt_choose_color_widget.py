from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


def test_choose_color_widget(qtapi):
    from pyvmmonitor_qt.qt_choose_color_widget import ChooseColorWidget
    from pyvmmonitor_qt.qt_event_loop import process_events
    from pyvmmonitor_core.math_utils import almost_equal
    color_widget = ChooseColorWidget()
    color_widget.show()

    process_events()
    color_wheel_widget = color_widget.color_wheel_widget
    color_widget.color_wheel_widget.repaint()
    size = color_widget.color_wheel_widget._pixmap.size()

    # Just checking that the color wheel was built on paint
    assert size.width() > 30
    assert size.height() > 30
    assert color_wheel_widget.width() == size.width()
    assert color_wheel_widget.height() == size.height()

    assert color_wheel_widget.saturation_from_point(size.width() / 2., size.height() / 2.) == 0.0
    assert color_wheel_widget.saturation_from_point(size.width(), 0.0) == 1.0
    assert almost_equal(
        color_wheel_widget.saturation_from_point(size.width() / 4., size.height() / 2.), 0.5)

    assert color_wheel_widget.hue_from_point(size.width(), size.height() / 2) == 0.0
    assert color_wheel_widget.hue_from_point(size.width() / 2., size.height()) == 0.25
