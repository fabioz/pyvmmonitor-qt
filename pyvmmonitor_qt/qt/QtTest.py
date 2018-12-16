from . import qt_api

if qt_api == 'pyqt':
    from PyQt4 import QtTest

elif qt_api == 'pyside2':
    from PySide2 import QtTest

elif qt_api == 'pyqt5':
    from PyQt5 import QtTest

else:
    from PySide import QtTest

QTest = QtTest.QTest
