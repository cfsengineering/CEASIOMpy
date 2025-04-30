#
# test for dynamic triangle trees
#

TEMPLATE = app
TARGET = test_tet4smooth
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread \
          warn_on \
          openmp fastlapack

CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_tet4smooth.cpp
