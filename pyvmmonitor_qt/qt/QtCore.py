from . import qt_api

if qt_api == 'pyqt':
    from PyQt4 import QtCore

    from PyQt4.QtCore import pyqtProperty as Property
    from PyQt4.QtCore import pyqtSignal as Signal
    from PyQt4.QtCore import pyqtSlot as Slot
    from PyQt4.Qt import QCoreApplication
    from PyQt4.Qt import Qt

    __version__ = QT_VERSION_STR
    __version_info__ = tuple(map(int, QT_VERSION_STR.split('.')))

elif qt_api == 'pyside':
    try:
        from PySide import __version__, __version_info__
    except ImportError:
        pass
    from PySide import QtCore
    # Needed for the auto-generated resources
    qRegisterResourceData = QtCore.qRegisterResourceData
    from PySide import QtGui
    QSortFilterProxyModel = QtGui.QSortFilterProxyModel
    QItemSelection = QtGui.QItemSelection
    QItemSelectionModel = QtGui.QItemSelectionModel
    QItemSelectionRange = QtGui.QItemSelectionRange

else:
    try:
        from PySide2 import __version__, __version_info__
    except ImportError:
        pass
    from PySide2 import QtCore
    QSortFilterProxyModel = QtCore.QSortFilterProxyModel
    QItemSelection = QtCore.QItemSelection
    QItemSelectionModel = QtCore.QItemSelectionModel
    QItemSelectionRange = QtCore.QItemSelectionRange


# import PySide2.QtCore
# for c in dir(PySide2.QtCore):
#     if c.startswith('Q'):
#         print('%s = QtCore.%s' % (c, c))

