'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
import sys
import time

from pygments.styles.monokai import MonokaiStyle

from pyvmmonitor_qt import compat, qt_utils
from pyvmmonitor_qt.pytest_plugin import qtapi  # @UnusedImport
from pyvmmonitor_qt.qt.QtCore import Qt
from pyvmmonitor_qt.qt.QtGui import QColor
from pyvmmonitor_qt.qt.QtTest import QTest


def test_python_code_text_edit_current_line(qtapi):
    from pyvmmonitor_qt.pyface_based.pygments_highlighter import PygmentsHighlighter
    from pyvmmonitor_qt.qt_utils import assert_focus_within_timeout
    from pyvmmonitor_qt.pyface_based.code_widget import CodeWidget

    PygmentsHighlighter.style = MonokaiStyle
    edit = CodeWidget(parent=None)
    edit.line_highlight_color = QColor(90, 90, 90)
    initial_code = '''a = 10
b = 20
c = 30'''
    edit.set_code(initial_code)
    edit.show()

    cursor = edit.textCursor()
    assert_focus_within_timeout(edit)
    cursor.setPosition(0)
    edit.setTextCursor(cursor)  # We must set it for it to be applied!

    assert edit.get_current_line_number() == 1  # 1-based
    edit.set_line_column(2, 1)
    assert edit.get_current_line_number() == 2


def test_python_code_text_edit(qtapi):
    from pyvmmonitor_qt.pyface_based.pygments_highlighter import PygmentsHighlighter
    from pyvmmonitor_qt.qt_utils import assert_focus_within_timeout
    from pyvmmonitor_qt.pyface_based.code_widget import CodeWidget

    PygmentsHighlighter.style = MonokaiStyle
    edit = CodeWidget(parent=None)
    edit.show()
    qtapi.add_widget(edit)
    edit.line_highlight_color = QColor(90, 90, 90)
    initial_code = '''class Error(object):
    pass'''
    edit.set_code(initial_code)

    cursor = edit.textCursor()
    assert_focus_within_timeout(edit)
    cursor.setPosition(len(initial_code))
    edit.setTextCursor(cursor)  # We must set it for it to be applied!

    assert edit.get_line_until_cursor() == '    pass'
    assert edit.get_current_line() == '    pass'

    QTest.sendKeyEvent(QTest.Click, edit, Qt.Key_Home, '', Qt.NoModifier)
    cursor = edit.textCursor()
    assert cursor.position(), len(initial_code) - len('pass')
    assert edit.get_line_until_cursor() == '    '
    assert edit.get_current_line() == '    pass'

    QTest.sendKeyEvent(QTest.Click, edit, Qt.Key_Home, '', Qt.NoModifier)
    cursor = edit.textCursor()
    assert cursor.position(), len(initial_code) - len('    pass')
    assert edit.get_line_until_cursor() == ''
    assert edit.get_current_line() == '    pass'

    edit.set_code("""class Foo(object):

    def Method(self):
        '''
        Docstring
        '''
        a = 10
        b += 20
        c = 'single line string'
        self.a = 10
        #Some comment
""")


def test_python_code_text_edit_save(qtapi, tmpdir):
    from pyvmmonitor_qt.pyface_based.saveable_code_widget import SaveableAdvancedCodeWidget
    from pyvmmonitor_qt.pyface_based.pygments_highlighter import PygmentsHighlighter
    try:
        # Python 3 has mock builtin
        from unittest.mock import patch
    except ImportError:
        # Python 2: use mock module
        from mock import patch

    p = tmpdir.mkdir("sub").join("hello.py")
    initial_code = '''class Error(object):
    pass'''
    p.write(initial_code)

    PygmentsHighlighter.style = MonokaiStyle
    edit = SaveableAdvancedCodeWidget(parent=None)
    qtapi.add_widget(edit)
    edit.code.line_highlight_color = QColor(90, 90, 90)
    new_code = 'a = 10'

    dirty = [True]

    def on_dirty_changed(is_dirty):
        dirty[0] = is_dirty

    edit.on_dirty_changed.register(on_dirty_changed)
    edit.code.set_code(new_code)
    assert not dirty[0]

    edit.filename = compat.unicode(p)

    edit.save()
    assert p.read() == new_code

    if sys.platform == 'win32':
        time.sleep(.001)  # pass some millis before changing
    else:
        time.sleep(1)  # Timeout must be higher for linux/mac.
    p.write(initial_code)

    from pyvmmonitor_qt.qt import QtWidgets

    with patch('pyvmmonitor_qt.qt.QtWidgets.QMessageBox.exec_') as m:
        m.return_value = QtWidgets.QMessageBox.AcceptRole
        edit.save()

        # I.e.: reloaded
        assert p.read() == initial_code
        assert edit.code.get_code() == initial_code

    p.write(new_code)
    with patch('pyvmmonitor_qt.qt.QtWidgets.QMessageBox.exec_') as m:
        m.return_value = QtWidgets.QMessageBox.RejectRole
        edit.save()

        # I.e.: not reloaded (overwrite)
        assert p.read() == initial_code
        assert edit.code.get_code() == initial_code

    p.write('foo')
    with patch.object(qt_utils, 'ask_save_filename') as m:
        m.return_value = compat.unicode(p), ''
        edit.filename = ''

        edit.save()

        assert edit.filename == compat.unicode(p)
        assert p.read() == initial_code
        assert edit.code.get_code() == initial_code

    p.write('foo')
    with patch.object(qt_utils, 'ask_save_filename') as m:
        m.return_value = '', ''
        edit.filename = ''

        edit.save()

        assert not edit.filename
        assert p.read() == 'foo'
        assert edit.code.get_code() == initial_code

    edit.filename = compat.unicode(p)
    edit.reload()
    assert p.read() == 'foo'
    assert edit.code.get_code() == 'foo'


def test_python_code_text_edit_dirty(qtapi, tmpdir):
    from pyvmmonitor_qt.pyface_based.saveable_code_widget import SaveableAdvancedCodeWidget
    from pyvmmonitor_qt.pyface_based.pygments_highlighter import PygmentsHighlighter

    p = tmpdir.mkdir("sub").join("hello.py")
    initial_code = '''class Error(object):
    pass'''
    p.write(initial_code)

    PygmentsHighlighter.style = MonokaiStyle
    edit = SaveableAdvancedCodeWidget(parent=None)
    qtapi.add_widget(edit)
    edit.code.line_highlight_color = QColor(90, 90, 90)
    new_code = 'a = 10'

    dirty = [True]

    def on_dirty_changed(is_dirty):
        dirty[0] = is_dirty

    edit.on_dirty_changed.register(on_dirty_changed)
    edit.code.set_code(new_code)
    assert not dirty[0]

    edit.code.autoindent_newline()
    assert new_code + '\n' == edit.code.get_code()
    assert dirty[0]

    edit.filename = compat.unicode(p)
    edit.save()
    assert not dirty[0]

    edit.code.autoindent_newline()
    assert dirty[0]
    edit.code.undo()
    assert not dirty[0]
