# License: LGPL
#
# Copyright: Brainwy Software

# Note: search on http://qt-project.org/search?search=qmdiarea
# Examples: https://qt.gitorious.org/pyvmmonitor_qt.qt/pyvmmonitor_qt.qt-examples
from __future__ import unicode_literals

from functools import wraps
import gc
import sys
import threading
from time import sleep
import time
import traceback
import warnings
import weakref

from pyvmmonitor_core import is_frozen
from pyvmmonitor_core.html import escape_html
from pyvmmonitor_core.nodes_tree import NodesTree, Node
from pyvmmonitor_core.ordered_set import OrderedSet
from pyvmmonitor_core.thread_utils import is_in_main_thread
from pyvmmonitor_core.weak_utils import get_weakref
from pyvmmonitor_core.weakmethod import WeakMethodProxy
from pyvmmonitor_qt.qt import QtGui, QtCore, qt_api
from pyvmmonitor_qt.qt.QtCore import QTimer, QObject, QEvent, Qt, QModelIndex
from pyvmmonitor_qt.qt.QtGui import (
    QMdiArea,
    QTabWidget,
    QMessageBox,
    QTextEdit,
    QApplication,
    QLabel,
    QCursor,
    QAbstractItemView,
    QToolBar,
    QWidget,
    QSizePolicy, QItemSelection, QItemSelectionModel, QDialog, QTextCursor, QSpacerItem,
    QTextBrowser, QTreeView, QHBoxLayout, QIcon, QStyle)
from pyvmmonitor_qt.stylesheet import apply_default_stylesheet


PY2 = sys.version_info[0] < 3
PY3 = not PY2

if PY3:
    def as_unicode(b):
        if b.__class__ != str:
            return b.decode('utf-8', 'replace')
        return b
else:
    def as_unicode(b):
        if b.__class__ != unicode:
            return b.decode('utf-8', 'replace')
        return b


_app = None


def obtain_qapp(apply_stylesheet=True):
    global _app

    if _app is None:
        _app = QtGui.QApplication.instance()
        if _app is None:
            _app = QtGui.QApplication(sys.argv)

        if apply_stylesheet:
            apply_default_stylesheet(_app)

    return _app


# ==================================================================================================
# Helpers to execute on the next event loop
# ==================================================================================================


class _ExecuteOnLoopEvent(QEvent):

    def __init__(self):
        QEvent.__init__(self, QEvent.User)


class _Receiver(QObject):

    def __init__(self):
        QObject.__init__(self)
        self.funcs = OrderedSet()

    def event(self, ev):
        if isinstance(ev, _ExecuteOnLoopEvent):
            try:
                while True:
                    with _lock:
                        if not self.funcs:
                            return True
                        else:
                            func, _ = self.funcs.popitem(last=False)

                    # Execute it without the lock
                    func()
            except:
                show_exception()
            return True
        return False

_lock = threading.Lock()

_receiver = _Receiver()


def process_queue():
    _receiver.event(_ExecuteOnLoopEvent())


def execute_on_next_event_loop(func):
    # Note: keeps a strong reference and stacks the same call to be run only once.
    with _lock:
        # Remove and add so that it gets to the end of the list
        _receiver.funcs.discard(func)
        _receiver.funcs.add(func)
    obtain_qapp().postEvent(_receiver, _ExecuteOnLoopEvent())


# ==================================================================================================
# Helpers to execute after some time
# ==================================================================================================
_timers_alive = {}
_timers_lock = threading.Lock()


class _TimerAlive(object):

    def __init__(self, func, timer):
        self.func = func
        self.timer = timer

    def __call__(self):
        if self.func is not None:
            with _timers_lock:
                try:
                    func = self.func

                    timer = self.timer
                    if timer is not None:
                        timer.stop()
                        timer.deleteLater()

                    self.func = None
                    self.timer = None

                    if _timers_alive.get(func) is self:
                        # Still only execute it in the next cycle (with proper stacking).
                        execute_on_next_event_loop(func)
                finally:
                    _timers_alive.pop(self, None)


