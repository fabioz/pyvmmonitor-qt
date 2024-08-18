from . import qt_api

if qt_api == 'pyqt':
    from PyQt4 import QtSvg

elif qt_api == 'pyside2':
    from PySide2 import QtSvg

elif qt_api == 'pyside6':
    from PySide6 import QtSvg
    from PySide6 import QtSvgWidgets

elif qt_api == 'pyqt5':
    from PyQt5 import QtSvg

else:
    from PySide import QtSvg

# import PySide2.QtSvg
# for c in dir(PySide2.QtSvg):
#     if c.startswith('Q'):
#         print('%s = QtSvg.%s' % (c, c))

try:
    QGraphicsSvgItem = QtSvg.QGraphicsSvgItem
    QSvgWidget = QtSvg.QSvgWidget
except Exception:
    QGraphicsSvgItem = QtSvgWidgets.QGraphicsSvgItem
    QSvgWidget = QtSvgWidgets.QSvgWidget

QSvgGenerator = QtSvg.QSvgGenerator
QSvgRenderer = QtSvg.QSvgRenderer
