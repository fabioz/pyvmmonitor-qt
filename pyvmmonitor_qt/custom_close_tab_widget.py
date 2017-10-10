'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
import weakref

from pyvmmonitor_core.callback import Callback
from pyvmmonitor_qt import qt_utils
from pyvmmonitor_qt.qt.QtWidgets import (QPushButton, QStackedWidget, QStyle,
                                         QTabBar, QVBoxLayout, QWidget)


class CustomCloseTabWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)

        self._tabbar = QTabBar(self)
        self._tabbar.currentChanged.connect(self._tab_changed)
        self._layout.addWidget(self._tabbar)

        self._stack = QStackedWidget(self)
        self._layout.addWidget(self._stack)

        self._widgets = []
        self._buttons = []
        self.setLayout(self._layout)
        # Called with: on_remove_requested(index)
        self.on_remove_requested = Callback()

    def _tab_changed(self, i):
        try:
            widget = self._widgets[i]
        except Exception:
            return  # Not there

        self._stack.setCurrentWidget(widget)

    def tab_text(self, i):
        return self._tabbar.tabText(i)
    tabText = tab_text

    def set_tab_text(self, i, text):
        return self._tabbar.setTabText(i, text)
    setTabText = set_tab_text

    def current_index(self):
        return self._tabbar.currentIndex()

    currentIndex = current_index

    def current_widget(self):
        return self._stack.currentWidget()

    currentWidget = current_widget

    def count(self):
        return len(self._widgets)

    __len__ = count

    def __iter__(self):
        i = 0
        while i < len(self):
            yield self.widget(i)
            i += 1

    def remove_tab(self, index):
        del self._widgets[index]
        del self._buttons[index]
        self._tabbar.removeTab(index)
    removeTab = remove_tab

    def index(self, widget):
        try:
            return self._widgets.index(widget)
        except ValueError:
            return -1

    def widget(self, i):
        return self._widgets[i]

    def add_tab(self, widget, label, closeable):
        widget.setParent(self._stack)

        self._widgets.append(widget)
        self._stack.addWidget(widget)
        self._tabbar.addTab(label)

        if closeable:

            bt = QPushButton(self._tabbar)
            bt.setFixedSize(20, 20)
            bt.setIcon(bt.style().standardIcon(QStyle.SP_DockWidgetCloseButton))
            self._tabbar.setTabButton(len(self._widgets) - 1, QTabBar.RightSide, bt)
            self._buttons.append(bt)

            weak_bt = weakref.ref(bt)
            weak_tab_widget = weakref.ref(self)

            def on_close():
                self = weak_tab_widget()
                bt = weak_bt()
                if self is None or bt is None:
                    return
                if not qt_utils.is_qobject_alive(self) or not qt_utils.is_qobject_alive(bt):
                    return
                i = self._buttons.index(bt)
                if i != -1:
                    self.on_remove_requested(i)
            bt.clicked.connect(on_close)
        else:
            self._buttons.append(None)

    addTab = add_tab