def execute_after_millis(millis, func):

    def register_timer():
        assert is_in_main_thread(), \
            'We can only create QTimers in the main thread '\
            '(or at least delete them in the same thread).'

        with _timers_lock:
            existing_timer = _timers_alive.get(func)
            if existing_timer is not None:
                timer = existing_timer.timer
                if timer is not None:
                    try:
                        timer.stop()
                        timer.start(millis)
                    except:
                        pass
                    return  # Restart it!

            timer = QTimer()
            timer_alive = _TimerAlive(func, timer)
            _timers_alive[func] = timer_alive

            timer.setSingleShot(True)
            timer.timeout.connect(timer_alive)
            timer.start(millis)
    if not is_in_main_thread():
        execute_on_next_event_loop(register_timer)
    else:
        register_timer()


# ==================================================================================================
# Helpers to process events
# ==================================================================================================
def process_events(collect=False):
    assert is_in_main_thread()
    if not collect:
        obtain_qapp().processEvents()

    else:

        app = obtain_qapp()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(app.exit)
        timer.start(0)
        app.exec_()


class QtWeakMethod(object):

    def __init__(self, qobject, method_name):
        assert is_qobject_alive(qobject)
        assert hasattr(qobject, method_name)

        self.qobject = get_weakref(qobject)
        self.method_name = method_name

    def __call__(self):
        obj = self.qobject()
        if obj is None or not is_qobject_alive(obj):
            return
        getattr(obj, self.method_name)()

    def __hash__(self, *args, **kwargs):
        return hash(self.method_name)

    def __eq__(self, o):
        if isinstance(o, QtWeakMethod):
            return self.method_name == o.method_name and self.qobject() is o.qobject()

        return False

    def __ne__(self, o):
        return not self == o


# ==================================================================================================
# QTreeView helpers
# ==================================================================================================
def children(tree):
    if hasattr(tree, 'topLevelItem'):
        return [tree.topLevelItem(i) for i in xrange(tree.topLevelItemCount())]
    else:
        raise AssertionError('Unable to get children for: %s' % (tree,))


def iter_widget_captions_and_items(
        widget,
        parent_index=None,
        prefix='',
        cols=(
            0,
        ),
        only_show_expanded=False,
        add_plus_to_new_level=True):
    from pyvmmonitor_qt.custom_close_tab_widget import CustomCloseTabWidget

    if isinstance(widget, QMdiArea):
        for sub in widget.subWindowList():
            yield sub.windowTitle(), sub

    elif isinstance(widget, (QTabWidget, CustomCloseTabWidget)):
        sz = widget.count()
        while sz > 0:
            sz -= 1
            txt = widget.tabText(sz)
            yield txt, widget.widget(sz)

    elif isinstance(widget, QAbstractItemView):
        model = widget.model()
        if parent_index is None:
            parent_index = QtCore.QModelIndex()
        row_count = model.rowCount(parent_index)

        for row in xrange(row_count):
            index = model.index(row, 0, parent_index)
            row_items = []

            for col in cols:
                index = model.index(row, col, parent_index)
                row_items.append(
                    prefix + model.data(index, QtCore.Qt.DisplayRole))

            if len(cols) > 1:
                yield row_items, index
            else:
                yield row_items[0], index

            if only_show_expanded and hasattr(widget, 'isExpanded'):
                index = model.index(row, 0, parent_index)
                if not widget.isExpanded(index):
                    continue

            for x in iter_widget_captions_and_items(
                    widget,
                    index,
                    prefix + '+' if add_plus_to_new_level else prefix,
                    cols,
                    only_show_expanded=only_show_expanded,
                    add_plus_to_new_level=add_plus_to_new_level):
                yield x
    else:
        raise AssertionError("Don't know how to list items for: %s" % (widget,))


