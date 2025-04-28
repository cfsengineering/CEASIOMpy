#
# qmake settings for all projects
#

cgns {
  DEFINES     += HAVE_CGNS
  # INCLUDEPATH += $$PREFIX/Develop/cgns
}

minizip {
  DEFINES     += HAVE_MINIZIP
  # INCLUDEPATH += ../minizip
}

posix_threads {
  DEFINES += USE_PTHREADS
} else {
  DEFINES -= USE_PTHREADS
}

# system dependencies

linux-g++-32 {

  !isEmpty( LOCAL_GCC ) {
    QMAKE_CXX       = $$LOCAL_GCC/bin/g++
    QMAKE_CC        = $$LOCAL_GCC/bin/gcc
    QMAKE_LINK      = $$LOCAL_GCC/bin/g++
  }
  
  QMAKE_LFLAGS += -m32 -L/usr/lib -L/usr/local/lib -L$$PREFIX/lib
  BASEFLAGS = -m32 
  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS --std=c99
  QMAKE_CXXFLAGS = $$BASEFLAGS

  PREFIX_LIB = $$PREFIX/lib
  
  INCLUDEPATH += /usr/include/GL
  
  release {
    DEFINES  += NDEBUG
    OPTFLAGS  = -O3 -fomit-frame-pointer -funroll-loops \
                -march=pentium4 -msse2 -mfpmath=sse \
                -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }  
  
  profile {
    DEFINES  += NDEBUG
    OPTFLAGS = -g -pg -O2 -funroll-loops \
               -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -pg
  }

  rpm {
    CONFIG       -= openmp sse3
    CONFIG       += localqt
  }
  
  staticlib {
    DESTDIR = $$PREFIX/lib
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  openmp {
    QMAKE_CFLAGS += -fopenmp
    QMAKE_CXXFLAGS += -fopenmp
    QMAKE_LFLAGS += -fopenmp
  }

  sse2 {
    DEFINES += ARCH_SSE2
    QMAKE_CFLAGS += -march=k8 -msse2
    QMAKE_CXXFLAGS += -march=k8 -msse2
  }

  sse3 {
    DEFINES += ARCH_SSE3
    QMAKE_CFLAGS += -march=core2 -msse3
    QMAKE_CXXFLAGS += -march=core2 -msse3
  }

  warn_on {
    QMAKE_CFLAGS += -Wshadow
    QMAKE_CXXFLAGS += -Wshadow
  }
}

linux-g++-64 {

  !isEmpty( LOCAL_GCC ) {
    QMAKE_CXX       = $$LOCAL_GCC/bin/g++
    QMAKE_CC        = $$LOCAL_GCC/bin/gcc
    QMAKE_LINK      = $$LOCAL_GCC/bin/g++
  }

  DEFINES      += HAVE_TR1 _LP64
  QMAKE_LFLAGS += -L/usr/local/lib64 -L$$PREFIX/lib
  BASEFLAGS     = -m64 
              
  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS --std=c99
  QMAKE_CXXFLAGS = $$BASEFLAGS
  INCLUDEPATH += /usr/include/GL
  
  PREFIX_LIB = $$PREFIX/lib64

  release {
    DEFINES      += NDEBUG
    OPTFLAGS      = -O3 -funroll-loops \
                    -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }  
  
  profile {
    DEFINES        += NDEBUG
    OPTFLAGS        = -g -pg -O2 -funroll-loops \
                      -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -pg
  }

  rpm {
    CONFIG       -= openmp sse3
    CONFIG       += localqt
  }
  
  staticlib {
    DESTDIR = $$PREFIX/lib64
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  openmp {
    QMAKE_CFLAGS += -fopenmp
    QMAKE_CXXFLAGS += -fopenmp
    QMAKE_LFLAGS += -fopenmp
  }

  sse2 {
    DEFINES += ARCH_SSE2
    QMAKE_CFLAGS += -march=k8 -msse2
    QMAKE_CXXFLAGS += -march=k8 -msse2
  }

  sse3 {
    DEFINES += ARCH_SSE3
    QMAKE_CFLAGS += -march=core2 -msse3
    QMAKE_CXXFLAGS += -march=core2 -msse3
  }

  warn_on {
    #QMAKE_CFLAGS += -Wshadow
    #QMAKE_CXXFLAGS += -Wshadow
  }
}

# fail-safe configuration

linux-g++ {

  QMAKE_LFLAGS += -L/usr/local/lib -L$$PREFIX/lib
              
  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS --std=c99
  QMAKE_CXXFLAGS = $$BASEFLAGS
  INCLUDEPATH += /usr/include/GL
  
  release {
    DEFINES      += NDEBUG 
    OPTFLAGS      = -O3 -funroll-loops \
                    -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }    
  
  staticlib {
    DESTDIR = $$PREFIX/lib
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }
}

linux-icc {

  PREFIX_LIB = $$PREFIX/lib64

# DEFINES      += HAVE_TETGEN
  QMAKE_LFLAGS += -L/usr/local/lib64 -L$$PREFIX_LIB
  BASEFLAGS     = 
              
  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS -std=c99
  QMAKE_CXXFLAGS = $$BASEFLAGS
  INCLUDEPATH += /usr/include/GL
  
  release {
    DEFINES      += NDEBUG ARCH_SSE2
# OPTFLAGS      = -O3 -xT -ip -no-prec-div -ansi-alias -unroll-aggressive
    OPTFLAGS    = -O3 -xHost -no-prec-div -ip -ansi-alias -unroll-aggressive
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }  
  
  profile {
    DEFINES      += NDEBUG
    OPTFLAGS      = -g -p -O2 -xT -no-prec-div 
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -p
  }
  
  staticlib {
    QMAKE_CFLAGS_STATIC_LIB    -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  openmp {
    QMAKE_CFLAGS += -openmp
    QMAKE_CXXFLAGS += -openmp
    QMAKE_LFLAGS += -openmp
  }

  sse2 {
    DEFINES += ARCH_SSE2
  }

  sse3 {
    DEFINES += ARCH_SSE3
  }
}

macx {

# switch between 32/64 bit compilation here
  CONFIG += osx32
  
  QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.4
  BASEFLAGS = 
  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS --std=c99
  QMAKE_CXXFLAGS = $$BASEFLAGS
 
  message($$CONFIG)

  osx64 {
    message("Mac OS X x86_64")

    # Mac OS X 10.5 has gcc 4.2
    QMAKE_CXX       = g++-4.2
    QMAKE_CC        = gcc-4.2
    QMAKE_LINK      = g++-4.2

    DEFINES += _LP64
    QMAKE_CXXFLAGS += "-arch x86_64" -march=core2
    QMAKE_CFLAGS += "-arch x86_64" -march=core2
    QMAKE_LFLAGS += "-arch x86_64" -L/usr/local/lib64

    PREFIX_LIB = $$PREFIX/lib64
    QMAKE_LFLAGS += -L/usr/local/lib64 -L$$PREFIX_LIB
  }
  
  osx32 {
    message("Mac OS X i386")
    PREFIX_LIB = $$PREFIX/lib
    QMAKE_CXXFLAGS += "-arch i386" -march=core2 -mfpmath=sse
    QMAKE_CFLAGS += "-arch i386" -march=core2 -mfpmath=sse
    QMAKE_LFLAGS += "-arch i386" -L/usr/local/lib -L$$PREFIX_LIB
  }
 
  release {
    DEFINES  += NDEBUG
    OPTFLAGS  = -O3 -fomit-frame-pointer -funroll-loops \
                -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }  
  
  profile {
    DEFINES  += NDEBUG
    OPTFLAGS = -g -pg -O2 -funroll-loops \
               -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -pg
  }
  
  staticlib {
    DESTDIR = $$PREFIX_LIB
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  openmp {
    QMAKE_CFLAGS += -fopenmp
    QMAKE_CXXFLAGS += -fopenmp
    QMAKE_LFLAGS += -fopenmp
  }

  sse2 {
    DEFINES += ARCH_SSE2
    QMAKE_CFLAGS += -march=core2 -msse2
  }

  sse3 {
    DEFINES += ARCH_SSE3
    QMAKE_CFLAGS += -march=core2 -msse3
  }

  CONFIG += sse3
}

win32-g++ {

  PREFIX_LIB = $$PREFIX/lib

  QMAKE_LFLAGS += -m32 -L$$PREFIX_LIB
  BASEFLAGS = -m32

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =

  # prevent windows.h from defining all kinds of generic
  # names as macros
  DEFINES += NOMINMAX

  release {
    OPTFLAGS  = -O2 -DNDEBUG -funroll-loops -fomit-frame-pointer \
                -march=pentium4 -mtune=generic -ffinite-math-only -fno-math-errno
  }

  profile {
    OPTFLAGS  = -O2 -DNDEBUG -funroll-loops  \
                -march=i686 -mtune=core2 -ffinite-math-only -fno-math-errno
    BASEFLAGS += -g -pg
    QMAKE_LFLAGS   += -pg
  }

  QMAKE_CFLAGS = $$BASEFLAGS --std=c99
  QMAKE_CXXFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
  QMAKE_CFLAGS_RELEASE += $$OPTFLAGS

  staticlib {
    DESTDIR = $$PREFIX_LIB
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

    # the GNU OpenMP implementation is built on top of
    # the pthread library, so we need to use pthreads
  openmp {
    CONFIG += posix_threads
    QMAKE_CFLAGS += -fopenmp
    QMAKE_CXXFLAGS += -fopenmp
    QMAKE_LFLAGS += -fopenmp
  }

  sse2 {
    DEFINES += ARCH_SSE2
    QMAKE_CFLAGS += -msse2
  }

  sse3 {
    DEFINES += ARCH_SSE3
    QMAKE_CFLAGS += -msse3
  }  
}

win32-msvc2005 | win32-msvc2008 {

  PREFIX_LIB=$$PREFIX"/lib"

  CONFIG += stl rtti exceptions

  # prevent windows.h from defining all kinds of generic
  # names as macros 
  DEFINES += NOMINMAX

  # Note : compiler options beyond -O2 switched off
  # as one of them leads to crash when loading model in vzm
  # Make sure to recompile *all* static libs when changing
  # anything here; the msvc build system is extremely fragile  

  release {
    DEFINES += NDEBUG
    #OPTFLAGS = -Ox
  }

  sse3 {
    #DEFINES += ARCH_SSE3
    #OPTFLAGS += -arch:SSE2
  }

  sse2 {
    #DEFINES += ARCH_SSE2
    #OPTFLAGS += -arch:SSE2
  }

  openmp {
    # disable for the moment
    #QMAKE_CFLAGS += -openmp
    #QMAKE_CXXFLAGS += -openmp
  }

  staticlib {
    CONFIG += create_prl
  } else {
    CONFIG += link_prl
  }

  fastlapack | reflapack {
     LIBS += -llapack_win32 -lblas_win32
  }

  QMAKE_CFLAGS += -EHsc
  QMAKE_CXXFLAGS += -EHsc
  #QMAKE_CFLAGS_RELEASE = $$OPTFLAGS
  #QMAKE_CXXFLAGS_RELEASE = $$OPTFLAGS
}
