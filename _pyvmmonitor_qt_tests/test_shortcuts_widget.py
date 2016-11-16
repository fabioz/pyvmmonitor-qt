import pytest

from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


@pytest.fixture(scope='session')
def session_shortcuts_manager():
    from pyvmmonitor_qt.shortcuts_config_widget import IShortcutsManager

    class ShortcutsManager(IShortcutsManager):

        def __init__(self):
            IShortcutsManager.__init__(self)

        def test_reset(self):
            pass

    return ShortcutsManager()


@pytest.yield_fixture
def shortcuts_manager(session_shortcuts_manager):
    session_shortcuts_manager.test_reset()
    yield session_shortcuts_manager
    session_shortcuts_manager.test_reset()


def test_shortcuts_widget(qtapi, shortcuts_manager):
    '''
    :param IShortcutsManager shortcuts_manager:
    '''
    from pyvmmonitor_qt.shortcuts_config_widget import ShortcutsConfigWidget
    widget = ShortcutsConfigWidget(shortcuts_manager)
    widget.show()