def list_wiget_item_captions(
        widget,
        parent_index=None,
        prefix='',
        cols=(
            0,
        ),
        only_show_expanded=False):
    '''
    Lists the items in a qt object (QMdiArea, QTreeView, QTabWidget, ...), returning
    a list where each element is either a string (if only one column was asked for) or
    a list(list(str)) if more than one column was asked for.
    '''
    return list(
        x[0] for x in iter_widget_captions_and_items(
            widget,
            parent_index,
            prefix,
            cols,
            only_show_expanded))


def _get_expanded_nodes_tree(
        widget,
        parent_index=None,
        parent_node=None,
        data=QtCore.Qt.DisplayRole):
    '''
    :return NodesTree:
        Returns a tree with the paths for the passed data.
    '''
    model = widget.model()
    if parent_index is None:
        parent_index = QtCore.QModelIndex()
    row_count = model.rowCount(parent_index)

    if parent_node is None:
        parent_node = NodesTree()

    for row in xrange(row_count):
        index = model.index(row, 0, parent_index)
        if not widget.isExpanded(index):
            continue
        node = parent_node.add_child(Node(model.data(index, data)))
        _get_expanded_nodes_tree(widget, parent_index=index, parent_node=node)

    return parent_node


def _set_expanded_nodes_tree(
        widget,
        nodes_tree=None,
        parent_index=None,
        data=QtCore.Qt.DisplayRole):
    '''
    We have to find a tree subpath which matches the passed path (in nodes_tree) and expand it
    accordingly.

    :param NodesTree nodes_tree:
    '''
    if not nodes_tree.children:
        return True

    model = widget.model()
    if parent_index is None:
        parent_index = QtCore.QModelIndex()
    row_count = model.rowCount(parent_index)

    found = 0

    for row in xrange(row_count):
        index = model.index(row, 0, parent_index)

        model_data = model.data(index, data)
        for node in nodes_tree.children:
            if node.data == model_data:
                # Ok, we have a match on this subtree (expand even if it means expanding
                # only partially).
                widget.setExpanded(index, True)

                # Ok, we have a possible match, let's go forward on this node
                if _set_expanded_nodes_tree(widget, nodes_tree=node, parent_index=index):
                    found += 1

    return found == len(nodes_tree.children)


def expanded_nodes_tree(widget, nodes_tree=None, data=QtCore.Qt.DisplayRole):
    if nodes_tree is not None:
        _set_expanded_nodes_tree(widget, nodes_tree=nodes_tree, data=data)
    else:
        return _get_expanded_nodes_tree(widget, data=data)


def scroll_pos(tree, val=None):
    vertical_scrollbar = tree.verticalScrollBar()
    if not val:
        return vertical_scrollbar.value()
    else:
        min_val = vertical_scrollbar.minimum()
        max_val = vertical_scrollbar.maximum()
        if min_val <= val <= max_val:
            vertical_scrollbar.setValue(val)
        else:
            weak = get_weakref(vertical_scrollbar)
            # We'll wait for the range to change to apply it (i.e.: if we're restoring the
            # contents of a tree, it may take a while until it actually receives a range).

            def _on_range_changed(self, *args, **kwargs):
                vertical_scrollbar = weak()  # Don't create a cycle
                if vertical_scrollbar is None:
                    return

                vertical_scrollbar.rangeChanged.disconnect(_on_range_changed)
                vertical_scrollbar.setValue(val)
            vertical_scrollbar.rangeChanged.connect(_on_range_changed)


def count_items(tree):
    return len(list_wiget_item_captions(tree))


if qt_api == 'pyside':
    try:
        from PySide import shiboken
    except:
        import shiboken

    def is_qobject_alive(obj):
        return shiboken.isValid(obj)

    if sys.platform == 'darwin':
        import PySide

        def handler(msg_type, msg_string):
            if 'QCocoaView handleTabletEvent' in msg_string:
                return
            if 'modalSession has been' in msg_string:
                return
            sys.stderr.write(msg_string)
        PySide.QtCore.qInstallMsgHandler(handler)
else:
    def is_qobject_alive(obj):
        raise AssertionError('Not supported')


