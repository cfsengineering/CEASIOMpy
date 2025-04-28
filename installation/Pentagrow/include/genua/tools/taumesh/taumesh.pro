#
# Load a supported mesh format and convert to taumesh
#

QT       -= core gui

TEMPLATE  = app
TARGET    = mx2taumesh
CONFIG   += netcdf console openmp fastlapack
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += taumesh.cpp
