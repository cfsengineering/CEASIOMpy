#
# test import of .UNV files, dataset 58/58b
#

QT       -= core gui

TEMPLATE  = app
TARGET    = unv58toHdf
CONFIG   += console hdf5
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components_debug
include(../../../config/appconfig.pri)
DESTDIR   = $$TARGET_BIN_DIR

SOURCES += main.cpp
