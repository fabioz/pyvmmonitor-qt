'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
import types

import pytest
from pytestqt.plugin import qtbot  # @UnusedImport

pytest_plugins = ['pytestqt.plugin']


def _list_widgets(qtbot):
    from pytestqt.qtbot import _iter_widgets
    return list(_iter_widgets(qtbot._request.node))


def __show_dialog_and_exec(parent, title, message, detailed_message, icon):
    raise AssertionError('Error: trying to show dialog with: %s\n\n%s\n\n%s' % (
        title, message, detailed_message))


@pytest.yield_fixture(autouse=True)
def mock_show_error():
    from pyvmmonitor_qt import qt_utils
    original = qt_utils.__show_dialog_and_exec
    qt_utils.__show_dialog_and_exec = __show_dialog_and_exec
    yield
    qt_utils.__show_dialog_and_exec = original


@pytest.yield_fixture
def qtapi(qtbot):
    from pyvmmonitor_qt.qt_app import obtain_qapp
    from pyvmmonitor_qt.qt_collect import start_collect_only_in_ui_thread

    obtain_qapp()  # Will make sure that the default stylesheet is also applied
    start_collect_only_in_ui_thread()  # Make sure we'll only collect items in the main thread

    def d(self, make_visible=True):
        widget_and_visibility = []
        for weak_widget in _list_widgets(self):
            widget = weak_widget()
            if widget is not None:
                widget_and_visibility.append((widget, widget.isVisible()))

        if make_visible:
            for w in widget_and_visibility:
                w[0].setVisible(True)

        from pyvmmonitor_qt.qt.QtWidgets import QApplication
        QApplication.instance().exec_()

        for widget, visible in widget_and_visibility:
            widget.setVisible(visible)

    qtbot.d = types.MethodType(d, qtbot)

    yield qtbot

    for w in _list_widgets(qtbot):
        w = w()
        if hasattr(w, 'set_data'):
            w.set_data(None)

        if hasattr(w, 'clear_cycles'):
            w.clear_cycles()

    from pyvmmonitor_qt.qt_event_loop import process_events
    process_events(collect=True)
