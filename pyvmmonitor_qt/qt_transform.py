'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
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


def iter_transform_list_tuple(points, qtransform):
    for point in points:
        yield qtransform.map(*point)


def transform_tuple(point, qtransform):
    return qtransform.map(*point)


def transform_to_raw_tuple(transform):
    return tuple(transform)


def raw_tuple_to_transform(tup):
    return Transform(*tup)


def calc_angle_in_radians_from_qtransform(qtransform):
    from pyvmmonitor_core.math_utils import calc_angle_in_radians

    p0 = qtransform.map(0., 0.)
    p1 = qtransform.map(0., 1.)  # Note: compute based on y, not on x.
    return calc_angle_in_radians(p0, p1)


def calculate_size_for_value_in_px(transform, value_in_px):
    p0 = transform.map(0.0, 0.0)
    p1 = transform.map(1.0, 0.0)

    size = 1.0 / (p1[0] - p0[0])
    size *= value_in_px

    return size
