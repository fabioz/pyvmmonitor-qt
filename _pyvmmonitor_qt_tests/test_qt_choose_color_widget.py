'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


def test_choose_color_widget(qtapi):
    from pyvmmonitor_qt.qt_choose_color_widget import ChooseColorWidget
    from pyvmmonitor_qt.qt_event_loop import process_events
    from pyvmmonitor_qt.qt.QtGui import QColor
    choose_color_widget = ChooseColorWidget()
    choose_color_widget.show()

    process_events()
    color_wheel_widget = choose_color_widget.color_wheel_widget
    choose_color_widget.color_wheel_widget.repaint()
    pixmap_size = choose_color_widget.color_wheel_widget._pixmap.size()

    choose_color_widget.set_color(QColor(255, 0, 0))

    # Just checking that the color wheel was built on paint
    assert pixmap_size.width() > 30
    assert pixmap_size.height() > 30
    assert color_wheel_widget.width() > pixmap_size.width()
    assert color_wheel_widget.height() > pixmap_size.height()

    center = color_wheel_widget._center

    assert color_wheel_widget.saturation_from_point(center[0], center[1]) == 0.0
    assert color_wheel_widget.saturation_from_point(pixmap_size.width(), 0.0) == 1.0
