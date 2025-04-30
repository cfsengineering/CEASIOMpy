#
# Collect fields from a set of files and recombine into one file
#

QT       -= core gui

TEMPLATE  = app
TARGET    = mergefields
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

SOURCES += mergefields.cpp
