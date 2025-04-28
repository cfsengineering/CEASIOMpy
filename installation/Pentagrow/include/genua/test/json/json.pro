#
# test for json integration
#

TEMPLATE = app
TARGET = test_json
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components_debug
} else {
  LIBS += -lgenua -lboost_components
}

CONFIG += thread warn_on console
CONFIG -= qt app_bundle

include(../../../config/appconfig.pri)
DESTDIR = .

SOURCES += test_json.cpp
