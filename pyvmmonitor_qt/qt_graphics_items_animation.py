from pyvmmonitor_core import overrides
from pyvmmonitor_core.disposable import Disposable


class _MarchingAnts(Disposable):

    def __init__(self, timer):
        super().__init__()
        self._marching_ants_handlers = set()
        self._timer = timer

    def _items(self, item1, item2):
        if self.is_disposed():
            raise RuntimeError('Already disposed.')

        from pyvmmonitor_qt.qt.QtCore import Qt

        pen = item1.pen()
        pen.setColor(Qt.white)
        item1.setPen(pen)

        pen = item2.pen()
        pen.setColor(Qt.black)
        item2.setPen(pen)

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

        return handler

    @overrides(Disposable._on_dispose)
    def _on_dispose(self):
        for handler in self._marching_ants_handlers.copy():
            handler.stop()

    def __len__(self):
        return len(self._marching_ants_handlers)


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
            self._last_offset = (self._last_offset + self._delta) % self._max_offset

            item1 = items[0]
            pen = item1.pen()
            pen.setDashOffset(self._last_offset)
            item1.setPen(pen)

            item2 = items[1]
            pen = item2.pen()
            pen.setDashOffset((self._last_offset + self._offset) % self._max_offset)
            item2.setPen(pen)
        else:
            import sys
            sys.stderr.write('_MarchingAntsHandler._update_marching_ants_offset: len(items)==%s' % (
                len(items)))

    def stop(self):
        container = self._container()
        if container is not None:
            if self in container._marching_ants_handlers:
                container._marching_ants_handlers.discard(self)

                container._timer.timeout.disconnect(self._update_marching_ants_offset)

                from pyvmmonitor_core.weak_utils import WeakList
                from pyvmmonitor_core.weak_utils import get_weakref

                self._items = WeakList()
                self._container = get_weakref(None)


class _HandleWrapper(object):

    def __init__(self, handle, animation):
        self.handle = handle
        self.animation = animation

    def stop(self):
        self.handle.stop()
        if len(self.animation) == 0:
            self.animation._timer.stop()
        self.handle = None
        self.animation = None


class GraphicsItemsAnimation(Disposable):
    '''
    To use:

    animation = GraphicsItemsAnimation(scene)

    # item1 and item2 should have the same visual representation as we use one
    # to draw in white and another to draw in black with different offsets.
    handle = animation.marching_ants(item1, item2)
    ...
    handle.stop()

    ...
    animation.dispose()  # Should be disposed before the scene is disposed.
    '''

    def __init__(self, timeout=200):
        super().__init__()
        from pyvmmonitor_qt.qt.QtCore import QTimer

        self._timer = QTimer()
        self._timeout = timeout
        self._marching_ants = None

    def marching_ants(self, item1, item2):
        assert not self.is_disposed()
        if self._marching_ants is None:
            self._marching_ants = _MarchingAnts(self._timer)
        ret = _HandleWrapper(self._marching_ants._items(item1, item2), self)
        self._timer.start(self._timeout)

        return ret

    def __len__(self):
        if self._marching_ants is None:
            return 0
        return len(self._marching_ants)

    def _on_dispose(self):
        if self._marching_ants is not None:
            self._marching_ants.dispose()
            self._marching_ants = None

        self._timer.stop()
        self._timer.deleteLater()
