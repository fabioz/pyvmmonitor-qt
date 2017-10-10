'''
License: LGPL

Copyright: Brainwy Software Ltda
'''
from pyvmmonitor_qt.qt.QtGui import QColor, QPalette
from pyvmmonitor_qt.qt_app import obtain_qapp


class AppStylesheet(object):

    def get_foreground(self):
        st = obtain_qapp().style()
        return st.standardPalette().color(QPalette.Text)
#         return QColor(0x32, 0x32, 0x32)


    def get_background(self):
        st = obtain_qapp().style()
        return st.standardPalette().color(QPalette.Base)
#         return QColor("white")

    def get_hover(self):
        return QColor('#6678D1')

    def get_cpu_plot_color(self):
        return QColor("#0026FF")

    def get_cpu_plot_fill_brush_color(self):
        color = QColor('#99B7FF')
        color.setAlpha(30)
        return color

STYLESHEET = '''
'''
