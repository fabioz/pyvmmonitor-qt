from . import qt_api

if qt_api == 'pyqt':
    from PyQt4 import QtOpenGL
    QGLFormat = QtOpenGL.QGLFormat
    QGLWidget = QtOpenGL.QGLWidget
    QGL = QtOpenGL.QGL

elif qt_api == 'pyside2':

    def create_gl_widget():
        # QGLWidget Not currently available in pyside2.
        # It has actually been deprecated and we should use
        # QtGui.QGLFormat and other related classes instead.
        from PySide2.QtWidgets import QOpenGLWidget
        from PySide2.QtGui import QSurfaceFormat
        from PySide2 import QtOpenGL
        QGLFormat = QtOpenGL.QGLFormat
        QGL = QtOpenGL.QGL
        open_gl_widget = QOpenGLWidget()
        fmt = QSurfaceFormat.defaultFormat()
        fmt.setSamples(8)
        open_gl_widget.setFormat(fmt)
        return open_gl_widget

    def is_good_opengl_version():
        from PySide2.QtGui import QSurfaceFormat
        default_format = QSurfaceFormat.defaultFormat()
        return default_format.majorVersion() >= 2

elif qt_api == 'pyqt5':

    def create_gl_widget():
        # QGLWidget Not currently available in pyside2.
        # It has actually been deprecated and we should use
        # QtGui.QGLFormat and other related classes instead.
        from PyQt5.QtWidgets import QOpenGLWidget
        from PyQt5.QtGui import QSurfaceFormat
        from PyQt5 import QtOpenGL
        QGLFormat = QtOpenGL.QGLFormat
        QGL = QtOpenGL.QGL
        open_gl_widget = QOpenGLWidget()
        fmt = QSurfaceFormat.defaultFormat()
        fmt.setSamples(8)
        open_gl_widget.setFormat(fmt)
        return open_gl_widget

    def is_good_opengl_version():
        from PyQt5.QtGui import QSurfaceFormat
        default_format = QSurfaceFormat.defaultFormat()
        return default_format.majorVersion() >= 2

else:
    from PySide import QtOpenGL
    QGLFormat = QtOpenGL.QGLFormat
    QGLWidget = QtOpenGL.QGLWidget
    QGL = QtOpenGL.QGL

    def create_gl_widget():
        from PySide.QtOpenGL import QGLWidget
        from PySide.QtOpenGL import QGL
        from PySide.QtOpenGL import QGLFormat
        return QGLWidget(QGLFormat(QGL.SampleBuffers))

    def is_good_opengl_version():
        from PySide.QtOpenGL import QGLFormat
        return QGLFormat.openGLVersionFlags() & QGLFormat.OpenGL_Version_2_0
