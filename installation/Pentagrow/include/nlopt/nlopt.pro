#
# qmake project file for libnlopt.a
#
TEMPLATE = lib
TARGET = nlopt

CONFIG += warn_on thread staticlib
CONFIG -= qt
CONFIG(debug, debug|release):TARGET = $$join(TARGET,,,_debug)

include(../config/rootconfig.pri)
INCLUDEPATH += . api auglag bobyqa cdirect cobyla crs direct esch isres
INCLUDEPATH += luksan mlsl mma neldermead newuoa praxis slsqp stogo util
DEFINES += HAVE_CONFIG_H HAVE_COPYSIGN

DESTDIR = $$TARGET_LIB_DIR

CONFIG(nlopt-nolgpl) {
  DEFINES += NLOPT_NO_LGPL
} else {
  DEFINES +=   NLOPT_LGPL
  HEADERS +=  ./luksan/luksan.h
  SOURCES +=  ./luksan/mssubs.c \
              ./luksan/plip.c \
              ./luksan/plis.c \
              ./luksan/pnet.c \
              ./luksan/pssubs.c
}

win32-msvc | win32-msvc2013 {
  # MSVC compiler crashes on cobyla.c
  message("nlopt: Excluding COBYLA");
} else {
  HEADERS += cobyla/cobyla.h
  SOURCES += cobyla/cobyla.c
}

HEADERS +=  ./api/f77funcs.h \
            ./api/f77funcs_.h \
            ./api/nlopt-internal.h \
            ./api/nlopt.hpp \
            ./api/nlopt.h \
            ./auglag/auglag.h \
            ./bobyqa/bobyqa.h \
            ./cdirect/cdirect.h \
            ./config.h \
            ./crs/crs.h \
            ./direct/direct-internal.h \
            ./direct/direct.h \
            ./esch/esch.h \
            ./isres/isres.h \
            ./mlsl/mlsl.h \
            ./mma/mma.h \
            ./neldermead/neldermead.h \
            ./newuoa/newuoa.h \
            ./praxis/praxis.h \
            ./slsqp/slsqp.h \
            ./stogo/global.h \
            ./stogo/linalg.h \
            ./stogo/local.h \
            ./stogo/rosen.h \
            ./stogo/stogo.h \
            ./stogo/stogo_config.h \
            ./stogo/testfun.h \
            ./stogo/tools.h \
            ./util/nlopt-util.h \
            ./util/redblack.h \
            ./util/soboldata.h

SOURCES +=  ./api/deprecated.c \
            ./api/f77api.c \
            ./api/general.c \
            ./api/optimize.c \
            ./api/options.c \
            ./auglag/auglag.c \
            ./bobyqa/bobyqa.c \
            ./cdirect/cdirect.c \
            ./cdirect/hybrid.c \
            ./crs/crs.c \
            ./direct/DIRect.c \
            ./direct/direct_wrap.c \
            ./direct/DIRserial.c \
            ./direct/DIRsubrout.c \
            ./esch/esch.c \
            ./isres/isres.c \
            ./mlsl/mlsl.c \
            ./mma/ccsa_quadratic.c \
            ./mma/mma.c \
            ./neldermead/nldrmd.c \
            ./neldermead/sbplx.c \
            ./newuoa/newuoa.c \
            ./praxis/praxis.c \
            ./slsqp/slsqp.c \
            ./stogo/global.cpp \
            ./stogo/linalg.cpp \
            ./stogo/local.cpp \
            ./stogo/stogo.cpp \
            ./stogo/tools.cpp \
            ./util/mt19937ar.c \
            ./util/qsort_r.c \
            ./util/redblack.c \
            ./util/redblack_test.c \
            ./util/rescale.c \
            ./util/sobolseq.c \
            ./util/stop.c \
            ./util/timer.c



















