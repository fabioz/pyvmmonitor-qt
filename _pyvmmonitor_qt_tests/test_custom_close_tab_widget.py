# License: LGPL
#
# Copyright: Brainwy Software
from pyvmmonitor_qt.custom_close_tab_widget import CustomCloseTabWidget
from pyvmmonitor_qt.pytest_plugin import qtapi
from pyvmmonitor_qt.qt.QtWidgets import QLabel


def test_custom_close_tab_widget(qtapi):

    custom = CustomCloseTabWidget()
    qtapi.add_widget(custom)

    label = QLabel(custom._stack)
    label.setText('Label 1')
    custom.addTab(label, 't1', closeable=False)

    label = QLabel(custom._stack)
    label.setText('Label 2')
    custom.addTab(label, 't2', True)

    label = QLabel(custom._stack)
    label.setText('Label 3')
    custom.addTab(label, 't3', False)

    label = QLabel(custom._stack)
    label.setText('Label 4')
    custom.addTab(label, 't4', True)

    assert custom.tabText(3) == 't4'

    def on_remove(i):
        custom.removeTab(i)
    custom.on_remove_requested.register(on_remove)

#     qtapi.d()
    while custom.count() > 0:
        custom.removeTab(0)
