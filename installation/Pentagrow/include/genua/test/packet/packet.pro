#
# test packet stream
#

TEMPLATE = app
TARGET = test_packet
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

INCLUDEPATH += ../../../eigen

CONFIG += thread warn_on openmp console
CONFIG -= qt app_bundle

macx-clang | macx-g++ {
    CONFIG *= no-mkl
}

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_packet.cpp
