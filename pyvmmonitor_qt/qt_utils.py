# License: LGPL
#
# Copyright: Brainwy Software

# Note: search on http://qt-project.org/search?search=qmdiarea
# Examples: https://qt.gitorious.org/pyvmmonitor_qt.qt/pyvmmonitor_qt.qt-examples
from __future__ import unicode_literals

from contextlib import contextmanager
from functools import wraps
import sys
import threading
from time import sleep
import time
import traceback
import warnings
import weakref

from pyvmmonitor_core.html import escape_html
from pyvmmonitor_core.thread_utils import is_in_main_thread
from pyvmmonitor_core.weak_utils import get_weakref
from pyvmmonitor_qt import compat
from pyvmmonitor_qt.qt import QtGui, QtCore, qt_api
from pyvmmonitor_qt.qt.QtCore import QTimer, Qt, QModelIndex, QPointF
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
    QTextBrowser, QHBoxLayout, QIcon, QStyle, QFileDialog)


# Modules moved (keep backward compatibility for now).
from .qt_app import obtain_qapp  # @NoMove

from .qt_collect import (  # @NoMove
    GarbageCollector, QtGarbageCollector, start_collect_only_in_ui_thread)  # @NoMove
from .qt_tree_utils import scroll_pos, expanded_nodes_tree  # @NoMove
from .qt_event_loop import process_queue, execute_on_next_event_loop, process_events  # @NoMove
from pyvmmonitor_qt.stylesheet import apply_default_stylesheet  # @NoMove


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
        return [tree.topLevelItem(i) for i in compat.xrange(tree.topLevelItemCount())]
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

        for row in compat.xrange(row_count):
            index = model.index(row, 0, parent_index)
            row_items = []

            for col in cols:
                index_in_col = model.index(row, col, parent_index)
                data = model.data(index_in_col, QtCore.Qt.DisplayRole)
                if data is None:
                    data = ''
                row_items.append(
                    prefix + data)

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
    ret = []
    for x in iter_widget_captions_and_items(
            widget,
            parent_index,
            prefix,
            cols,
            only_show_expanded):
        ret.append(x[0])
    return ret


def count_items(widget):
    i = 0

    for _ in iter_widget_captions_and_items(
            widget,
            parent_index=None,
            prefix='',
            cols=(0,),
            only_show_expanded=False):
        i += 1
    return i

if qt_api == 'pyside':
    try:
        from PySide import shiboken
    except ImportError:
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
    fp = compat.StringIO()

    traceback.print_exc(file=fp)
    # Print to console
    stack_trace = fp.getvalue()

    sys.stderr.write(stack_trace)

    if isinstance(stack_trace, compat.bytes):
        stack_trace = stack_trace.decode(sys.getfilesystemencoding(), 'replace')

    info = sys.exc_info()
    message = escape_html(str(info[1]))
    if _ADDITIONAL_EXCEPTION_MSG:
        message += u'\n\n' + _ADDITIONAL_EXCEPTION_MSG
    show_message(message, stack_trace, parent=get_main_window())


def handle_exception_in_method_return_val(return_val):
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
                if traceback is not None:
                    traceback.print_exc()
                if sys is not None:
                    sys.excepthook(*sys.exc_info())
                return return_val
        return wrapper
    return handle_exception_in_method


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
            if traceback is not None:
                traceback.print_exc()
            if sys is not None:
                sys.excepthook(*sys.exc_info())
        finally:
            args = None
            kwargs = None
    return wrapper


def _except_hook(*args, **kwargs):
    show_exception()


def install_except_hook():
    sys.excepthook = _except_hook


