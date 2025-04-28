#
# test Schur decomposition
#

TEMPLATE = app
TARGET = test_schur
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread warn_on openmp console
CONFIG -= qt app_bundle

macx-clang | macx-g++ {
    CONFIG *= no-mkl
    LIBS += -lvecLibFort
}

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_schur.cpp
