#
# evaluate problem with compiling NURBS basis function evaluation
#

TEMPLATE = app

CONFIG += thread warn_on console
CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_piegl.cpp
