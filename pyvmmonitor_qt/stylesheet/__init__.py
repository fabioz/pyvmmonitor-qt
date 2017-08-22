# License: LGPL
#
# Copyright: Brainwy Software
from pyvmmonitor_core.callback import Callback
from pyvmmonitor_core.weak_utils import WeakSet
from pyvmmonitor_qt import compat


_applied_stylesheet = False

THEMES = ['DARK', 'NATIVE', 'DARK_ORANGE']
_USE_THEME = 'DARK'

on_stylesheet_changed = Callback()


def set_default_stylesheet(theme):
    global _USE_THEME
    _USE_THEME = theme.strip().upper()


def get_app_stylesheet():
    if _USE_THEME == 'DARK':
        from pyvmmonitor_qt.stylesheet.dark import AppStylesheet
    elif _USE_THEME == 'DARK_ORANGE':
        from pyvmmonitor_qt.stylesheet.dark import AppStylesheetDarkOrange as AppStylesheet
    else:
        from pyvmmonitor_qt.stylesheet.light import AppStylesheet

    return AppStylesheet()


_is_dark_to_resource_modules = {}
_currently_applied_resource_modules = set()


class _Resource(object):

    def __init__(self, resource_module_name):
        self.resource_module_name = resource_module_name
        self._module = None

    def _load_module(self):
        ret = __import__(self.resource_module_name)
        for part in self.resource_module_name.split('.')[1:]:
            ret = getattr(ret, part)
        return ret

    def load(self):
        if self._module is None:
            self._module = self._load_module()
            return  # Just importing it loads it.
        self._module.qInitResources()

    def unload(self):
        if self._module is None:
            return
        self._module.qCleanupResources()


def register_resource_module(resource_module_name, is_dark):
    _is_dark_to_resource_modules.setdefault(is_dark, set()).add(_Resource(resource_module_name))


register_resource_module('pyvmmonitor_qt.stylesheet.dark_resources', is_dark=True)
register_resource_module('pyvmmonitor_qt.stylesheet.light_resources', is_dark=False)


def _switch_resources_to_style(is_dark):
    if _currently_applied_resource_modules:
        for resource in _currently_applied_resource_modules:
            resource.unload()
        _currently_applied_resource_modules.clear()

    resources_to_apply = _is_dark_to_resource_modules.get(is_dark)
    for resource in resources_to_apply:
        resource.load()
    _currently_applied_resource_modules.update(resources_to_apply)


def apply_default_stylesheet(app, force=False):
    global _applied_stylesheet

    if not _applied_stylesheet or force:
        _applied_stylesheet = True

        if _USE_THEME == 'DARK_ORANGE':
            from pyvmmonitor_qt.stylesheet.dark import STYLESHEET
            # app.setStyle("plastique")
            # app.setStyle("cleanlooks")
            # app.setStyle("motif")
            # app.setStyle("cde")
            is_dark = True
        elif _USE_THEME == 'DARK':
            import qdarkstyle
            # setup stylesheet
            STYLESHEET = qdarkstyle.load_stylesheet()
            is_dark = True
        else:  # Native or error...
            from pyvmmonitor_qt.stylesheet.light import STYLESHEET
            is_dark = False

        app.setStyleSheet(STYLESHEET)

        from pyvmmonitor_qt.qt.QtGui import QPalette
        from pyvmmonitor_qt.qt.QtGui import QIcon

        pal = QPalette(app.palette())
        foreground = get_app_stylesheet().get_foreground()
        pal.setColor(QPalette.Link, foreground)
        pal.setColor(QPalette.LinkVisited, foreground)
        app.setPalette(pal)

        _switch_resources_to_style(is_dark)
        for icon_name, actions in compat.iteritems(_styled_qt_objects):
            for action in actions:
                action.setIcon(QIcon(icon_name))

        on_stylesheet_changed()


def is_light_theme():
    return not _USE_THEME.startswith('DARK')


_styled_qt_objects = {}


def CreateStyledQAction(
        parent,
        icon_name,
        text='',
        shortcut=None,
        status_tip=None,
        connect_to=None):
    '''
    :param icon_name: Name to find icon (i.e.: :appbar.page.edit.svg)
    '''
    from pyvmmonitor_qt.qt.QtGui import QIcon
    from pyvmmonitor_qt.qt.QtWidgets import QAction

    icon = QIcon(icon_name)
    ret = QAction(icon, text, parent)
    _styled_qt_objects.setdefault(icon_name, WeakSet()).add(ret)

    if shortcut is not None:
        ret.setShortcut(shortcut)

    if status_tip is not None:
        ret.setStatusTip(status_tip)

    if connect_to is not None:
        ret.triggered.connect(connect_to)
    return ret


def CreateStyledQPushButton(parent, icon_name, text=''):
    '''
    :param icon_name: Name to find icon (i.e.: :appbar.page.edit.svg)
    '''
    from pyvmmonitor_qt.qt.QtWidgets import QPushButton
    from pyvmmonitor_qt.qt.QtGui import QIcon

    ret = QPushButton(parent)
    ret.setIcon(QIcon(icon_name))
    _styled_qt_objects.setdefault(icon_name, WeakSet()).add(ret)
    return ret
