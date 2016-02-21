from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtCore import *

    from PyQt4.QtCore import pyqtProperty as Property
    from PyQt4.QtCore import pyqtSignal as Signal
    from PyQt4.QtCore import pyqtSlot as Slot
    from PyQt4.Qt import QCoreApplication
    from PyQt4.Qt import Qt

    __version__ = QT_VERSION_STR
    __version_info__ = tuple(map(int, QT_VERSION_STR.split('.')))

else:
    try:
        from PySide import __version__, __version_info__
    except ImportError:
        pass
    from PySide.QtCore import *


# for c in dir(PySide.QtCore):
#     if c.startswith('Q'):
#         print c, '=', c
# Just to make auto-import work better

QAbstractAnimation = QAbstractAnimation
QAbstractEventDispatcher = QAbstractEventDispatcher
QAbstractFileEngine = QAbstractFileEngine
QAbstractFileEngineHandler = QAbstractFileEngineHandler
QAbstractFileEngineIterator = QAbstractFileEngineIterator
QAbstractItemModel = QAbstractItemModel
QAbstractListModel = QAbstractListModel
QAbstractState = QAbstractState
QAbstractTableModel = QAbstractTableModel
QAbstractTransition = QAbstractTransition
QAnimationGroup = QAnimationGroup
QBasicTimer = QBasicTimer
QBitArray = QBitArray
QBuffer = QBuffer
QByteArray = QByteArray
QByteArrayMatcher = QByteArrayMatcher
QChildEvent = QChildEvent
QCoreApplication = QCoreApplication
QCryptographicHash = QCryptographicHash
QDataStream = QDataStream
QDate = QDate
QDateTime = QDateTime
QDir = QDir
QDirIterator = QDirIterator
QDynamicPropertyChangeEvent = QDynamicPropertyChangeEvent
QEasingCurve = QEasingCurve
QElapsedTimer = QElapsedTimer
QEvent = QEvent
QEventLoop = QEventLoop
QEventTransition = QEventTransition
QFSFileEngine = QFSFileEngine
QFactoryInterface = QFactoryInterface
QFile = QFile
QFileInfo = QFileInfo
QFileSystemWatcher = QFileSystemWatcher
QFinalState = QFinalState
QGenericArgument = QGenericArgument
QGenericReturnArgument = QGenericReturnArgument
QHistoryState = QHistoryState
QIODevice = QIODevice
QLibraryInfo = QLibraryInfo
QLine = QLine
QLineF = QLineF
QLocale = QLocale
QMargins = QMargins
QMetaClassInfo = QMetaClassInfo
QMetaEnum = QMetaEnum
QMetaMethod = QMetaMethod
QMetaObject = QMetaObject
QMetaProperty = QMetaProperty
QMimeData = QMimeData
QModelIndex = QModelIndex
QMutex = QMutex
QMutexLocker = QMutexLocker
QObject = QObject
QParallelAnimationGroup = QParallelAnimationGroup
QPauseAnimation = QPauseAnimation
QPersistentModelIndex = QPersistentModelIndex
QPluginLoader = QPluginLoader
QPoint = QPoint
QPointF = QPointF
QProcess = QProcess
QProcessEnvironment = QProcessEnvironment
QPropertyAnimation = QPropertyAnimation
QReadLocker = QReadLocker
QReadWriteLock = QReadWriteLock
QRect = QRect
QRectF = QRectF
QRegExp = QRegExp
QResource = QResource
QRunnable = QRunnable
QSemaphore = QSemaphore
QSequentialAnimationGroup = QSequentialAnimationGroup
QSettings = QSettings
QSignalMapper = QSignalMapper
QSignalTransition = QSignalTransition
QSize = QSize
QSizeF = QSizeF
QSocketNotifier = QSocketNotifier
QState = QState
QStateMachine = QStateMachine
QSysInfo = QSysInfo
QSystemLocale = QSystemLocale
QSystemSemaphore = QSystemSemaphore
QT_TRANSLATE_NOOP = QT_TRANSLATE_NOOP
QT_TRANSLATE_NOOP3 = QT_TRANSLATE_NOOP3
QT_TRANSLATE_NOOP_UTF8 = QT_TRANSLATE_NOOP_UTF8
QT_TR_NOOP = QT_TR_NOOP
QT_TR_NOOP_UTF8 = QT_TR_NOOP_UTF8
QTemporaryFile = QTemporaryFile
QTextBoundaryFinder = QTextBoundaryFinder
QTextCodec = QTextCodec
QTextDecoder = QTextDecoder
QTextEncoder = QTextEncoder
QTextStream = QTextStream
QTextStreamManipulator = QTextStreamManipulator
QThread = QThread
QThreadPool = QThreadPool
QTime = QTime
QTimeLine = QTimeLine
QTimer = QTimer
QTimerEvent = QTimerEvent
QTranslator = QTranslator
QUrl = QUrl
QUuid = QUuid
QVariantAnimation = QVariantAnimation
QWaitCondition = QWaitCondition
QWriteLocker = QWriteLocker
QXmlStreamAttribute = QXmlStreamAttribute
QXmlStreamAttributes = QXmlStreamAttributes
QXmlStreamEntityDeclaration = QXmlStreamEntityDeclaration
QXmlStreamEntityResolver = QXmlStreamEntityResolver
QXmlStreamNamespaceDeclaration = QXmlStreamNamespaceDeclaration
QXmlStreamNotationDeclaration = QXmlStreamNotationDeclaration
QXmlStreamReader = QXmlStreamReader
QXmlStreamWriter = QXmlStreamWriter
Qt = Qt
QtConcurrent = QtConcurrent
QtCriticalMsg = QtCriticalMsg
QtDebugMsg = QtDebugMsg
QtFatalMsg = QtFatalMsg
QtMsgType = QtMsgType
QtSystemMsg = QtSystemMsg
QtValidLicenseForDeclarativeModule = QtValidLicenseForDeclarativeModule
QtValidLicenseForMultimediaModule = QtValidLicenseForMultimediaModule
QtValidLicenseForOpenVGModule = QtValidLicenseForOpenVGModule
QtWarningMsg = QtWarningMsg