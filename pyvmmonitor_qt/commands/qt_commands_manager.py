'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
from pyvmmonitor_core import implements, interface
from pyvmmonitor_core.commands_manager import ICommandsManager
from pyvmmonitor_core.weak_utils import get_weakref


class IQtCommandsManager(object):

    DEFAULT_SCOPE = ICommandsManager.DEFAULT_SCOPE

    def register_scope(self, scope):
        '''
        A scope is first registered and later it should be set to a widget (so, when the given
        widget is active the related shortcuts should be active).
        :param str scope:
        '''

    def set_scope_widget(self, scope, widget):
        '''
        :param str scope:
        :param QWidget widget:
        '''

    def set_shortcut(self, command_id, shortcut, scope=DEFAULT_SCOPE):
        '''
        :param str command_id:
        :param QKeySequence|str shortcut:
            Either the QKeySequence to be used, a string to be used to create the QKeySequence
            or a MouseShortcut.
        :param str scope:
            The widget scope for the shortcut (if not passed uses default widget scope).
        '''

    def remove_shortcut(self, command_id, shortcut, scope=DEFAULT_SCOPE):
        '''
        :param str command_id:
        :param shortcut:
            Either the QKeySequence to be used, a string to be used to create the QKeySequence
            or a MouseShortcut.
        :param str scope:
            The widget scope for the shortcut (if not passed uses default widget scope).
        '''

    def mouse_shortcut_activated(self, mouse_shortcut, scope=DEFAULT_SCOPE):
        '''
        Users should call to activate some mouse shortcut (which can't be handled by QShortcut).
        :param MouseShortcut mouse_shortcut:
        '''

    def register_command(self, command_id, command_name, icon=None, status_tip=None):
        '''
        Registers a command and makes it available to be activated (if no handler is available
        after being registered, nothing is done if it's activated).

        :param str command_id:
        :param str command_name:
        :param object icon:
            May be the actual icon or a way to identify it (at core it doesn't make
            a difference, it just stores the value to be consumed later on).
        :param str status_tip:
            A tip for the command (if not given, a default one may be given based on the
            command_name).
        '''

    def get_command_info(self, command_id):
        '''
        :param str command_id:
            The command id for which we want the info.

        :return: _CommandInfo
        '''

    def set_command_handler(self, command_id, command_handler, scope=DEFAULT_SCOPE):
        '''
        Sets a handler to the given command id (optionally with a different scope).

        The command_handler must be a callable -- it may accept arguments (which then will need to
        be passed in #activate).

        It's possible to pass None to set no command handler in the context (also see
        remove_command_handler to remove a registered command handler -- in case it's registered
        and then removed).
        '''

    def remove_command_handler(self, command_id, command_handler, scope=DEFAULT_SCOPE):
        '''
        Removes a registered handler if it's the current handler at a given scope (does nothing
        if it's not the current handler).
        '''

    def activate(self, command_id, __scope__=DEFAULT_SCOPE, **kwargs):
        '''
        Activates a given command.

        kwargs are passed on to the handler of the command. Note that only arguments which are
        simple python objects should be passed.

        Namely: int/long/float/complex/str/bytes/bool/tuple/list/set (this restriction is enforced
        so that clients can be sure that they can easily replicate a command invocation).
        '''

    def list_command_ids(self):
        '''
        Returns the available command ids.
        '''


class MouseShortcut(object):

    MOUSE_WHEEL_UP = 'Mouse Wheel Up'
    MOUSE_WHEEL_DOWN = 'Mouse Wheel Down'

    def __init__(self, *parts):
        self._parts = frozenset(parts)

    def __eq__(self, o):
        if isinstance(o, _MouseQShortcut):
            return o._parts == self._parts

        return False

    def toString(self):
        return ', '.join(self._parts)

    def __ne__(self, o):
        return not self == o

    def __hash__(self):
        return hash(self._parts)


CTRL_MOUSE_WHEEL_UP = MouseShortcut('Ctrl', MouseShortcut.MOUSE_WHEEL_UP)
CTRL_MOUSE_WHEEL_DOWN = MouseShortcut('Ctrl', MouseShortcut.MOUSE_WHEEL_DOWN)
CTRL_ALT_MOUSE_WHEEL_UP = MouseShortcut('Ctrl', 'Alt', MouseShortcut.MOUSE_WHEEL_UP)
CTRL_ALT_MOUSE_WHEEL_DOWN = MouseShortcut('Ctrl', 'Alt', MouseShortcut.MOUSE_WHEEL_DOWN)
ALT_MOUSE_WHEEL_UP = MouseShortcut('Alt', MouseShortcut.MOUSE_WHEEL_UP)
ALT_MOUSE_WHEEL_DOWN = MouseShortcut('Alt', MouseShortcut.MOUSE_WHEEL_DOWN)

