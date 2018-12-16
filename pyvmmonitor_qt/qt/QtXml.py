from . import qt_api

if qt_api == 'pyqt':
    from PyQt4 import QtXml

elif qt_api == 'pyside2':
    from PySide2 import QtXml

elif qt_api == 'pyqt5':
    from PyQt5 import QtXml

else:
    from PySide import QtXml

# import PySide2.QtXml
# for c in dir(PySide2.QtXml):
#     if c.startswith('Q'):
#         print('%s = QtXml.%s' % (c, c))

QDomAttr = QtXml.QDomAttr
QDomCDATASection = QtXml.QDomCDATASection
QDomCharacterData = QtXml.QDomCharacterData
QDomComment = QtXml.QDomComment
QDomDocument = QtXml.QDomDocument
QDomDocumentFragment = QtXml.QDomDocumentFragment
QDomDocumentType = QtXml.QDomDocumentType
QDomElement = QtXml.QDomElement
QDomEntity = QtXml.QDomEntity
QDomEntityReference = QtXml.QDomEntityReference
QDomImplementation = QtXml.QDomImplementation
QDomNamedNodeMap = QtXml.QDomNamedNodeMap
QDomNode = QtXml.QDomNode
QDomNodeList = QtXml.QDomNodeList
QDomNotation = QtXml.QDomNotation
QDomProcessingInstruction = QtXml.QDomProcessingInstruction
QDomText = QtXml.QDomText
QXmlAttributes = QtXml.QXmlAttributes
QXmlContentHandler = QtXml.QXmlContentHandler
QXmlDTDHandler = QtXml.QXmlDTDHandler
QXmlDeclHandler = QtXml.QXmlDeclHandler
QXmlDefaultHandler = QtXml.QXmlDefaultHandler
QXmlEntityResolver = QtXml.QXmlEntityResolver
QXmlErrorHandler = QtXml.QXmlErrorHandler
QXmlInputSource = QtXml.QXmlInputSource
QXmlLexicalHandler = QtXml.QXmlLexicalHandler
QXmlLocator = QtXml.QXmlLocator
QXmlNamespaceSupport = QtXml.QXmlNamespaceSupport
QXmlParseException = QtXml.QXmlParseException
QXmlReader = QtXml.QXmlReader
QXmlSimpleReader = QtXml.QXmlSimpleReader
