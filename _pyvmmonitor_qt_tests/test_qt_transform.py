def test_qt_transform_equals():
    from pyvmmonitor_qt.qt.QtGui import QTransform
    qtransform1 = QTransform()
    qtransform2 = QTransform()
    assert qtransform1 == qtransform2
    qtransform1.translate(0, 0)
    assert qtransform1 == qtransform2
    qtransform1.translate(1, 0)
    assert not qtransform1 == qtransform2
    qtransform1.translate(-1, 0)
    assert qtransform1 == qtransform2


def test_qt_transform_tuple():
    from pyvmmonitor_qt.qt.QtGui import QTransform
    from pyvmmonitor_qt.qt_transform import transform_tuple
    qtransform = QTransform()
    qtransform.translate(3, 0)
    assert transform_tuple((2.5, 2), qtransform) == (5.5, 2)


def test_iter_transform_list_tuple():
    from pyvmmonitor_qt.qt.QtGui import QTransform
    qtransform = QTransform()
    qtransform.translate(3, 0)
    from pyvmmonitor_qt.qt_transform import iter_transform_list_tuple
    assert list(iter_transform_list_tuple([(1, 0), (0, 1)], qtransform)) == [(4.0, 0.0), (3.0, 1.0)]
