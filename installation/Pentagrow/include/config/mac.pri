#
# Determine OSX version
#    Mac OS X 10.6 -> DARWIN_VERSION = 10
#    Mac OS X 10.7 -> DARWIN_VERSION = 11
#    Mac OS X 10.8 -> DARWIN_VERSION = 12
#    Mac OS X 10.9 -> DARWIN_VERSION = 13
#    Mac OS X 10.9 -> DARWIN_VERSION = 14
#
DARWIN_VERSION = $$system(uname -r |  cut -d "." -f 1)

#SDK_SEARCHPATH = /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/
SDK_SEARCHPATH = /Library/Developer/CommandLineTools/SDKs/

exists($$SDK_SEARCHPATH/MacOSX.sdk) {
    message("Targeting default SDK")
    QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.14
    MAC_SDKROOT = $$SDK_SEARCHPATH/MacOSX.sdk
    QMAKE_MAC_SDK = macosx10.14
}

isEmpty(MAC_SDKROOT) {
exists($$SDK_SEARCHPATH/MacOSX10.7.sdk) {
    message("Targeting OS X 10.7")
    QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.7
    MAC_SDKROOT = $$SDK_SEARCHPATH/MacOSX10.7.sdk
    QMAKE_MAC_SDK = macosx10.7
}
}

isEmpty(MAC_SDKROOT) {
exists($$SDK_SEARCHPATH/MacOSX10.8.sdk) {
    message("Targeting OS X 10.8")
    QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.8
    MAC_SDKROOT = $$SDK_SEARCHPATH/MacOSX10.8.sdk
    QMAKE_MAC_SDK = macosx10.8
}
}

isEmpty(MAC_SDKROOT) {
exists($$SDK_SEARCHPATH/MacOSX10.9.sdk) {
    message("Targeting OS X 10.9")
    QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.9
    MAC_SDKROOT = $$SDK_SEARCHPATH/MacOSX10.9.sdk
    QMAKE_MAC_SDK = macosx10.9
}
}

isEmpty(MAC_SDKROOT) {
exists($$SDK_SEARCHPATH/MacOSX10.11.sdk) {
    message("Targeting OS X 10.11")
    QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.9
    MAC_SDKROOT = $$SDK_SEARCHPATH/MacOSX10.11.sdk
    QMAKE_MAC_SDK = macosx10.11
}
}

isEmpty(MAC_SDKROOT) {
exists($$SDK_SEARCHPATH/MacOSX10.12.sdk) {
    message("Targeting OS X 10.12")
    QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.9
    MAC_SDKROOT = $$SDK_SEARCHPATH/MacOSX.sdk
    QMAKE_MAC_SDK = macosx10.12
}
}

MAC_FRAMEWORKS = $$MAC_SDKROOT/System/Library/Frameworks

#
# Detect and configure 3rd-party components
#

TARGET_LIB_DIR = $$PREFIX/lib64

# F*cking fortran runtime disappears with each update
CONFIG += no-mesquite no-arpack

# MESQUITE
!no-mesquite {
    exists(/opt/mesquite) {
        message("Configured with MESQUITE")
        CONFIG *= mesquite
        MESQUITE_PREFIX = /opt/mesquite
        DEFINES *= HAVE_MESQUITE
        INCLUDEPATH *= $$MESQUITE_PREFIX/include
        LIBS += -L$$MESQUITE_PREFIX/lib -lmesquite
    }
}

# switch off CGNS3 for now
CONFIG += no-cgns3

# CGNS 3.x
!no-cgns3 {
  exists(/usr/local/lib/libcgns.a) {
    message("Configured for system CGNS3")
    CONFIG *= system_cgns3
    DEFINES *= GENUA_SYSTEM_CGNS3
    INCLUDEPATH *= /usr/local/include
    LIBS *= /usr/local/lib/libcgns.a
    LIBS *= /usr/local/lib/libhdf5.a
    LIBS *= /usr/local/lib/libsz.a
  }
}

