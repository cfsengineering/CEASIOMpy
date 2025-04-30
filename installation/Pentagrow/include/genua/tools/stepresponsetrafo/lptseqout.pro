#
# Read time-dependent sampling data from unsteady run and transform to
# laplace domain
#

QT       -= core gui

TEMPLATE  = app
TARGET    = stepresponsetrafo
CONFIG   += console openmp
CONFIG   -= app_bundle

LIBS += -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += \
    lpstransform.cpp \
    main.cpp

HEADERS += \
    lpstransform.h
