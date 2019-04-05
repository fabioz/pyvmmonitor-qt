import pytest

from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


@pytest.fixture
def mocked_clipboard():
    # Note: to test the real clipboard we shouldn't use this mock (right now the test
    # checks only the dummy clipboard, but we don't want to mess with the real clipboard
    # when testing).
    from pyvmmonitor_qt.qt_clipboard import push_clipboard
    with push_clipboard() as clipboard:
        yield clipboard


def test_clipboard(qtapi, mocked_clipboard):
    from pyvmmonitor_qt.qt_clipboard import get_clipboard
    from pyvmmonitor_qt.qt.QtGui import QImage
    from pyvmmonitor_qt.qt.QtCore import Qt

    image = QImage(20, 10, QImage.Format_ARGB32)
    image.fill(Qt.red)

    clipboard = get_clipboard()
    clipboard.image = image
    assert clipboard.image == image

    clipboard.text = 'foo'
    assert clipboard.text == 'foo'

    with pytest.raises(AttributeError):
        clipboard.foo = 'error'

    with pytest.raises(AttributeError):
        clipboard.foo
