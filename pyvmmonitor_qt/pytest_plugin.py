# License: LGPL
#
# Copyright: Brainwy Software
import types

import pytest

from pyvmmonitor_qt import qt_utils
from pyvmmonitor_qt.qt_utils import obtain_qapp, start_collect_only_in_ui_thread


@pytest.yield_fixture
def qtapi(qtbot):
    obtain_qapp()  # Will make sure that the default stylesheet is also applied
    start_collect_only_in_ui_thread()  # Make sure we'll only collect items in the main thread

    def d(self, make_visible=True):
        widget_and_visibility = []
        for weak_widget in self._widgets:
            widget = weak_widget()
            if widget is not None:
                widget_and_visibility.append((widget, widget.isVisible()))

        if make_visible:
            for w in widget_and_visibility:
                w[0].setVisible(True)

        self._app.exec_()

        for widget, visible in widget_and_visibility:
            widget.setVisible(visible)
    qtbot.d = types.MethodType(d, qtbot)

    yield qtbot

    for w in qtbot._widgets:
        w = w()
        if hasattr(w, 'set_data'):
            w.set_data(None)

        if hasattr(w, 'clear_cycles'):
            w.clear_cycles()

    qt_utils.process_events(collect=True)
