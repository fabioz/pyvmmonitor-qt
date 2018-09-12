def create_mouse_press_event(button='left'):
    from pyvmmonitor_qt.qt.QtGui import QMouseEvent
    from pyvmmonitor_qt.qt.QtCore import QEvent
    from pyvmmonitor_qt.qt.QtCore import QPointF
    from pyvmmonitor_qt.qt.QtCore import Qt

    if button == 'left':
        button = Qt.LeftButton
    elif button == 'right':
        button = Qt.RightButton
    elif button == 'middle':
        button = Qt.MiddleButton

    return QMouseEvent(
        QEvent.MouseButtonPress, QPointF(0, 0), button, button, Qt.NoModifier)
