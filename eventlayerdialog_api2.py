# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from ui_eventlayerdialogbase import Ui_EventLayerDialogBase

class EventLayerDialog( QDialog,  Ui_EventLayerDialogBase ):
    def __init__(self,  iface , parent):
        #QDialog.__init__( self,  None )
        QDialog.__init__( self,  parent )    # parent keeps the dialog in front of the parent window (without locking it).
        self.setupUi( self )
        self.mIface = iface
        QObject.connect( self.mEventTableComboBox,  SIGNAL("currentIndexChanged(int)"),  self.eventTableIndexChanged )
        QObject.connect( self.mLineLayerComboBox,  SIGNAL("currentIndexChanged(int)"),  self.lineLayerComboIndexChanged)
        QObject.connect( self.mPointRadioButton,  SIGNAL("toggled(bool)"),  self.pointButtonToggled)
        self.mLineRadioButton.setChecked( True )
        self.mOutputLayerNameEdit.setText( QCoreApplication.translate("EventLayerDialog","Event layer") )

        #get available line / event table layers
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for layerId in layerMap:
            layer = layerMap[layerId]
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue
            self.mEventTableComboBox.addItem( layer.name(),  layerId )


            # QGIS API backwards compatibility...
            if QGis.QGIS_VERSION_INT < 21400:
                if layer.wkbType() == QGis.WKBLineString25D or layer.wkbType() == QGis.WKBMultiLineString25D:
                    self.mLineLayerComboBox.addItem( layer.name(),  layerId )
            else:
                if QgsWKBTypes.singleType( QgsWKBTypes.flatType( QGis.fromOldWkbType(layer.wkbType() ) )) == QgsWKBTypes.LineString and ( QgsWKBTypes.hasZ( QGis.fromOldWkbType(layer.wkbType() )  ) or QgsWKBTypes.hasM( QGis.fromOldWkbType(layer.wkbType() )  ) ):
                #if layer.wkbType() == QgsWKBTypes.LineStringM or layer.wkbType() == QgsWKBTypes.MultiLineStringM:
                    self.mLineLayerComboBox.addItem( layer.name(),  layerId )



        if self.mLineLayerComboBox.count() < 1:
            #self.mButtonBox.button( QDialogButtonBox.Ok ).setEnabled( False )
            self.btnOK.setEnabled(False)
        else:
            self.btnOK.setEnabled(True)


    def eventTableIndexChanged(self,  index):

        #fill combo boxes with fields
        self.mEventFieldComboBox.clear()
        self.mFromFieldComboBox.clear()
        self.mToFieldComboBox.clear()
        self.mOffsetFieldComboBox.clear()
        self.mOffsetFieldComboBox.addItem(QCoreApplication.translate("Event layer",  "None"),  -1)

         # if none, return: This happens, when a layer is removed from the legend
        # no good but an easy way to prevent an error..
        if  self.mEventTableComboBox.itemData( index ) is None:
            return

        layerId = self.mEventTableComboBox.itemData( index )
        layer = QgsMapLayerRegistry.instance().mapLayers()[layerId]
        fieldMap = layer.pendingFields()
        key = 0
        while key < fieldMap.count():
            self.mEventFieldComboBox.addItem( fieldMap.at(key).name(),  key )
            if fieldMap.at(key).typeName() != 'String':
                self.mFromFieldComboBox.addItem( fieldMap.at(key).name(),  key )
                self.mToFieldComboBox.addItem(fieldMap.at(key).name(),  key )
                self.mOffsetFieldComboBox.addItem( fieldMap.at(key).name(),  key )
            key = key + 1

    def lineLayerComboIndexChanged(self,  index ):

        self.mLineFieldComboBox.clear()

        # if none, return: This happens, when a layer is removed from the legend
        # no good but an easy way to prevent an error..
        if  self.mLineLayerComboBox.itemData( index ) is None:
            return

        layerId = self.mLineLayerComboBox.itemData( index )
        layer = QgsMapLayerRegistry.instance().mapLayers()[layerId]
        fieldMap = layer.pendingFields()
        key = 0
        while key < fieldMap.count():
            self.mLineFieldComboBox.addItem( fieldMap.at(key).name(),  key )
            key = key + 1
    def pointButtonToggled(self,  enabled ):
        self.mToFieldComboBox.setEnabled( not enabled )
        if enabled:
            self.mFromFieldLabel.setText( QCoreApplication.translate("EventLayerDialog","At") )
            self.mToFieldLabel.setEnabled( False )
        else:
            self.mFromFieldLabel.setText( QCoreApplication.translate("EventLayerDialog","From") )
            self.mToFieldLabel.setEnabled( True )

    def lineLayer(self):
        return self.mLineLayerComboBox.itemData( self.mLineLayerComboBox.currentIndex() )

    def lineField(self):
        return self.mLineFieldComboBox.itemData( self.mLineFieldComboBox.currentIndex() )

    def eventLayer(self):
        return self.mEventTableComboBox.itemData( self.mEventTableComboBox.currentIndex() )

    def eventField(self):
        return self.mEventFieldComboBox.itemData( self.mEventFieldComboBox.currentIndex() )

    def fromField(self):
        return self.mFromFieldComboBox.itemData( self.mFromFieldComboBox.currentIndex() )

    def toField(self):
        if not self.mToFieldComboBox.isEnabled():
            return -1
        return self.mToFieldComboBox.itemData( self.mToFieldComboBox.currentIndex() )

    def offsetField(self):
        return self.mOffsetFieldComboBox.itemData( self.mOffsetFieldComboBox.currentIndex() )

    def offsetScale(self):
        return self.mOffsetScaleSpinBox.value()

    def outputName(self):
        return self.mOutputLayerNameEdit.text()

    def forceSingleType(self):
        return self.mForceSingleTypeCheckBox.isChecked()
