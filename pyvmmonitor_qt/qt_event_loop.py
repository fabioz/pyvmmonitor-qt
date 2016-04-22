import threading

from pyvmmonitor_core.ordered_set import OrderedSet
from pyvmmonitor_core.weak_utils import get_weakref
from pyvmmonitor_qt.qt.QtCore import QObject, QEvent


# ==================================================================================================
# Helpers to execute on the next event loop
# ==================================================================================================
class _ExecuteOnLoopEvent(QEvent):

    def __init__(self):
        QEvent.__init__(self, QEvent.User)


class _Receiver(QObject):

    def __init__(self):
        QObject.__init__(self)
        self.funcs = OrderedSet()

    def event(self, ev):
        if isinstance(ev, _ExecuteOnLoopEvent):
            try:
                while True:
                    with _lock:
                        if not self.funcs:
                            return True
                        else:
                            func, _ = self.funcs.popitem(last=False)

                    # Execute it without the lock
                    func()
            except:
                from .qt_utils import show_exception
                show_exception()
            return True
        return False

_lock = threading.Lock()

_receiver = _Receiver()


def process_queue():
    _receiver.event(_ExecuteOnLoopEvent())


def process_events(collect=False):
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


def execute_on_next_event_loop(func):
    # Note: keeps a strong reference and stacks the same call to be run only once.
    with _lock:
        # Remove and add so that it gets to the end of the list
        _receiver.funcs.discard(func)
        _receiver.funcs.add(func)

    from .qt_app import obtain_qapp
    obtain_qapp().postEvent(_receiver, _ExecuteOnLoopEvent())


class NextEventLoopUpdater(object):

    def __init__(self, function):
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
