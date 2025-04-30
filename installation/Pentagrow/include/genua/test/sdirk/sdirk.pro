#
# test SDIRK integrator
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_sdirk
CONFIG   += console hdf5
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components_debug
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += main.cpp