QAbstractAnimation = QtCore.QAbstractAnimation
QAbstractEventDispatcher = QtCore.QAbstractEventDispatcher
QAbstractItemModel = QtCore.QAbstractItemModel
QAbstractListModel = QtCore.QAbstractListModel
# QAbstractProxyModel = QtCore.QAbstractProxyModel
QAbstractState = QtCore.QAbstractState
QAbstractTableModel = QtCore.QAbstractTableModel
QAbstractTransition = QtCore.QAbstractTransition
QAnimationGroup = QtCore.QAnimationGroup
# QBasicMutex = QtCore.QBasicMutex
QBasicTimer = QtCore.QBasicTimer
QBitArray = QtCore.QBitArray
QBuffer = QtCore.QBuffer
QByteArray = QtCore.QByteArray
QByteArrayMatcher = QtCore.QByteArrayMatcher
QChildEvent = QtCore.QChildEvent
QCoreApplication = QtCore.QCoreApplication
QCryptographicHash = QtCore.QCryptographicHash
QDataStream = QtCore.QDataStream
QDate = QtCore.QDate
QDateTime = QtCore.QDateTime
QDir = QtCore.QDir
QDirIterator = QtCore.QDirIterator
QDynamicPropertyChangeEvent = QtCore.QDynamicPropertyChangeEvent
QEasingCurve = QtCore.QEasingCurve
QElapsedTimer = QtCore.QElapsedTimer
QEvent = QtCore.QEvent
QEventLoop = QtCore.QEventLoop
QEventTransition = QtCore.QEventTransition
QFactoryInterface = QtCore.QFactoryInterface
QFile = QtCore.QFile
# QFileDevice = QtCore.QFileDevice
QFileInfo = QtCore.QFileInfo
QFileSystemWatcher = QtCore.QFileSystemWatcher
QFinalState = QtCore.QFinalState
QGenericArgument = QtCore.QGenericArgument
QGenericReturnArgument = QtCore.QGenericReturnArgument
QHistoryState = QtCore.QHistoryState
QIODevice = QtCore.QIODevice
# QJsonArray = QtCore.QJsonArray
# QJsonDocument = QtCore.QJsonDocument
# QJsonParseError = QtCore.QJsonParseError
# QJsonValue = QtCore.QJsonValue
QLibraryInfo = QtCore.QLibraryInfo
QLine = QtCore.QLine
QLineF = QtCore.QLineF
QLocale = QtCore.QLocale
QMargins = QtCore.QMargins
# QMessageLogContext = QtCore.QMessageLogContext
QMetaClassInfo = QtCore.QMetaClassInfo
QMetaEnum = QtCore.QMetaEnum
QMetaMethod = QtCore.QMetaMethod
QMetaObject = QtCore.QMetaObject
QMetaProperty = QtCore.QMetaProperty
QMimeData = QtCore.QMimeData
QModelIndex = QtCore.QModelIndex
QMutex = QtCore.QMutex
QMutexLocker = QtCore.QMutexLocker
QObject = QtCore.QObject
QParallelAnimationGroup = QtCore.QParallelAnimationGroup
QPauseAnimation = QtCore.QPauseAnimation
QPersistentModelIndex = QtCore.QPersistentModelIndex
QPluginLoader = QtCore.QPluginLoader
QPoint = QtCore.QPoint
QPointF = QtCore.QPointF
QProcess = QtCore.QProcess
QProcessEnvironment = QtCore.QProcessEnvironment
QPropertyAnimation = QtCore.QPropertyAnimation
QReadLocker = QtCore.QReadLocker
QReadWriteLock = QtCore.QReadWriteLock
QRect = QtCore.QRect
QRectF = QtCore.QRectF
QRegExp = QtCore.QRegExp
QResource = QtCore.QResource
QRunnable = QtCore.QRunnable
QSemaphore = QtCore.QSemaphore
QSequentialAnimationGroup = QtCore.QSequentialAnimationGroup
QSettings = QtCore.QSettings
QSignalMapper = QtCore.QSignalMapper
QSignalTransition = QtCore.QSignalTransition
QSize = QtCore.QSize
QSizeF = QtCore.QSizeF
QSocketNotifier = QtCore.QSocketNotifier
QState = QtCore.QState
QStateMachine = QtCore.QStateMachine
QSysInfo = QtCore.QSysInfo
QSystemSemaphore = QtCore.QSystemSemaphore
QT_TRANSLATE_NOOP = QtCore.QT_TRANSLATE_NOOP
QT_TRANSLATE_NOOP3 = QtCore.QT_TRANSLATE_NOOP3
QT_TRANSLATE_NOOP_UTF8 = QtCore.QT_TRANSLATE_NOOP_UTF8
QT_TR_NOOP = QtCore.QT_TR_NOOP
QT_TR_NOOP_UTF8 = QtCore.QT_TR_NOOP_UTF8
QTemporaryFile = QtCore.QTemporaryFile
QTextBoundaryFinder = QtCore.QTextBoundaryFinder
QTextCodec = QtCore.QTextCodec
QTextDecoder = QtCore.QTextDecoder
QTextEncoder = QtCore.QTextEncoder
QTextStream = QtCore.QTextStream
QTextStreamManipulator = QtCore.QTextStreamManipulator
QThread = QtCore.QThread
QThreadPool = QtCore.QThreadPool
QTime = QtCore.QTime
QTimeLine = QtCore.QTimeLine
QTimer = QtCore.QTimer
QTimerEvent = QtCore.QTimerEvent
QTranslator = QtCore.QTranslator
QUrl = QtCore.QUrl
QVariantAnimation = QtCore.QVariantAnimation
QWaitCondition = QtCore.QWaitCondition
# QWinEventNotifier = QtCore.QWinEventNotifier
QWriteLocker = QtCore.QWriteLocker
QXmlStreamAttribute = QtCore.QXmlStreamAttribute
QXmlStreamAttributes = QtCore.QXmlStreamAttributes
QXmlStreamEntityDeclaration = QtCore.QXmlStreamEntityDeclaration
QXmlStreamEntityResolver = QtCore.QXmlStreamEntityResolver
QXmlStreamNamespaceDeclaration = QtCore.QXmlStreamNamespaceDeclaration
QXmlStreamNotationDeclaration = QtCore.QXmlStreamNotationDeclaration
QXmlStreamReader = QtCore.QXmlStreamReader
QXmlStreamWriter = QtCore.QXmlStreamWriter
Qt = QtCore.Qt
QtCriticalMsg = QtCore.QtCriticalMsg
QtDebugMsg = QtCore.QtDebugMsg
QtFatalMsg = QtCore.QtFatalMsg
# QtInfoMsg = QtCore.QtInfoMsg
QtMsgType = QtCore.QtMsgType
QtSystemMsg = QtCore.QtSystemMsg
QtWarningMsg = QtCore.QtWarningMsg