# standard os installs of netcdf link to HDF5, openssl etc. which lead to long
# dependency chains and are utterly unecessary because the TAU format only uses
# netcdf3 anyway. therefore, compile netcdf locally with
#
# ./configure --prefix=$HOME --disable-shared --disable-netcdf-4 --disable-dap
#
!no-netcdf {
    exists($(HOME)/lib/libnetcdf.a) {
        message("Configured for NetCDF in $(HOME)/lib")
        CONFIG *= netcdf
        DEFINES *= HAVE_NETCDF
        INCLUDEPATH += $(HOME)/include
        LIBS += $(HOME)/lib/libnetcdf.a
    } else:exists(/usr/local/lib/libnetcdf.a) {
        message("Configured for NetCDF in /usr/local/lib")
        CONFIG *= netcdf
        DEFINES *= HAVE_NETCDF
        INCLUDEPATH *= /usr/local/include
        LIBS *= /usr/local/lib/libnetcdf.a
        LIBS *= /usr/local/lib/libhdf5_hl.a
        LIBS *= /usr/local/lib/libhdf5.a
        LIBS *= /usr/local/lib/libsz.a
    }
}

!no-hdf {
    exists(/usr/local/lib/libhdf5_hl.a) {
        message("Configured for HDF5 in /usr/local/lib/")
        CONFIG *= hdf5
        DEFINES *= HAVE_HDF5
        INCLUDEPATH += $(HOME)/include
        LIBS *= /usr/local/lib/libhdf5_hl.a
        LIBS *= /usr/local/lib/libhdf5.a
        LIBS *= /usr/local/lib/libsz.a -lz
    }
}

# thread building blocks
!no-tbb {
    exists(/usr/local/include/tbb/parallel_invoke.h) {
        message("Detected TBB")
        DEFINES += HAVE_TBB
        INCLUDEPATH *= /usr/local/include/
        LIBS += -L/usr/local/lib -ltbb -ltbbmalloc
    }
}

# check whether spooles is available
!no-spooles {
    exists(../spooles/SPOOLES.h) {
        CONFIG *= spooles
        message(Detected SPOOLES)
        DEFINES += HAVE_SPOOLES
        CONFIG(debug, debug|release) {
            LIBS += -lspooles # -lspooles_debug
        } else {
            LIBS += -lspooles
        }
    }
}

# find suite-sparse, implies GPL
!no-spqr {
    message(Looking in $$TARGET_LIB_DIR)
    exists($$TARGET_LIB_DIR/libspqr.a) {
      CONFIG += suite-sparse spqr lapack
      message(Detected static SuiteSparse)
      DEFINES += HAVE_SPQR HAVE_UMFPACK HAVE_CHOLMOD
      INCLUDEPATH *= $$TARGET_LIB_DIR/../include
      LIBS += $$TARGET_LIB_DIR/libspqr.a $$TARGET_LIB_DIR/libumfpack.a \
              $$TARGET_LIB_DIR/libcholmod.a $$TARGET_LIB_DIR/libsuitesparseconfig.a \
              $$TARGET_LIB_DIR/libccolamd.a $$TARGET_LIB_DIR/libcolamd.a \
              $$TARGET_LIB_DIR/libcamd.a $$TARGET_LIB_DIR/libamd.a -ltbb
    } else {
      exists(/usr/local/include/SuiteSparseQR.hpp) {
          CONFIG += suite-sparse spqr lapack
          message(Detected SuiteSparse in /usr/local)
          DEFINES += HAVE_SPQR HAVE_UMFPACK HAVE_CHOLMOD
          INCLUDEPATH *= /usr/local/include
          LIBS += -lspqr -lumfpack -lcholmod -lsuitesparseconfig -lccolamd -lcolamd -lcamd -lamd -ltbb
      }
    }
}


# find FFTW3, implies GPL
!no-fftw {
    exists(/usr/local/include/fftw3.h) {
        CONFIG += fftw3
        message(Detected FFTW3)
        DEFINES += HAVE_FFTW3
        INCLUDEPATH *= /usr/local/include
        LIBS += -lfftw3
    }
}

