# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from ui_eventlayerdialogbase import Ui_EventLayerDialogBase

class EventLayerDialog( QDialog,  Ui_EventLayerDialogBase ):
    def __init__(self,  iface ):
        QDialog.__init__( self,  None )
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
            if layer.wkbType() == QGis.WKBLineString25D or layer.wkbType() == QGis.WKBMultiLineString25D:
                self.mLineLayerComboBox.addItem( layer.name(),  layerId )
                
        if self.mLineLayerComboBox.count() < 1:
            self.mButtonBox.button( QDialogButtonBox.Ok ).setEnabled( False )
    
    def eventTableIndexChanged(self,  index):
        #fill combo boxes with fields
        self.mEventFieldComboBox.clear()
        self.mFromFieldComboBox.clear()
        self.mToFieldComboBox.clear()
        self.mOffsetFieldComboBox.clear()
        self.mOffsetFieldComboBox.addItem(QCoreApplication.translate("Event layer",  "None"),  -1)
        
        layerId = self.mEventTableComboBox.itemData( index ).toString()
        layer = QgsMapLayerRegistry.instance().mapLayers()[layerId]
        fieldMap = layer.pendingFields()
        for key in fieldMap:
            self.mEventFieldComboBox.addItem( fieldMap[key].name(),  key )
            if fieldMap[key].type() != QVariant.String:
                self.mFromFieldComboBox.addItem( fieldMap[key].name(),  key )
                self.mToFieldComboBox.addItem( fieldMap[key].name(),  key )
                self.mOffsetFieldComboBox.addItem( fieldMap[key].name(),  key )
        
        
    def lineLayerComboIndexChanged(self,  index ):
        self.mLineFieldComboBox.clear()
        layerId = self.mLineLayerComboBox.itemData( index ).toString()
        layer = QgsMapLayerRegistry.instance().mapLayers()[layerId]
        fieldMap = layer.pendingFields()
        for key in fieldMap:
            self.mLineFieldComboBox.addItem( fieldMap[key].name(),  key )
            
    def pointButtonToggled(self,  enabled ):
        self.mToFieldComboBox.setEnabled( not enabled )
        if enabled:
            self.mFromFieldLabel.setText( QCoreApplication.translate("EventLayerDialog","At") )
            self.mToFieldLabel.setEnabled( False )
        else:
            self.mFromFieldLabel.setText( QCoreApplication.translate("EventLayerDialog","From") )
            self.mToFieldLabel.setEnabled( True )
            
    def lineLayer(self):
        return self.mLineLayerComboBox.itemData( self.mLineLayerComboBox.currentIndex() ).toString()
        
    def lineField(self):
        return self.mLineFieldComboBox.itemData( self.mLineFieldComboBox.currentIndex() ).toInt()
        
    def eventLayer(self):
        return self.mEventTableComboBox.itemData( self.mEventTableComboBox.currentIndex() ).toString()
        
    def eventField(self):
        return self.mEventFieldComboBox.itemData( self.mEventFieldComboBox.currentIndex() ).toInt()
        
    def fromField(self):
        return self.mFromFieldComboBox.itemData( self.mFromFieldComboBox.currentIndex() ).toInt()
        
    def toField(self):
        if not self.mToFieldComboBox.isEnabled():
            return (-1,  False)
        return self.mToFieldComboBox.itemData( self.mToFieldComboBox.currentIndex() ).toInt()
        
    def offsetField(self):
        return self.mOffsetFieldComboBox.itemData( self.mOffsetFieldComboBox.currentIndex() ).toInt()
        
    def offsetScale(self):
        return self.mOffsetScaleSpinBox.value()
        
    def outputName(self):
        return self.mOutputLayerNameEdit.text()
        
    def forceSingleType(self):
        return self.mForceSingleTypeCheckBox.isChecked()