class GarbageCollector(object):

    def __init__(self):
        self.threshold = gc.get_threshold()

    def check(self):
        assert is_in_main_thread()
        DEBUG = False
        # Uncomment for debug
        if DEBUG:
            flags = (
                gc.DEBUG_COLLECTABLE |
                gc.DEBUG_UNCOLLECTABLE |
                gc.DEBUG_INSTANCES |
                gc.DEBUG_SAVEALL |   # i.e.: put in gc.garbage!
                gc.DEBUG_OBJECTS
            )
        else:
            flags = 0

        gc.set_debug(flags)
        l0, l1, l2 = gc.get_count()

        if l0 > self.threshold[0]:
            num = gc.collect(0)
            if DEBUG:
                print ('collecting gen 0, found:', num, 'unreachable')

            if l1 > self.threshold[1]:
                num = gc.collect(1)
                if DEBUG:
                    print ('collecting gen 1, found:', num, 'unreachable')

                if l2 > self.threshold[2]:
                    num = gc.collect(2)
                    if DEBUG:
                        print ('collecting gen 2, found:', num, 'unreachable')

        # uncomment for debug
        if DEBUG:
            garbage = gc.garbage
            if garbage:
                for obj in garbage:
                    print ('Error: cycle in: %s (%r) %s' % (obj, repr(obj), type(obj)))

            del gc.garbage[:]

        gc.set_debug(0)


class QtGarbageCollector(QObject):

    '''
    Disable automatic garbage collection and instead collect manually
    every INTERVAL milliseconds.

    This is done to ensure that garbage collection only happens in the GUI
    thread, as otherwise Qt can crash.
    '''

    if is_frozen():
        INTERVAL = 10000
    else:
        INTERVAL = 4000

    instance = None

    def __init__(self):
        assert is_in_main_thread()
        QObject.__init__(self)
        self._collector = GarbageCollector()

        timer = self.timer = QTimer()
        timer.timeout.connect(WeakMethodProxy(self.check))
        timer.start(self.INTERVAL)

    def check(self):
        self._collector.check()


def start_collect_only_in_ui_thread():
    gc.disable()

    if QtGarbageCollector.instance is None:
        QtGarbageCollector.instance = QtGarbageCollector()


_main_window = get_weakref(None)


def set_main_window(main_window):
    global _main_window
    _main_window = weakref.ref(main_window)


def get_main_window():
    m = _main_window()
    if m is None or not is_qobject_alive(m):
        return None
    return m


_ADDITIONAL_EXCEPTION_MSG = ''  # Unicode


def show_exception():
    '''
    Meant to be used when showing an exception.

    i.e.:

    try:
        foo()
    except:
        show_exception()
    '''
    import StringIO
    fp = StringIO.StringIO()

    traceback.print_exc(file=fp)
    # Print to console
    stack_trace = fp.getvalue()

    sys.stderr.write(stack_trace)

    if isinstance(stack_trace, str):
        stack_trace = stack_trace.decode(sys.getfilesystemencoding(), 'replace')

    info = sys.exc_info()
    message = escape_html(str(info[1]))
    if _ADDITIONAL_EXCEPTION_MSG:
        message += u'\n\n' + _ADDITIONAL_EXCEPTION_MSG
    show_message(message, stack_trace, parent=get_main_window())


def handle_exception_in_method(method):
    '''
    All qt function which are called by qt itself should have a
    handle_exception_in_method decorator so that we can see the exceptions
    properly (PySide will loose the exception if we don't).
    '''
    @wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except:
            if sys is not None:
                sys.excepthook(*sys.exc_info())
    return wrapper


def _except_hook(*args, **kwargs):
    show_exception()


def install_except_hook():
    sys.excepthook = _except_hook


def set_additional_exception_msg(exception_msg):
    global _ADDITIONAL_EXCEPTION_MSG
    if isinstance(exception_msg, str):
        exception_msg = exception_msg.decode('utf-8', 'replace')

    _ADDITIONAL_EXCEPTION_MSG = exception_msg


