#
# Nastran .f06 to MxMesh converter tool
#

QT       -= core gui

TEMPLATE  = app
TARGET    = nastran2zml 
CONFIG   += console openmp fastlapack
CONFIG   -= app_bundle

CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lgenua_debug -lpredicates -lboost_components_debug
} else {
  LIBS += -lsurf -lgenua -lpredicates -lboost_components
}

include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += nastran2zml.cpp

