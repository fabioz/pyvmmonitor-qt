from pyvmmonitor_qt.qt import qt_api

if qt_api == 'pyqt':
    from PyQt4 import QtGui as QtWidgets

elif qt_api == 'pyside':
    from PySide import QtGui as QtWidgets

elif qt_api == 'pyqt5':
    from PyQt5 import QtWidgets

elif qt_api == 'pyside6':
    from PySide6 import QtWidgets

else:
    from PySide2 import QtWidgets

# import PySide2.QtWidgets
# for c in dir(PySide2.QtWidgets):
#     if c.startswith('Q'):
#         print('%s = QtWidgets.%s' % (c, c))

QAbstractButton = QtWidgets.QAbstractButton
QAbstractGraphicsShapeItem = QtWidgets.QAbstractGraphicsShapeItem
QAbstractItemDelegate = QtWidgets.QAbstractItemDelegate
QAbstractItemView = QtWidgets.QAbstractItemView
QAbstractScrollArea = QtWidgets.QAbstractScrollArea
QAbstractSlider = QtWidgets.QAbstractSlider
QAbstractSpinBox = QtWidgets.QAbstractSpinBox
QApplication = QtWidgets.QApplication
QBoxLayout = QtWidgets.QBoxLayout
QButtonGroup = QtWidgets.QButtonGroup
QCalendarWidget = QtWidgets.QCalendarWidget
QCheckBox = QtWidgets.QCheckBox
QColorDialog = QtWidgets.QColorDialog
QColumnView = QtWidgets.QColumnView
QComboBox = QtWidgets.QComboBox
QCommandLinkButton = QtWidgets.QCommandLinkButton
QCommonStyle = QtWidgets.QCommonStyle
QCompleter = QtWidgets.QCompleter
QDataWidgetMapper = QtWidgets.QDataWidgetMapper
QDateEdit = QtWidgets.QDateEdit
QDateTimeEdit = QtWidgets.QDateTimeEdit
# QDesktopWidget = QtWidgets.QDesktopWidget
QDial = QtWidgets.QDial
QDialog = QtWidgets.QDialog
QDialogButtonBox = QtWidgets.QDialogButtonBox
# QDirModel = QtWidgets.QDirModel
QDockWidget = QtWidgets.QDockWidget
QDoubleSpinBox = QtWidgets.QDoubleSpinBox
QErrorMessage = QtWidgets.QErrorMessage
QFileDialog = QtWidgets.QFileDialog
QFileIconProvider = QtWidgets.QFileIconProvider
QFileSystemModel = QtWidgets.QFileSystemModel
QFocusFrame = QtWidgets.QFocusFrame
QFontComboBox = QtWidgets.QFontComboBox
QFontDialog = QtWidgets.QFontDialog
QFormLayout = QtWidgets.QFormLayout
QFrame = QtWidgets.QFrame
QGesture = QtWidgets.QGesture
QGestureEvent = QtWidgets.QGestureEvent
QGestureRecognizer = QtWidgets.QGestureRecognizer
QGraphicsAnchor = QtWidgets.QGraphicsAnchor
QGraphicsAnchorLayout = QtWidgets.QGraphicsAnchorLayout
QGraphicsBlurEffect = QtWidgets.QGraphicsBlurEffect
QGraphicsColorizeEffect = QtWidgets.QGraphicsColorizeEffect
QGraphicsDropShadowEffect = QtWidgets.QGraphicsDropShadowEffect
QGraphicsEffect = QtWidgets.QGraphicsEffect
QGraphicsEllipseItem = QtWidgets.QGraphicsEllipseItem
QGraphicsGridLayout = QtWidgets.QGraphicsGridLayout
QGraphicsItem = QtWidgets.QGraphicsItem
# QGraphicsItemAnimation = QtWidgets.QGraphicsItemAnimation
QGraphicsItemGroup = QtWidgets.QGraphicsItemGroup
QGraphicsLayout = QtWidgets.QGraphicsLayout
QGraphicsLayoutItem = QtWidgets.QGraphicsLayoutItem
QGraphicsLineItem = QtWidgets.QGraphicsLineItem
QGraphicsLinearLayout = QtWidgets.QGraphicsLinearLayout
QGraphicsObject = QtWidgets.QGraphicsObject
QGraphicsOpacityEffect = QtWidgets.QGraphicsOpacityEffect
QGraphicsPathItem = QtWidgets.QGraphicsPathItem
QGraphicsPixmapItem = QtWidgets.QGraphicsPixmapItem
QGraphicsPolygonItem = QtWidgets.QGraphicsPolygonItem
QGraphicsProxyWidget = QtWidgets.QGraphicsProxyWidget
QGraphicsRectItem = QtWidgets.QGraphicsRectItem
QGraphicsRotation = QtWidgets.QGraphicsRotation
QGraphicsScale = QtWidgets.QGraphicsScale
QGraphicsScene = QtWidgets.QGraphicsScene
QGraphicsSceneContextMenuEvent = QtWidgets.QGraphicsSceneContextMenuEvent
QGraphicsSceneDragDropEvent = QtWidgets.QGraphicsSceneDragDropEvent
QGraphicsSceneEvent = QtWidgets.QGraphicsSceneEvent
QGraphicsSceneHelpEvent = QtWidgets.QGraphicsSceneHelpEvent
QGraphicsSceneHoverEvent = QtWidgets.QGraphicsSceneHoverEvent
QGraphicsSceneMouseEvent = QtWidgets.QGraphicsSceneMouseEvent
QGraphicsSceneMoveEvent = QtWidgets.QGraphicsSceneMoveEvent
QGraphicsSceneResizeEvent = QtWidgets.QGraphicsSceneResizeEvent
QGraphicsSceneWheelEvent = QtWidgets.QGraphicsSceneWheelEvent
QGraphicsSimpleTextItem = QtWidgets.QGraphicsSimpleTextItem
QGraphicsTextItem = QtWidgets.QGraphicsTextItem
QGraphicsTransform = QtWidgets.QGraphicsTransform
QGraphicsView = QtWidgets.QGraphicsView
QGraphicsWidget = QtWidgets.QGraphicsWidget
QGridLayout = QtWidgets.QGridLayout
QGroupBox = QtWidgets.QGroupBox
QHBoxLayout = QtWidgets.QHBoxLayout
QHeaderView = QtWidgets.QHeaderView
QInputDialog = QtWidgets.QInputDialog
QItemDelegate = QtWidgets.QItemDelegate
QItemEditorCreatorBase = QtWidgets.QItemEditorCreatorBase
QItemEditorFactory = QtWidgets.QItemEditorFactory
# QKeyEventTransition = QtWidgets.QKeyEventTransition
QLCDNumber = QtWidgets.QLCDNumber
QLabel = QtWidgets.QLabel
QLayout = QtWidgets.QLayout
QLayoutItem = QtWidgets.QLayoutItem
QLineEdit = QtWidgets.QLineEdit
QListView = QtWidgets.QListView
QListWidget = QtWidgets.QListWidget
QListWidgetItem = QtWidgets.QListWidgetItem
QMainWindow = QtWidgets.QMainWindow
QMdiArea = QtWidgets.QMdiArea
QMdiSubWindow = QtWidgets.QMdiSubWindow
QMenu = QtWidgets.QMenu
QMenuBar = QtWidgets.QMenuBar
QMessageBox = QtWidgets.QMessageBox
# QMouseEventTransition = QtWidgets.QMouseEventTransition
QPanGesture = QtWidgets.QPanGesture
QPinchGesture = QtWidgets.QPinchGesture
QPlainTextDocumentLayout = QtWidgets.QPlainTextDocumentLayout
QPlainTextEdit = QtWidgets.QPlainTextEdit
QProgressBar = QtWidgets.QProgressBar
QProgressDialog = QtWidgets.QProgressDialog
QPushButton = QtWidgets.QPushButton
QRadioButton = QtWidgets.QRadioButton
QRubberBand = QtWidgets.QRubberBand
QScrollArea = QtWidgets.QScrollArea
QScrollBar = QtWidgets.QScrollBar

