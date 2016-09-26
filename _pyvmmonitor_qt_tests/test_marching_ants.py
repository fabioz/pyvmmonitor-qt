from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport


def test_marching_ants(qtapi):
    from pyvmmonitor_qt.qt.QtGui import QGraphicsView
    view = QGraphicsView()
    view.show()
    from pyvmmonitor_qt.qt.QtGui import QGraphicsScene
    scene = QGraphicsScene(view)
    view.setScene(scene)

    from pyvmmonitor_qt import marching_ants

    ants = marching_ants.MarchingAnts(scene)
    handle = ants.animate(((0, 0), (40, 0), (40, 20)))
    assert handle in ants._marching_ants_handlers
    handle.stop()
    assert handle not in ants._marching_ants_handlers
    ants.dispose()

    scene.deleteLater()
    scene = None

    view.deleteLater()
    view = None