def set_additional_exception_msg(exception_msg):
    global _ADDITIONAL_EXCEPTION_MSG
    if isinstance(exception_msg, compat.bytes):
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
    if isinstance(icon, compat.bytes):
        icon = icon.decode('utf-8', 'replace')

    if isinstance(icon, compat.unicode):
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
        if size:
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

        title = compat.as_unicode(title)
        message = compat.as_unicode(message)
        detailed_message = compat.as_unicode(detailed_message)

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

    if isinstance(icon, (compat.bytes, compat.unicode)):
        from pyvmmonitor_qt.stylesheet import CreateStyledQAction
        default_action = CreateStyledQAction(parent, icon)
    else:
        default_action = QtGui.QAction(parent)
        if icon is not None:
            default_action.setIcon(icon)

    default_action.triggered.connect(toolbutton.showMenu)
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
    if isinstance(caption, (compat.bytes, compat.unicode)):
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
        elif isinstance(c, (compat.bytes, compat.unicode)):
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


def ask_save_filename(parent, caption, initial_dir, files_filter):
    return QFileDialog.getSaveFileName(parent, caption, initial_dir, files_filter)


def set_painter_antialiased(painter, antialias, widget):
    '''
    Besides antialising the QPainter, if we have an OpenGL backend, the OpenGL antialiasing also
    needs to be turned on (so, if the widget can be a QGLWidget, the widget is required).

    In the case that there's no related widget (such as drawing to a QImage), the widget should be
    None (it's not default because it's really important to pass it in the case that there's a
    widget, so, making it required so that each case actually takes it into account).
    '''
    from pyvmmonitor_qt.qt.QtGui import QPainter
    RENDER_HINTS = (QPainter.Antialiasing |
                    QPainter.TextAntialiasing |
                    QPainter.SmoothPixmapTransform |
                    QPainter.HighQualityAntialiasing)
    # painter.setRenderHint(QPainter.NonCosmeticDefaultPen, False)
    use_opengl = hasattr(widget, 'makeCurrent')
    if use_opengl:
        from OpenGL import GL
        widget.makeCurrent()

    if antialias:
        painter.setRenderHints(RENDER_HINTS)
        if use_opengl:
            GL.glEnable(GL.GL_MULTISAMPLE)
            GL.glEnable(GL.GL_LINE_SMOOTH)
    else:
        painter.setRenderHints(RENDER_HINTS, False)
        if use_opengl:
            GL.glDisable(GL.GL_MULTISAMPLE)
            GL.glDisable(GL.GL_LINE_SMOOTH)


def create_painter_path_from_points(points):
    from pyvmmonitor_qt.qt.QtGui import QPainterPath
    path = QPainterPath()
    path.moveTo(*points[0])
    for p in points[1:]:
        path.lineTo(*p)
    path.lineTo(*points[0])  # Close
    return path


@contextmanager
def painter_on(device, antialias, widget=None):
    if device.width() <= 0 or device.height() <= 0:
        sys.stderr.write('Warning: trying to create painter on device with empty size.\n')
    from pyvmmonitor_qt.qt.QtGui import QPainter
    painter = QPainter(device)
    set_painter_antialiased(painter, antialias, widget)
    try:
        yield painter
    finally:
        if painter.isActive():
            painter.end()


def qimage_as_numpy(image):
    '''
    Provide a way to get a QImage as a numpy array.
    '''
    if not isinstance(image, QtGui.QImage):
        raise TypeError("image argument must be a QImage instance")

    shape = image.height(), image.width()
    strides0 = image.bytesPerLine()

    image_format = image.format()
    if image_format == QtGui.QImage.Format_Indexed8:
        dtype = "|u1"
        strides1 = 1
    elif image_format in (
            QtGui.QImage.Format_RGB32,
            QtGui.QImage.Format_ARGB32,
            QtGui.QImage.Format_ARGB32_Premultiplied):
        dtype = "|u4"
        strides1 = 4
    elif image_format == QtGui.QImage.Format_Invalid:
        raise ValueError("qimage_as_numpy got invalid QImage")
    else:
        raise ValueError("qimage_as_numpy can only handle 8- or 32-bit QImages")

    image.__array_interface__ = {
        'shape': shape,
        'typestr': dtype,
        'data': image.bits(),
        'strides': (strides0, strides1),
        'version': 3,
    }

    import numpy
    result = numpy.asarray(image)
    del image.__array_interface__
    return result


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
