#
# Test implementation of lz4 stream
#

QT       -= core gui

TEMPLATE  = app
TARGET    = lz4test
CONFIG   += console openmp
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += lz4.cpp
