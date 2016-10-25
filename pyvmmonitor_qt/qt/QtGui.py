from . import qt_api
if qt_api == 'pyqt':
    from PyQt4 import Qt
    from PyQt4 import QtGui
    QTextCursor = Qt.QTextCursor
    QKeySequence = Qt.QKeySequence

elif qt_api == 'pyside2':
    from PySide2 import QtGui
    QTextCursor = QtGui.QTextCursor
    QKeySequence = QtGui.QKeySequence

else:
    from PySide import QtGui
    QTextCursor = QtGui.QTextCursor
    QKeySequence = QtGui.QKeySequence

try:
    xrange = xrange
except:
    xrange = range

# import PySide2.QtGui
# for c in dir(PySide2.QtGui):
#     if c.startswith('Q'):
#         print('%s = QtGui.%s' % (c, c))

QAbstractTextDocumentLayout = QtGui.QAbstractTextDocumentLayout
QAccessibleEvent = QtGui.QAccessibleEvent
QActionEvent = QtGui.QActionEvent
QBitmap = QtGui.QBitmap
QBrush = QtGui.QBrush
QClipboard = QtGui.QClipboard
QCloseEvent = QtGui.QCloseEvent
QColor = QtGui.QColor
QConicalGradient = QtGui.QConicalGradient
QContextMenuEvent = QtGui.QContextMenuEvent
QCursor = QtGui.QCursor
QDoubleValidator = QtGui.QDoubleValidator
QDrag = QtGui.QDrag
QDragEnterEvent = QtGui.QDragEnterEvent
QDragLeaveEvent = QtGui.QDragLeaveEvent
QDragMoveEvent = QtGui.QDragMoveEvent
QDropEvent = QtGui.QDropEvent
QFileOpenEvent = QtGui.QFileOpenEvent
QFocusEvent = QtGui.QFocusEvent
QFont = QtGui.QFont
QFontDatabase = QtGui.QFontDatabase
QFontInfo = QtGui.QFontInfo
QFontMetrics = QtGui.QFontMetrics
QFontMetricsF = QtGui.QFontMetricsF
QGradient = QtGui.QGradient
# QGuiApplication = QtGui.QGuiApplication
QHelpEvent = QtGui.QHelpEvent
QHideEvent = QtGui.QHideEvent
QHoverEvent = QtGui.QHoverEvent
QIcon = QtGui.QIcon
QIconDragEvent = QtGui.QIconDragEvent
QIconEngine = QtGui.QIconEngine
QImage = QtGui.QImage
QImageIOHandler = QtGui.QImageIOHandler
QImageReader = QtGui.QImageReader
QImageWriter = QtGui.QImageWriter
QInputEvent = QtGui.QInputEvent
QInputMethodEvent = QtGui.QInputMethodEvent
QIntValidator = QtGui.QIntValidator
QKeyEvent = QtGui.QKeyEvent
QLinearGradient = QtGui.QLinearGradient
QMatrix = QtGui.QMatrix
QMatrix2x2 = QtGui.QMatrix2x2
QMatrix2x3 = QtGui.QMatrix2x3
QMatrix2x4 = QtGui.QMatrix2x4
QMatrix3x2 = QtGui.QMatrix3x2
QMatrix3x3 = QtGui.QMatrix3x3
QMatrix3x4 = QtGui.QMatrix3x4
QMatrix4x2 = QtGui.QMatrix4x2
QMatrix4x3 = QtGui.QMatrix4x3
QMatrix4x4 = QtGui.QMatrix4x4
QMouseEvent = QtGui.QMouseEvent
QMoveEvent = QtGui.QMoveEvent
QMovie = QtGui.QMovie
# QPagedPaintDevice = QtGui.QPagedPaintDevice
QPaintDevice = QtGui.QPaintDevice
QPaintEngine = QtGui.QPaintEngine
QPaintEngineState = QtGui.QPaintEngineState
QPaintEvent = QtGui.QPaintEvent
QPainter = QtGui.QPainter
QPainterPath = QtGui.QPainterPath
QPainterPathStroker = QtGui.QPainterPathStroker
QPalette = QtGui.QPalette
QPen = QtGui.QPen
QPicture = QtGui.QPicture
QPictureIO = QtGui.QPictureIO
QPixmap = QtGui.QPixmap
QPixmapCache = QtGui.QPixmapCache
QPolygon = QtGui.QPolygon
QPolygonF = QtGui.QPolygonF
QPyTextObject = QtGui.QPyTextObject
QQuaternion = QtGui.QQuaternion
QRadialGradient = QtGui.QRadialGradient
QRegExpValidator = QtGui.QRegExpValidator
QRegion = QtGui.QRegion
QResizeEvent = QtGui.QResizeEvent
QSessionManager = QtGui.QSessionManager
QShortcutEvent = QtGui.QShortcutEvent
QShowEvent = QtGui.QShowEvent
QStandardItem = QtGui.QStandardItem
QStandardItemModel = QtGui.QStandardItemModel
QStatusTipEvent = QtGui.QStatusTipEvent
QStringListModel = QtGui.QStringListModel
# QSurface = QtGui.QSurface
# QSurfaceFormat = QtGui.QSurfaceFormat
QSyntaxHighlighter = QtGui.QSyntaxHighlighter
QTabletEvent = QtGui.QTabletEvent
QTextBlock = QtGui.QTextBlock
QTextBlockFormat = QtGui.QTextBlockFormat
QTextBlockGroup = QtGui.QTextBlockGroup
QTextBlockUserData = QtGui.QTextBlockUserData
QTextCharFormat = QtGui.QTextCharFormat
QTextDocument = QtGui.QTextDocument
QTextDocumentFragment = QtGui.QTextDocumentFragment
QTextFormat = QtGui.QTextFormat
QTextFragment = QtGui.QTextFragment
QTextFrame = QtGui.QTextFrame
QTextFrameFormat = QtGui.QTextFrameFormat
QTextImageFormat = QtGui.QTextImageFormat
QTextInlineObject = QtGui.QTextInlineObject
QTextItem = QtGui.QTextItem
QTextLayout = QtGui.QTextLayout
QTextLength = QtGui.QTextLength
QTextLine = QtGui.QTextLine
QTextList = QtGui.QTextList
QTextListFormat = QtGui.QTextListFormat
QTextObject = QtGui.QTextObject
QTextObjectInterface = QtGui.QTextObjectInterface
QTextOption = QtGui.QTextOption
QTextTable = QtGui.QTextTable
QTextTableCell = QtGui.QTextTableCell
QTextTableCellFormat = QtGui.QTextTableCellFormat
QTextTableFormat = QtGui.QTextTableFormat
QToolBarChangeEvent = QtGui.QToolBarChangeEvent
# QTouchDevice = QtGui.QTouchDevice
QTouchEvent = QtGui.QTouchEvent
QTransform = QtGui.QTransform
QValidator = QtGui.QValidator
QVector2D = QtGui.QVector2D
QVector3D = QtGui.QVector3D
QVector4D = QtGui.QVector4D
QWhatsThisClickedEvent = QtGui.QWhatsThisClickedEvent
QWheelEvent = QtGui.QWheelEvent
# QWindow = QtGui.QWindow
QWindowStateChangeEvent = QtGui.QWindowStateChangeEvent