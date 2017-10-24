import logging

YES = 'yes'
NO = 'no'
CANCEL = 'cancel'

logger = logging.getLogger(__name__)


def create_ask_ok_cancel_dialog(
        parent=None,
        window_title=u'Error',
        text=u'Something happened',
        informative_text=u'What do you want to do?',
        button_accept_text=u'Try with option 1',
        button_reject_text=u'Try with option 2'):
    if parent is None:
        from pyvmmonitor_qt.qt_utils import get_main_window
        parent = get_main_window()

    from pyvmmonitor_qt.qt.QtWidgets import QMessageBox
    dialog = QMessageBox(parent)
    dialog.setWindowTitle(window_title)
    dialog.setText(text)

    dialog.setInformativeText(informative_text)
    button_accept = dialog.addButton(button_accept_text, QMessageBox.AcceptRole)
    button_reject = dialog.addButton(button_reject_text, QMessageBox.RejectRole)
    dialog.setDefaultButton(button_accept)
    return dialog
    # dialog.exec_()


def ask_save_filename(parent, caption, initial_dir, files_filter, selected_filter=None):
    from pyvmmonitor_qt.qt.QtWidgets import QFileDialog
    if selected_filter is None:

        if files_filter is not None:
            selected_filter = files_filter.split(';;')[0]
    return QFileDialog.getSaveFileName(parent, caption, initial_dir, files_filter, selected_filter)


def ask_yes_no_cancel(
        title, msg, yes_caption='Yes', no_caption='No', cancel_caption='Cancel', parent=None):

    if parent is None:
        from pyvmmonitor_qt.qt_utils import get_main_window
        parent = get_main_window()

    from pyvmmonitor_qt.qt.QtWidgets import QMessageBox
    bbox = QMessageBox(QMessageBox.Question, title, msg, QMessageBox.NoButton, parent)
    bbox.addButton(yes_caption, QMessageBox.YesRole)
    bbox.addButton(no_caption, QMessageBox.NoRole)
    bbox.addButton(cancel_caption, QMessageBox.RejectRole)

    ret = bbox.exec_()
    if ret == 0:
        return YES
    if ret == 1:
        return NO
    if ret == 2:
        return CANCEL

    logger.critical('Unexpected return: %s' % (ret,))
    return CANCEL

    # Code below could be used for a more customized dialog

#     from pyvmmonitor_qt.qt_utils import CustomMessageDialog
#
#     def create_contents(dialog):
#         dialog.create_label(msg)
#         from pyvmmonitor_qt.qt.QtWidgets import QDialogButtonBox
#         dialog.bbox = bbox = QDialogButtonBox()
#
#         bt_yes = bbox.addButton(yes_caption, QDialogButtonBox.YesRole)
#         bt_no = bbox.addButton(no_caption, QDialogButtonBox.NoRole)
#         bbox.addButton(cancel_caption, QDialogButtonBox.RejectRole)
#
#         def yes():
#             dialog.done(1)
#
#         def no():
#             dialog.done(2)
#
#         bt_yes.clicked.connect(yes)
#         bt_no.clicked.connect(no)
#         bbox.rejected.connect(dialog.reject)
#
#         dialog._layout.addWidget(bbox)
#
#     dialog = CustomMessageDialog(parent, create_contents, title=title)
#     dialog.adjustSize()
#     ret = dialog.exec_()


if __name__ == '__main__':
    from pyvmmonitor_qt.qt_app import obtain_qapp
    obtain_qapp()
    print(ask_yes_no_cancel(
        'What?', '\nFoo is dirty, is this ok?\n', '&Save', 'Do &not Save', '&Cancel'))
