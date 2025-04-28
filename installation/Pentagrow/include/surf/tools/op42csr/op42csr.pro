#
# Nastran OUTPUT4 -> CsrMatrix converter
#

QT       -= core gui

TEMPLATE  = app
TARGET    = op42csr
CONFIG   += console openmp fastlapack
CONFIG   -= app_bundle

LIBS += -lsurf -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += op42csr.cpp