# find locally installed nlopt
!no-nlopt {
  exists(/usr/local/opt/nlopt/lib/libnlopt_cxx.a) {
    message(Detected NLopt in /usr/local)
    CONFIG *= nlopt
    DEFINES += HAVE_NLOPT
    INCLUDEPATH += /usr/local/opt/nlopt/include/
    LIBS += /usr/local/opt/nlopt/lib/libnlopt_cxx.a
  }
}

# look for arpack
# NOTE: Must use ARPACK >= 3.2.0, earlier versions contain an
# ordering bug which yields the wrong eigenvalues
!no-arpack {
  exists($(HOME)/lib/libarpack.2.dylib) {
      message(Detected ARPACK in $$(HOME)/lib/)
      CONFIG *= arpack lapack
      DEFINES += HAVE_ARPACK
      LIBS += $(HOME)/lib/libarpack.2.dylib
  } else {
    exists(/usr/local/lib/libarpack.a) {
      message(Detected ARPACK in /usr/local)
      CONFIG *= arpack lapack
      DEFINES += HAVE_ARPACK
      LIBS += -larpack
    }
  }
}

# look for metis
!no-metis {
  exists(/usr/local/include/metis.h) {
      message(Detected METIS in /usr/local/)
      CONFIG += metis
      DEFINES += HAVE_METIS
      INCLUDEPATH *= /usr/local/include/
      QMAKE_LFLAGS *= -L/usr/local/lib
      LIBS += -lmetis
  } else {
    exists(/usr/local/opt/metis4/include/metis.h) {
      message(Detected METIS-4 in /usr/local/opt)
      CONFIG += metis4
      DEFINES += HAVE_METIS=4
      INCLUDEPATH *= /usr/local/opt/metis4/include/
      LIBS += /usr/local/opt/metis4/lib/libmetis.dylib
    }
  }
}

# Find the 3DConnexion SDK
SDK_3DCX=/Library/Frameworks/3DconnexionClient.framework
exists($$SDK_3DCX/Headers/ConnexionClientAPI.h) {
  contains(QT, gui) {
    message("Configured for 3DConnexion SDK")
    CONFIG *= spacenav
    DEFINES += HAVE_SPACENAV
    INCLUDEPATH += $$SDK_3DCX/Headers
    LIBS += -F/Library/Frameworks -weak_framework 3DConnexionClient
  }
}

