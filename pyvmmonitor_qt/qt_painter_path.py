

def create_painter_path_from_points(points, clockwise=None):
    if clockwise is not None:
        from pyvmmonitor_core import math_utils
        if clockwise != math_utils.is_clockwise(points):
            points = reversed(points)
    from pyvmmonitor_qt.qt.QtGui import QPainterPath
    path = QPainterPath()
    it = iter(points)
    first = next(it)
    path.moveTo(*first)
    for p in it:
        path.lineTo(*p)
    path.lineTo(*first)  # Close
    return path


def create_equilateral_triangle_painter_path(triangle_size):
    from pyvmmonitor_core import math_utils
    from pyvmmonitor_qt.qt.QtGui import QPainterPath

    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(triangle_size, 0)
    path.lineTo(triangle_size / 2, -math_utils.equilateral_triangle_height(triangle_size))
    path.lineTo(0, 0)

    return path