def show_message(
        message,
        detailed_message='',
        title='Error',
        parent=None,
        icon=QMessageBox.Critical):
    '''
    :param icon:
        QMessageBox.NoIcon
        QMessageBox.Question
        QMessageBox.Information
        QMessageBox.Warning
        QMessageBox.Critical
    '''
    if isinstance(icon, basestring):
        icon = icon.lower()
        if icon == 'error':
            icon = QMessageBox.Critical
        elif icon in ('warning', 'warn'):
            icon = QMessageBox.Warning
        elif icon in ('information', 'info'):
            icon = QMessageBox.Information
        elif icon == 'question':
            icon = QMessageBox.Question
        else:
            warnings.warn('Invalid icon: %s' % (icon,))
            icon = QMessageBox.NoIcon

    if not is_in_main_thread():
        # Important: if we're not in the main thread, we have to schedule to run it later
        # (in the UI thread).
        def func():
            show_message(message, detailed_message, title, parent, icon)
        execute_on_next_event_loop(func)
        return

    if parent is None:
        parent = get_main_window()

    get_icon = obtain_qapp().style().standardIcon

    if icon == QMessageBox.Information:
        icon = get_icon(QStyle.SP_MessageBoxInformation)
    elif icon == QMessageBox.Critical:
        icon = get_icon(QStyle.SP_MessageBoxCritical)
    elif icon == QMessageBox.Warning:
        icon = get_icon(QStyle.SP_MessageBoxWarning)
    elif icon == QMessageBox.Question:
        icon = get_icon(QStyle.SP_MessageBoxQuestion)
    else:
        icon = QIcon()
    message_box = _ResizeMessageBox(parent, title, message, detailed_message, icon)

    return message_box.exec_()


def create_message_box_with_custom_ok_cancel(
        parent=None,
        window_title=u'Error',
        text=u'Something happened',
        informative_text=u'What do you want to do?',
        button_accept_text=u'Try with option 1',
        button_reject_text=u'Try with option 2'):
    if parent is None:
        parent = get_main_window()
    dialog = QtGui.QMessageBox(parent())
    dialog.setWindowTitle(window_title)
    dialog.setText(text)

    dialog.setInformativeText(informative_text)
    button_accept = dialog.addButton(button_accept_text, QtGui.QMessageBox.AcceptRole)
    button_reject = dialog.addButton(button_reject_text, QtGui.QMessageBox.RejectRole)
    dialog.setDefaultButton(button_accept)
    return dialog
    # dialog.exec_()


class CustomMessageDialog(QDialog):

    def __init__(self, parent, create_contents=None, title=' ', size=(640, 540), flags=None):
        if flags is not None:
            QDialog.__init__(self, parent, flags)
        else:
            QDialog.__init__(self, parent)

        from pyvmmonitor_qt.qt.QtGui import QVBoxLayout
        self.setWindowTitle(title)

        self._layout = QVBoxLayout()
        if create_contents:
            create_contents(self)
        else:
            self._create_contents()
        self.setLayout(self._layout)
        self.resize(*size)

    def get_layout(self):
        return self._layout

    def _create_contents(self):
        pass

    def create_label(self, txt='', layout=None):
        widget = QLabel(self)
        widget.setText(txt)
        if layout is None:
            layout = self._layout
        layout.addWidget(widget)
        return widget

    def create_text_browser(self, txt='', open_links=False):
        text_browser = QTextBrowser(self)
        text_browser.setOpenExternalLinks(open_links)
        text_browser.setOpenLinks(open_links)
        text_browser.setContextMenuPolicy(Qt.NoContextMenu)
        text_browser.setText(txt)
        self._layout.addWidget(text_browser)
        return text_browser

    def create_text(self, txt='', read_only=False, line_wrap=True, is_html=True, font=None):
        widget = QTextEdit(self)
        widget.setReadOnly(read_only)
        if line_wrap:
            widget.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            widget.setLineWrapMode(QTextEdit.NoWrap)
        if is_html:
            widget.setHtml(txt)
        else:
            widget.setText(txt)

        if font is not None:
            widget.setFont(font)
        self._layout.addWidget(widget)
        return widget

    def create_spacer(self):
        spacer = QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self._layout.addItem(spacer)
        return spacer

    def create_buttons(self, show_ok=True, show_cancel=True):
        from pyvmmonitor_qt.qt.QtGui import QDialogButtonBox
        assert show_ok or show_cancel

        if show_ok and show_cancel:
            flags = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        elif show_ok:
            flags = QDialogButtonBox.Ok
        else:
            flags = QDialogButtonBox.Cancel

        self.bbox = bbox = QDialogButtonBox(flags)

        bbox.rejected.connect(self.reject)
        bbox.accepted.connect(self.accept)
        self._layout.addWidget(bbox)

    def create_close_button(self):
        from pyvmmonitor_qt.qt.QtGui import QDialogButtonBox
        flags = QDialogButtonBox.Close

        self.bbox = bbox = QDialogButtonBox(flags)

        bbox.rejected.connect(self.reject)
        self._layout.addWidget(bbox)