# Private API from now On.


class _CustomActivatedSlot(object):

    def __init__(self, mouse_qshortcut):
        '''
        :param _MouseQShortcut mouse_qshortcut:
        '''
        from pyvmmonitor_core.callback import Callback
        self.mouse_qshortcut = mouse_qshortcut

        self.on_call = Callback()

    def __call__(self):
        self.on_call()

    def connect(self, func):
        self.on_call.register(func)

    def disconnect(self, func):
        self.on_call.unregister(func)


class _MouseQShortcut(object):

    def __init__(self, mouse_shortcut):
        '''
        :param MouseShortcut mouse_shortcut:
        '''
        self.mouse_shortcut = mouse_shortcut
        self.activated = _CustomActivatedSlot(self)

    def deleteLater(self):
        pass

    def __eq__(self, o):
        if isinstance(o, _MouseQShortcut):
            return o.mouse_shortcut == self.mouse_shortcut

        return False

    def __ne__(self, o):
        return not self == o

    def __hash__(self):
        return hash(self.mouse_shortcut)


class _Shortcut(object):

    __slots__ = ['command_id', 'shortcut', 'scope', 'commands_manager', '__weakref__', '_shortcut_repr']

    def __init__(self, command_id, shortcut, scope, commands_manager):
        self.command_id = command_id
        self.shortcut = shortcut
        self.scope = scope
        self.commands_manager = get_weakref(commands_manager)
        if isinstance(shortcut, str):
            self._shortcut_repr = shortcut
        else:
            self._shortcut_repr = shortcut.toString()

    def __str__(self) -> str:
        return '_Shortcut(%s, %s, %s, %s)' % (self._shortcut_repr, self.command_id, self.scope, self.shortcut)

    def _activated(self):
        commands_manager = self.commands_manager()
        if commands_manager is not None:
            commands_manager.activate(self.command_id, self.scope)

    def __eq__(self, o):
        # Note that the command id is not used for equals!
        if isinstance(o, _Shortcut):
            return (
                self.shortcut == o.shortcut and
                self.scope == o.scope
            )

        return False

    def __ne__(self, o):
        return not self == o

    def __hash__(self):
        return hash((self._shortcut_repr, self.scope))


