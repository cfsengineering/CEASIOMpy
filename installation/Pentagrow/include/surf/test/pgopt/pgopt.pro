#
# test for use of NLOPT for envelope improvement
#

TEMPLATE = app
TARGET = pgopt

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



HEADERS += ../pentagrow/frontend.h

SOURCES += test_pgopt.cpp \
           ../pentagrow/frontend.cpp


