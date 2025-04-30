#
# Map nastran deformation fields / eigenmodes to surface mesh
#

QT       -= core gui

TEMPLATE  = app
TARGET    = surfmap
CONFIG   += console openmp 
CONFIG   -= app_bundle

!win32:CONFIG+=fastlapack

debug {
    LIBS += -lsurf_debug -lgenua_debug -lboost_components -lexpat -lz
} else {
    LIBS += -lsurf -lgenua -lboost_components -lexpat -lz
}

include(../../../config/appconfig.pri)

win32:LIBS *= $$TARGET_LIB_DIR/mkl_sumo.lib

message("Libraries: " $$LIBS)

DESTDIR   = $$TARGET_BIN_DIR
SOURCES += surfmap.cpp
