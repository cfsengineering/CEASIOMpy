#
# test delta compression of numerical data using LZ4
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_lz4diff
CONFIG   += console preset-vzm
CONFIG   -= app_bundle

LIBS += -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = $$TARGET_BIN_DIR

SOURCES += main.cpp \
  lz4.c

HEADERS += \
  lz4.h
