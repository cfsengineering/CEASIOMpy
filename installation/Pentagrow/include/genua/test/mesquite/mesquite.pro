#
# Test interface for Mesquite
#

QT       -= core gui
TEMPLATE  = app
TARGET    = test_mesquite
CONFIG   += console openmp mesquite netcdf fastlapack
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += mesquite.cpp

