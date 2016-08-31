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
