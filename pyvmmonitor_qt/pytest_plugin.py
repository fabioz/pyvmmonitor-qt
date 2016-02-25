# License: LGPL
#
# Copyright: Brainwy Software
import types

import pytest

from pyvmmonitor_qt import qt_utils
from pyvmmonitor_qt.qt_utils import obtain_qapp, start_collect_only_in_ui_thread


def _list_widgets(qtbot):
    from pytestqt.qtbot import _iter_widgets
    return list(_iter_widgets(qtbot._request.node))


@pytest.yield_fixture
def qtapi(qtbot):
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

        from pyvmmonitor_qt.qt.QtGui import QApplication
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

    qt_utils.process_events(collect=True)
