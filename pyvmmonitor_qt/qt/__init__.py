#------------------------------------------------------------------------------
# Copyright (c) 2010, Enthought Inc
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD license.

#
# Author: Enthought Inc
# Description: Qt API selector. Can be used to switch between pyQt and PySide
#------------------------------------------------------------------------------

import os


def prepare_pyqt4():
    # Set PySide compatible APIs.
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)


qt_api = os.environ.get('QT_API')

root_symbol = None

if qt_api is None:
    try:
        import PySide
        qt_api = 'pyside'
        root_symbol = PySide
    except ImportError:
        try:
            prepare_pyqt4()
            import PyQt4
            root_symbol = PyQt4
            qt_api = 'pyqt'
        except ImportError:
            try:
                import PySide2
                root_symbol = PySide2
                qt_api = 'pyside2'
            except ImportError:
                try:
                    import PyQt5
                    root_symbol = PyQt5
                    qt_api = 'pyqt5'
                except:
                    try:
                        import PySide6
                        root_symbol = PySide6
                        qt_api = 'pyside6'
                    except:
                        raise ImportError('Cannot import PySide, PySide2, PySide6, PyQt4 or PyQt5')

elif qt_api == 'pyqt':
    root_symbol = PyQt4
    prepare_pyqt4()

elif qt_api == 'pyside':
    import PySide
    root_symbol = PySide

elif qt_api == 'pyside2':
    import PySide2
    root_symbol = PySide2

elif qt_api == 'pyside6':
    import PySide6
    root_symbol = PySide6

elif qt_api == 'pyqt5':
    import PyQt5
    root_symbol = PyQt5

else:
    raise RuntimeError("Invalid Qt API %r, valid values are: 'pyqt', 'pyside', 'pyside2', 'pyside6'"
                       % qt_api)

_plugins_loaded = False


def load_plugin_dirs():
    '''
    Helper method to load the available plugins (needed for viewing svgs).
    '''
    global _plugins_loaded
    if _plugins_loaded:
        return

    try:
        from pyvmmonitor_qt.qt.QtWidgets import QApplication
        qApp = QApplication.instance()
        check_paths = []
        for p in root_symbol.__path__:
            plugins_dir = os.path.join(p, "plugins")
            check_paths.append(plugins_dir)

        for plugins_dir in check_paths:
            if os.path.isdir(plugins_dir):
                qApp.addLibraryPath(plugins_dir)
                for d in os.listdir(plugins_dir):
                    if os.path.isdir(os.path.join(plugins_dir, d)):
                        qApp.addLibraryPath(os.path.join(plugins_dir, d))

    finally:
        _plugins_loaded = True