@interface.check_implements(IQtCommandsManager)
class _DefaultQtCommandsManager(object):

    def __init__(self, widget):
        from pyvmmonitor_core.commands_manager import create_default_commands_manager
        commands_manager = create_default_commands_manager()

        self._commands_manager = commands_manager

        self._qshortcuts = {}
        self._scope_to_widget = {IQtCommandsManager.DEFAULT_SCOPE: get_weakref(widget)}
        self._shortcuts_registered = set()

    def _get_widget_for_scope(self, scope):
        w = self._scope_to_widget.get(scope)
        if w is None:
            return None
        return w()

    @implements(IQtCommandsManager.set_shortcut)
    def set_shortcut(self, command_id, shortcut, scope=IQtCommandsManager.DEFAULT_SCOPE):
        s = _Shortcut(command_id, shortcut, scope, self)
        if s in self._shortcuts_registered:
            prev = self._shortcuts_registered.pop(s)
            self._remove_shortcut(prev)
        self._shortcuts_registered.add(s)
        self._apply_shortcut(s)

    def _apply_shortcut(self, shortcut: _Shortcut):
        w = self._get_widget_for_scope(shortcut.scope)
        if w is not None:
            qshortcut = self._obtain_qshortcut(
                shortcut.shortcut, w, shortcut.scope)
            qshortcut.activated.connect(shortcut._activated)

    def _remove_shortcut(self, shortcut: _Shortcut):
        w = self._get_widget_for_scope(shortcut.scope)
        if w is not None:
            qshortcut = self._obtain_qshortcut(
                shortcut.shortcut, w, shortcut.scope, remove=True)
            if qshortcut is not None:
                # We don't disconnect (because we create a new _Shortcut
                # the reference to remove wouldn't be correct).
                # As we delete it, it shouldn't make a difference.
                # qshortcut.activated.disconnect(shortcut._activated)

                # Note: even doing a deleteLater, we have to setKey(0), otherwise
                # a new key created for the same shortcut doesn't work.
                qshortcut.setKey(0)
                qshortcut.deleteLater()
        self._shortcuts_registered.discard(shortcut)

    @implements(IQtCommandsManager.remove_shortcut)
    def remove_shortcut(self, command_id, shortcut, scope=IQtCommandsManager.DEFAULT_SCOPE):
        s = _Shortcut(command_id, shortcut, scope, self)
        if s in self._shortcuts_registered:
            self._remove_shortcut(s)

    @implements(IQtCommandsManager.activate)
    def activate(self, command_id, __scope__=IQtCommandsManager.DEFAULT_SCOPE, **kwargs):
        self._commands_manager.activate(command_id, __scope__, **kwargs)

    def _obtain_qshortcut(self, shortcut, widget, scope, remove=False):
        '''
        Helper method to get a QShortcut from a shortcut.
        :param str|MouseShortcut shortcut:
        '''
        from pyvmmonitor_qt.qt.QtGui import QKeySequence
        from pyvmmonitor_qt.qt.QtWidgets import QShortcut
        from pyvmmonitor_qt.qt.QtCore import Qt

        assert isinstance(shortcut, (str, QKeySequence, MouseShortcut)), 'Did not expect: %s' % (
            shortcut.__class__,)

        if shortcut.__class__ == MouseShortcut:
            cache_key = (shortcut, scope)
        else:
            key_sequence = QKeySequence(shortcut)
            cache_key = (key_sequence.toString(), scope)

        ret = self._qshortcuts.get(cache_key)
        if ret is not None:
            if remove:
                del self._qshortcuts[cache_key]
            return ret

        if remove:
            return None

        if shortcut.__class__ == MouseShortcut:
            ret = _MouseQShortcut(shortcut)
            self._qshortcuts[cache_key] = ret
            return ret

        qshortcut = QShortcut(key_sequence, widget)
        if scope != IQtCommandsManager.DEFAULT_SCOPE:
            qshortcut.setContext(Qt.WidgetWithChildrenShortcut)
        # qshortcut.setContext(Qt.WidgetShortcut)
        # qshortcut.setContext(Qt.WindowShortcut)
        # qshortcut.setContext(Qt.ApplicationShortcut)
        self._qshortcuts[cache_key] = qshortcut

        return qshortcut

    @implements(IQtCommandsManager.mouse_shortcut_activated)
    def mouse_shortcut_activated(self, mouse_shortcut, scope=ICommandsManager.DEFAULT_SCOPE):
        qshortcut = self._qshortcuts.get((mouse_shortcut, scope))
        if qshortcut is not None and qshortcut.__class__ == _MouseQShortcut:
            qshortcut.activated()

    @implements(IQtCommandsManager.register_scope)
    def register_scope(self, scope):
        self._commands_manager.register_scope(scope)
        self._scope_to_widget[scope] = get_weakref(None)

    @implements(IQtCommandsManager.set_scope_widget)
    def set_scope_widget(self, scope, widget):
        self._scope_to_widget[scope] = get_weakref(widget)
        for shortcut in self._shortcuts_registered:
            if shortcut.scope == scope:
                self._apply_shortcut(shortcut)

    # IQtCommandsManager delegates
    @implements(IQtCommandsManager.register_command)
    def register_command(self, command_id, command_name, icon=None, status_tip=None):
        return self._commands_manager.register_command(
            command_id, command_name, icon=icon, status_tip=status_tip)

    @implements(IQtCommandsManager.get_command_info)
    def get_command_info(self, command_id):
        return self._commands_manager.get_command_info(command_id)

    @implements(IQtCommandsManager.set_command_handler)
    def set_command_handler(
            self, command_id, command_handler, scope=IQtCommandsManager.DEFAULT_SCOPE):
        return self._commands_manager.set_command_handler(command_id, command_handler, scope)

    @implements(IQtCommandsManager.remove_command_handler)
    def remove_command_handler(
            self, command_id, command_handler, scope=IQtCommandsManager.DEFAULT_SCOPE):
        return self._commands_manager.remove_command_handler(command_id, command_handler, scope)

    @implements(IQtCommandsManager.list_command_ids)
    def list_command_ids(self):
        return self._commands_manager.list_command_ids()


def create_default_qt_commands_manager(widget):
    return _DefaultQtCommandsManager(widget)
