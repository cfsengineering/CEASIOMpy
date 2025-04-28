#
# test hdf5 interface
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_hdf5
CONFIG   += console hdf5
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components_debug
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += main.cpp
