#
# test for PentaGrow

TEMPLATE = app
TARGET = benzitest
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread warn_on openmp no-spooles

CONFIG -= qt app_bundle
QT -= core gui

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_benzi.cpp
