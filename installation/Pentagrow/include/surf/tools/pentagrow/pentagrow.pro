#
# test for PentaGrow

TEMPLATE = app
TARGET = pentagrow
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lpredicates -lgenua_debug -lboost_components
} else {
  LIBS += -lsurf -lpredicates -lgenua -lboost_components -lz
}

CONFIG += console thread warn_on openmp reflapack

CONFIG -= qt app_bundle
QT -= core gui

include(../../../config/appconfig.pri)
DESTDIR = $$TARGET_BIN_DIR

win32:LIBS *= $$TARGET_LIB_DIR/mkl_sumo.lib
SOURCES += \
    test_pentagrow.cpp \
    frontend.cpp

HEADERS += \
    frontend.h
