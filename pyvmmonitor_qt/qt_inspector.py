'''
License: LGPL

Note: this is unfinished.
'''

from pyvmmonitor_core import compat
from pyvmmonitor_qt.qt.QtWidgets import QWidget
from pyvmmonitor_qt.qt_utils import QtWeakMethod

_SHOW_INFO = {
    'size': 'QSize',
    'sizeHint': 'QSize',
    'minimumSize': 'QSize',
}


class _WidgetViewer(QWidget):

    def __init__(self, parent=None):
        from pyvmmonitor_qt.qt.QtWidgets import QGridLayout
        super(_WidgetViewer, self).__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)
        self._widget = None

        from pyvmmonitor_qt.qt_widget_builder import WidgetBuilderCols
        widget_builder = WidgetBuilderCols(2, self, layout)
        self._method_name_to_line_edit = {}
        for method_name in _SHOW_INFO:
            widget_builder.create_label(method_name)
            self._method_name_to_line_edit[method_name] = widget_builder.create_line_edit()

    def set_data(self, widget):
        if self._widget is not None:
            if hasattr(self._widget, 'setStyleSheet'):
                self._widget.setStyleSheet("")

        self._widget = widget
        if hasattr(widget, 'setStyleSheet'):
            widget.setStyleSheet("background-color:red;")
        from pyvmmonitor_qt.qt.QtCore import QSize
        for method_name in _SHOW_INFO:
            method = getattr(widget, method_name, None)
            if method is not None:
                value = method()
                if isinstance(value, QSize):
                    self._method_name_to_line_edit[method_name].setText(
                        '%s x %s' % (value.width(), value.height()))
                else:
                    self._method_name_to_line_edit[method_name].setText(str(value))


class _LiveAppInspector(QWidget):

    def __init__(self, parent=None, roots=None):
        from pyvmmonitor_qt.qt_term import QtTermWidget
        from pyvmmonitor_qt.qt_widget_builder import WidgetBuilder
        from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView

        super(_LiveAppInspector, self).__init__(parent)
        self._roots = roots

        layout = WidgetBuilder.create_layout('horizontal')
        self.setLayout(layout)

        widget_builder1 = WidgetBuilder()
        widget_builder1.create_widget(self)
        qtree_view = widget_builder1.add_qtree_view()

        self._widget_viewer = widget_viewer = _WidgetViewer()
        self._id_to_widget = {}
        self._widget_id_to_attr_name = {}
        widget_builder1.add_widget(widget_viewer)

        widget_builder1.create_custom_buttons([
            ['Refresh', self.refresh],
        ])

        self.tree = tree = PythonicQTreeView(
            qtree_view,
            has_children=QtWeakMethod(self, '_has_children'),
            create_children=QtWeakMethod(self, '_create_children'),
        )
        tree.columns = ['Widget']

        widget_builder2 = WidgetBuilder()
        widget_builder2.create_widget(self)
        widget_builder2.create_label('Terminal (Ctrl+Enter to evaluate)')
        self._term_widget = w = QtTermWidget(self)
        w.set_locals({'inspector':  self})
        widget_builder2.add_widget(w)

        layout.addWidget(widget_builder1.widget)
        layout.addWidget(widget_builder2.widget)

        self.refresh()
        qtree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _has_children(self, pythonic_tree, node):
        return True

    def _create_children(self, pythonic_tree, node):
        if node is None:
            from pyvmmonitor_qt.qt_app import obtain_qapp
            if self._roots is None:
                top_level_widgets = obtain_qapp().topLevelWidgets()
            else:
                top_level_widgets = self._roots

            for widget in top_level_widgets:
                self._create_node(pythonic_tree, widget, '', self._widget_id_to_attr_name)
        else:
            parent_obj_id = node.obj_id
            widget = self._id_to_widget[parent_obj_id]
            if widget is not None:
                print('%s - children: %s' % (widget, widget.children()))
                for child in widget.children():
                    self._create_node(pythonic_tree, child, parent_obj_id, self._widget_id_to_attr_name)
            else:
                print('None widget:', parent_obj_id, widget)

    def _create_node(self, pythonic_tree, widget, parent_id, widget_id_to_attr_name):
        widget_id_to_attr_name.update(self._get_id_to_attr_name(widget))

        obj_id = parent_id + '.' + compat.unicode(id(widget))
        self._id_to_widget[obj_id] = widget

        s = '%s (%s)' % (widget.__class__.__name__, id(widget))
        if widget.objectName():
            s += ' (%s)' % (widget.objectName(),)

        found_as_attr_name = widget_id_to_attr_name.get(id(widget))
        if found_as_attr_name:
            s += ' (%s)' % (found_as_attr_name,)

        return pythonic_tree.add_node(parent_id or None, obj_id, [s])

    def _get_id_to_attr_name(self, obj):
        id_to_name = {}
        for name in dir(obj):
            w = getattr(obj, name, None)
            if w is not None:
                id_to_name[id(w)] = '%s in %s (%s)' % (name, obj.__class__.__name__, id(obj))
        return id_to_name

    def refresh(self):
        self._widget_id_to_attr_name.clear()
        self._id_to_widget.clear()
        self.tree.clear()

    def _on_selection_changed(self):
        from pyvmmonitor_qt.qt_event_loop import execute_on_next_event_loop
        execute_on_next_event_loop(self._update_selection)

    def _update_selection(self):
        selection = self.tree.get_selection()
        if selection:
            obj_id = next(iter(selection))
            widget = self._id_to_widget[obj_id]
            self._term_widget.set_locals({'widget': widget})
            self._widget_viewer.set_data(widget)


def create_live_app_inspector(parent=None, roots=None):
    app_inspector = _LiveAppInspector(parent, roots=roots)
    return app_inspector
