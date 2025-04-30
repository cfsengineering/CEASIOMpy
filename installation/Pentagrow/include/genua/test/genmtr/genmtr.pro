#
# test for PentaGrow

TEMPLATE = app
TARGET = genmtr
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread warn_on openmp

CONFIG -= qt app_bundle
QT -= core gui

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_genmtr.cpp
