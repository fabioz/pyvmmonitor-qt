class WidgetBuilder(object):
    '''
    Helper to build a widget adding components in a vertical or horizontal layout.

    Use as:

    widget_builder = WidgetBuilder()
    widget_builder.create_widget()
    widget_builder.create_label()
    ...

    widget_builder.widget.show()
    '''

    def __init__(self, widget=None, layout=None):
        self._widget = widget
        self._layout = layout

    def create_widget(self, parent, layout='vertical', margin=0):
        '''
        :param parent:
        :param layout: 'vertical' or 'horizontal'
        '''
        from pyvmmonitor_qt.qt.QtWidgets import QWidget
        self._widget = QWidget(parent)

        self._layout = self.create_layout(layout, margin)
        self._widget.setLayout(self._layout)

    @property
    def widget(self):
        return self._widget

    @classmethod
    def create_layout(cls, layout='vertical', margin=0):
        if layout == 'vertical':
            from pyvmmonitor_qt.qt.QtWidgets import QVBoxLayout
            layout = QVBoxLayout()
        else:
            from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
            layout = QHBoxLayout()

        layout.setContentsMargins(margin, margin, margin, margin)
        return layout

    def add_widget(self, widget, layout=None):
        if layout is None:
            layout = self._layout
        if layout is None:
            raise RuntimeError('layout must be passed at constructor or created in create_widget.')
        layout.addWidget(widget)
        return widget

    def create_label(self, txt='', layout=None):
        from pyvmmonitor_qt.qt.QtWidgets import QLabel
        widget = QLabel(self._widget)
        widget.setText(txt)
        return self.add_widget(widget, layout=layout)

    def create_line_edit(self):
        from pyvmmonitor_qt.qt.QtWidgets import QLineEdit
        widget = QLineEdit(self._widget)
        return self.add_widget(widget)

    def create_text_browser(self, txt='', open_links=False):
        from pyvmmonitor_qt.qt.QtWidgets import QTextBrowser
        from pyvmmonitor_qt.qt.QtCore import Qt
        text_browser = QTextBrowser(self._widget)
        text_browser.setOpenExternalLinks(open_links)
        text_browser.setOpenLinks(open_links)
        text_browser.setContextMenuPolicy(Qt.NoContextMenu)
        text_browser.setText(txt)
        return self.add_widget(text_browser)

    def create_text(self, txt='', read_only=False, line_wrap=True, is_html=True, font=None):
        from pyvmmonitor_qt.qt.QtWidgets import QTextEdit
        widget = QTextEdit(self._widget)
        widget.setReadOnly(read_only)
        if line_wrap:
            widget.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            widget.setLineWrapMode(QTextEdit.NoWrap)
        if is_html:
            widget.setHtml(txt)
        else:
            widget.setText(txt)

        if font is not None:
            widget.setFont(font)
        return self.add_widget(widget)

    def add_qtree_view(self):
        from pyvmmonitor_qt.qt.QtWidgets import QTreeView
        return self.add_widget(QTreeView(self._widget))

    def create_spacer(self):
        from pyvmmonitor_qt.qt_utils import add_expanding_spacer_to_layout
        return add_expanding_spacer_to_layout(self._layout)

    def create_custom_buttons(self, label_and_callback):
        '''
        i.e.: create_custom_buttons(
        [
            ['Apply', QDialogButtonBox.ApplyRole],
            ['Ok', QDialogButtonBox.Ok],
            ['Cancel', QDialogButtonBox.Cancel],
        ]
        )
        '''
        from pyvmmonitor_qt.qt.QtWidgets import QDialogButtonBox
        roles = iter([
            QDialogButtonBox.ApplyRole,
            QDialogButtonBox.AcceptRole,
            QDialogButtonBox.ResetRole,
            QDialogButtonBox.RejectRole
        ])

        bbox = QDialogButtonBox()
        for label, callback in label_and_callback:
            button = bbox.addButton(label, next(roles))
            button.clicked.connect(callback)
        return self.add_widget(bbox)

    def create_buttons(self, show_ok=True, show_cancel=True):
        '''
        Note that clients should connect to the QDialogButtonBox rejected and accepted signals:

        bbox.rejected.connect(self.reject)
        bbox.accepted.connect(self.accept)
        '''
        assert show_ok or show_cancel
        from pyvmmonitor_qt.qt.QtWidgets import QDialogButtonBox

        if show_ok and show_cancel:
            flags = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        elif show_ok:
            flags = QDialogButtonBox.Ok
        else:
            flags = QDialogButtonBox.Cancel

        bbox = QDialogButtonBox(flags)
        return self.add_widget(bbox)

    def create_close_button(self):
        from pyvmmonitor_qt.qt.QtWidgets import QDialogButtonBox
        flags = QDialogButtonBox.Close

        bbox = QDialogButtonBox(flags)
        return self.add_widget(bbox)


class WidgetBuilderCols(WidgetBuilder):

    def __init__(self, columns, *args, **kwargs):
        super(WidgetBuilderCols, self).__init__(*args, **kwargs)
        self._columns = columns
        self._curr_col = 0
        self._curr_row = 0

    def add_widget(self, widget, layout=None):
        from pyvmmonitor_qt.qt.QtWidgets import QGridLayout
        if layout is None:
            layout = self._layout
        if layout is None:
            raise RuntimeError('layout must be passed at constructor or created in create_widget.')

        assert isinstance(layout, QGridLayout), 'Must work with a QGridLayout.'

        layout.addWidget(widget, self._curr_row, self._curr_col)
        self._curr_col += 1
        if self._curr_col == self._columns:
            self._curr_col = 0
            self._curr_row += 1

        return widget
