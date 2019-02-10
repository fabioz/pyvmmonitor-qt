from contextlib import contextmanager

_clipboard_stack = []


class _DummyClipboard(object):

    _qimage = None
    _mime_data = None

    def setImage(self, qimage):
        self._qimage = qimage
        self._mime_data = None

    def image(self):
        from pyvmmonitor_qt.qt_utils import bytes_as_qimage
        if self._qimage is not None:
            return self._qimage

        if self._mime_data is not None:
            mime_data = self._mime_data
            png_data = mime_data.data('PNG')
            qimage = bytes_as_qimage(png_data.data())
            return qimage

        return None

    def setMimeData(self, mime_data):
        self._mime_data = mime_data


def get_clipboard():
    '''
    :return QClipboard
    '''
    if _clipboard_stack:
        return _clipboard_stack[-1]

    from pyvmmonitor_qt.qt.QtWidgets import QApplication
    return QApplication.clipboard()


@contextmanager
def push_clipboard():
    clipboard = _DummyClipboard()
    _clipboard_stack.append(clipboard)
    try:
        yield clipboard
    finally:
        pop_clipboard()


def pop_clipboard():
    del _clipboard_stack[-1]
