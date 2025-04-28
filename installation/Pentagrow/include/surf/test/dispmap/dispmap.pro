#
# test for displacement mapping
#

TEMPLATE = app
TARGET = dispmap
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lgenua_debug -lboost_components -lpredicates
} else {
  LIBS += -lsurf -lgenua -lboost_components -lpredicates
}

CONFIG += thread openmp fastlapack no-spooles

CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_dispmap.cpp


