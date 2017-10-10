'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
import pytest

from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


@pytest.fixture
def qgradient_slider():
    from pyvmmonitor_qt.qt_event_loop import process_events
    from pyvmmonitor_qt.qt_gradient_slider import QGradientSlider
    slider = QGradientSlider()
    yield slider
    slider.deleteLater()
    process_events(collect=True)


def test_qgradient_slider(qtapi, qgradient_slider, capsys):
    import logging
    from pyvmmonitor_core.log_utils import logger_level
    from pyvmmonitor_qt.qt.QtGui import QColor
    from pyvmmonitor_qt.qt.QtCore import Qt
    qgradient_slider.show()
    assert qgradient_slider.value == 0
    assert qgradient_slider.min_value == 0
    assert qgradient_slider.max_value == 100

    qgradient_slider.set_gradient_stops([
        (0, QColor(Qt.red)),
        (0.5, QColor(Qt.yellow)),
        (1.0, QColor(Qt.blue)),
    ])

    values = []

    def on_value_changed(slider, new_val):
        assert slider is qgradient_slider
        values.append(new_val)

    qgradient_slider.on_value.register(on_value_changed)
    try:
        qgradient_slider.value = 40
        assert values == [40]
        assert qgradient_slider.normalized_value == 0.4
        assert qgradient_slider.value == 40

        qgradient_slider.resize(100, 100)

        # Force the creation without waiting for a draw event.
        qgradient_slider.force_create_pixmap()

        # It's lower because the pixmap width < widget width
        assert qgradient_slider.value_from_point(30, 30) == 27

        logger = logging.getLogger()
        with logger_level(logger, logging.CRITICAL):
            # Trying to set > max or < min changes to the max or min value
            qgradient_slider.value = 999
            assert values == [40, 100]
            assert qgradient_slider.value == 100
            qgradient_slider.value = -1
            assert qgradient_slider.value == 0
            assert values == [40, 100, 0]

        with pytest.raises(ValueError):
            qgradient_slider.min_value = 1000

        with pytest.raises(ValueError):
            qgradient_slider.max_value = -1000

        assert (qgradient_slider.min_value, qgradient_slider.max_value) == (0, 100)  # unchanged
    finally:
        qgradient_slider.on_value.unregister(on_value_changed)
