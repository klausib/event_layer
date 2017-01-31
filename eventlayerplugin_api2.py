# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.analysis import *
from qgis.core import *
from qgis.gui import *
import resources, copy
from eventlayerdialog_api2 import EventLayerDialog
from gui_save_failed import *

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


class EventLayerPlugin(QDialog):    # inherit of QDialog is needed to install an Event Filter on Objects of this class
    def __init__(self,  iface):
        self.mIface = iface
        QDialog.__init__( self )


    def initGui(self):
        self.mAction = QAction( QIcon(":/plugins/eventlayer/eventlayer.png"),  QCoreApplication.translate("EventLayerPluginAPI2", "Add Event layer"),  self.mIface.mainWindow() )

        #QObject.connect(self.mAction, SIGNAL("triggered()"), self.run)
        QObject.connect(self.mAction, SIGNAL("triggered()"), self.show_main_window)
        QObject.connect(QgsProject.instance(),  SIGNAL("readProject(const QDomDocument&)"),  self.readProject)
        QObject.connect(QgsProject.instance(),  SIGNAL("writeProject(QDomDocument&)"),  self.writeProject)
        #QObject.connect(self,  SIGNAL("writeProject(QDomDocument&)"),  self.writeProject)


        #self.mIface.addToolBarIcon( self.mAction )
        self.mIface.addPluginToVectorMenu(QCoreApplication.translate("EventLayerPluginAPI2",  "Event layer"),  self.mAction)
        self.mIface.addVectorToolBarIcon( self.mAction )
        self.mMemoryLayers = {} #store layer ids and event layer parameters



        # Container Widget for QGIS Dual View inkluding 'Save Records' Button
        self.save_f = GuiSaveFailed(self.mIface.mainWindow())
        # Event Filtering for the QGIS Dual View
        self.save_f.installEventFilter(self)    # alternative, a custom signal could be used...
        QObject.connect(self.save_f.btnSave,  SIGNAL("pressed()"),  self.SaveFailed)
        QObject.connect(self.save_f.btnClose,  SIGNAL("pressed()"),  self.Close)


        # QGIS DualView -> Tabele View of Layer Attributes
        self.ViewError = QgsDualView(self.save_f.frmTabelle)
        self.ViewError.setView(0)   # Attribute Table View!


        # define plain object variable to make the  event filter definition possible in this case
        self.dialog = object()


    def unload(self):
        self.mIface.removeVectorToolBarIcon( self.mAction )
        self.mIface.removePluginVectorMenu( QCoreApplication.translate("EventLayerPluginAPI2",  "Event layer"),  self.mAction )


    # start main window
    def show_main_window(self):

        # main window
        self.dialog = EventLayerDialog( self.mIface, self.mIface.mainWindow() )
        self.dialog.show()
         # Event Filtering for the Plugin Window
        self.dialog.installEventFilter(self)


        QObject.connect(self.dialog.btnRefresh,  SIGNAL("pressed()"),  self.refresh)
        QObject.connect(self.dialog.btnOK,  SIGNAL("pressed()"),  self.run)
        QObject.connect(self.dialog.btnCancel,  SIGNAL("pressed()"),  self.cancel)


         # emits a layer add event
        QObject.connect( QgsMapLayerRegistry.instance(), SIGNAL("layersAdded (QList< QgsMapLayer * > )"), self.add_layer)
        # emits a layer remove event
        QObject.connect( QgsMapLayerRegistry.instance(), SIGNAL("layersRemoved (QStringList )"),  self.remove_layer)

    def cancel(self):
        self.dialog.close()


    ##############################################################
    # Event filter for the Plugin GUI -> Catching the Close Event
    ##############################################################
    def eventFilter(self,objekt,event):

        if not event == None and not objekt == None:

            if objekt == self.dialog:
                if event.type() == QEvent.Close: # close event
                   # disconnect from QGIS!
                    QObject.disconnect( QgsMapLayerRegistry.instance(), SIGNAL("layersAdded (QList< QgsMapLayer * > )"), self.add_layer)
                    QObject.disconnect( QgsMapLayerRegistry.instance(), SIGNAL("layersRemoved (QStringList )"),  self.remove_layer)
                    return True
                else:   # pass through every event
                    return False

            elif objekt == self.save_f:
                if event.type() == QEvent.Resize: # close event
                    self.new_size()
                    return True
                else:   # pass through every event
                    return False
            else:   # pass through every event
                return False

    # run event layer calculation
    def run(self):
        dialog = self.dialog

        lineLayer = QgsMapLayerRegistry.instance().mapLayers()[dialog.lineLayer()]
        eventLayer = QgsMapLayerRegistry.instance().mapLayers()[dialog.eventLayer()]

        #output
        layertype = "MultiLineString"
        if dialog.forceSingleType():
            layertype = "LineString"

        if dialog.toField() == -1:
            if dialog.forceSingleType():
                layertype = "Point"
            else:
                layertype = "MultiPoint";

        memoryProviderUrl = QUrl()
        memoryProviderUrl.addQueryItem( "geometry",  layertype )
        memoryProviderUrl.addQueryItem( "crs",  "proj4:" + lineLayer.crs().toProj4() )
        outputLayer = self.mIface.addVectorLayer( str(memoryProviderUrl) ,dialog.outputName(),"memory" )
        memoryProvider = outputLayer.dataProvider()

        analyzer = QgsGeometryAnalyzer()

        #notify user about progress
        pd = QProgressDialog()
        pd.setLabelText( QCoreApplication.translate("EventLayerPluginAPI2","Creating event layer...") )
        pd.setCancelButtonText( QCoreApplication.translate("EventLayerPluginAPI2","Abort") )



        #API up to 2.2
        if QGis.QGIS_VERSION_INT < 20300:
            returnValue = analyzer.eventLayer( lineLayer,  eventLayer,  dialog.lineField(),  dialog.eventField(), "",  "", "", dialog.fromField(),  dialog.toField(),   dialog.offsetField(),  dialog.offsetScale(),  dialog.forceSingleType(),  memoryProvider,  pd )
            if returnValue == True:
                outputLayer.updateFields()
                self.mIface.mapCanvas().refresh()
                #print returnValue
                if not returnValue:
                    warningText = QCoreApplication.translate("EventLayerPluginAPI2", "Linear referencing failed for %1 features" ).arg( len( returnValue[1] ) )
                    QMessageBox.warning( None,  QCoreApplication.translate("EventLayerPluginAPI2", "Unreferenced features"),  warningText )

                self.mMemoryLayers[outputLayer.id()] = EventLayerParameters( dialog.lineLayer(),  dialog.eventLayer(),  dialog.lineField(),  dialog.eventField(),  dialog.fromField(),  dialog.toField(),  outputLayer.id(),  dialog.forceSingleType(),  dialog.offsetField(),  dialog.offsetScale() )

        #API from 2.3
        else:
            returnValue = analyzer.eventLayer( lineLayer,  eventLayer,  dialog.lineField(),  dialog.eventField(), "",  "",dialog.fromField(),  dialog.toField(),   dialog.offsetField(),  dialog.offsetScale(),  dialog.forceSingleType(),  memoryProvider,  pd)

            if returnValue[0] == True:
                outputLayer.updateFields()
                self.mIface.mapCanvas().refresh()
                #print returnValue[1]
                if len( returnValue[1] ) > 0:
                    self.show_msgb(returnValue[1],eventLayer)

                self.mMemoryLayers[outputLayer.id()] = EventLayerParameters( dialog.lineLayer(),  dialog.eventLayer(),  dialog.lineField(),  dialog.eventField(),  dialog.fromField(),  dialog.toField(),  outputLayer.id(),  dialog.forceSingleType(),  dialog.offsetField(),  dialog.offsetScale() )

    ###############################################################
    # read the event layer definitions from the QGIS Project File
    # and recalculate all the memory based event layer
    ###############################################################
    def readProject(self,  domDocument):



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




        listSizes = [ len(lineLayers),  len(eventLayers),  len(lineFields),  len(eventFields),  len(fromFields),  len(toFields),  len(memoryLayers) ]
        nListEntries = min( listSizes )



        self.mMemoryLayers.clear()
        for i in range( 0,  nListEntries ):

            lineLayerId = lineLayers[i]
            eventLayerId = eventLayers[i]
            memoryLayerId = memoryLayers[i]
            if not  lineLayerId in layerMap or not eventLayerId in layerMap or not memoryLayerId in layerMap:
                continue # layers are not there anymore

            lineLayer = layerMap[lineLayerId]
            eventLayer = layerMap[eventLayerId]
            memoryLayer = layerMap[memoryLayerId ]

            # remove memory layer attibute fileds first
            # they are new created
            # by the eventlayer method!
            memoryLayer.startEditing()
            memoryLayer.deleteAttributes(memoryLayer.attributeList())
            memoryLayer.commitChanges()


            analyzer = QgsGeometryAnalyzer()

            # notify user about progress
            pd = QProgressDialog()
            pd.setLabelText( QCoreApplication.translate("EventLayerPluginAPI2","Creating event layer...") )
            pd.setCancelButtonText( QCoreApplication.translate("EventLayerPluginAPI2","Abort") )

            forceSingleGeoms = False
            if forceSingleGeometries[i] == "true":
                forceSingleGeoms = True


            #API up to 2.2
            if QGis.QGIS_VERSION_INT < 20300:
                returnValue = analyzer.eventLayer( lineLayer,  eventLayer,  int(lineFields[i][0]),  int(eventFields[i]),"", "", "", int(fromFields[i]),  int(toFields[i]),  int(offsetFields[i]),  float(offsetScales[i]),  forceSingleGeoms,  memoryLayer.dataProvider(),  pd )
                if returnValue == True:
                    memoryLayer.updateFields()
                    self.mMemoryLayers[memoryLayerId] = EventLayerParameters( lineLayerId,  eventLayerId,  int(lineFields[i]),  int(eventFields[i]),   int(fromFields[i]),  int(toFields[i]),  memoryLayerId,  forceSingleGeoms,  int(offsetFields[i]),  float(offsetScales[i]) )

                if not returnValue:
                    warningText = QCoreApplication.translate("EventLayerPluginAPI2", "Linear referencing failed for %1 features" ).arg( len( returnValue[1] ) )
                    QMessageBox.warning( None,  QCoreApplication.translate("EventLayerPluginAPI2", "Unreferenced features"),  warningText )

                self.mMemoryLayers[outputLayer.id()] = EventLayerParameters( dialog.lineLayer(),  dialog.eventLayer(),  dialog.lineField(),  dialog.eventField(),  dialog.fromField(),  dialog.toField(),  outputLayer.id(),  dialog.forceSingleType(),  dialog.offsetField(),  dialog.offsetScale() )


            #API from 2.3
            else:
                returnValue = analyzer.eventLayer( lineLayer,  eventLayer,  int(lineFields[i][0]),  int(eventFields[i]),"", "", int(fromFields[i]),  int(toFields[i]),  int(offsetFields[i]),  float(offsetScales[i]),  forceSingleGeoms,  memoryLayer.dataProvider(),  pd )
                if returnValue[0] == True:
                    memoryLayer.updateFields()
                    self.mMemoryLayers[memoryLayerId] = EventLayerParameters( lineLayerId,  eventLayerId,  int(lineFields[i]),  int(eventFields[i]),   int(fromFields[i]),  int(toFields[i]),  memoryLayerId,  forceSingleGeoms,  int(offsetFields[i]),  float(offsetScales[i]) )
                if len( returnValue[1] ) > 0:
                    self.show_msgb(returnValue[1],eventLayer)




        self.mIface.mapCanvas().refresh()



    ###############################################################
    # write the event layer definitions into the QGIS PRoject File
    ###############################################################
    def writeProject(self,  domDocument ):
        lineLayers = []
        eventLayers = []
        lineFields = []
        eventFields = []
        fromFields = []
        toFields = []
        memoryLayers = []
        forceSingleGeometries = []
        offsetFields = []
        offsetScales = []

        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for k,  v in self.mMemoryLayers.iteritems():
            #layer id still there?
            if k in layerMap:
                entry = self.mMemoryLayers[k]
                lineLayers.append( entry.mLineLayer)
                eventLayers.append( entry.mEventLayer )
                lineFields.append( str( entry.mLineField ) )
                eventFields.append( str( entry.mEventField ) )
                fromFields.append( str( entry.mFromField ) )
                toFields.append(  str( entry.mToField ) )
                memoryLayers.append( k )

                if entry.mForceSingleGeometry:
                   forceSingleGeometries.append("true")
                else:
                    forceSingleGeometries.append("false")

                offsetFields.append( str( entry.mOffsetField ) )
                offsetScales.append( str( entry.mOffsetScale ) )

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



    #################################################################
    # refresh all Layers (in case of data changes)
    #################################################################
    def refresh(self):

        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for k,  v in self.mMemoryLayers.iteritems():
            #layer id still there?
            if k in layerMap:
                entry = self.mMemoryLayers[k]
                lineLayer = layerMap[entry.mLineLayer]
                eventLayer = layerMap[entry.mEventLayer]
                lineField = str( entry.mLineField )
                eventField = str( entry.mEventField )
                fromField = str( entry.mFromField )
                toField = str( entry.mToField )
                forceSingleGeoms = entry.mForceSingleGeometry


                offsetField = str( entry.mOffsetField )
                offsetScale= str( entry.mOffsetScale )

                memoryLayerId =  k
                memoryLayer = layerMap[memoryLayerId ]



                # edit session
                memoryLayer.startEditing()
                # in case of an update, delete all existing features first
                memoryLayer.selectAll()
                memoryLayer.deleteSelectedFeatures()



                analyzer = QgsGeometryAnalyzer()

                #notify user about progress
                pd = QProgressDialog()
                pd.setLabelText( QCoreApplication.translate("EventLayerPluginAPI2","Creating event layer...") )
                pd.setCancelButtonText( QCoreApplication.translate("EventLayerPluginAPI2","Abort") )


                #API up to 2.2
                if QGis.QGIS_VERSION_INT < 20300:
                    returnValue = analyzer.eventLayer( lineLayer,  eventLayer,  int(lineField),  int(eventField),"", "", "", int(fromField),  int(toField),  int(offsetField),  float(offsetScale),  forceSingleGeoms,  memoryLayer.dataProvider(),  pd )
                    if returnValue == True:
                        memoryLayer.updateFields()
                    if not returnValue:
                        warningText = QCoreApplication.translate("EventLayerPluginAPI2", "Linear referencing failed for %1 features" ).arg( len( returnValue[1] ) )
                        QMessageBox.warning( None,  QCoreApplication.translate("EventLayerPluginAPI2", "Unreferenced features"),  warningText )


                #API from 2.3
                else:
                    returnValue = analyzer.eventLayer( lineLayer,  eventLayer,  int(lineField),  int(eventField),"", "", int(fromField),  int(toField),  int(offsetField),  float(offsetScale),  forceSingleGeoms,  memoryLayer.dataProvider(),  pd )
                    if returnValue[0] == True:
                        memoryLayer.updateFields()
                    if len( returnValue[1] ) > 0:
                        self.show_msgb(returnValue[1],eventLayer, memoryLayer.name())

                memoryLayer.commitChanges()# write changes to the layer Object

        self.mIface.mapCanvas().refresh()


    ################################################
    #Remove Layers from the Combo Box in case they
    #are removed from the QGIS Legend
    ################################################
    def remove_layer(self, layer = None):

        # first clear everything
        self.dialog.mEventTableComboBox.clear()
        self.dialog.mLineLayerComboBox.clear()
        #then reove line / event table layers
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for layerId in layerMap:
            layer = layerMap[layerId]
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue
            self.dialog.mEventTableComboBox.addItem( layer.name(),  layerId )
            if layer.wkbType() == QGis.WKBLineString25D or layer.wkbType() == QGis.WKBMultiLineString25D:
                    self.dialog.mLineLayerComboBox.addItem( layer.name(),  layerId )

        if self.dialog.mLineLayerComboBox.count() < 1:
            #self.mButtonBox.button( QDialogButtonBox.Ok ).setEnabled( False )
            self.dialog.btnOK.setEnabled(False)
        else:
            self.dialog.btnOK.setEnabled(True)


    ################################################################
    # show info and/or not table view including all records of the
    # event table that faild to position along the lineM layer
    ################################################################
    def show_msgb(self, ret_val,eventLayer, linelayer_name = None):
        if linelayer_name != None:
            warningText = linelayer_name + ': ' + QCoreApplication.translate("EventLayerPluginAPI2", "Linear referencing failed for ") + str(len( ret_val)) + QCoreApplication.translate("EventLayerPluginAPI2", " features. Should they be displayed?" )#.arg( len( returnValue[1] ) )
        else:
            warningText = QCoreApplication.translate("EventLayerPluginAPI2", "Linear referencing failed for ") + str(len( ret_val)) + QCoreApplication.translate("EventLayerPluginAPI2", " features. Should they be displayed?" )#.arg( len( returnValue[1] ) )

        # show simple info in a message box
        ret = QMessageBox()
        ret.setText(warningText)
        ret.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        zentrum = self.mIface.mainWindow().frameGeometry().center()
        # fixed size
        laenge = 500
        hoehe = 100
        ret.geometry().setWidth(500)
        ret.geometry().setHeight(100)
        zentrum.setX(zentrum.x() - laenge/2)
        zentrum.setY(zentrum.y() - hoehe/2)
        ret.move(zentrum)
        req = ret.exec_()



        # if true, show attribute view with failed event table records
        if req == QMessageBox.Yes:
            eventLayer.setSelectedFeatures(ret_val)
            request = QgsFeatureRequest()
            self.ViewError.init(eventLayer,self.mIface.mapCanvas(),QgsFeatureRequest().setFilterFids(ret_val),QgsAttributeEditorContext())
            self.save_f.setModal(True)
            self.save_f.setWindowTitle(eventLayer.name())
            self.save_f.exec_()


    # Save the failed Records of the event Table (shown in the DualView Table)
    # to Disc - as Dbase File
    def SaveFailed(self):
        mm = self.ViewError.masterModel()
        mm_ly = mm.layer()
        name = QFileDialog.getSaveFileName(self, "Save file", self.save_f.windowTitle() + '_error', "*.dbf")
        writer = QgsVectorFileWriter(name, "utf8", mm_ly.dataProvider().fields(),QGis.WKBUnknown, mm_ly.dataProvider().crs(), "DBF file")
        Selection = mm_ly.selectedFeatures()

        for selr in Selection:
            writer.addFeature(selr)

        self.save_f.close()

    # resize the DualView Widget, so that it fits exactly into its surrounfing Frame
    # (called via eventFilter, wenn the Container Widget is resized)
    def new_size(self):
        self.ViewError.resize(self.save_f.frmTabelle.frameGeometry().width(),self.save_f.frmTabelle.frameGeometry().height())
        self.ViewError.setFocus()
        self.save_f.update()


    # close the tabular view of failed records
    def Close(self):
        self.save_f.close()

    ######################################################################
    #Add new loaded Layers to the Combo Boxes (while the Plugin is active)
    ######################################################################
    def add_layer(self, lyr_list):

        # clear first
        #self.dialog.mEventTableComboBox.clear()
        #get available line / event table layers
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for layerId in layerMap:
            layer = layerMap[layerId]
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue
            self.dialog.mEventTableComboBox.addItem( layer.name(),  layerId )
            if layer.wkbType() == QGis.WKBLineString25D or layer.wkbType() == QGis.WKBMultiLineString25D:
                self.dialog.mLineLayerComboBox.addItem( layer.name(),  layerId )

        if self.dialog.mLineLayerComboBox.count() < 1:
            self.dialog.btnOK.setEnabled(False)
        else:
            self.dialog.btnOK.setEnabled(True)



#################################################
# class definition: tabular view of failed records
#################################################
class GuiSaveFailed(QDialog, Ui_frmSpeichern):

##    # Custum Signal -- to pass a resize event
##    ResizeGuiSaveFailed = QtCore.pyqtSignal(object)

    def __init__(self,parent):
        QDialog.__init__(self,parent)
        Ui_frmSpeichern.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)

##    # reimplementation of the resize event handler
##    # resize events now emit our custom signal
##    def resizeEvent(self,event=None):
##        self.ResizeGuiSaveFailed.emit(self)
