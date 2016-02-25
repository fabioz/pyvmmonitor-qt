# License: LGPL
#
# Copyright: Brainwy Software
import io
import threading
import time
import weakref

from pyvmmonitor_qt import compat
from pyvmmonitor_qt.pytest_plugin import qtapi
from pyvmmonitor_qt.qt.QtGui import QTreeView, QStandardItemModel, QStandardItem, QMenu
from pyvmmonitor_qt.qt_utils import execute_after_millis, process_events,\
    expanded_nodes_tree, expanded_nodes_tree, count_widget_children


def test_execute_in_millis(qtapi):
    called_at = []

    def later():
        called_at.append(time.time())

    initial = time.time()
    execute_after_millis(100, later)
    execute_after_millis(100, later)
    execute_after_millis(100, later)
    execute_after_millis(100, later)
    execute_after_millis(100, later)

    processed = 0
    while len(called_at) == 0:
        processed += 1
        process_events()
        time.sleep(0.01)

    assert processed >= 2, 'It takes at least one loop to enable the timer and another to call it!'
    assert len(called_at) == 1
    # When using 0.1 we had fails such as 1393329951.561 >= (1393329951.462 + 0.1)
    assert called_at[0] >= initial + 0.098


def create_item(txt):
    ret = QStandardItem()
    ret.setText(txt)
    return ret


def test_expanded_items(qtapi):
    qtree_view = QTreeView()
    qtapi.add_widget(qtree_view)
    model = QStandardItemModel()
    qtree_view.setModel(model)

    model.appendRow(create_item('Item 1'))
    item2_no_children = create_item('Item 2a')
    model.appendRow(item2_no_children)
    item2 = create_item('Item 2')
    model.appendRow(item2)
    item3 = create_item('Item 3')
    item2.appendRow(item3)
    item4 = create_item('Item 4')
    model.appendRow(item4)
    item3_on_root = create_item('Item 3')
    model.appendRow(item3_on_root)

    qtree_view.setExpanded(item2.index(), True)
    qtree_view.setExpanded(item3.index(), True)
    qtree_view.setExpanded(item4.index(), True)
    stream = io.StringIO()
    initial_expanded = expanded_nodes_tree(qtree_view)
    initial_expanded.print_rep(stream=stream)

    expected_initial_expanded = u'''unicode: Item 2
  unicode: Item 3
unicode: Item 4
'''.replace('\r\n', '\n').replace('\r', '\n')

    if compat.PY3:
        expected_initial_expanded = expected_initial_expanded.replace('unicode', 'str')
    assert stream.getvalue() == expected_initial_expanded

    qtree_view.setExpanded(item2.index(), False)
    qtree_view.setExpanded(item3.index(), False)
    qtree_view.setExpanded(item4.index(), False)
    stream = io.StringIO()
    expanded_nodes_tree(qtree_view).print_rep(stream=stream)
    assert stream.getvalue() == u''

    expanded_nodes_tree(qtree_view, initial_expanded)

    stream = io.StringIO()
    expanded_nodes_tree(qtree_view).print_rep(stream=stream)
    assert stream.getvalue() == expected_initial_expanded

#     qtapi.d()


def test_menu_creator(qtapi):
    from pyvmmonitor_qt.qt_utils import MenuCreator
    menu_creator = MenuCreator()
    submenu = menu_creator.add_submenu('Sort')

    class Class(object):

        def cumulative(self):
            print('cumulative')

        def total(self):
            print('total')

    c = Class()
    submenu.add_action('Cumulative', c.cumulative)
    action = submenu.add_action('Total')
    action.triggered.connect(c.total)

    another = submenu.add_submenu('Another')
    another.add_action('F1')
    another.add_action('F2')

    menu = menu_creator.create_menu()
    qtapi.add_widget(menu)
    assert isinstance(menu, QMenu)
    # I'd like to check what's there, but it seems QMenu doesn't have that API.

    # view interactively
    # from pyvmmonitor_qt.qt.QtGui import QCursor
    # menu.exec_(QCursor.pos())

    # Check that it doesn't keep a strong reference for bound methods
    c = weakref.ref(c)
    assert c() is None


def test_count_children(qtapi):
    from pyvmmonitor_qt.qt.QtGui import QWidget
    qwidget = QWidget()
    qwidget2 = QWidget(qwidget)
    qwidget3 = QWidget(qwidget2)
    qwidget4 = QWidget(qwidget2)
    qtapi.add_widget(qwidget)
    assert count_widget_children(qwidget) == 3


def test_execute_process(qtapi):
    from pyvmmonitor_qt.qt_utils import LaunchExecutableDialog
    dialog = LaunchExecutableDialog(None, close_on_finish=True)
    import sys
    code = '''
import time
for i in xrange(10):
    print('Curr: %s' % i)
'''
    dialog.set_cmd([sys.executable, '-c', code, ])
    dialog.exec_()
