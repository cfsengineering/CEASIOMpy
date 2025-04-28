#
# qmake project file for libpredicates.a
#
TEMPLATE = lib
TARGET = predicates

CONFIG += warn_on thread staticlib
CONFIG -= qt
CONFIG(debug, debug|release):TARGET = $$join(TARGET,,,_debug)

include(../config/rootconfig.pri)
INCLUDEPATH += ..

linux-g++-64 {

  # default configuration on 64-bit Linux systems
  CONFIG += sse3

  !isEmpty( LOCAL_GCC ) {
    QMAKE_CXX       = $$LOCAL_GCC/bin/g++
    QMAKE_CC        = $$LOCAL_GCC/bin/gcc
    QMAKE_LINK      = $$LOCAL_GCC/bin/g++
  }

  DEFINES      += _LP64

  TARGET_LIB_DIR = $$PREFIX/lib64
  BASEFLAGS     = -m64 -mfpmath=sse

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS

  release {
    OPTFLAGS      = -DNDEBUG -Os -march=core2
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }

  profile {
    OPTFLAGS        = -DNDEBUG -g -pg -Os -march=core2
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -pg
  }

  staticlib {
    DESTDIR = $$PREFIX/lib64
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }
}

linux-g++-32 {

  # default configuration on 32-bit Linux systems
  CONFIG += sse3

  !isEmpty( LOCAL_GCC ) {
    QMAKE_CXX       = $$LOCAL_GCC/bin/g++
    QMAKE_CC        = $$LOCAL_GCC/bin/gcc
    QMAKE_LINK      = $$LOCAL_GCC/bin/g++
  }

  TARGET_LIB_DIR = $$PREFIX/lib
  BASEFLAGS     = -m32 -mfpmath=sse

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS

  release {
    OPTFLAGS      = -DNDEBUG -Os -march=core2
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }

  profile {
    OPTFLAGS        = -DNDEBUG -g -pg -Os -march=core2
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -pg
  }

  staticlib {
    DESTDIR = $$PREFIX/lib
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }
}

linux-icc | linux-icc-32 | linux-icc-64 {

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS
  DEFINES *= ARCH_SSE2
  
  release {
    DEFINES      += NDEBUG
    OPTFLAGS    = -xSSE2 -Os 
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }  
  
  profile {
    DEFINES      += NDEBUG
    OPTFLAGS      = -g -p -xSSE2 -Os 
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -p
  }

  debug:DEFINES -= NDEBUG
}

macx-g++ | macx-g++42 | macx-clang {

  BASEFLAGS = $$CFLAGS_LIBS
  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS --std=c99 -O0
  QMAKE_CXXFLAGS = $$BASEFLAGS

  CONFIG(x86_64) {

    message("Mac OS X x86_64")
    CONFIG += sse3

    # Mac OS > 10.5 has gcc 4.2
    QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.5

    DEFINES += _LP64
    QMAKE_CXXFLAGS += "-arch x86_64" -march=core2 -mfpmath=sse
    QMAKE_CFLAGS += "-arch x86_64" -march=core2 -mfpmath=sse
    TARGET_LIB_DIR = $$PREFIX/lib64
  }

  CONFIG(x86) {
    message("Mac OS X i386")
    QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.4
    TARGET_LIB_DIR = $$PREFIX/lib
    QMAKE_CXXFLAGS += "-arch i386" -march=core2 -mfpmath=sse
    QMAKE_CFLAGS += "-arch i386" -march=core2 -mfpmath=sse
    QMAKE_LFLAGS += "-arch i386" -L/usr/local/lib -L$TARGET_LIB_DIR
  }

  release {
    OPTFLAGS  = -O0 -DNDEBUG -fomit-frame-pointer -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }

  profile {
    PROFFLAGS = -g -pg
    QMAKE_CXXFLAGS += $$PROFFLAGS
    QMAKE_CFLAGS   += $$PROFFLAGS
    QMAKE_CFLAGS_RELEASE -= -fomit-frame-pointer
    QMAKE_CXXFLAGS_RELEASE -= -fomit-frame-pointer
  }

  staticlib {
    DESTDIR = $$PREFIX_LIB
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }
}

win32-msvc2005|win32-msvc2008|win32-msvc2010 {

  profile {
    # put debug symbols into release build .pdb so that CodeAnalyst shows
    # functions and source code along with assembly
    CONFIG *= release
    OPTFLAGS *= -Zi -DEBUG
    QMAKE_LFLAGS *= -DEBUG
  }

  release {
    OPTFLAGS =
    DEFINES *= NDEBUG
  }

  # msvc intrinsics for SSE are incomplete, disable

  sse2 {
    DEFINES += ARCH_SSE2
    intel32:OPTFLAGS += -arch:SSE2
  }

  staticlib {
    CONFIG += create_prl
  } else {
    CONFIG += link_prl
  }

  QMAKE_CFLAGS =
  QMAKE_CXXFLAGS =
  QMAKE_CXXFLAGS_RELEASE = -MD
  QMAKE_CFLAGS_RELEASE = -MD
  QMAKE_CXXFLAGS_DEBUG = -MDd -Zi
  QMAKE_CFLAGS_DEBUG = -MDd -Zi
  BASEFLAGS = -wd4100

  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
  QMAKE_CFLAGS_RELEASE += $$OPTFLAGS
}

win32-icc {

  OPTFLAGS = -Os -QxSSE2

  release {
    DEFINES *= NDEBUG
  }

  # default for 32bit
  sse2 {
    DEFINES *= ARCH_SSE2
  }

  # default for 64bit
  sse3 {
    DEFINES *= ARCH_SSE3
    OPTFLAGS -= -arch:SSE2
    OPTFLAGS *= -arch:SSE3
  }

  staticlib {
    CONFIG += create_prl
  } else {
    CONFIG += link_prl
  }

  # remove deprecated option, automatically set by -QVc9
  QMAKE_CXXFLAGS -= -GX

  QMAKE_CFLAGS =
  QMAKE_CXXFLAGS =
  BASEFLAGS =

  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS -Qcxx-features
  QMAKE_CXXFLAGS_RELEASE = -MD
  QMAKE_CFLAGS_RELEASE = -MD
  QMAKE_CXXFLAGS_DEBUG = -MDd
  QMAKE_CFLAGS_DEBUG = -MDd
  QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
  QMAKE_CFLAGS_RELEASE += $$OPTFLAGS
}

DESTDIR = $$TARGET_LIB_DIR

HEADERS += predicates.h
SOURCES += predicates.c


















