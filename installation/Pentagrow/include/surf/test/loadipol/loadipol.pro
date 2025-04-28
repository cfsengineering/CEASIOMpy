#-------------------------------------------------
#
# Project created by QtCreator 2010-09-27T15:07:54
#
#-------------------------------------------------

QT       -= core gui

TARGET = loadipol
CONFIG   += console openmp fastlapack
CONFIG   -= app_bundle

TEMPLATE = app
LIBS += -lsurf -lgenua -lboost_components

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += testipol.cpp
