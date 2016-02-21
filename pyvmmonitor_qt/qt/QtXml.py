from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtXml import *

else:
    from PySide.QtXml import *
