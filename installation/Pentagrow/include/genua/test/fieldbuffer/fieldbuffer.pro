#
# Test MxFieldBuffer abstraction layer
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_fieldbuffer
CONFIG   += console openmp fastlapack
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += fieldbuffer.cpp
