import gc

from pyvmmonitor_core import is_frozen
from pyvmmonitor_core.thread_utils import is_in_main_thread
from pyvmmonitor_qt.qt.QtCore import QObject, QTimer


class GarbageCollector(object):

    def __init__(self):
        self.threshold = gc.get_threshold()

    def check(self):
        assert is_in_main_thread()
        DEBUG = False
        # Uncomment for debug
        if DEBUG:
            flags = (
                gc.DEBUG_COLLECTABLE |
                gc.DEBUG_UNCOLLECTABLE |
                gc.DEBUG_SAVEALL   # i.e.: put in gc.garbage!
            )

            try:
                flags |= gc.DEBUG_INSTANCES  # @UndefinedVariable
            except AttributeError:
                pass

            try:
                flags |= gc.DEBUG_OBJECTS  # @UndefinedVariable
            except AttributeError:
                pass

            try:
                flags |= gc.DEBUG_LEAK
            except AttributeError:
                pass

            try:
                flags |= gc.DEBUG_STATS
            except AttributeError:
                pass

        else:
            flags = 0

        gc.set_debug(flags)
        l0, l1, l2 = gc.get_count()

        if l0 > self.threshold[0]:
            num = gc.collect(0)
            if DEBUG:
                print('collecting gen 0, found:', num, 'unreachable')

            if l1 > self.threshold[1]:
                num = gc.collect(1)
                if DEBUG:
                    print('collecting gen 1, found:', num, 'unreachable')

                if l2 > self.threshold[2]:
                    num = gc.collect(2)
                    if DEBUG:
                        print('collecting gen 2, found:', num, 'unreachable')

        # uncomment for debug
        if DEBUG:
            garbage = gc.garbage
            if garbage:
                for obj in garbage:
                    print('Error: cycle in: %s (%r) %s' % (obj, repr(obj), type(obj)))

            del gc.garbage[:]

        gc.set_debug(0)


class QtGarbageCollector(QObject):

    '''
    Disable automatic garbage collection and instead collect manually
    every INTERVAL milliseconds.

    This is done to ensure that garbage collection only happens in the GUI
    thread, as otherwise Qt can crash.
    '''

    if is_frozen():
        INTERVAL = 10000
    else:
        INTERVAL = 4000

    instance = None

    def __init__(self):
        assert is_in_main_thread()
        QObject.__init__(self)
        self._collector = GarbageCollector()

        timer = self.timer = QTimer()
        timer.timeout.connect(self.check)
        timer.start(self.INTERVAL)

    def check(self):
        self._collector.check()


def start_collect_only_in_ui_thread():
    gc.disable()

    if QtGarbageCollector.instance is None:
        QtGarbageCollector.instance = QtGarbageCollector()
