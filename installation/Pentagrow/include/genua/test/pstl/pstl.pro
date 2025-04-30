#
# test Intel paralllel STL version
#

QT       -= core gui

TEMPLATE  = app
TARGET    = test_pstl
CONFIG   += console 
CONFIG   -= app_bundle

LIBS += -lgenua -lboost_components
include(../../../config/appconfig.pri)
DESTDIR   = .

QMAKE_CXXFLAGS_DEBUG += -std:c++14

SOURCES += main.cpp
