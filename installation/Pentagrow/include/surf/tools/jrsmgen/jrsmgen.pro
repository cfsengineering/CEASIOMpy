#
# Interface to triangle.c
#

QT       -= core gui

TEMPLATE  = app
TARGET    = jrsmgen
CONFIG   += console openmp 
CONFIG   -= app_bundle
CONFIG   *= fastlapack no-spooles

win32:DEFINES += NO_TIMER

debug {
    DEFINES += SELF_CHECK
    LIBS += -lsurf_debug -lgenua_debug -lpredicates -lboost_components
} else {
    LIBS += -lsurf -lgenua -lpredicates -lboost_components
}

include(../../../config/appconfig.pri)
message("Libraries: " $$LIBS)

DESTDIR  = $$TARGET_BIN_DIR
SOURCES += main.cpp
