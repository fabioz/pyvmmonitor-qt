# License: LGPL
#
# Copyright: Brainwy Software
import codecs
import os
import re

from pyvmmonitor_core.callback import Callback
from pyvmmonitor_qt import qt_utils
from pyvmmonitor_qt.pyface_based.code_widget import AdvancedCodeWidget
from pyvmmonitor_qt.qt import QtGui
from pyvmmonitor_qt.qt_utils import handle_exception_in_method


def get_python_file_encoding(bytestr):
    parts = bytestr.split(b'\n', 2)

    encoding = 'utf-8'  # default

    i = 0
    for line in parts:
        if i == 2:
            break
        i += 1
        line = line.strip()
        if line and line[0] == '#':
            result = re.search("coding[:=]\s*([-\w.]+)", line)
            if result:
                try:
                    c = codecs.lookup(result.group(1))
                    return c.name
                except Exception:
                    pass

    return encoding


def get_python_file_contents_as_unicode(filename):
    with open(filename, 'rb') as f:
        bytestr = f.read()

    text = bytestr.decode(get_python_file_encoding(bytestr))
    return text


class SaveableAdvancedCodeWidget(AdvancedCodeWidget):

    def __init__(self, parent, font=None, lexer=None):
        AdvancedCodeWidget.__init__(self, parent, font=font, lexer=lexer)
        self._filename = ''
        self._file_mtime = -1
        self.code.document().modificationChanged.connect(self._on_contents_changed)

        # Called with on_dirty_changed(is_dirty)
        self.on_dirty_changed = Callback()

    @handle_exception_in_method
    def _on_contents_changed(self, *args, **kwargs):
        if self.code.document().isModified():
            self.on_dirty_changed(True)
        else:
            self.on_dirty_changed(False)

    def get_filename(self):
        return self._filename

    def set_filename(self, filename):
        self._filename = filename
        if filename:
            try:
                self._file_mtime = os.path.getmtime(filename)
            except:
                # I.e.: the file does not exist
                self._file_mtime = -1
        else:
            self._file_mtime = -1

    filename = property(get_filename, set_filename)

    @handle_exception_in_method
    def keyPressEvent(self, event):
        key_sequence = QtGui.QKeySequence(event.key() + int(event.modifiers()))

        if key_sequence.matches(QtGui.QKeySequence.Save):
            self.save()

        return super(SaveableAdvancedCodeWidget, self).keyPressEvent(event)

    def save(self, filename=None):
        if filename is None:
            filename = self._filename

        if not filename:
            selected, _selected_filter = qt_utils.ask_save_filename(
                self,
                'Filename to save',
                None,
                "PY (*.py)")
            if not selected:
                return
            self.filename = filename = selected

        if self._stop_save_if_file_was_changed(filename):
            return

        text = self.code.get_code()

        first_2_lines = u'\n'.join(text.split(u'\n', 2)[0:2])
        bb = text.encode(get_python_file_encoding(first_2_lines.encode('ascii', 'replace')))

        f = open(filename, 'wb')
        try:
            f.write(bb)
        finally:
            f.close()

        self.code.document().setModified(False)
        self.filename = filename

    def reload(self):
        if not self._filename:
            return
        filename = self._filename

        code = self.code
        current_line = code.textCursor().blockNumber()

        text = get_python_file_contents_as_unicode(filename)
        code.set_code(text)
        # Try to keep the current line
        code.go_to_line(current_line)

    def _stop_save_if_file_was_changed(self, filename):
        if not os.path.isfile(filename) or filename != self._filename:
            return False

        mtime = os.path.getmtime(filename)
        if mtime != self._file_mtime:

            dlg = QtGui.QMessageBox(self)
            dlg.setWindowTitle('File changed outside editor')
            dlg.setText('The file was changed outside of the editor:\n' + filename)

            dlg.setInformativeText('What do you want to do?')
            reload_role = QtGui.QMessageBox.AcceptRole
            reload_button = dlg.addButton('Reload', reload_role)
            dlg.addButton('Overwrite file with editor contents', QtGui.QMessageBox.RejectRole)
            dlg.setDefaultButton(reload_button)

            self._file_mtime = mtime

            result = dlg.exec_()
            if result == reload_role:
                self.reload()
                return True

        return False