class _ResizeMessageBox(CustomMessageDialog):

    def __init__(self, parent, title, message, detailed_message, icon):
        CustomMessageDialog.__init__(self, parent)

        title = as_unicode(title)
        message = as_unicode(message)
        detailed_message = as_unicode(detailed_message)

        cp = [title, message]
        if detailed_message:
            cp.append(detailed_message)
        self._copy_text = u'\n---------------------\n'.join(cp)
        self._initial_pos = QCursor.pos()
        self._use_initial_pos = True
        self.setWindowTitle(title)

        self._hor_layout = QHBoxLayout()
        if icon is not None:
            self._label_icon = QLabel(self)
            self._label_icon.setPixmap(icon.pixmap(32, 32))
            self._label_icon.setFixedSize(40, 40)

        self._hor_layout.addWidget(self._label_icon)
        message = message.replace('\n', '<br/>')
        label = self.create_label(message, layout=self._hor_layout)
        self._layout.addLayout(self._hor_layout)

        label.setTextFormat(Qt.RichText)
        label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label.setOpenExternalLinks(True)

        from pyvmmonitor_qt.qt.QtGui import QDialogButtonBox

        self.bbox = bbox = QDialogButtonBox()
        if detailed_message:
            self.bt_copy = bbox.addButton(u'Copy to clipboard', QDialogButtonBox.ApplyRole)
        else:
            self.bt_copy = None

        self.bt_close = bbox.addButton(u'Ok', QDialogButtonBox.RejectRole)
        if detailed_message:
            self.bt_show_details = bbox.addButton(u'Show Details...', QDialogButtonBox.AcceptRole)
        else:
            self.bt_show_details = None

        bbox.clicked.connect(self._clicked_button)

        self._layout.addWidget(bbox)
        if detailed_message:
            self.tx_details = self.create_text(
                detailed_message, read_only=True, line_wrap=False, is_html=False)

            self.tx_details.setVisible(False)

        self.adjustSize()

    def _clicked_button(self, bt):
        if bt == self.bt_copy:
            QApplication.clipboard().setText(self._copy_text)
            self.bt_copy.setText('Copied to clipboard')

        elif bt == self.bt_show_details:
            if self.tx_details.isVisible():
                self.tx_details.setVisible(False)
                self.bt_show_details.setText('Show Details...')
                self.adjustSize()

            else:
                self.tx_details.setVisible(True)
                self.bt_show_details.setText('Hide Details...')
                self.resize(640, 480)
                self.move(
                    QApplication.desktop().availableGeometry(self._initial_pos).center() -
                    self.rect().center())

        elif bt == self.bt_close:
            self.reject()


def create_right_aligned_toolbar(parent):
    '''
    Creates a toolbar with an expanding widget in the beginning.
    '''
    toolbar = QToolBar(parent)
    spacer = QWidget(toolbar)
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    toolbar.addWidget(spacer)
    return toolbar


