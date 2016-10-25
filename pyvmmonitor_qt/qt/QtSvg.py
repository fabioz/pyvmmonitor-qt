from . import qt_api

if qt_api == 'pyqt':
    from PyQt4 import QtSvg

elif qt_api == 'pyside2':
    from PySide2 import QtSvg

else:
    from PySide import QtSvg

# import PySide2.QtSvg
# for c in dir(PySide2.QtSvg):
#     if c.startswith('Q'):
#         print('%s = QtSvg.%s' % (c, c))

QGraphicsSvgItem = QtSvg.QGraphicsSvgItem
QSvgGenerator = QtSvg.QSvgGenerator
QSvgRenderer = QtSvg.QSvgRenderer
QSvgWidget = QtSvg.QSvgWidget
