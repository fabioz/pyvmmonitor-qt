

class MarchingAnts(object):
    '''
    To use:

    marching_ants = MarchingAnts(scene)
    ants = marching_ants.MarchingAnts(scene)
    handle = ants.animate(((0, 0), (40, 0), (40, 20)))
    ...
    handle.stop()

    ...
    ants.dispose()  # Should be disposed before the scene is disposed.
    '''

    def __init__(self, scene):
        import itertools
        self._next = itertools.count(0).__next__
        self._marching_ants_handlers = set()
        self._scene = scene

        from pyvmmonitor_qt.qt.QtCore import QTimer
        self._timer = QTimer()
        self._disposed = False

        import atexit
        atexit.register(self._check_properly_disposed)

    def _check_properly_disposed(self):
        if not self._disposed:
            import sys
            # It should be disposed before the scene!
            sys.stderr.write('MarchingAnts: not properly disposed before shutdown.\n')
            self.dispose()

    def animate(self, polygon):
        if self._disposed:
            raise RuntimeError('Already disposed.')

        from pyvmmonitor_qt.qt.QtCore import Qt
        from pyvmmonitor_qt.qt.QtGui import QPolygonF
        from pyvmmonitor_qt.qt.QtCore import QPointF
        from pyvmmonitor_qt.qt.QtGui import QGraphicsPolygonItem

        item1 = QGraphicsPolygonItem(QPolygonF([QPointF(*tup) for tup in polygon]))
        item2 = QGraphicsPolygonItem(QPolygonF([QPointF(*tup) for tup in polygon]))

        pen = item1.pen()
        pen.setColor(Qt.white)
        item1.setPen(pen)

        pen = item2.pen()
        pen.setColor(Qt.black)
        item2.setPen(pen)

        self._scene.addItem(item1)
        self._scene.addItem(item2)

        offset = 5
        handler = _MarchingAntsHandler((item1, item2), offset, offset * 4, 1, self)
        timer = self._timer
        self._marching_ants_handlers.add(handler)

        for item in item1, item2:
            pen = item.pen()
            pen.setWidthF(0)
            pen.setCosmetic(True)
            pen.setDashPattern([offset, offset, offset, offset])
            item.setPen(pen)
            timer.timeout.connect(handler._update_marching_ants_offset)
            timer.start(250)
        return handler

    def dispose(self):
        for handler in self._marching_ants_handlers.copy():
            handler.stop()

        self._timer.stop()
        self._timer.deleteLater()
        import atexit
        atexit.unregister(self._check_properly_disposed)
        self._disposed = True


class _MarchingAntsHandler(object):

    def __init__(self, items, offset, max_offset, delta, container):
        from pyvmmonitor_core.weak_utils import WeakList
        from pyvmmonitor_core.weak_utils import get_weakref

        self._items = WeakList(items)
        self._offset = offset
        self._last_offset = 0
        self._max_offset = max_offset
        self._delta = delta
        self._container = get_weakref(container)

    def _update_marching_ants_offset(self):
        items = list(self._items)
        if len(items) == 2:
            self._last_offset += self._delta
            self._last_offset = self._last_offset % self._max_offset

            item1 = items[0]
            pen = item1.pen()
            pen.setDashOffset(self._last_offset)
            item1.setPen(pen)

            item2 = items[1]
            pen = item2.pen()
            pen.setDashOffset((self._last_offset + self._offset) % self._max_offset)
            item2.setPen(pen)

    def stop(self):
        container = self._container()
        if container is not None:
            if self in container._marching_ants_handlers:
                container._marching_ants_handlers.discard(self)
                for item in self._items:
                    container._scene.removeItem(item)

                from pyvmmonitor_core.weak_utils import WeakList
                from pyvmmonitor_core.weak_utils import get_weakref

                self._items = WeakList()
                self._container = get_weakref(None)
