#
# test for class Topology & Co.
#

TEMPLATE = app
TARGET = topology
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lgenua_debug -lboost_components
} else {
  LIBS += -lsurf -lgenua -lboost_components
}

CONFIG += thread warn_on openmp fastlapack

CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_topology.cpp
