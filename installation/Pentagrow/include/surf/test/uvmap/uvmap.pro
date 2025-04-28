#
# test for UvMapping etc.
#

TEMPLATE = app
TARGET = uvmap
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lgenua_debug -lboost_components
} else {
  LIBS += -lsurf -lgenua -lboost_components
}

CONFIG += thread \
          warn_on \
          openmp reflapack

CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_uvmap.cpp
