import sys

from pyvmmonitor_qt.stylesheet import apply_default_stylesheet


_app = None


def obtain_qapp(apply_stylesheet=True):
    global _app

    if _app is None:
        from pyvmmonitor_qt.qt.QtWidgets import QApplication
        _app = QApplication.instance()
        if _app is None:
            _app = QApplication(sys.argv)

        if apply_stylesheet:
            apply_default_stylesheet(_app)

    return _app
