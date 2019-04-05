from contextlib import contextmanager

_clipboard_stack = []


def _set_qimage_in_mime_data(qimage, mime_data=None):
    from pyvmmonitor_qt.qt_utils import qimage_as_bytes
    from pyvmmonitor_qt.qt.QtCore import QMimeData

    if mime_data is None:
        mime_data = QMimeData()
    mime_data.setData('PNG', qimage_as_bytes(qimage))
    return mime_data


def _get_qimage_from_mime_data(mime_data):
        from pyvmmonitor_qt.qt_utils import bytes_as_qimage
        data = mime_data.data('PNG')
        if data is not None:
            return bytes_as_qimage(data)
        return data


class _AbstractClipboard(object):

    __slots__ = []
    _wrapped_clipboard = None  # Subclasses must provide the clipboard with mimeData()/setMimeData()

    @property
    def image(self):

        image = self._wrapped_clipboard.image()
        if image is not None and image.width() > 0:
            return image
        mime_data = self._wrapped_clipboard.mimeData()
        return _get_qimage_from_mime_data(mime_data)

    @image.setter
    def image(self, qimage):
        # clipboard.setImage() would be better, but other programs don't read transparency
        # that way (at least on windows), so, create a mime data saying that it's a PNG
        # (and everything else is mostly so that we use this accessor class for any other
        # quirk in qt).
        self._wrapped_clipboard.setMimeData(_set_qimage_in_mime_data(qimage))

    @property
    def text(self):
        return self._wrapped_clipboard.mimeData().text()

    @text.setter
    def text(self, text):
        from pyvmmonitor_qt.qt.QtCore import QMimeData
        mime_data = QMimeData()
        mime_data.setText(text)
        self._wrapped_clipboard.setMimeData(mime_data)


class _DummyClipboard(_AbstractClipboard):

    __slots__ = ['_wrapped_clipboard']

    def __init__(self):

        class _StubClibpoard(object):

            def __init__(self):
                from pyvmmonitor_qt.qt.QtCore import QMimeData
                self._mime_data = QMimeData()

            def mimeData(self):
                return self._mime_data

            def setMimeData(self, mime_data):
                self._mime_data = mime_data

            def image(self):
                return None

        self._wrapped_clipboard = _StubClibpoard()


class _DefaultClipboard(_AbstractClipboard):

    _instance = None

    __slots__ = ['_wrapped_clipboard']

    @classmethod
    def get_clipboard(cls):
        if cls._instance is None:
            cls._instance = _DefaultClipboard()
        return cls._instance

    def __init__(self):
        from pyvmmonitor_qt.qt.QtWidgets import QApplication
        self._wrapped_clipboard = QApplication.clipboard()


def get_clipboard():
    '''
    :return QClipboard
    '''
    if _clipboard_stack:
        return _clipboard_stack[-1]

    return _DefaultClipboard.get_clipboard()


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
