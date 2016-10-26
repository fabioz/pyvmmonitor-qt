import threading

from pyvmmonitor_core import compat
from pyvmmonitor_qt.qt.QtCore import QObject, QEvent


# ==================================================================================================
# Helpers to execute on the next event loop
# ==================================================================================================
class _ExecuteOnLoopEvent(QEvent):

    def __init__(self, handle_future_events):
        QEvent.__init__(self, QEvent.User)
        self.handle_future_events = handle_future_events


class _Receiver(QObject):

    def __init__(self):
        QObject.__init__(self)
        from pyvmmonitor_core.ordered_set import OrderedSet

        self.funcs = OrderedSet()

    def event(self, ev):
        if isinstance(ev, _ExecuteOnLoopEvent):
            try:
                while True:
                    with _lock:
                        found = len(self.funcs)
                        if not found:
                            return True

                    for _i in compat.xrange(found):
                        # Note: we execute all currently registered functions, but new functions
                        # scheduled in such a function are only called in a new loop (to avoid
                        # a possible event recursion).
                        with _lock:
                            if not self.funcs:
                                return True
                            else:
                                func, _ = self.funcs.popitem(last=False)

                        # Execute it without the lock
                        func()

                    if not ev.handle_future_events:
                        break
            except:
                from .qt_utils import show_exception
                show_exception()
            return True
        return False

_lock = threading.Lock()

_receiver = _Receiver()


def process_queue(handle_future_events=False):
    _receiver.event(_ExecuteOnLoopEvent(handle_future_events))


def process_events(collect=False, handle_future_events=False):
    from pyvmmonitor_core.thread_utils import is_in_main_thread
    from pyvmmonitor_qt.qt.QtCore import QTimer
    from .qt_app import obtain_qapp

    assert is_in_main_thread()

    if not collect:
        obtain_qapp().processEvents()

    else:
        app = obtain_qapp()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(app.exit)
        timer.start(0)
        app.exec_()

    if handle_future_events:
        process_queue(handle_future_events=True)


def execute_on_next_event_loop(func):
    # Note: keeps a strong reference and stacks the same call to be run only once.
    with _lock:
        # Remove and add so that it gets to the end of the list
        _receiver.funcs.discard(func)
        _receiver.funcs.add(func)

    from .qt_app import obtain_qapp
    obtain_qapp().postEvent(_receiver, _ExecuteOnLoopEvent(False))


class NextEventLoopUpdater(object):
    '''
    Helper to call a function in the next event loop after a call to invalidate.

    next_event_loop_updater = NextEventLoopUpdater(func)

    # Schedules func to be executed in the next event loop.
    next_event_loop_updater.invalidate()
    '''

    def __init__(self, function):
        from pyvmmonitor_core.weak_utils import get_weakref
        self._update_method = get_weakref(function)
        self._disposed = False
        self._invalidate = False

    def __call__(self):
        if not self._disposed:

            if self._invalidate:
                method = self._update_method()
                try:
                    if method is not None:
                        try:
                            method()
                        except:
                            from .qt_utils import show_exception
                            show_exception()
                        finally:
                            del method
                finally:
                    self._invalidate = False

    def invalidate(self, *args, **kwargs):
        if not self._disposed:
            self._invalidate = True
            execute_on_next_event_loop(self)

    def dispose(self):
        self._disposed = True
