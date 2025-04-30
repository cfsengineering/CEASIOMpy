#
# Convert Mxmesh in ZML format to edge/bmsh
#

QT       -= core gui

TEMPLATE  = app
TARGET    = zml2bmsh
CONFIG   += console openmp fastlapack
CONFIG   -= app_bundle

LIBS += -lgenua_debug -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = .

SOURCES += zml2bmsh.cpp
