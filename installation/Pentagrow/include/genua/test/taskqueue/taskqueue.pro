#
# test for different flavors of task queues
#

TEMPLATE = app
TARGET = test_workqueue
CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lgenua_debug -lboost_components
} else {
  LIBS += -lgenua -lboost_components
}

DEFINES *= BOOST_THREAD_PROVIDES_FUTURE
DEFINES *= BOOST_THREAD_VERSION=4

CONFIG += console thread warn_on openmp builtin_expat
CONFIG -= qt app_bundle

tbb {
  TBB_ROOT = /usr/local
  TBB_BUILD = /usr/local/lib64
  INCLUDEPATH += $$TBB_ROOT/include
  DEFINES += HAVE_TBB
  LIBS += -L$$TBB_BUILD -ltbb -ltbbmalloc
}

include(../../../config/appconfig.pri)
DESTDIR = .

HEADERS += atomicop.h \
    threadpool.h \
    sort.h
SOURCES += test_taskqueue.cpp

