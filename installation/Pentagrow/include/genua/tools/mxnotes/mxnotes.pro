#
# Coomand-line utility to manage annotations in MxMesh files
#

QT       -= core gui

TEMPLATE  = app
TARGET    = mxnotes
CONFIG   += console openmp fastlapack
CONFIG   -= app_bundle

LIBS += -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += mxnotes.cpp
