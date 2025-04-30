#
# Test & time pentahedron intersection
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_penta
CONFIG   += console openmp
CONFIG   -= app_bundle

macx-icc {
  CONFIG += avx
}

LIBS += -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += pentahedron.cpp \
    penta.cpp

HEADERS += \
    penta.h \
    qr.h
