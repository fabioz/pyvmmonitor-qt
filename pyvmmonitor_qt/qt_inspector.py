'''
License: LGPL

Note: this is unfinished.
'''

from pyvmmonitor_core import compat
from pyvmmonitor_qt.qt.QtWidgets import QWidget

_SHOW_INFO = {
    'sizeHint': 'QSize',
    'minimumSize': 'QSize',
}


class _WidgetViewer(QWidget):

    def __init__(self, parent=None):
        from pyvmmonitor_qt.qt.QtWidgets import QGridLayout
        super(_WidgetViewer, self).__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)

        from pyvmmonitor_qt.qt_widget_builder import WidgetBuilderCols
        widget_builder = WidgetBuilderCols(2, self, layout)
        self._method_name_to_line_edit = {}
        for method_name in _SHOW_INFO:
            widget_builder.create_label(method_name)
            self._method_name_to_line_edit[method_name] = widget_builder.create_line_edit()

    def set_data(self, widget):
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

    def __init__(self, parent=None):
        super(_LiveAppInspector, self).__init__(parent)

        from pyvmmonitor_qt.qt_widget_builder import WidgetBuilder
        from pyvmmonitor_qt.tree.pythonic_tree_view import PythonicQTreeView

        layout = WidgetBuilder.create_layout()
        self.setLayout(layout)
        widget_builder = WidgetBuilder(self, layout)

        qtree_view = widget_builder.add_qtree_view()
        self.tree = tree = PythonicQTreeView(qtree_view)
        tree.columns = ['Widget']

        self._widget_viewer = widget_viewer = _WidgetViewer()
        self._id_to_widget_ref = {}
        widget_builder.add_widget(widget_viewer)
        widget_builder.create_custom_buttons([
            ['Refresh', self.refresh],
        ])

        self.refresh()
        qtree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _get_id_to_attr_name(self, obj):
        id_to_name = {}
        for name in dir(obj):
            w = getattr(obj, name, None)
            if w is not None:
                id_to_name[id(w)] = '%s in %s (%s)' % (name, obj.__class__.__name__, id(obj))
        return id_to_name

    def refresh(self):
        self.tree.clear()
        self._id_to_widget_ref.clear()

        from pyvmmonitor_qt.qt_app import obtain_qapp
        top_level_widgets = obtain_qapp().topLevelWidgets()
        for widget in top_level_widgets:
            self._fill(widget, None, {})

    def _fill(self, widget, parent_id, widget_id_to_attr_name):
        import weakref
        widget_id_to_attr_name.update(self._get_id_to_attr_name(widget))

        obj_id = compat.unicode(id(widget))
        self._id_to_widget_ref[obj_id] = weakref.ref(widget)
        if obj_id not in self.tree:
            s = '%s (%s)' % (widget.__class__.__name__, id(widget))
            if widget.objectName():
                s += ' (%s)' % (widget.objectName(),)

            found_as_attr_name = widget_id_to_attr_name.get(id(widget))
            if found_as_attr_name:
                s += ' (%s)' % (found_as_attr_name,)

            self.tree.add_node(parent_id, obj_id, [s])

            for child in widget.children():
                self._fill(child, obj_id, widget_id_to_attr_name)

    def _on_selection_changed(self):
        from pyvmmonitor_qt.qt_event_loop import execute_on_next_event_loop
        execute_on_next_event_loop(self._update_selection)

    def _update_selection(self):
        selection = self.tree.get_selection()
        if selection:
            obj_id = next(iter(selection))
            widget_ref = self._id_to_widget_ref[obj_id]
            widget = widget_ref()
            self._widget_viewer.set_data(widget)


def create_live_app_inspector(parent=None):
    return _LiveAppInspector(parent)
