#
# Print summary for zml file
#

QT       -= core gui

TEMPLATE  = app
TARGET    = zmlprint
CONFIG   += console openmp
CONFIG   -= app_bundle

LIBS += -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += zmlprint.cpp
