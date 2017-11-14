'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
from __future__ import unicode_literals

import sys
import threading
import time
import traceback
import weakref
from contextlib import contextmanager
from functools import wraps

from pyvmmonitor_core import overrides
from pyvmmonitor_core.log_utils import get_logger
from pyvmmonitor_core.thread_utils import is_in_main_thread
from pyvmmonitor_core.weak_utils import get_weakref
from pyvmmonitor_qt import compat
from pyvmmonitor_qt.qt import QtCore, qt_api
from pyvmmonitor_qt.qt.QtCore import QModelIndex, Qt, QTimer
from pyvmmonitor_qt.qt.QtWidgets import QDialog

logger = get_logger(__name__)

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
                        from pyvmmonitor_qt.qt_event_loop import execute_on_next_event_loop
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
                    except Exception:
                        pass
                    return  # Restart it!

            timer = QTimer()
            timer_alive = _TimerAlive(func, timer)
            _timers_alive[func] = timer_alive

            timer.setSingleShot(True)
            timer.timeout.connect(timer_alive)
            timer.start(millis)

    if not is_in_main_thread():
        from pyvmmonitor_qt.qt_event_loop import execute_on_next_event_loop
        execute_on_next_event_loop(register_timer)
    else:
        register_timer()


class QtWeakMethod(object):

    def __init__(self, qobject, method_name):
        assert is_qobject_alive(qobject)
        assert hasattr(qobject, method_name)

        self.qobject = get_weakref(qobject)
        self.method_name = method_name

    def __call__(self, *args, **kwargs):
        obj = self.qobject()
        if obj is None or not is_qobject_alive(obj):
            return
        return getattr(obj, self.method_name)(*args, **kwargs)

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
    from pyvmmonitor_qt.qt.QtWidgets import QMdiArea
    from pyvmmonitor_qt.qt.QtWidgets import QTabWidget
    from pyvmmonitor_qt.qt.QtWidgets import QAbstractItemView

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

elif qt_api == 'pyside2':
    try:
        from PySide2 import shiboken2
    except ImportError:
        import shiboken2

    def is_qobject_alive(obj):
        return shiboken2.isValid(obj)

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


def show_exception(*exc_info):
    '''
    Meant to be used when showing an exception.

    i.e.:

    try:
        foo()
    except:
        show_exception()
    '''
    fp = compat.StringIO()

    try:
        if not exc_info:
            exc_info = sys.exc_info()

        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=fp)

        # Print to console
        stack_trace = fp.getvalue()

        sys.stderr.write(stack_trace)

        if isinstance(stack_trace, compat.bytes):
            stack_trace = stack_trace.decode(sys.getfilesystemencoding(), 'replace')

        from pyvmmonitor_core.html import escape_html
        message = escape_html(str(exc_info[1]))
    finally:
        # After reporting it, clear the traceback so that we don't hold
        # frames alive longer than needed (when tests failed, having this
        # meant that we could crash at exit time because we kept frames alive
        # longer than needed).
        exc_info[1].__traceback__ = None
        # Make sure we don't hold a reference to it.
        exc_info = None

    if _ADDITIONAL_EXCEPTION_MSG:
        message += u'\n\n' + _ADDITIONAL_EXCEPTION_MSG

    logger.error(message)
    logger.error(stack_trace)

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
            except Exception:
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
        except Exception:
            if traceback is not None:
                traceback.print_exc()
            if sys is not None:
                sys.excepthook(*sys.exc_info())
        finally:
            args = None
            kwargs = None

    return wrapper


