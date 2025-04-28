#
# Read files in any supported format and convert to ZML
#

QT       -= core gui

TEMPLATE  = app
TARGET    = any2zml
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

SOURCES += any2zml.cpp
