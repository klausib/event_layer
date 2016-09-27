# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from qgis.core import *
import locale
import os
import resources


#support for multiple languages
translator = QTranslator(QCoreApplication.instance())
localeCode = QLocale.system().name()
if localeCode:
    translator.load("eventlayer_" + localeCode + ".qm",  os.path.dirname(__file__))
    QCoreApplication.instance().installTranslator(translator)

def name():
    return QCoreApplication.translate("init","Event layer plugin")

def description():
    return QCoreApplication.translate("init","A plugin for creating event themes using linear referencing functions (locate_between, locate_along)")

def icon():
	return "eventlayer.png"

def version():
    return "1.3.1"

def qgisMinimumVersion():
  return "1.0"

def category():
  return "Vector"

def classFactory(iface):

    #prepare for the API Brake with QGIS 2.0
    if QGis.QGIS_VERSION_INT < 10900:
        from eventlayerplugin import EventLayerPlugin
    else:
        from eventlayerplugin_api2 import EventLayerPlugin
    return EventLayerPlugin(iface)
