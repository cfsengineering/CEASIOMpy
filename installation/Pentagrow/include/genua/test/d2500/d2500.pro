#
# test for dynamic triangle trees
#

TEMPLATE = app
TARGET = test_d2500
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread warn_on openmp reflapack
CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += emlord_mod.c \
           emlord.cpp
