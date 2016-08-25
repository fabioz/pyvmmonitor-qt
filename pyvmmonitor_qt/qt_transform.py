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
