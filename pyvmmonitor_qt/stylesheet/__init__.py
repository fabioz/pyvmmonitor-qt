# License: LGPL
#
# Copyright: Brainwy Software
from pyvmmonitor_core.callback import Callback
from pyvmmonitor_qt.qt.QtGui import QPalette

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


def apply_default_stylesheet(app, force=False):
    global _applied_stylesheet

    if not _applied_stylesheet or force:
        _applied_stylesheet = True

        if _USE_THEME == 'DARK_ORANGE':
            from pyvmmonitor_qt.stylesheet.dark import STYLESHEET
            from pyvmmonitor_qt.stylesheet import dark_resources  # @UnusedImport
            # app.setStyle("plastique")
            # app.setStyle("cleanlooks")
            # app.setStyle("motif")
            # app.setStyle("cde")
        elif _USE_THEME == 'DARK':
            import qdarkstyle
            from pyvmmonitor_qt.stylesheet import dark_resources  # @UnusedImport @Reimport
            # setup stylesheet
            STYLESHEET = qdarkstyle.load_stylesheet()
        else:  # Native or error...
            from pyvmmonitor_qt.stylesheet.light import STYLESHEET
            from pyvmmonitor_qt.stylesheet import light_resources  # @UnusedImport

        app.setStyleSheet(STYLESHEET)

        pal = QPalette(app.palette())
        foreground = get_app_stylesheet().get_foreground()
        pal.setColor(QPalette.Link, foreground)
        pal.setColor(QPalette.LinkVisited, foreground)
        app.setPalette(pal)
        on_stylesheet_changed()


def is_light_theme():
    return not _USE_THEME.startswith('DARK')
