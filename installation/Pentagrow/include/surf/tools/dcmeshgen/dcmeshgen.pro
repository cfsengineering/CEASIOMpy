#
# read raw surface xml output from sumo 2.x and generate
# mesh with wakes using the topology-based classes
#

TEMPLATE = app
TARGET = dcmeshgen
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

SOURCES += dcmeshgen.cpp


