from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


def test_choose_color_widget(qtapi):
    from pyvmmonitor_qt.qt_choose_color_widget import ChooseColorWidget
    from pyvmmonitor_qt.qt_event_loop import process_events
    color_widget = ChooseColorWidget()
    color_widget.show()

    color_widget.resize(300, 300)
    process_events()
    color_widget.color_wheel_widget.repaint()
    size = color_widget.color_wheel_widget._pixmap.size()

    # Just checking that the color wheel was built on paint
    # It's not exactly 300 x 300 because of borders and decorations
    assert size.width() > 250
    assert size.height() > 250
