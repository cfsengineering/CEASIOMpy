#
# Convert zipped binary to plain text xml
#

QT       -= core gui

TEMPLATE  = app
TARGET    = zml2xml
CONFIG   += console openmp preset-vzm
CONFIG   -= app_bundle

LIBS += -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = $$TARGET_BIN_DIR

SOURCES += zml2xml.cpp
