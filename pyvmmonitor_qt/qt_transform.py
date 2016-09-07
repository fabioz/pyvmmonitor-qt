from collections import namedtuple
Transform = namedtuple('Transform', 'm11 m12 m13 m21 m22 m23 m31 m32 m33')


def copy_qtransform(transform):
    from pyvmmonitor_qt.qt.QtGui import QTransform
    return QTransform(
        transform.m11(),
        transform.m12(),
        transform.m13(),

        transform.m21(),
        transform.m22(),
        transform.m23(),

        transform.m31(),
        transform.m32(),
        transform.m33()
    )


def qtransform_to_tuple(transform):
    return Transform(
        transform.m11(),
        transform.m12(),
        transform.m13(),

        transform.m21(),
        transform.m22(),
        transform.m23(),

        transform.m31(),
        transform.m32(),
        transform.m33()
    )


def tuple_to_qtransform(tup):
    from pyvmmonitor_qt.qt.QtGui import QTransform
    return QTransform(*tup)


def transform_tuple(point, qtransform):
    from pyvmmonitor_qt.qt.QtCore import QPointF

    p = qtransform.map(QPointF(*point))
    return p.x(), p.y()


def calc_angle_in_radians_from_qtransform(qtransform):
    from pyvmmonitor_qt.qt.QtCore import QPointF
    from pyvmmonitor_core.math_utils import calc_angle_in_radians

    p0 = qtransform.map(QPointF(0, 0))
    p1 = qtransform.map(QPointF(0, 1))  # Note: compute based on y, not on x.
    return calc_angle_in_radians((p0.x(), p0.y()), (p1.x(), p1.y()))


def calculate_size_for_value_in_px(transform, value_in_px):
    p0 = transform.map(0.0, 0.0)
    p1 = transform.map(1.0, 0.0)

    size = 1.0 / (p1[0] - p0[0])
    size *= value_in_px

    return size
