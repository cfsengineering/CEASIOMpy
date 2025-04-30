#
# test for WakeSurf
#

TEMPLATE = app
TARGET = wakesurf
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lpredicates -lgenua_debug -lboost_components
} else {
  LIBS += -lsurf -lpredicates -lgenua -lboost_components
}

CONFIG += thread \
          warn_on \
          openmp fastlapack

CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_wakesurf.cpp