macx-clang {

  message($$CONFIG)

  !no-clang-omp {
    exists(/usr/local/opt/libomp) {
      INCLUDEPATH += /usr/local/opt/libomp/include
      QMAKE_LFLAGS += -L/usr/local/opt/libomp/lib
      LIBS += -lomp
      BASEFLAGS += -Xpreprocessor -fopenmp
    }
  }

  # check whether MKL is installed; if so, enable MKL support
  !no-mkl {
    exists(/opt/intel/mkl/lib/libmkl_core.a) {
      CONFIG *= mklpardiso
      message(Using MKL)
    }
  }

  # warning enabled later
  CONFIG -= warn_on
  CONFIG += x86_64 target-64bit builtin_judy
  CONFIG *= avx

  BASEFLAGS += $$CFLAGS_LIBS
  BUILD_TAG = "clang-64"

  sse2 {
    DEFINES += ARCH_SSE2
    BASEFLAGS *= -march=k8 -mtune=corei7-avx2 -msse2
  }

  sse3 {
    DEFINES += ARCH_SSE3
    BASEFLAGS *= -march=core2 -mtune=corei7-avx2 -msse3
  }

  sse41 {
    DEFINES += ARCH_SSE41
    BASEFLAGS *= -march=core2 -mtune=corei7-avx2 -msse4.1
  }

  avx {
    DEFINES += ARCH_AVX
    BASEFLAGS *= -march=corei7-avx -mtune=corei7-avx2 -mavx
  }

  avx2 {
    DEFINES += ARCH_AVX2
    BASEFLAGS *= -march=core-avx2 -mavx2 -ffp-contract=fast
  }

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS

  QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.13

  DEFINES += _LP64
  QMAKE_CXXFLAGS += "-arch x86_64" -std=c++11 -stdlib=libc++
  QMAKE_CFLAGS += "-arch x86_64"
  QMAKE_LFLAGS += "-arch x86_64" -std=c++11 -stdlib=libc++

  # switch off clang's warnings for plain c code (which is not ours, and usually
  # cgns and judy trigger hundreds of warnings (pointer-to-int casts etc))
  QMAKE_CFLAGS *= -w
  QMAKE_CXXFLAGS *= -W -Wall -Wno-unknown-pragmas -Werror=return-type

  QMAKE_LFLAGS += -L$$TARGET_LIB_DIR

  release {
    OPTFLAGS  = -O3 -DNDEBUG -fno-math-errno -ffinite-math-only \
                -fno-stack-protector
    hostopt {
      OPTFLAGS += -march=native
    }
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }

  profile {
    #PROFFLAGS = -O1 -g -fsanitize=address -fsanitize=undefined -fno-optimize-sibling-calls -fno-omit-frame-pointer
    #PROFFLAGS = -O2 -fno-math-errno -g -fno-omit-frame-pointer
    PROFFLAGS = -g -O2 -fno-math-errno -fno-omit-frame-pointer -DNDEBUG
    QMAKE_CXXFLAGS += $$PROFFLAGS
    QMAKE_CFLAGS   += $$PROFFLAGS
    QMAKE_CFLAGS_RELEASE -= -O3 -DNDEBUG -fno-stack-protector
    QMAKE_CXXFLAGS_RELEASE -= -O3 -DNDEBUG -fno-stack-protector
    # QMAKE_LFLAGS   += -g -fsanitize=address -fsanitize=undefined # -gline-tables-only
  }

  sanitize {
    message("configured for clang address sanitizer")
    SANFLAGS = -O1 -g -fsanitize=address -fsanitize=undefined -fno-optimize-sibling-calls -fno-omit-frame-pointer
    QMAKE_CXXFLAGS += $$SANFLAGS
    QMAKE_CFLAGS   += $$SANFLAGS
    QMAKE_LFLAGS   += -g -fsanitize=address -fsanitize=undefined
  }

  staticlib {
    DESTDIR = $$PREFIX_LIB
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  mpi {
    DEFINES += HAVE_MPI
    QMAKE_CXX = mpicxx
    QMAKE_CC = mpicc
    QMAKE_LINK_C = $$QMAKE_CC
    QMAKE_LINK_C_SHLIB = $$QMAKE_CC
    QMAKE_LINK       = $$QMAKE_CXX
    QMAKE_LINK_SHLIB = $$QMAKE_CXX
  }

  mklpardiso | mkl {
    CONFIG -= reflapack
    CONFIG -= fastlapack
    ICCROOT = /opt/intel
    MKLROOT = $$ICCROOT/mkl
    QMAKE_LFLAGS += -L$$ICCROOT/lib -DMKL_DIRECT_CALL
    QMAKE_LIBS +=  $$MKLROOT/lib/libmkl_intel_lp64.a \
                   $$MKLROOT/lib/libmkl_core.a \
                   $$MKLROOT/lib/libmkl_intel_thread.a \
                   -liomp5 -ldl -lpthread -lm
    DEFINES += HAVE_MKL_PARDISO HAVE_MKL MKL_DIRECT_CALL
    INCLUDEPATH *= $$MKLROOT/include
  } else {

    reflapack | fastlapack {

      # openblas from brew is much too slow
#      exists(/usr/local/opt/openblas/lib/libopenblas.a) {
#        message("Detected OpenBLAS.")
#        LIBS += -L/usr/local/opt/openblas/lib -L/usr/local/opt/gcc/lib/gcc/5
#        LIBS += -lopenblas -lgfortran
#        INCLUDEPATH += /usr/local/opt/openblas/include
#      exists($$TARGET_LIB_DIR/libopenblas.dylib) {
#        message("Detected OpenBLAS.")
#        LIBS += -lopenblas
#        LIBS += `gfortran --print-file-name libgfortran.dylib`
#      } else {
        exists(/usr/local/lib/libvecLibFort.a) {
          LIBS += /usr/local/lib/libvecLibFort.a
        }
        LIBS +=  -framework Accelerate
#       }
    }
  }

  qglviewer {
    DEFINES *= QGLVIEWER_STATIC
    INCLUDEPATH *= ../QGLViewer
    CONFIG(debug, debug|release) {
      LIBS *= -lQGLViewer_debug
    } else {
      LIBS *= -lQGLViewer
    }
    QT += opengl xml
  }

  # linker flags: look for dylibs in ../lib ../Frameworks ../Libraries
  # do not forget to
  # install_name_tool -id @rpath/libblabla.dylib libblabla.dylib
  app_bundle {
    QMAKE_LFLAGS += '-Wl,-rpath,\'@loader_path/../Frameworks\' '
    QMAKE_LFLAGS += '-Wl,-rpath,\'@loader_path/../Libraries\' '
  } else {
    QMAKE_LFLAGS += '-Wl,-rpath,\'@loader_path/../Libraries\' '
    QMAKE_LFLAGS += '-Wl,-rpath,\'@loader_path/../lib\' '
  }

  # configuration for boost libs
  DEFINES += BOOST_THREAD_DONT_PROVIDE_INTERRUPTIONS BOOST_THREAD_VERSION=4
}

macx-icc {

  # architecture is set using
  # CONFIG x86 or x86_64
  BUILD_TAG = "icc-64"
  CONFIG += x86_64 tbb

  # use IPP-based zlib
  # CONFIG += ippz

  BASE_CFLAGS = -Wno-unknown-pragmas -use-clang-env
  BASE_CXXFLAGS = $$BASE_CFLAGS -std=c++11 -stdlib=libc++
  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASE_CFLAGS
  QMAKE_CXXFLAGS = $$BASE_CXXFLAGS

  message("Intel C++ on Mac OS X 64bit")
  CONFIG += openmp

  QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.7

  DEFINES += _LP64 BOOST_THREAD_USES_MOVE BOOST_THREAD_VERSION=4
  DEFINES += _LIBCPP_HAS_NO_ADVANCED_SFINAE  __USE_INTEL_ATOMICS
  # DEFINES += BOOST_ERROR_CODE_HEADER_ONLY
  # DEFINES += BOOST_CHRONO_DONT_PROVIDE_HYBRID_ERROR_HANDLING
  QMAKE_CXXFLAGS += "-arch x86_64" -wd63
  QMAKE_CFLAGS += "-arch x86_64"
  QMAKE_LFLAGS += "-arch x86_64" -std=c++11 -stdlib=libc++

  TARGET_LIB_DIR = $$PREFIX/lib64
  QMAKE_LFLAGS += -L$$TARGET_LIB_DIR

  # linker search paths for libiomp
  QMAKE_LFLAGS += '-Wl,-rpath,\'/opt/intel/lib\''

  # do not use "-ansi-alias" with complex number arithmetic, there is either
  # aliasing in phi or an aliasing analysis bug in icc <= 12.1.6 (at least)

  profile {
    DEFINES *= NDEBUG
    OPTFLAGS  = -g -O2 -xHost -fp-model fast -rcd \
                -complex-limited-range
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }

  release {
    DEFINES *= NDEBUG
    !profile {
    OPTFLAGS  = -O3 -fp-model fast -rcd -ip -finline \
                -complex-limited-range -use-intel-optimized-headers
 #               -qopt-report=5
    hostopt {
        OPTFLAGS += -xHost
    }
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS -diag-disable cpu-dispatch
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS -diag-disable cpu-dispatch
    }
  }

  ipo {
    QMAKE_CXXFLAGS_RELEASE += -ipo
    QMAKE_CFLAGS_RELEASE   += -ipo
    QMAKE_LFLAGS   += -ipo
  }

  staticlib {
    DESTDIR = $$PREFIX_LIB
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  mpi {
    DEFINES += HAVE_MPI
    QMAKE_CXX = mpicxx
    QMAKE_CC = mpicc
    QMAKE_LINK_C = $$QMAKE_CC
    QMAKE_LINK_C_SHLIB = $$QMAKE_CC
    QMAKE_LINK       = $$QMAKE_CXX
    QMAKE_LINK_SHLIB = $$QMAKE_CXX
  }

  openmp {
    QMAKE_CFLAGS += -openmp
    QMAKE_CXXFLAGS += -openmp
    QMAKE_LFLAGS += -openmp
  } else {
    QMAKE_CFLAGS += -openmp-stubs
    QMAKE_CXXFLAGS += -openmp-stubs
    QMAKE_LFLAGS += -openmp-stubs
  }

  avx2 {
    CONFIG -= avx sse42 sse3
    DEFINES += ARCH_AVX2
    QMAKE_CXXFLAGS += -xCORE-AVX2
  }

  avx {
    CONFIG -= sse42 sse3
    DEFINES += ARCH_AVX
    QMAKE_CXXFLAGS += -xAVX
  }

  sse42 {
    CONFIG -= sse3
    DEFINES += ARCH_SSE42
    QMAKE_CXXFLAGS += -xSSE4.2
  }

  sse2 | sse3 {
    DEFINES += ARCH_SSE3
    QMAKE_CXXFLAGS += -xSSSE3
  }

  fftw3 {
    DEFINES += HAVE_FFTW3
    INCLUDEPATH *= /usr/local/include
  }

  mklpardiso {
    DEFINES += HAVE_MKL_PARDISO
    MKLROOT = /opt/intel/mkl
    INCLUDEPATH *= $$MKLROOT/include
  }

  qglviewer {
    DEFINES *= QGLVIEWER_STATIC
    INCLUDEPATH *= ../QGLViewer
    CONFIG(debug, debug|release) {
      LIBS *= -lQGLViewer_debug
    } else {
      LIBS *= -lQGLViewer
    }
    QT += opengl xml
  }

  app_bundle {
    QMAKE_LFLAGS += '-Wl,-rpath,\'@loader_path/../Frameworks\' '
    QMAKE_LFLAGS += '-Wl,-rpath,\'@loader_path/../Libraries\' '
  } else {
    QMAKE_LFLAGS += '-Wl,-rpath,\'@loader_path/../Libraries\' '
    QMAKE_LFLAGS += '-Wl,-rpath,\'@loader_path/../lib\' '
  }
}

macx-g++ | macx-g++42 {

  exists(/usr/local/bin/g++-4.2) {
    QMAKE_CC = /usr/local/bin/gcc-4.2
    QMAKE_CXX = /usr/local/bin/g++-4.2
    QMAKE_LINK = /usr/local/bin/g++-4.2
    INCLUDEPATH *= /usr/include/c++/4.2.1
  }

  # architecture is set using
  # CONFIG x86 or x86_64
  CONFIG += x86_64 target-64bit
  DEFINES += BOOST_THREAD_USES_MOVE

  QMAKE_MACOSX_DEPLOYMENT_TARGET = 10.7

  BASEFLAGS = $$CFLAGS_LIBS
  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS

  CONFIG(x86_64) {

    BUILD_TAG = "gcc-64"
    CONFIG += sse3

    DEFINES += _LP64
    QMAKE_CXXFLAGS += "-arch x86_64" -march=core2
    QMAKE_CFLAGS += "-arch x86_64" -march=core2 -fno-strict-aliasing
    QMAKE_LFLAGS += "-arch x86_64"

    gcc47 {
        QMAKE_CXXFLAGS += -mtune=corei7-avx
        QMAKE_CXXFLAGS_X86_64 -= -Xarch_x86_64
        QMAKE_CFLAGS += -mtune=corei7-avx
        QMAKE_CFLAGS_X86_64 -= -Xarch_x86_64
        QMAKE_LFLAGS -= -Xarch_x86_64
        CONFIG *= posix_threads
        DEFINES *= USE_PTHREADS
    }

    TARGET_LIB_DIR = $$PREFIX/lib64
    QMAKE_LFLAGS += -L$$TARGET_LIB_DIR
  }

  CONFIG(x86) {
    BUILD_TAG = "gcc-32"
    message("Mac OS X i386")
    TARGET_LIB_DIR = $$PREFIX/lib
    QMAKE_CXXFLAGS += "-arch i386" -march=core2 -mfpmath=sse
    QMAKE_CFLAGS += "-arch i386" -march=core2 -mfpmath=sse -fno-strict-aliasing
    QMAKE_LFLAGS += "-arch i386" -L/usr/local/lib -L$$TARGET_LIB_DIR
  }

  release {
    OPTFLAGS  = -O3 -DNDEBUG -fomit-frame-pointer -funroll-loops \
                -fno-math-errno -ffinite-math-only \
                -falign-loops=16
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS -ftree-vectorize
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS
  }

  profile {
    PROFFLAGS = -g -pg -O2
    QMAKE_CXXFLAGS += $$PROFFLAGS
    QMAKE_CFLAGS   += $$PROFFLAGS
    QMAKE_CFLAGS_RELEASE -= -O3 -fomit-frame-pointer
    QMAKE_CXXFLAGS_RELEASE -= -O3 -fomit-frame-pointer
    QMAKE_LFLAGS   += -pg
  }

  staticlib {
    DESTDIR = $$PREFIX_LIB
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  mpi {
    DEFINES += HAVE_MPI
    QMAKE_CXX = mpicxx
    QMAKE_CC = mpicc
    QMAKE_LINK_C = $$QMAKE_CC
    QMAKE_LINK_C_SHLIB = $$QMAKE_CC
    QMAKE_LINK       = $$QMAKE_CXX
    QMAKE_LINK_SHLIB = $$QMAKE_CXX
  }

  openmp {
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

  fftw3 {
    DEFINES += HAVE_FFTW3
    INCLUDEPATH *= /usr/local/include
  }

  # when linking to MKL using gcc, the sequential version must be used
  # since otherwise, the Intel OpenMP runtime will clash with libgomp.
  mklpardiso | mkl {
    CONFIG -= reflapack fastlapack
    ICCROOT = /opt/intel
    MKLROOT = $$ICCROOT/mkl
    QMAKE_LFLAGS += -L$$ICCROOT/lib
    QMAKE_LIBS += $$MKLROOT/lib/libmkl_intel_lp64.a \
                  $$MKLROOT/lib/libmkl_sequential.a \
                  $$MKLROOT/lib/libmkl_core.a -lpthread -lm
    DEFINES += HAVE_MKL_PARDISO
    INCLUDEPATH *= $$MKLROOT/include
  }

  reflapack | fastlapack {
    exists(/usr/local/lib/libvecLibFort.a) {
      LIBS += /usr/local/lib/libvecLibFort.a
    }
    LIBS +=  -framework Accelerate
  }

  sparsehash {
    DEFINES += USE_GOOGLE_SPARSEHASH
    INCLUDEPATH += /usr/local/include
  }

  qglviewer {
    DEFINES *= QGLVIEWER_STATIC
    INCLUDEPATH *= ../QGLViewer
    CONFIG(debug, debug|release) {
      LIBS *= -lQGLViewer_debug
    } else {
      LIBS *= -lQGLViewer
    }
    QT += opengl xml
  }

  spacenav {
    DEFINES += HAVE_SPACENAV
    INCLUDEPATH += $$SDK_3DCX/Headers
    LIBS += -weak_framework 3DconnexionClient
  }
}

judy {
    DEFINES *= HAVE_JUDY
}

builtin_judy {
    INCLUDEPATH += ../genua/judy/src
}
