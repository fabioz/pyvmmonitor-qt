'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
import sys
import weakref

import pytest

from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


@pytest.yield_fixture
def _shortcuts_main_window(qtapi):
    from pyvmmonitor_qt.qt.QtWidgets import QMainWindow
    main_window = QMainWindow()
    try:
        yield weakref.ref(main_window)
    finally:
        main_window.deleteLater()
        main_window = None


def _test_shortcuts_widget(qtapi, _commands_manager):
    '''
    :param ICommandsManager _commands_manager:
    '''
    from pyvmmonitor_qt.commands.shortcuts_config_widget import ShortcutsConfigWidget
    widget = ShortcutsConfigWidget(_commands_manager)
    widget.show()


@pytest.mark.skipif(
    sys.platform != 'win32',
    reason='keyPress not activating accelerator as it should.')
def test_shortcuts_in_app(qtapi, _shortcuts_main_window):
    from pyvmmonitor_qt.commands.qt_commands_manager import create_default_qt_commands_manager
    from pyvmmonitor_qt.commands.qt_commands_manager import DEFAULT_SCHEME
    from pyvmmonitor_qt.qt.QtCore import Qt
    from pyvmmonitor_qt.qt.QtGui import QKeySequence
    from pyvmmonitor_qt.qt_event_loop import process_events
    try:
        main_window = _shortcuts_main_window()
        main_window.show()
        process_events()

        activated = []

        def on_copy():
            activated.append('on_copy')

        qt_commands_manager = create_default_qt_commands_manager(main_window)
        # : :type qt_commands_manager: _DefaultQtShortcutsManager

        qt_commands_manager.register_command('copy', 'Copy')
        qt_commands_manager.set_command_handler('copy', on_copy)

        qt_commands_manager.set_shortcut(DEFAULT_SCHEME, 'copy', QKeySequence('Ctrl+C'))
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)

        assert activated == ['on_copy']
        del activated[:]

        qt_commands_manager.remove_shortcut(DEFAULT_SCHEME, 'copy', 'Ctrl+C')
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)
        assert activated == []

        qt_commands_manager.set_shortcut(DEFAULT_SCHEME, 'copy', 'Ctrl+D')
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_copy']
        del activated[:]

        # Both active (Ctrl+C, Ctrl+D)
        qt_commands_manager.set_shortcut(DEFAULT_SCHEME, 'copy', 'Ctrl+C')
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_copy']
        del activated[:]
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_copy']
        del activated[:]

        qt_commands_manager.remove_shortcut(DEFAULT_SCHEME, 'copy', 'Ctrl+C')
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)
        assert activated == []

        qt_commands_manager.add_shortcuts_scheme('MyScheme')
        qt_commands_manager.set_shortcut('MyScheme', 'copy', 'Ctrl+C')
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)
        assert activated == []
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_copy']
        del activated[:]

        qt_commands_manager.activate_scheme('MyScheme')
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_copy']
        del activated[:]
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        assert activated == []
    finally:
        main_window = None


@pytest.mark.skipif(
    sys.platform != 'win32',
    reason='keyPress not activating accelerator as it should.')
def test_mouse_shortcuts_in_app(qtapi, _shortcuts_main_window):
    from pyvmmonitor_qt.commands.qt_commands_manager import create_default_qt_commands_manager
    from pyvmmonitor_qt.commands.qt_commands_manager import DEFAULT_SCHEME
    from pyvmmonitor_qt.commands.qt_commands_manager import CTRL_MOUSE_WHEEL_DOWN
    from pyvmmonitor_qt.qt.QtCore import Qt
    from pyvmmonitor_qt.qt_event_loop import process_events
    try:
        main_window = _shortcuts_main_window()
        main_window.show()
        process_events()

        activated = []

        def on_zoom_out():
            activated.append('on_zoom_out')

        qt_commands_manager = create_default_qt_commands_manager(main_window)
        # : :type qt_commands_manager: _DefaultQtShortcutsManager

        qt_commands_manager.register_command('zoom_out', 'Zoom Out')
        qt_commands_manager.set_command_handler('zoom_out', on_zoom_out)

        qt_commands_manager.set_shortcut(DEFAULT_SCHEME, 'zoom_out', CTRL_MOUSE_WHEEL_DOWN)
        qt_commands_manager.mouse_shortcut_activated(CTRL_MOUSE_WHEEL_DOWN)
        assert activated == ['on_zoom_out']
        del activated[:]

        qt_commands_manager.set_shortcut(DEFAULT_SCHEME, 'zoom_out', 'Ctrl+D')
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_zoom_out']
        del activated[:]
        qt_commands_manager.mouse_shortcut_activated(CTRL_MOUSE_WHEEL_DOWN)
        assert activated == ['on_zoom_out']
        del activated[:]

        qt_commands_manager.add_shortcuts_scheme('MyScheme')
        qt_commands_manager.activate_scheme('MyScheme')
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        qt_commands_manager.mouse_shortcut_activated(CTRL_MOUSE_WHEEL_DOWN)
        assert activated == []
    finally:
        main_window = None