class MenuCreator(object):
    '''Helper class to create menus.'''

    def __init__(self, parent=None, parent_menu=None, caption=None):
        self.parent = parent
        from pyvmmonitor_qt.qt.QtGui import QMenu
        self.menu = QMenu(parent)
        if parent_menu is not None:
            parent_menu.addMenu(self.menu)

        if caption is not None:
            self.menu.setTitle(caption)

    def add_action(self, caption, callback=None, checkable=False):
        action = self.menu.addAction(caption)
        if callback is not None:
            action.triggered.connect(callback)
        if checkable:
            action.setCheckable(True)
        return action

    def add_submenu(self, caption):
        return MenuCreator(self.parent, parent_menu=self.menu, caption=caption)

    def create_menu(self):
        return self.menu


def count_widget_children(qwidget):
    total = 0
    for c in qwidget.children():
        total += count_widget_children(c) + 1
    return total


def create_toolbuttton_with_menu(parent, menu, icon=None):
    toolbutton = QtGui.QToolButton(parent)
    toolbutton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)

    default_action = QtGui.QAction(parent)
    default_action.triggered.connect(toolbutton.showMenu)

    if icon is not None:
        default_action.setIcon(icon)

    toolbutton.setDefaultAction(default_action)
    toolbutton.setMenu(menu)
    return toolbutton


def upate_font(widget, scale=1., make_bold=False):
    font = widget.font()
    if font is None:
        return
    if scale != 1.:
        point_size = font.pointSizeF()
        if point_size <= 0:
            pixel_size = font.pixelSize()
            if pixel_size > 0:
                font.setPixelSize(int(pixel_size * scale))
        else:
            font.setPointSizeF(point_size * scale)

    if make_bold:
        font.setBold(True)

    widget.setFont(font)


def select_rows(tree, rows, parent_index=None):
    if not isinstance(rows, (tuple, list)):
        rows = (rows,)

    model = tree.model()
    if parent_index is None:
        parent_index = QModelIndex()

    last_col = model.columnCount() - 1
    selection = tree.selectionModel()

    for i, row in enumerate(rows):
        selection_mode = QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows if i == 0 \
            else QItemSelectionModel.Rows

        selection.select(
            QItemSelection(
                model.index(
                    row, 0, parent_index), model.index(
                    row, last_col, parent_index)), selection_mode)


def show_message_with_copy_to_clipboard(
        title,
        msg,
        font=None,
        parent=None,
        size=None,
        read_only=True):
    if parent is None:
        parent = get_main_window()

    def copy():
        QApplication.clipboard().setText(msg)
        dialog.bt_copy.setText('Copied to clipboard')

    def create_contents(dialog):
        dialog.create_text(msg, read_only=read_only, line_wrap=False, is_html=False, font=font)
        from pyvmmonitor_qt.qt.QtGui import QDialogButtonBox
        dialog.bbox = bbox = QDialogButtonBox()

        dialog.bt_copy = bbox.addButton('Copy to clipboard', QDialogButtonBox.AcceptRole)
        bbox.addButton('Close', QDialogButtonBox.RejectRole)

        bbox.accepted.connect(copy)
        bbox.rejected.connect(dialog.reject)
        dialog._layout.addWidget(bbox)

    dialog = CustomMessageDialog(parent, create_contents, title=title)
    if size is None:
        dialog.adjustSize()
    else:
        dialog.resize(*size)
    ret = dialog.exec_()
    return ret


