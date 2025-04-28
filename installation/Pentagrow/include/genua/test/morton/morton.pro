#
# test for z-order sorting
#

TEMPLATE = app
TARGET = test_morton
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread \
          warn_on \
          openmp reflapack

CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += morton.cpp
