#
# test for linear BVH construction
#

TARGET = test_lbvh
TEMPLATE = app
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

DEFINES *= BOOST_THREAD_PROVIDES_FUTURE
DEFINES *= BOOST_THREAD_VERSION=4

CONFIG += thread warn_on openmp netcdf fastlapack
CONFIG -= qt app_bundle

tbb {
  TBB_ROOT = /usr/local
  TBB_BUILD = /usr/local/lib
  INCLUDEPATH += $$TBB_ROOT/include
  DEFINES += HAVE_TBB
  LIBS += -L$$TBB_BUILD -ltbb -ltbbmalloc
}

include(../../../config/appconfig.pri)
DESTDIR = .

HEADERS += unbalancedbvtree.h
SOURCES += test_lbvh.cpp

