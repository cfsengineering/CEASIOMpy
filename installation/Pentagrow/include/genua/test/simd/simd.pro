#
# test for SIMD support
#

TEMPLATE = app
TARGET = test_simd
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread warn_on sse3
CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += simd.cpp