def _except_hook(*exc_info):
    show_exception(*exc_info)


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
        icon=None):
    '''
    :param icon:
        QMessageBox.NoIcon
        QMessageBox.Question
        QMessageBox.Information
        QMessageBox.Warning
        QMessageBox.Critical
    '''
    from pyvmmonitor_qt.qt.QtWidgets import QMessageBox
    if icon is None:
        icon = QMessageBox.Critical
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
            logger.warn('Invalid icon: %s' % (icon,))
            icon = QMessageBox.NoIcon

    if not is_in_main_thread():

        # Important: if we're not in the main thread, we have to schedule to run it later
        # (in the UI thread).
        def func():
            show_message(message, detailed_message, title, parent, icon)

        from pyvmmonitor_qt.qt_event_loop import execute_on_next_event_loop
        execute_on_next_event_loop(func)
        return

    if parent is None:
        parent = get_main_window()

    from pyvmmonitor_qt.qt_app import obtain_qapp
    get_icon = obtain_qapp().style().standardIcon

    from pyvmmonitor_qt.qt.QtWidgets import QStyle
    if icon == QMessageBox.Information:
        icon = get_icon(QStyle.SP_MessageBoxInformation)
    elif icon == QMessageBox.Critical:
        icon = get_icon(QStyle.SP_MessageBoxCritical)
    elif icon == QMessageBox.Warning:
        icon = get_icon(QStyle.SP_MessageBoxWarning)
    elif icon == QMessageBox.Question:
        icon = get_icon(QStyle.SP_MessageBoxQuestion)
    else:
        from pyvmmonitor_qt.qt.QtGui import QIcon
        icon = QIcon()

    return __show_dialog_and_exec(parent, title, message, detailed_message, icon)


def __show_dialog_and_exec(parent, title, message, detailed_message, icon):
    # Internal API: Just available to be mocked in tests!
    message_box = _ResizeMessageBox(parent, title, message, detailed_message, icon)

    return message_box.exec_()


def add_expanding_spacer_to_layout(layout, row=None, col=None, direction='both'):
    from pyvmmonitor_qt.qt.QtWidgets import QSpacerItem
    from pyvmmonitor_qt.qt.QtWidgets import QSizePolicy
    if direction == 'both':
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
    elif direction == 'vertical':
        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

    elif direction == 'horizontal':
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
    else:
        raise AssertionError('Unexpected direction: %s' % (direction,))

    if row is None and col is None:
        layout.addItem(spacer)
    else:
        layout.addItem(spacer, row, col)
    return spacer


class CustomMessageDialog(QDialog):

    def __init__(self, parent, create_contents=None, title=' ', size=(640, 540), flags=None):
        from pyvmmonitor_qt.qt_widget_builder import WidgetBuilder
        if flags is not None:
            QDialog.__init__(self, parent, flags)
        else:
            QDialog.__init__(self, parent)

        self.setWindowTitle(title)

        from pyvmmonitor_qt.qt.QtWidgets import QVBoxLayout
        self._layout = QVBoxLayout()
        self._widget_builder = WidgetBuilder(self, self._layout)
        if create_contents:
            create_contents(self)
        else:
            self._create_contents()
        self.setLayout(self._layout)
        if size:
            self.resize(*size)

    def get_layout(self):
        return self._layout

    def get_widget_builder(self):
        return self._widget_builder

    def _create_contents(self):
        pass

    def create_label(self, txt='', layout=None):
        return self._widget_builder.create_label(txt=txt, layout=layout)

    def create_text_browser(self, txt='', open_links=False):
        return self._widget_builder.create_text_browser(txt=txt, open_links=open_links)

    def create_text(self, txt='', read_only=False, line_wrap=True, is_html=True, font=None):
        return self._widget_builder.create_text(
            txt=txt, read_only=read_only, line_wrap=line_wrap, is_html=is_html, font=font)

    def create_spacer(self):
        return self._widget_builder.create_spacer()

    def create_buttons(self, show_ok=True, show_cancel=True):
        bbox = self.bbox = self._widget_builder.create_buttons(
            show_ok=show_ok, show_cancel=show_cancel)

        bbox.rejected.connect(self.reject)
        bbox.accepted.connect(self.accept)
        return bbox

    def create_close_button(self):
        bbox = self.bbox = self._widget_builder.create_close_button()

        bbox.rejected.connect(self.reject)
        return bbox


