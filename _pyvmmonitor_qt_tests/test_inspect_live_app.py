from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


def test_inspect_live_app(qtapi):
    from pyvmmonitor_qt import qt_inspector
    inspector = qt_inspector.create_live_app_inspector()
    inspector.show()
    inspector.deleteLater()
