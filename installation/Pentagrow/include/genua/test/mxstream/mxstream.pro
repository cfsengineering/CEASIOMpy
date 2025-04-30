#
# Test streaming output
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_mxstream
CONFIG   += console openmp fastlapack netcdf
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += mxstream.cpp
