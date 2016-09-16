# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.analysis import *
from qgis.core import *
import resources
from eventlayerdialog import EventLayerDialog

class EventLayerParameters:
    def __init__(self,  lineLayer,  eventLayer,  lineField,  eventField,  fromField,  toField,  memoryLayer,  forceSingleGeometry,  offsetField,  offsetScale ):
        self.mLineLayer = lineLayer
        self.mEventLayer = eventLayer
        self.mLineField = lineField
        self.mEventField = eventField
        self.mFromField = fromField
        self.mToField = toField
        self.mMemoryLayer = memoryLayer
        self.mForceSingleGeometry = forceSingleGeometry
        self.mOffsetField = offsetField
        self.mOffsetScale = offsetScale

class EventLayerPlugin:
    def __init__(self,  iface):
        self.mIface = iface

    def initGui(self):
        self.mAction = QAction( QIcon(":/plugins/eventlayer/eventlayer.png"),  QCoreApplication.translate("EventLayerPlugin", "Add Event layer"),  self.mIface.mainWindow() )

        QObject.connect(self.mAction, SIGNAL("triggered()"), self.run)
        QObject.connect(QgsProject.instance(),  SIGNAL("readProject(const QDomDocument&)"),  self.readProject)
        QObject.connect(QgsProject.instance(),  SIGNAL("writeProject(QDomDocument&)"),  self.writeProject)

        #self.mIface.addToolBarIcon( self.mAction )
        self.mIface.addPluginToVectorMenu(QCoreApplication.translate("EventLayerPlugin",  "Event layer"),  self.mAction)
        self.mIface.addVectorToolBarIcon( self.mAction )
        self.mMemoryLayers = {} #store layer ids and event layer parameters

    def unload(self):
        self.mIface.removeVectorToolBarIcon( self.mAction )
        self.mIface.removePluginVectorMenu( QCoreApplication.translate("EventLayerPlugin",  "Event layer"),  self.mAction )

    def run(self):
        dialog = EventLayerDialog( self.mIface )
        if dialog.exec_() == QDialog.Accepted:
            lineLayer = QgsMapLayerRegistry.instance().mapLayers()[dialog.lineLayer()]
            eventLayer = QgsMapLayerRegistry.instance().mapLayers()[dialog.eventLayer()]

            #output
            layertype = "MultiLineString"
            if dialog.forceSingleType():
                layertype = "LineString"

            if dialog.toField()[0] == -1:
                if dialog.forceSingleType():
                    layertype = "Point"
                else:
                    layertype = "MultiPoint";

            memoryProviderUrl = QUrl()
            memoryProviderUrl.addQueryItem( "geometry",  layertype )
            memoryProviderUrl.addQueryItem( "crs",  "proj4:" + lineLayer.crs().toProj4() )
            outputLayer = self.mIface.addVectorLayer( memoryProviderUrl.toString() ,dialog.outputName(),"memory" )
            memoryProvider = outputLayer.dataProvider()

            analyzer = QgsGeometryAnalyzer()

            #notify user about progress
            pd = QProgressDialog()
            pd.setLabelText( QCoreApplication.translate("EventLayerPlugin","Creating event layer...") )
            pd.setCancelButtonText( QCoreApplication.translate("EventLayerPlugin","Abort") )


            returnValue = analyzer.eventLayer( lineLayer,  eventLayer,  dialog.lineField()[0],  dialog.eventField()[0], "",  "",  dialog.fromField()[0],  dialog.toField()[0],   dialog.offsetField()[0],  dialog.offsetScale(),  dialog.forceSingleType(),  memoryProvider,  pd )
            if returnValue[0] == True:
                outputLayer.updateFieldMap()
                self.mIface.mapCanvas().refresh()

                #print returnValue[1]
                if len( returnValue[1] ) > 0:
                    warningText = QCoreApplication.translate("EventLayerPlugin", "Linear referencing failed for %1 features" ).arg( len( returnValue[1] ) )
                    QMessageBox.warning( None,  QCoreApplication.translate("EventLayerPlugin", "Unreferenced features"),  warningText )

                self.mMemoryLayers[outputLayer.id()] = EventLayerParameters( dialog.lineLayer(),  dialog.eventLayer(),  dialog.lineField()[0],  dialog.eventField()[0],  dialog.fromField()[0],  dialog.toField()[0],  outputLayer.id(),  dialog.forceSingleType(),  dialog.offsetField()[0],  dialog.offsetScale() )

    def readProject(self,  domDocument ):
        layerMap = QgsMapLayerRegistry.instance().mapLayers()

        lineLayers = QgsProject.instance().readListEntry( "EventLayer",  "LineLayers" )[0]
        eventLayers = QgsProject.instance().readListEntry( "EventLayer",  "EventLayers" )[0]
        lineFields = QgsProject.instance().readListEntry( "EventLayer",  "LineFields" )[0]
        eventFields = QgsProject.instance().readListEntry( "EventLayer", "EventFields" )[0]
        fromFields = QgsProject.instance().readListEntry( "EventLayer",  "FromFields" )[0]
        toFields = QgsProject.instance().readListEntry( "EventLayer",  "ToFields" )[0]
        memoryLayers = QgsProject.instance().readListEntry( "EventLayer",  "MemoryLayers" )[0]
        forceSingleGeometries = QgsProject.instance().readListEntry( "EventLayer",  "ForceSingleGeometries")[0]
        offsetFields = QgsProject.instance().readListEntry("EventLayer",  "OffsetFields")[0]
        offsetScales = QgsProject.instance().readListEntry("EventLayer",  "OffsetScales")[0]

        listSizes = [ lineLayers.count(),  eventLayers.count(),  lineFields.count(),  eventFields.count(),  fromFields.count(),  toFields.count(),  memoryLayers.count() ]
        nListEntries = min( listSizes )

        self.mMemoryLayers.clear()
        for i in range( 0,  nListEntries ):

            lineLayerId = lineLayers[i]
            eventLayerId = eventLayers[i]
            memoryLayerId = memoryLayers[i]
            if not  lineLayerId in layerMap or not eventLayerId in layerMap or not memoryLayerId in layerMap:
                continue #layers are not there anymore

            lineLayer = layerMap[lineLayerId]
            eventLayer = layerMap[eventLayerId]
            memoryLayer = layerMap[memoryLayerId ]

            analyzer = QgsGeometryAnalyzer()

            #notify user about progress
            pd = QProgressDialog()
            pd.setLabelText( QCoreApplication.translate("EventLayerPlugin","Creating event layer...") )
            pd.setCancelButtonText( QCoreApplication.translate("EventLayerPlugin","Abort") )

            forceSingleGeoms = False
            if forceSingleGeometries[i] == "true":
                forceSingleGeoms = True
            returnValue = analyzer.eventLayer( lineLayer,  eventLayer,  lineFields[i].toInt()[0],  eventFields[i].toInt()[0],  "",  "",  fromFields[i].toInt()[0],  toFields[i].toInt()[0],  offsetFields[i].toInt()[0],  offsetScales[i].toDouble()[0],  forceSingleGeoms,  memoryLayer.dataProvider(),  pd )
            if returnValue[0] == True:
                memoryLayer.updateFieldMap()
                self.mMemoryLayers[memoryLayerId] = EventLayerParameters( lineLayerId,  eventLayerId,  lineFields[i].toInt()[0],  eventFields[i].toInt()[0],   fromFields[i].toInt()[0],  toFields[i].toInt()[0],  memoryLayerId,  forceSingleGeoms,  offsetFields[i].toInt()[0],  offsetScales[i].toDouble()[0] )
        self.mIface.mapCanvas().refresh()


    def writeProject(self,  domDocument ):
        lineLayers = QStringList()
        eventLayers = QStringList()
        lineFields = QStringList()
        eventFields = QStringList()
        fromFields = QStringList()
        toFields = QStringList()
        memoryLayers = QStringList()
        forceSingleGeometries = QStringList()
        offsetFields = QStringList()
        offsetScales = QStringList()

        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for k,  v in self.mMemoryLayers.iteritems():
            #layer id still there?
            if k in layerMap:
                entry = self.mMemoryLayers[k]
                lineLayers.append( entry.mLineLayer )
                eventLayers.append( entry.mEventLayer )
                lineFields.append( QString.number( entry.mLineField ) )
                eventFields.append( QString.number( entry.mEventField ) )
                fromFields.append( QString.number( entry.mFromField ) )
                toFields.append( QString.number ( entry.mToField ) )
                memoryLayers.append( k )
                if entry.mForceSingleGeometry:
                   forceSingleGeometries.append("true")
                else:
                    forceSingleGeometries.append("false")
                offsetFields.append( QString.number( entry.mOffsetField ) )
                offsetScales.append( QString.number( entry.mOffsetScale ) )

        QgsProject.instance().writeEntry( "EventLayer",  "LineLayers",  lineLayers )
        QgsProject.instance().writeEntry( "EventLayer", "EventLayers",  eventLayers )
        QgsProject.instance().writeEntry( "EventLayer",  "LineFields",  lineFields )
        QgsProject.instance().writeEntry( "EventLayer",  "EventFields", eventFields )
        QgsProject.instance().writeEntry( "EventLayer",  "FromFields",  fromFields )
        QgsProject.instance().writeEntry( "EventLayer",  "ToFields",  toFields )
        QgsProject.instance().writeEntry( "EventLayer",  "MemoryLayers",  memoryLayers )
        QgsProject.instance().writeEntry( "EventLayer",  "ForceSingleGeometries",  forceSingleGeometries )
        QgsProject.instance().writeEntry( "EventLayer",  "OffsetFields",  offsetFields )
        QgsProject.instance().writeEntry( "EventLayer",  "OffsetScales",  offsetScales )

