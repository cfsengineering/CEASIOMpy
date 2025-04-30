#
# test wrapper around trnlsp solver from Intel MKL
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_trnlsp
CONFIG   += console mklpardiso
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components_debug
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += main.cpp
