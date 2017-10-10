import pytest

from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


@pytest.fixture
def qpixmap_widget():
    from pyvmmonitor_qt.qt_event_loop import process_events
    from pyvmmonitor_qt.qt_pixmap_widget import QPixmapWidget
    widget = QPixmapWidget()
    yield widget
    widget.deleteLater()
    process_events(collect=True)


def test_qpixmap_widget(qtapi, qpixmap_widget):
    from pyvmmonitor_qt.qt.QtGui import QPixmap
    from pyvmmonitor_qt.qt.QtCore import Qt
    qpixmap_widget.show()
    qpixmap_widget.regenerate_pixmap_on_resize = False
    pixmap = QPixmap(20, 20)
    pixmap.fill(Qt.red)
    qpixmap_widget.pixmap = pixmap
