from pyvmmonitor_qt import qt_event_loop
from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


def test_marching_ants(qtapi):
    from pyvmmonitor_qt.qt.QtGui import QGraphicsView
    view = QGraphicsView()
    view.show()
    from pyvmmonitor_qt.qt.QtGui import QGraphicsScene
    scene = QGraphicsScene(view)
    view.setScene(scene)

    from pyvmmonitor_qt import qt_graphics_items_animation

    animation = qt_graphics_items_animation.GraphicsItemsAnimation(timeout=0)

    from pyvmmonitor_qt.qt.QtGui import QPolygonF
    from pyvmmonitor_qt.qt.QtCore import QPointF
    from pyvmmonitor_qt.qt.QtGui import QGraphicsPolygonItem

    polygon = ((0, 0), (40, 0), (40, 20))
    item1 = QGraphicsPolygonItem(QPolygonF([QPointF(*tup) for tup in polygon]))
    item2 = QGraphicsPolygonItem(QPolygonF([QPointF(*tup) for tup in polygon]))

    scene.addItem(item1)
    scene.addItem(item2)

    assert not animation._timer.isActive()
    handle = animation.marching_ants(item1, item2)
    assert animation._timer.isActive()
    assert item1.pen().dashOffset() == 0.0
    assert item2.pen().dashOffset() == 0.0
    qt_event_loop.process_events()
    assert item1.pen().dashOffset() == 2.0
    assert item2.pen().dashOffset() == 7.0
    ants_handle = handle.handle
    assert ants_handle in animation._marching_ants._marching_ants_handlers
    handle.stop()

    assert ants_handle not in animation._marching_ants._marching_ants_handlers
    assert handle.handle is None
    assert not animation._timer.isActive()
    animation.dispose()

    scene.deleteLater()
    scene = None

    view.deleteLater()
    view = None
