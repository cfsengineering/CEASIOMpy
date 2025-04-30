#
# Connect shell elements to internal beam
#

QT       -= core gui

TEMPLATE  = app
TARGET    = rbeconnect
CONFIG   += console openmp 
CONFIG   -= app_bundle
CONFIG   *= fastlapack no-spqr no-spooles

debug {
    LIBS += -lsurf_debug -lgenua_debug -lboost_components
} else {
    LIBS += -lsurf -lgenua -lboost_components
}

include(../../../config/appconfig.pri)

message("Libraries: " $$LIBS)

DESTDIR   = $$TARGET_BIN_DIR
SOURCES += \ 
    main.cpp
