#
# Project modeshapes onto surface normals
#

QT       -= core gui

TEMPLATE  = app
TARGET    = modeprj
CONFIG   += console openmp
CONFIG   -= app_bundle

CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lpredicates -lboost_components_debug
} else {
  LIBS += -lgenua -lpredicates -lboost_components
}
include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += main.cpp
