#
# test for class LazyIsecTree
#

TEMPLATE = app
TARGET = lazytree
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lpredicates_debug -lgenua_debug -lboost_components
} else {
  LIBS += -lsurf -lpredicates -lgenua -lboost_components
}

#LIBS += $(HOME)/lib64/liblapack.a $(HOME)/lib64/librefblas.a `/usr/local/bin/gfortran -m64 -print-file-name=libgfortran.a`

CONFIG += thread warn_on openmp fastlapack

CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_lazytree.cpp
