from pyvmmonitor_core import interface, implements
from pyvmmonitor_core.commands_manager import ICommandsManager

DEFAULT_SCHEME = 'Default'


class IQtCommandsManager(ICommandsManager):

    DEFAULT_SCHEME = DEFAULT_SCHEME

    def add_shortcuts_scheme(self, scheme_name):
        pass

    def activate_scheme(self, scheme_name):
        pass

    def set_shortcut(self, scheme, command_id, shortcut):
        '''
        :param str scheme:
        :param str command_id:
        :param QKeySequence|str shortcut:
            Either the QKeySequence to be used, a string to be used to create the QKeySequence
            or a MouseShortcut.
        '''

    def remove_shortcut(self, scheme, command_id, shortcut):
        '''
        :param str scheme:
        :param str command_id:
        :param shortcut:
            Either the QKeySequence to be used, a string to be used to create the QKeySequence
            or a MouseShortcut.
        '''

    def mouse_shortcut_activated(self, mouse_shortcut):
        '''
        Users should call to activate some mouse shortcut (which can't be handled by QShortcut).
        :param MouseShortcut mouse_shortcut:
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

    def __eq__(self, o):
        if isinstance(o, _MouseQShortcut):
            return o.mouse_shortcut == self.mouse_shortcut

        return False

    def __ne__(self, o):
        return not self == o

    def __hash__(self):
        return hash(self.mouse_shortcut)


class _CommandInfo(object):

    __slots__ = [
        'command_id',
        'shortcut',
        '__weakref__',
        'on_activated',
        'enabled',
    ]

    def __init__(self, command_id, shortcut, on_activated):
        self.command_id = command_id
        self.shortcut = shortcut
        self.on_activated = on_activated
        self.enabled = False

    def _activated(self):
        if self.enabled:
            self.on_activated(self)

    def enable(self, qshortcut):
        if not self.enabled:
            qshortcut.activated.connect(self._activated)
            self.enabled = True

    def disable(self, qshortcut):
        if qshortcut is not None and self.enabled:
            self.enabled = False
            qshortcut.activated.disconnect(self._activated)


class _Scheme(object):

    def __init__(self, commands_manager, obtain_qshortcut):
        from pyvmmonitor_core.weak_utils import get_weakref

        self._shortcut_cache_key_to_commad_id_to_command_infos = {}
        self._commands_manager = get_weakref(commands_manager)
        self._obtain_qshortcut = obtain_qshortcut

    def set_shortcut(self, command_id, shortcut, enable, widget):
        from pyvmmonitor_qt.qt_utils import QtWeakMethod

        cache_key_qshortcut, qshortcut = self._obtain_qshortcut(shortcut)

        existing = self._shortcut_cache_key_to_commad_id_to_command_infos.get(cache_key_qshortcut)

        if existing is None:
            existing = self._shortcut_cache_key_to_commad_id_to_command_infos[
                cache_key_qshortcut] = {}

        command_info = existing.get(command_id)
        if command_info is None:
            command_info = _CommandInfo(
                command_id, shortcut, QtWeakMethod(self, '_on_activated_command_info'))
            existing[command_id] = command_info

        if enable:
            command_info.enable(qshortcut)

    def remove_shortcut(self, command_id, shortcut, enable, widget):
        cache_key_qshortcut, qshortcut = self._obtain_qshortcut(shortcut)

        existing = self._shortcut_cache_key_to_commad_id_to_command_infos.get(cache_key_qshortcut)
        if existing is None:
            return

        command_info = existing.get(command_id)
        if command_info is not None:
            command_info.disable(qshortcut)

    def deactivate(self):
        from pyvmmonitor_qt import compat
        for command_id_to_command_info in compat.itervalues(
                self._shortcut_cache_key_to_commad_id_to_command_infos):

            for command_info in compat.itervalues(command_id_to_command_info):
                command_info.disable(self._obtain_qshortcut(command_info.shortcut)[1])

    def activate(self, widget):
        from pyvmmonitor_qt import compat
        for command_id_to_command_info in compat.itervalues(
                self._shortcut_cache_key_to_commad_id_to_command_infos):

            for command_info in compat.itervalues(command_id_to_command_info):
                command_info.enable(self._obtain_qshortcut(command_info.shortcut)[1])

    def _on_activated_command_info(self, command_info):
        if command_info.enabled:
            #: :type commands_manager: ICommandsManager
            commands_manager = self._commands_manager()
            commands_manager.activate(command_info.command_id)


@interface.check_implements(IQtCommandsManager)
class _DefaultQtCommandsManager(object):

    def __init__(self, widget, commands_manager=None):
        from pyvmmonitor_core.weak_utils import get_weakref
        if commands_manager is None:
            from pyvmmonitor_core.commands_manager import create_default_commands_manager
            commands_manager = create_default_commands_manager()

        self._widget = get_weakref(widget)
        self._commands_manager = commands_manager
        self._scheme_name_to_scheme = {}
        self._actions = {}

        # Default scheme is always there
        self.add_shortcuts_scheme(DEFAULT_SCHEME)
        self._active_scheme = DEFAULT_SCHEME
        self._qshortcuts = {}

    def _obtain_qshortcut(self, shortcut):
        '''
        Helper method to get a QShortcut from a shortcut.
        :param str shortcut:
        '''
        from pyvmmonitor_qt.qt.QtGui import QKeySequence
        from pyvmmonitor_qt.qt.QtWidgets import QShortcut

        if shortcut.__class__ == MouseShortcut:
            ret = _MouseQShortcut(shortcut)
            cache_key = shortcut
            self._qshortcuts[cache_key] = ret
            return cache_key, ret

        key_sequence = QKeySequence(shortcut)
        cache_key = key_sequence.toString()
        qshortcut = self._qshortcuts.get(cache_key)
        if qshortcut is None:
            widget = self._widget()
            qshortcut = QShortcut(key_sequence, widget)
            self._qshortcuts[cache_key] = qshortcut
        return cache_key, qshortcut

    @implements(IQtCommandsManager.add_shortcuts_scheme)
    def add_shortcuts_scheme(self, scheme_name):
        from pyvmmonitor_qt.qt_utils import QtWeakMethod

        if scheme_name in self._scheme_name_to_scheme:
            raise AssertionError('Scheme: %s already added.' % (scheme_name,))
        self._scheme_name_to_scheme[scheme_name] = _Scheme(
            self, QtWeakMethod(self, '_obtain_qshortcut'))

    @implements(IQtCommandsManager.activate_scheme)
    def activate_scheme(self, scheme_name):
        if scheme_name not in self._scheme_name_to_scheme:
            raise KeyError('Scheme: %s not available.' % (scheme_name,))

        if scheme_name == self._active_scheme:
            return

        curr_scheme = self._scheme_name_to_scheme[self._active_scheme]
        curr_scheme.deactivate()

        self._active_scheme = scheme_name
        curr_scheme = self._scheme_name_to_scheme[self._active_scheme]
        curr_scheme.activate(widget=self._widget())

    @implements(IQtCommandsManager.set_shortcut)
    def set_shortcut(self, scheme, command_id, shortcut):
        self._scheme_name_to_scheme[scheme].set_shortcut(
            command_id, shortcut, enable=scheme == self._active_scheme, widget=self._widget())

    @implements(IQtCommandsManager.remove_shortcut)
    def remove_shortcut(self, scheme, command_id, shortcut):
        self._scheme_name_to_scheme[scheme].remove_shortcut(
            command_id, shortcut, enable=scheme == self._active_scheme, widget=self._widget())

    @implements(IQtCommandsManager.mouse_shortcut_activated)
    def mouse_shortcut_activated(self, mouse_shortcut):
        qshortcut = self._qshortcuts.get(mouse_shortcut)
        if qshortcut is not None and qshortcut.__class__ == _MouseQShortcut:
            qshortcut.activated()

    # ICommandsManager delegates
    @implements(ICommandsManager.register_scope)
    def register_scope(self, scope):
        return self._commands_manager.register_scope(scope)

    @implements(ICommandsManager.activate_scope)
    def activate_scope(self, scope):
        return self._commands_manager.activate_scope(scope)

    @implements(ICommandsManager.deactivate_scope)
    def deactivate_scope(self, scope):
        return self._commands_manager.deactivate_scope(scope)

    @implements(ICommandsManager.register_command)
    def register_command(self, command_id, command_name, icon=None, status_tip=None):
        return self._commands_manager.register_command(
            command_id, command_name, icon=icon, status_tip=status_tip)

    @implements(ICommandsManager.get_command_info)
    def get_command_info(self, command_id):
        return self._commands_manager.get_command_info(command_id)

    @implements(ICommandsManager.set_command_handler)
    def set_command_handler(
            self, command_id, command_handler, scope=ICommandsManager.DEFAULT_SCOPE):
        return self._commands_manager.set_command_handler(command_id, command_handler, scope)

    @implements(ICommandsManager.activate)
    def activate(self, command_id, **kwargs):
        return self._commands_manager.activate(command_id, **kwargs)


def create_default_qt_commands_manager(widget, commands_manager=None):
    return _DefaultQtCommandsManager(widget, commands_manager=commands_manager)
