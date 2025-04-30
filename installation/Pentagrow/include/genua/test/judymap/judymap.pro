#
# test for dynamic triangle trees
#

TEMPLATE = app
TARGET = test_judymap
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread warn_on openmp judy
CONFIG -= qt app_bundle

INCLUDEPATH += /usr/local/include

include(../../../config/appconfig.pri)
QMAKE_LFLAGS += -L$(HOME)/lib64
DESTDIR = .

SOURCES += test_judymap.cpp
