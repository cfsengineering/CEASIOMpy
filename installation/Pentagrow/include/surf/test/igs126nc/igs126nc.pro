#
# test for BasicPart
#

TEMPLATE = app
TARGET = igs126nc
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lgenua_debug -lboost_components -lpredicates
} else {
  LIBS += -lsurf -lgenua -lboost_components -lpredicates
}

CONFIG += console thread openmp fastlapack no-spooles
CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)

win32:LIBS += -lAdvapi32

DESTDIR = .

SOURCES += main.cpp