try:
    QAction = QtWidgets.QAction
    QActionGroup = QtWidgets.QActionGroup
    QShortcut = QtWidgets.QShortcut
except AttributeError:
    from PySide6 import QtGui
    QAction = QtGui.QAction
    QActionGroup = QtGui.QActionGroup
    QShortcut = QtGui.QShortcut

QSizeGrip = QtWidgets.QSizeGrip
QSizePolicy = QtWidgets.QSizePolicy
QSlider = QtWidgets.QSlider
QSpacerItem = QtWidgets.QSpacerItem
QSpinBox = QtWidgets.QSpinBox
QSplashScreen = QtWidgets.QSplashScreen
QSplitter = QtWidgets.QSplitter
QSplitterHandle = QtWidgets.QSplitterHandle
QStackedLayout = QtWidgets.QStackedLayout
QStackedWidget = QtWidgets.QStackedWidget
QStatusBar = QtWidgets.QStatusBar
QStyle = QtWidgets.QStyle
QStyleFactory = QtWidgets.QStyleFactory
QStyleHintReturn = QtWidgets.QStyleHintReturn
QStyleHintReturnMask = QtWidgets.QStyleHintReturnMask
QStyleHintReturnVariant = QtWidgets.QStyleHintReturnVariant
QStyleOption = QtWidgets.QStyleOption
QStyleOptionButton = QtWidgets.QStyleOptionButton
QStyleOptionComboBox = QtWidgets.QStyleOptionComboBox
QStyleOptionComplex = QtWidgets.QStyleOptionComplex
QStyleOptionDockWidget = QtWidgets.QStyleOptionDockWidget
QStyleOptionFocusRect = QtWidgets.QStyleOptionFocusRect
QStyleOptionFrame = QtWidgets.QStyleOptionFrame
QStyleOptionGraphicsItem = QtWidgets.QStyleOptionGraphicsItem
QStyleOptionGroupBox = QtWidgets.QStyleOptionGroupBox
QStyleOptionHeader = QtWidgets.QStyleOptionHeader
QStyleOptionMenuItem = QtWidgets.QStyleOptionMenuItem
QStyleOptionProgressBar = QtWidgets.QStyleOptionProgressBar
QStyleOptionRubberBand = QtWidgets.QStyleOptionRubberBand
QStyleOptionSizeGrip = QtWidgets.QStyleOptionSizeGrip
QStyleOptionSlider = QtWidgets.QStyleOptionSlider
QStyleOptionSpinBox = QtWidgets.QStyleOptionSpinBox
QStyleOptionTab = QtWidgets.QStyleOptionTab
QStyleOptionTabBarBase = QtWidgets.QStyleOptionTabBarBase
QStyleOptionTabWidgetFrame = QtWidgets.QStyleOptionTabWidgetFrame
QStyleOptionTitleBar = QtWidgets.QStyleOptionTitleBar
QStyleOptionToolBar = QtWidgets.QStyleOptionToolBar
QStyleOptionToolBox = QtWidgets.QStyleOptionToolBox
QStyleOptionToolButton = QtWidgets.QStyleOptionToolButton
QStyleOptionViewItem = QtWidgets.QStyleOptionViewItem
QStylePainter = QtWidgets.QStylePainter
QStyledItemDelegate = QtWidgets.QStyledItemDelegate
QSwipeGesture = QtWidgets.QSwipeGesture
QSystemTrayIcon = QtWidgets.QSystemTrayIcon
QTabBar = QtWidgets.QTabBar
QTabWidget = QtWidgets.QTabWidget
QTableView = QtWidgets.QTableView
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QTableWidgetSelectionRange = QtWidgets.QTableWidgetSelectionRange
QTapAndHoldGesture = QtWidgets.QTapAndHoldGesture
QTapGesture = QtWidgets.QTapGesture
QTextBrowser = QtWidgets.QTextBrowser
QTextEdit = QtWidgets.QTextEdit
# QTileRules = QtWidgets.QTileRules
QTimeEdit = QtWidgets.QTimeEdit
QToolBar = QtWidgets.QToolBar
QToolBox = QtWidgets.QToolBox
QToolButton = QtWidgets.QToolButton
QToolTip = QtWidgets.QToolTip
QTreeView = QtWidgets.QTreeView
QTreeWidget = QtWidgets.QTreeWidget
QTreeWidgetItem = QtWidgets.QTreeWidgetItem
QTreeWidgetItemIterator = QtWidgets.QTreeWidgetItemIterator
# QUndoCommand = QtWidgets.QUndoCommand
# QUndoGroup = QtWidgets.QUndoGroup
# QUndoStack = QtWidgets.QUndoStack
# QUndoView = QtWidgets.QUndoView
QVBoxLayout = QtWidgets.QVBoxLayout
QWhatsThis = QtWidgets.QWhatsThis
QWidget = QtWidgets.QWidget
QWidgetAction = QtWidgets.QWidgetAction
QWidgetItem = QtWidgets.QWidgetItem
QWizard = QtWidgets.QWizard
QWizardPage = QtWidgets.QWizardPage
