#
# experiment with boost::compute
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_bcl
CONFIG   += console 
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components -framework OpenCL
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += bcl.cpp
