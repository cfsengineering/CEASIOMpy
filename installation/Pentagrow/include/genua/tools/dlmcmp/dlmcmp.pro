#
# dlmcmp: Compare DLM DeltaCp data with surface pressure distributions
#

QT       -= core gui

TEMPLATE  = app
TARGET    = dlmcmp
CONFIG   += no-mesquite no-spooles
CONFIG   += console openmp warn_on
CONFIG   -= app_bundle

LIBS += -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += main.cpp \
    lntree.cpp \
    tritree.cpp \
    moeller.c

HEADERS += \
    lntree.h \
    treetraverse.h \
    tritree.h \
    lazytree.h \
    moeller.h