class LaunchExecutableDialog(CustomMessageDialog):

    def __init__(
            self,
            parent,
            title=' ',
            size=(
                480,
                360),
            flags=None,
            close_on_finish=True,
            cmd=None,
            env=None,
            stop_condition=None):
        '''
        :param close_on_finish: if False we'll keep on a busy loop until the user
        presses Cancel/Close or 'stopped' is set to True.

        :param stop_condition: callable()->bool
            If it returns True we'll consider that the process stopped and close the dialog.
        '''
        self._close_on_finish = close_on_finish
        if flags is None:
            flags = Qt.CustomizeWindowHint | Qt.WindowTitleHint
        if parent is None:
            parent = get_main_window()
        CustomMessageDialog.__init__(
            self, parent, title=title, size=size, flags=flags)
        if stop_condition is None:
            stop_condition = lambda: False
        self.stop_condition = stop_condition
        if not cmd:
            cmd = []
        self.cmd = cmd
        self.env = env
        self._popen = None
        self.stopped = False

    def set_cmd(self, cmd):
        self.cmd = cmd

    def reject(self, *args, **kwargs):
        self.stopped = True

    def exec_(self):
        from pyvmmonitor_core import exec_external
        p = self._popen = exec_external.ExecExternal(self.cmd, env=self.env)
        threading.Thread(target=p.call).start()

        self.setVisible(True)
        try:
            edit = self._edit
            while not p.finished:
                output = p.get_output()
                if output:
                    edit.moveCursor(QTextCursor.End)
                    edit.insertPlainText(output)
                    edit.moveCursor(QTextCursor.End)

                if self.stop_condition():
                    self.stopped = True

                if self.stopped:
                    break

                process_events()
                sleep(1. / 30.)

            output = p.get_output()
            if output:
                edit.moveCursor(QTextCursor.End)
                edit.insertPlainText(output)
                edit.moveCursor(QTextCursor.End)

            self.bt_cancel.setText('Close (Finished)')

            if not self._close_on_finish:

                while not self.stopped:
                    if self.stop_condition():
                        self.stopped = True

                    process_events()
                    sleep(1. / 30.)

            if not p.finished:
                p.cancel()

        finally:
            self.setVisible(False)

    def _create_contents(self):
        self.create_label('Process output')
        self._edit = self.create_text(read_only=True, line_wrap=True, is_html=False)

        from pyvmmonitor_qt.qt.QtGui import QDialogButtonBox
        self.bbox = bbox = QDialogButtonBox()
        self.bt_cancel = bbox.addButton('Cancel', QDialogButtonBox.RejectRole)
        bbox.rejected.connect(self.reject)
        self._layout.addWidget(bbox)


def expand(tree, caption):
    '''
    :param QTreeView tree:
    :param unicode caption:
    '''
    if isinstance(caption, basestring):
        caption = set([caption])
    else:
        assert isinstance(caption, (list, tuple, set))
        caption = set(caption)

    for found_caption, item in iter_widget_captions_and_items(
            tree, add_plus_to_new_level=False):

        if found_caption in caption:
            tree.setExpanded(item, True)


class _ObjData(object):
    def __init__(self, obj):
        self.obj = obj


def convert_obj_to_data(obj):
    '''
    This utility should be used when we set some data to qt (i.e.: tree view item, graphics item,
    etc). As if we don't do that we'll convert strings to unicode automatically, or tuples to
    lists, which is usually not what we want.
    '''
    return _ObjData(obj)


def convert_data_to_obj(data):
    return data.obj


def assert_condition_within_timeout(condition, timeout=2.):
    assert is_in_main_thread()
    initial = time.time()
    while True:
        c = condition()
        if isinstance(c, bool):
            if c:
                return
        elif isinstance(c, basestring):
            if not c:
                return
        else:
            raise AssertionError('Expecting bool or string as the return.')

        if time.time() - initial > timeout:
            raise AssertionError(
                u'Could not reach condition before timeout: %s (condition return: %s)' %
                (timeout, c))

        # process_events()
        process_queue()
        time.sleep(1 / 60.)

# ==================================================================================================
# main -- manual testing
# ==================================================================================================
if __name__ == '__main__':
    obtain_qapp()
#     show_message_with_copy_to_clipboard('tuesot', 'usneothuaosnetuho usnatuh ounoth uao')

#     l = QLabel('bar')
#     l.show()
#     l.move(QApplication.desktop().availableGeometry(1).center() - l.rect().center())
#
#     show_message('what do you want')
#

    _ADDITIONAL_EXCEPTION_MSG = '<br/>Report at: <a href="http://google.com">foo</a>'

    def m1():
        raise AssertionError('foo error <a href="foo">foo</a>')
    try:
        m1()
    except:
        show_exception()
