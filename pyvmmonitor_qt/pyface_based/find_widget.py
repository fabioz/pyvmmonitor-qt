#------------------------------------------------------------------------------
# Copyright (c) 2010, Enthought Inc
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD license.

#
# Author: Enthought Inc
# Description: <Enthought pyface code editor>
#------------------------------------------------------------------------------

import weakref

from pyvmmonitor_qt.qt import QtCore
from pyvmmonitor_qt.qt.QtWidgets import QWidget


class FindWidget(QWidget):

    def __init__(self, parent):
        from pyvmmonitor_qt.qt.QtWidgets import QFormLayout
        from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout
        from pyvmmonitor_qt.qt.QtWidgets import QPushButton

        super(FindWidget, self).__init__(parent)
        self.adv_code_widget = weakref.ref(parent)

        self.button_size = self.fontMetrics().width(u'Replace All') + 20

        form_layout = QFormLayout()
        form_layout.addRow('Fin&d', self._create_find_control())

        layout = QHBoxLayout()
        layout.addLayout(form_layout)

        close_button = QPushButton('Close')
        layout.addWidget(close_button, 1, QtCore.Qt.AlignRight)
        close_button.clicked.connect(self.hide)

        self.setLayout(layout)

    def setFocus(self):
        self.line_edit.setFocus()

    def _create_find_control(self):
        from pyvmmonitor_qt.qt.QtWidgets import QWidget
        from pyvmmonitor_qt.qt.QtWidgets import QLineEdit
        from pyvmmonitor_qt.qt.QtWidgets import QPushButton
        from pyvmmonitor_qt.qt.QtWidgets import QMenu
        from pyvmmonitor_qt.qt.QtWidgets import QAction
        from pyvmmonitor_qt.qt.QtWidgets import QHBoxLayout

        control = QWidget(self)

        self.line_edit = QLineEdit()
        self.next_button = QPushButton('&Next')
        self.next_button.setFixedWidth(self.button_size)
        self.prev_button = QPushButton('&Prev')
        self.prev_button.setFixedWidth(self.button_size)
        self.options_button = QPushButton('&Options')
        self.options_button.setFixedWidth(self.button_size)

        options_menu = QMenu(self)
        self.case_action = QAction('Match &case', options_menu)
        self.case_action.setCheckable(True)
        self.word_action = QAction('Match words', options_menu)
        self.word_action.setCheckable(True)
        self.wrap_action = QAction('Wrap search', options_menu)
        self.wrap_action.setCheckable(True)
        self.wrap_action.setChecked(True)
        options_menu.addAction(self.case_action)
        options_menu.addAction(self.word_action)
        options_menu.addAction(self.wrap_action)
        self.options_button.setMenu(options_menu)

        layout = QHBoxLayout()
        layout.addWidget(self.line_edit)
        layout.addWidget(self.next_button)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.options_button)
        layout.addStretch(2)
        layout.setContentsMargins(0, 0, 0, 0)

        control.setLayout(layout)
        return control
