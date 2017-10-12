class WidgetBuilder(object):
    '''
    Helper to build a widget adding components in a vertical or horizontal layout.
    '''

    def __init__(self, widget=None, layout=None):
        self.widget = widget
        self.layout = layout

    def create_widget(self, parent, layout='vertical', margin=0):
        '''
        :param parent:
        :param layout: 'vertical' or 'horizontal'
        '''
        from pyvmmonitor_qt.qt.QtWidgets import QWidget
        self.widget = QWidget(parent)

        if layout == 'vertical':
            from pyvmmonitor_qt.qt.QtWidgets import QVBoxLayout
            self.layout = QVBoxLayout()
        else:
            from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
            self.layout = QHBoxLayout()

        self.layout.setContentsMargins(margin, margin, margin, margin)
        self.widget.setLayout(self.layout)

    def add_widget(self, widget):
        self.layout.addWidget(widget)
        return widget

    def create_label(self, txt='', layout=None):
        from pyvmmonitor_qt.qt.QtWidgets import QLabel
        widget = QLabel(self.widget)
        widget.setText(txt)
        if layout is None:
            layout = self.layout
        return self.add_widget(widget)

    def create_text_browser(self, txt='', open_links=False):
        from pyvmmonitor_qt.qt.QtWidgets import QTextBrowser
        from pyvmmonitor_qt.qt.QtCore import Qt
        text_browser = QTextBrowser(self.widget)
        text_browser.setOpenExternalLinks(open_links)
        text_browser.setOpenLinks(open_links)
        text_browser.setContextMenuPolicy(Qt.NoContextMenu)
        text_browser.setText(txt)
        return self.add_widget(text_browser)

    def create_text(self, txt='', read_only=False, line_wrap=True, is_html=True, font=None):
        from pyvmmonitor_qt.qt.QtWidgets import QTextEdit
        widget = QTextEdit(self.widget)
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

    def create_spacer(self):
        from pyvmmonitor_qt.qt_utils import add_expanding_spacer_to_layout
        return add_expanding_spacer_to_layout(self.layout)

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