class _ResizeMessageBox(CustomMessageDialog):

    def __init__(self, parent, title, message, detailed_message, icon):
        from pyvmmonitor_qt.qt.QtGui import QCursor
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

        from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
        from pyvmmonitor_qt.qt.QtWidgets import QLabel

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

        from pyvmmonitor_qt.qt.QtWidgets import QDialogButtonBox
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
        from pyvmmonitor_qt.qt.QtWidgets import QApplication
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
    from pyvmmonitor_qt.qt.QtWidgets import QToolBar
    from pyvmmonitor_qt.qt.QtWidgets import QWidget
    from pyvmmonitor_qt.qt.QtWidgets import QSizePolicy

    toolbar = QToolBar(parent)
    spacer = QWidget(toolbar)
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    toolbar.addWidget(spacer)
    return toolbar


class MenuCreator(object):
    '''Helper class to create menus.'''

    def __init__(self, parent=None, parent_menu=None, caption=None):
        from pyvmmonitor_qt.qt.QtWidgets import QMenu
        self.parent = parent
        self.menu = QMenu(parent)
        if parent_menu is not None:
            parent_menu.addMenu(self.menu)

        if caption is not None:
            self.menu.setTitle(caption)

    def add_qaction(self, qaction):
        self.menu.addAction(qaction)
        return qaction

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
    from pyvmmonitor_qt.qt.QtWidgets import QToolButton

    from pyvmmonitor_qt.qt.QtWidgets import QAction

    toolbutton = QToolButton(parent)
    toolbutton.setPopupMode(QToolButton.MenuButtonPopup)

    if isinstance(icon, (compat.bytes, compat.unicode)):
        from pyvmmonitor_qt.stylesheet import CreateStyledQAction
        default_action = CreateStyledQAction(parent, icon)
    else:
        default_action = QAction(parent)
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

    from pyvmmonitor_qt.qt.QtCore import QItemSelectionModel
    from pyvmmonitor_qt.qt.QtCore import QItemSelection

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

    from pyvmmonitor_qt.qt.QtWidgets import QApplication

    def copy():
        QApplication.clipboard().setText(msg)
        dialog.bt_copy.setText('Copied to clipboard')

    def create_contents(dialog):
        dialog.create_text(msg, read_only=read_only, line_wrap=False, is_html=False, font=font)
        from pyvmmonitor_qt.qt.QtWidgets import QDialogButtonBox
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
        presses Cancel/Close or stop_condition returns True.

        :param stop_condition: callable()->bool
            If it returns True we'll consider that the process stopped and close the dialog.
        '''
        self._close_on_finish = close_on_finish
        if flags is None:
            flags = Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        if parent is None:
            parent = get_main_window()
        CustomMessageDialog.__init__(
            self, parent, title=title, size=size, flags=flags)
        if stop_condition is None:

            def stop_condition(): return False

        self.stop_condition = stop_condition
        if not cmd:
            cmd = []
        self.cmd = cmd
        self.env = env
        self._popen = None
        self.stopped = False

    def set_cmd(self, cmd):
        self.cmd = cmd

    @overrides(CustomMessageDialog.timerEvent)
    def timerEvent(self, ev):
        from pyvmmonitor_qt.qt.QtGui import QTextCursor

        p = self._popen
        if p is None:
            self._set_finished()
            return

        edit = self._edit
        output = p.get_output()
        if output:
            edit.moveCursor(QTextCursor.End)
            edit.insertPlainText(output)
            edit.moveCursor(QTextCursor.End)

        if p.finished or self.stop_condition():
            self._set_finished()

    def _set_finished(self):
        self.bt_cancel.setText('Close (Finished)')
        if self._close_on_finish or self.stop_condition():
            self.reject()

    @handle_exception_in_method
    def exec_(self):
        from pyvmmonitor_core import exec_external
        p = self._popen = exec_external.ExecExternal(self.cmd, env=self.env)
        threading.Thread(target=p.call).start()

        timer_id = self.startTimer(1. / 30.)
        try:
            return super(LaunchExecutableDialog, self).exec_()
        finally:
            try:
                if not p.finished:
                    p.cancel()
            finally:
                self.killTimer(timer_id)
                self._popen = None

    def get_text(self):
        return self._edit.toPlainText()

    def _create_contents(self):
        from pyvmmonitor_qt.qt.QtWidgets import QDialogButtonBox

        self.create_label('Process output')
        self._edit = self.create_text(read_only=True, line_wrap=True, is_html=False)

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

    '''
    :param callable condition:
        A callable which may return a bool or a string (if True or an empty
        string, the condition is considered matched).

    :param float timeout:
        Timeout in seconds
    '''
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

        # from pyvmmonitor_qt.qt_event_loop import process_events
        # process_events()

        from pyvmmonitor_qt.qt_event_loop import process_queue
        process_queue()
        time.sleep(1 / 50.)


def ask_save_filename(parent, caption, initial_dir, files_filter, selected_filter=None):
    # Kept for backward compatibilyt
    from pyvmmonitor_qt import qt_ask
    return qt_ask.ask_save_filename(parent, caption, initial_dir, files_filter, selected_filter)


def _is_opengl_available():
    try:
        return _is_opengl_available.__cached__
    except AttributeError:
        try:
            from OpenGL import GL
            _is_opengl_available.__cached__ = True
        except ImportError:
            _is_opengl_available.__cached__ = False

        return _is_opengl_available.__cached__


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
    use_opengl = hasattr(widget, 'makeCurrent') and _is_opengl_available()

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


def create_painter_path_from_points(points, clockwise=None):
    from pyvmmonitor_qt import qt_painter_path
    return qt_painter_path.create_painter_path_from_points(points, clockwise)


def create_qpolygon_from_points(points, clockwise=None):
    from pyvmmonitor_qt.qt.QtGui import QPolygonF
    from pyvmmonitor_qt.qt.QtCore import QPointF

    if clockwise is not None:
        from pyvmmonitor_core import math_utils
        if clockwise != math_utils.is_clockwise(points):
            points = reversed(points)
    return QPolygonF([QPointF(*point) for point in points])


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


@contextmanager
def qimage_as_numpy(image):

    '''
    Provide a way to get a QImage as a numpy array.

    Used as a context manager because if the qimage dies the numpy array is invalid.

    i.e.:

    with qimage_as_numpy(image) as numpy_array:
        ...
    '''
    from pyvmmonitor_qt.qt.QtGui import QImage
    if not isinstance(image, QImage):
        raise TypeError("image argument must be a QImage instance")

    shape = image.height(), image.width()
    strides0 = image.bytesPerLine()

    image_format = image.format()
    if image_format == QImage.Format_Indexed8:
        dtype = "|u1"
        strides1 = 1
    elif image_format in (
            QImage.Format_RGB32,
            QImage.Format_ARGB32,
            QImage.Format_ARGB32_Premultiplied):
        dtype = "|u4"
        strides1 = 4
    elif image_format == QImage.Format_Invalid:
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
    yield result


def set_background_color(widget, qcolor):

    '''
    :param QWidget widget:
    :param QColor qcolor:
    '''
    from pyvmmonitor_qt.qt.QtGui import QPalette
    pal = widget.palette()

    pal.setColor(QPalette.Background, qcolor)
    widget.setPalette(pal)


def set_foreground_color(widget, qcolor):

    '''
    :param QWidget widget:
    :param QColor qcolor:
    '''
    from pyvmmonitor_qt.qt.QtGui import QPalette
    pal = widget.palette()

    pal.setColor(QPalette.Foreground, qcolor)
    widget.setPalette(pal)

# # ======================================================================
# # main -- manual testing
# # ======================================================================
# if __name__ == '__main__':
#     from pyvmmonitor_qt.qt_app import obtain_qapp
#     obtain_qapp()
# #     show_message_with_copy_to_clipboard('tuesot', 'usneothuaosnetuho usnatuh ounoth uao')
#
# #     l = QLabel('bar')
# #     l.show()
# #     l.move(QApplication.desktop().availableGeometry(1).center() - l.rect().center())
# #
# #     show_message('what do you want')
# #
#
#     _ADDITIONAL_EXCEPTION_MSG = '<br/>Report at: <a href="http://google.com">foo</a>'
#
#     def m1():
#         raise AssertionError('foo error <a href="foo">foo</a>')
#     try:
#         m1()
#     except:
#         show_exception()
