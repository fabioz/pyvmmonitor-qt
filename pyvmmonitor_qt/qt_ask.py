import logging

YES = 'yes'
NO = 'no'
CANCEL = 'cancel'

logger = logging.getLogger(__name__)


def ask_yes_no_cancel(
        title, msg, yes_caption='Yes', no_caption='No', cancel_caption='Cancel', parent=None):

    if parent is None:
        from pyvmmonitor_qt.qt_utils import get_main_window
        parent = get_main_window()

    from pyvmmonitor_qt.qt.QtWidgets import QMessageBox
    bbox = QMessageBox(QMessageBox.Question, title, msg)
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
