#
# aerel2zml: Convert aerel plot files to something readable by scope
#

QT       -= core gui

TEMPLATE  = app
TARGET    = aerel2zml
CONFIG   += console openmp warn_on
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components_debug
include(../../../config/appconfig.pri)
DESTDIR   = $$PREFIX/bin

SOURCES += main.cpp


