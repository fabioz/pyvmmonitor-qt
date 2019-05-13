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
    from pyvmmonitor_qt.qt_widget_builder import WidgetBuilder
    main_window = QMainWindow()
    try:

        widget_builder = WidgetBuilder()
        widget_builder.create_widget(parent=main_window)
        main_window.label1 = widget_builder.create_label('label 1')
        main_window.line_edit1 = widget_builder.create_line_edit()
        main_window.label1 = widget_builder.create_label('label 2')
        main_window.line_edit2 = widget_builder.create_line_edit()

        main_window.setCentralWidget(widget_builder.widget)

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
def test_widget_scopes(qtapi, _shortcuts_main_window):
    '''

    '''
    from pyvmmonitor_qt.commands.qt_commands_manager import create_default_qt_commands_manager
    from pyvmmonitor_qt.qt.QtCore import Qt
    from pyvmmonitor_qt.qt.QtGui import QKeySequence
    from pyvmmonitor_qt.qt_event_loop import process_events
    from pyvmmonitor_qt.qt_utils import assert_focus_within_timeout
    try:
        main_window = _shortcuts_main_window()
        main_window.show()

        process_events()

        activated = []

        def on_g():
            activated.append('on_g')

        def on_d():
            activated.append('on_d')

        def on_b():
            activated.append('on_b')

        qt_commands_manager = create_default_qt_commands_manager(main_window)
        qt_commands_manager.register_scope('line_edit1')
        qt_commands_manager.register_scope('line_edit2')
        # : :type qt_commands_manager: _DefaultQtShortcutsManager

        qt_commands_manager.register_command('cmd_g', 'CMD_G')
        qt_commands_manager.set_command_handler('cmd_g', on_g)
        qt_commands_manager.set_shortcut('cmd_g', QKeySequence('Ctrl+G'))

        qt_commands_manager.register_command('cmd_d', 'CMD_D')
        qt_commands_manager.set_command_handler('cmd_d', on_d, 'line_edit1')
        qt_commands_manager.set_shortcut('cmd_d', QKeySequence('Ctrl+D'), scope='line_edit1')

        qt_commands_manager.register_command('cmd_b', 'CMD_B')
        qt_commands_manager.set_command_handler('cmd_b', on_b, 'line_edit2')
        qt_commands_manager.set_shortcut('cmd_b', QKeySequence('Ctrl+B'), scope='line_edit2')

        qt_commands_manager.set_scope_widget('line_edit2', main_window.line_edit2)
        qt_commands_manager.set_scope_widget('line_edit1', main_window.line_edit1)

        qtapi.keyPress(main_window, 'G', Qt.KeyboardModifier.ControlModifier)
        qtapi.keyPress(main_window.line_edit1, 'G', Qt.KeyboardModifier.ControlModifier)
        qtapi.keyPress(main_window.line_edit2, 'G', Qt.KeyboardModifier.ControlModifier)

        assert activated == ['on_g', 'on_g', 'on_g']
        del activated[:]

        qtapi.keyPress(main_window, 'B', Qt.KeyboardModifier.ControlModifier)
        assert activated == []
        assert_focus_within_timeout(main_window.line_edit1)
        qtapi.keyPress(main_window.line_edit1, 'B', Qt.KeyboardModifier.ControlModifier)
        assert activated == []
        assert_focus_within_timeout(main_window.line_edit2)
        qtapi.keyPress(main_window.line_edit2, 'B', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_b']
        del activated[:]

        qtapi.keyPress(main_window, 'D', Qt.KeyboardModifier.ControlModifier)
        assert activated == []
        assert_focus_within_timeout(main_window.line_edit1)
        qtapi.keyPress(main_window.line_edit1, 'D', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_d']
        assert_focus_within_timeout(main_window.line_edit2)
        qtapi.keyPress(main_window.line_edit2, 'D', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_d']
        del activated[:]

    finally:
        main_window = None


@pytest.mark.skipif(
    sys.platform != 'win32',
    reason='keyPress not activating accelerator as it should.')
def test_shortcuts_in_app(qtapi, _shortcuts_main_window):
    from pyvmmonitor_qt.commands.qt_commands_manager import create_default_qt_commands_manager
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

        qt_commands_manager.set_shortcut('copy', QKeySequence('Ctrl+C'))
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)

        assert activated == ['on_copy']
        del activated[:]

        qt_commands_manager.remove_shortcut('copy', 'Ctrl+C')
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)
        assert activated == []

        qt_commands_manager.set_shortcut('copy', 'Ctrl+D')
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_copy']
        del activated[:]

        # Both active (Ctrl+C, Ctrl+D)
        qt_commands_manager.set_shortcut('copy', 'Ctrl+C')
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_copy']
        del activated[:]
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_copy']
        del activated[:]

        qt_commands_manager.remove_shortcut('copy', 'Ctrl+C')
        qtapi.keyPress(main_window, 'c', Qt.KeyboardModifier.ControlModifier)
        assert activated == []
    finally:
        main_window = None


@pytest.mark.skipif(
    sys.platform != 'win32',
    reason='keyPress not activating accelerator as it should.')
def test_mouse_shortcuts_in_app(qtapi, _shortcuts_main_window):
    from pyvmmonitor_qt.commands.qt_commands_manager import create_default_qt_commands_manager
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

        qt_commands_manager.set_shortcut('zoom_out', CTRL_MOUSE_WHEEL_DOWN)
        qt_commands_manager.mouse_shortcut_activated(CTRL_MOUSE_WHEEL_DOWN)
        assert activated == ['on_zoom_out']
        del activated[:]

        qt_commands_manager.set_shortcut('zoom_out', 'Ctrl+D')
        qtapi.keyPress(main_window, 'd', Qt.KeyboardModifier.ControlModifier)
        assert activated == ['on_zoom_out']
        del activated[:]
        qt_commands_manager.mouse_shortcut_activated(CTRL_MOUSE_WHEEL_DOWN)
        assert activated == ['on_zoom_out']
        del activated[:]
    finally:
        main_window = None
