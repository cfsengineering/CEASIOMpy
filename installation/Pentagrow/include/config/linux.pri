
# standard os installs of netcdf link to HDF5, openssl etc. which lead to long
# dependency chains and are utterly unecessary because the TAU format only uses
# netcdf3 anyway. therefore, compile netcdf locally with
#
# ./configure --prefix=$HOME --disable-shared --disable-netcdf-4 --disable-dap
#
!no-netcdf {
    exists($(HOME)/lib64/libnetcdf.a) {
        message("Configured for NetCDF")
        CONFIG *= netcdf
        DEFINES *= HAVE_NETCDF
        INCLUDEPATH += $(HOME)/include
        LIBS += $(HOME)/lib64/libnetcdf.a
    }
}

# find FFTW3, implies GPL
!no-fftw {
    exists(/usr/include/fftw3.h) {
        CONFIG += fftw3
        message(Detected FFTW3)
        DEFINES += HAVE_FFTW3
        LIBS += -lfftw3
    }
}

# Intel MKL
!no-mkl {
    exists(/opt/intel/mkl/include/mkl_service.h) {
        message("Detected MKL")
        CONFIG += mkl mklpardiso
    }
}

# check whether spooles is available
!no-spooles {
    exists(../spooles/SPOOLES.h) {
        CONFIG *= spooles
        message(Detected SPOOLES)
        DEFINES += HAVE_SPOOLES
        LIBS += -lspooles
    }
}

# find suite-sparse, implies GPL
!no-spqr {

    # prefer locally installed version
    exists($(HOME)/lib64/libspqr.so) {
            CONFIG += suite-sparse spqr lapack 
            message(Detected local SuiteSparse)
            DEFINES += HAVE_SPQR HAVE_UMFPACK HAVE_CHOLMOD HAVE_METIS
            INCLUDEPATH *= $(HOME)/include/suitesparse 
            SSPDIR = $(HOME)/lib64/
            LIBS *= -L$$SSPDIR
            LIBS += $$SSPDIR/libspqr.so $$SSPDIR/libumfpack.so 
            LIBS += $$SSPDIR/libcholmod.so $$SSPDIR/libsuitesparseconfig.so
            LIBS += $$SSPDIR/libccolamd.so $$SSPDIR/libcolamd.so
            LIBS += $$SSPDIR/libcamd.so $$SSPDIR/libamd.so
            LIBS *= -lmetis
            LIBS *= -ltbb
    } else {
        exists(/usr/include/suitesparse/SuiteSparseQR.hpp) {
            CONFIG += suite-sparse spqr lapack
            message(Detected system SuiteSparse)
            DEFINES += HAVE_SPQR HAVE_UMFPACK HAVE_CHOLMOD
            INCLUDEPATH *= /usr/include/suitesparse
            LIBS += -lspqr -lumfpack -lcholmod -lsuitesparseconfig 
            LIBS += -lccolamd -lcolamd -lcamd -lamd
            LIBS *= -lmetis
            LIBS *= -ltbb
        }
    }
}

# find locally installed nlopt
!no-nlopt {
  exists($(HOME)/lib64/libnlopt_cxx.a) {
    message(Detected local NLopt)
    CONFIG *= nlopt
    DEFINES += HAVE_NLOPT
    INCLUDEPATH += $(HOME)/include
    LIBS += $(HOME)/lib64/libnlopt_cxx.a
  }
}

# look for system-wide metis
!no-metis {
  exists(/usr/include/metis.h) {
      message(Detected system METIS)
      CONFIG += metis
      DEFINES += HAVE_METIS
      LIBS += -lmetis
  }
}

# look for multithreded metis (experimental)
!no-mtmetis {
    exists($(HOME)/include/mtmetis.h) {
        message(Deteted MT-METIS)
        CONFIG *= mtmetis
        DEFINES += HAVE_MTMETIS
        LIBS += $(HOME)/lib/libmtmetis.a
    }
}

# look for static HDF5 libraries
!no-hdf {
  exists(/usr/include/hdf5_hl.h) {
      message(Detected system HDF5)
      CONFIG += hdf5
      DEFINES += HAVE_HDF5
      LIBS += /usr/lib64/libhdf5_hl.a /usr/lib64/libhdf5.a
  }
}

linux-g++ | linux-g++-64 {

  # thread building blocks
  !no-tbb {
    exists($(HOME)/include/tbb/parallel_invoke.h) {
    	message("Detected TBB in $HOME")
        DEFINES += HAVE_TBB
        INCLUDEPATH *= $(HOME)/include/
        LIBS += -L$(HOME)/lib64 -ltbb
    } else {
      exists(/usr/local/include/tbb/parallel_invoke.h) {
          message("Detected TBB in /usr/local")
          DEFINES += HAVE_TBB
          INCLUDEPATH *= /usr/local/include/
          LIBS += -L/usr/local/lib -ltbb
      } else {
        exists(/usr/include/tbb/parallel_invoke.h) {
            message("Detected system TBB")
            DEFINES += HAVE_TBB
            LIBS += -ltbb
        }
      }
    }
  }

  BUILD_TAG = "gcc-64"

  # default configuration on 64-bit Linux systems
  CONFIG += openmp target-64bit c++11

  # allow to override compiler using environment variable
  LOCAL_CC=$$(CC)
  !isEmpty(LOCAL_CC) {
    message("Using CC = " $$LOCAL_CC)
    QMAKE_CC   = $$LOCAL_CC
    QMAKE_LINK = $$LOCAL_CC
  }

  LOCAL_CXX=$$(CXX)
  !isEmpty(LOCAL_CXX) {
    message("Using CXX = " $$LOCAL_CXX)
    QMAKE_CXX  = $$LOCAL_CXX
    QMAKE_LINK = $$LOCAL_CXX
  }

  # use devtoolset-3 if present
  #exists(/opt/rh/devtoolset-3/root/usr/bin/g++) {
  #  LOCAL_GCC_PATH  = /opt/rh/devtoolset-3/root/usr/
  #}

  # detect devtoolset-2 on CentOS-6, which is needed for
  # a useable C++ 2011 compiler on that system
  exists(/opt/rh/devtoolset-2/root/usr/bin/g++) {
    LOCAL_GCC_PATH  = /opt/rh/devtoolset-2/root/usr/
  }
  exists(/opt/rh/devtoolset-4/root/usr/bin/g++) {
    LOCAL_GCC_PATH  = /opt/rh/devtoolset-4/root/usr/
  }

  !isEmpty( LOCAL_GCC_PATH ) {
    QMAKE_CXX       = $$LOCAL_GCC_PATH/bin/g++
    QMAKE_CC        = $$LOCAL_GCC_PATH/bin/gcc
    QMAKE_LINK      = $$LOCAL_GCC_PATH/bin/g++
  }

  !isEmpty( GCC_SUFFIX ) {
    QMAKE_CXX       = join("g++", $$GCC_SUFFIX)
    QMAKE_CC        = join("gcc", $$GCC_SUFFIX)
    QMAKE_LINK      = join("g++", $$GCC_SUFFIX)
    message("Using compiler: "$$QMAKE_CXX);
  }

  DEFINES      += HAVE_TR1 _LP64 BOOST_THREAD_USES_MOVE \
                  BOOST_SYSTEM_NO_DEPRECATED

  TARGET_LIB_DIR = $$PREFIX/lib64
  QMAKE_LFLAGS += -m64 -L/usr/local/lib64 -L/usr/lib64 -L$$TARGET_LIB_DIR
  BASEFLAGS     = -m64 -Wno-unknown-pragmas -Wno-deprecated-declarations -fext-numeric-literals

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS -Wno-sign-compare -Wno-unused-variable -Wno-unused-parameter -Wno-unknown-pragmas
  QMAKE_CXXFLAGS = $$BASEFLAGS -std=c++11 

  LIBS += -lrt

  # put executable path into library search path
  # to allow bundling of compiler libs
  QMAKE_LFLAGS += '-Wl,-rpath,\'\$$ORIGIN/../lib\''
  QMAKE_LFLAGS += '-Wl,-rpath,\'\$$ORIGIN/../lib64\''

  release {
    OPTFLAGS      = -DNDEBUG -O3 -funroll-loops \
                    -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS -Wno-sign-compare -Wno-unused-parameter
  }

  profile {
    OPTFLAGS        = -DNDEBUG -g -pg -O2 -funroll-loops -march=core2 \
                      -mtune=generic -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -pg
  }

  rpm {
    CONFIG       -= openmp sse41
    CONFIG       += localqt
  }

  staticlib {
    DESTDIR = $$PREFIX/lib64
    #QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    #QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  mpi {
    QMAKE_CXX = mpicxx
    QMAKE_CC = mpicc
    QMAKE_LINK_C = $$QMAKE_CC
    QMAKE_LINK_C_SHLIB = $$QMAKE_CC
    QMAKE_LINK       = $$QMAKE_CXX
    QMAKE_LINK_SHLIB = $$QMAKE_CXX
  }

  hostopt {
    CONFIG -= sse2 sse3
    QMAKE_CFLAGS *= -march=native
    QMAKE_CXXFLAGS *= -march=native
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

  sse41 {
    DEFINES += ARCH_SSE41
    QMAKE_CFLAGS += -march=core2 -mtune=corei7-avx -msse4.1
    QMAKE_CXXFLAGS += -march=core2 -mtune=corei7-avx -msse4.1
  }

  avx {
    DEFINES += ARCH_AVX
    QMAKE_CFLAGS += -march=corei7-avx -mavx
    QMAKE_CXXFLAGS += -march=corei7-avx -mavx
  }

  avx2 {
    DEFINES += ARCH_AVX2
    QMAKE_CFLAGS += -march=core-avx2 -mavx2
    QMAKE_CXXFLAGS += -march=core-avx2 -mavx2
  }

  warn_on {
    #QMAKE_CFLAGS += -Wshadow
    #QMAKE_CXXFLAGS += -Wshadow
  }

  # when linking to MKL using gcc, the sequential version must be used
  # since otherwise, the Intel OpenMP runtime will clash with libgomp.
  mklpardiso | mkl {

    CONFIG -= reflapack fastlapack
    ICCROOT = /opt/intel
    MKLROOT = $$ICCROOT/mkl
    QMAKE_LFLAGS += -L$$ICCROOT/lib/intel64
    message("MKL Root at:" $$MKLROOT)

    LIBS += -Wl,--start-group $$MKLROOT/lib/intel64/libmkl_intel_lp64.a \
            $$MKLROOT/lib/intel64/libmkl_core.a \
            $$MKLROOT/lib/intel64/libmkl_gnu_thread.a \
            -Wl,--end-group -ldl -lpthread -lm

#    # tbb-threaded version of MKL
#    LIBS += -Wl,--start-group \
#                  $$MKLROOT/lib/intel64/libmkl_intel_lp64.a \
#                  $$MKLROOT/lib/intel64/libmkl_core.a \
#                  $$MKLROOT/lib/intel64/libmkl_tbb_thread.a \
#                  -Wl,--end-group -ltbb -lpthread -lm

    DEFINES += HAVE_MKL_PARDISO HAVE_MKL
    INCLUDEPATH *= $$MKLROOT/include
  }

  reflapack | fastlapack {

    # fortan runtime can be specified in environment variable
    F90RNTM = $$(FORTRAN_RUNTIME)
    isEmpty(F90RNTM) {
        message("Fortran runtime environment variable not defined.")
        F90RNTM = `gfortran -m64 -print-file-name=libgfortran.a`
        message("Fortran runtime set:")
        message($$F90RNTM)
    }

    exists($(HOME)/lib64/libopenblas.so) {
        # prefer locally compiled OpenBLAS
        message(Using OpenBLAS in $(HOME)/lib64)
        LIBS *= $(HOME)/lib64/libopenblas.so 
        DEFINES += HAVE_OPENBLAS HAVE_LAPACK HAVE_LAPACKE
        INCLUDEPATH *= $(HOME)/include
    } else {
        # if there is no local OpenBLAS, check if there is a system version
        exists(/usr/lib64/libopenblas.so) | exists(/usr/lib/libopenblas.so) {
            message(Using OpenBLAS in /usr/lib64)
            DEFINES += HAVE_OPENBLAS HAVE_LAPACK
            LIBS += -llapack -lopenblas
        } else {
            LIBS += -llapack -lblas $$F90RNTM
        }
    }
  }

  qglviewer {
    DEFINES *= QGLVIEWER_STATIC
    INCLUDEPATH *= ../QGLViewer
    CONFIG(debug, debug|release) {
      LIBS *= -lQGLViewer
    } else {
      LIBS *= -lQGLViewer
    }
    QT += opengl xml
    LIBS += -lGLU
  }

  LIBS += -fPIC -lrt -lm -ldl
}

linux-g++-32 {

  # thread building blocks
  !no-tbb {
    exists($(HOME)/include/tbb/parallel_invoke.h) {
    	message("Detected TBB in $HOME")
        DEFINES += HAVE_TBB
        INCLUDEPATH *= $(HOME)/include/
        LIBS += -L$(HOME)/lib64 -ltbb
    } else {
      exists(/usr/local/include/tbb/parallel_invoke.h) {
          message("Detected TBB in /usr/local")
          DEFINES += HAVE_TBB
          INCLUDEPATH *= /usr/local/include/
          LIBS += -L/usr/local/lib -ltbb
      } else {
        exists(/usr/include/tbb/parallel_invoke.h) {
            message("Detected system TBB")
            DEFINES += HAVE_TBB
            LIBS += -ltbb
        }
      }
    }
  }

  BUILD_TAG = "gcc-32"

  # default configuration on 32-bit Linux systems
  CONFIG += openmp target-32bit c++11

  # allow to override compiler using environment variable
  LOCAL_CC=$$(CC)
  !isEmpty(LOCAL_CC) {
    message("Using CC = " $$LOCAL_CC)
    QMAKE_CC   = $$LOCAL_CC
    QMAKE_LINK = $$LOCAL_CC
  }

  LOCAL_CXX=$$(CXX)
  !isEmpty(LOCAL_CXX) {
    message("Using CXX = " $$LOCAL_CXX)
    QMAKE_CXX  = $$LOCAL_CXX
    QMAKE_LINK = $$LOCAL_CXX
  }

  # use devtoolset-3 if present
  #exists(/opt/rh/devtoolset-3/root/usr/bin/g++) {
  #  LOCAL_GCC_PATH  = /opt/rh/devtoolset-3/root/usr/
  #}

  # detect devtoolset-2 on CentOS-6, which is needed for
  # a useable C++ 2011 compiler on that system
  exists(/opt/rh/devtoolset-2/root/usr/bin/g++) {
    LOCAL_GCC_PATH  = /opt/rh/devtoolset-2/root/usr/
  }
  exists(/opt/rh/devtoolset-4/root/usr/bin/g++) {
    LOCAL_GCC_PATH  = /opt/rh/devtoolset-4/root/usr/
  }

  !isEmpty( LOCAL_GCC_PATH ) {
    QMAKE_CXX       = $$LOCAL_GCC_PATH/bin/g++
    QMAKE_CC        = $$LOCAL_GCC_PATH/bin/gcc
    QMAKE_LINK      = $$LOCAL_GCC_PATH/bin/g++
  }

  !isEmpty( GCC_SUFFIX ) {
    QMAKE_CXX       = join("g++", $$GCC_SUFFIX)
    QMAKE_CC        = join("gcc", $$GCC_SUFFIX)
    QMAKE_LINK      = join("g++", $$GCC_SUFFIX)
    message("Using compiler: "$$QMAKE_CXX);
  }

  DEFINES      += HAVE_TR1 BOOST_THREAD_USES_MOVE \
                  BOOST_SYSTEM_NO_DEPRECATED

  TARGET_LIB_DIR = $$PREFIX/lib
  QMAKE_LFLAGS += -m32 -L/usr/local/lib -L/usr/lib -L$$TARGET_LIB_DIR
  BASEFLAGS     = -m32 -Wno-unknown-pragmas -Wno-deprecated-declarations

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS -Wno-sign-compare -Wno-unused-variable -Wno-unused-parameter -Wno-unknown-pragmas
  QMAKE_CXXFLAGS = $$BASEFLAGS -std=c++11 

  LIBS += -lrt

  # put executable path into library search path
  # to allow bundling of compiler libs
  QMAKE_LFLAGS += '-Wl,-rpath,\'\$$ORIGIN/../lib\''

  release {
    OPTFLAGS      = -DNDEBUG -O3 -funroll-loops \
                    -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
    QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS -Wno-sign-compare -Wno-unused-parameter
  }

  profile {
    OPTFLAGS        = -DNDEBUG -g -pg -O2 -funroll-loops -march=core2 \
                      -mtune=generic -fno-math-errno -ffinite-math-only
    QMAKE_CXXFLAGS += $$OPTFLAGS
    QMAKE_CFLAGS   += $$OPTFLAGS
    QMAKE_LFLAGS   += -pg
  }

  rpm {
    CONFIG       -= openmp sse41
    CONFIG       += localqt
  }

  staticlib {
    DESTDIR = $$PREFIX/lib
    #QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    #QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }

  mpi {
    QMAKE_CXX = mpicxx
    QMAKE_CC = mpicc
    QMAKE_LINK_C = $$QMAKE_CC
    QMAKE_LINK_C_SHLIB = $$QMAKE_CC
    QMAKE_LINK       = $$QMAKE_CXX
    QMAKE_LINK_SHLIB = $$QMAKE_CXX
  }

  hostopt {
    CONFIG -= sse2 sse3
    QMAKE_CFLAGS *= -march=native
    QMAKE_CXXFLAGS *= -march=native
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

  sse41 {
    DEFINES += ARCH_SSE41
    QMAKE_CFLAGS += -march=core2 -mtune=corei7-avx -msse4.1
    QMAKE_CXXFLAGS += -march=core2 -mtune=corei7-avx -msse4.1
  }

  avx {
    DEFINES += ARCH_AVX
    QMAKE_CFLAGS += -march=corei7-avx -mavx
    QMAKE_CXXFLAGS += -march=corei7-avx -mavx
  }

  avx2 {
    DEFINES += ARCH_AVX2
    QMAKE_CFLAGS += -march=core-avx2 -mavx2
    QMAKE_CXXFLAGS += -march=core-avx2 -mavx2
  }

  warn_on {
    #QMAKE_CFLAGS += -Wshadow
    #QMAKE_CXXFLAGS += -Wshadow
  }

  reflapack | fastlapack {

    # fortan runtime can be specified in environment variable
    F90RNTM = $$(FORTRAN_RUNTIME)
    isEmpty(F90RNTM) {
        message("Fortran runtime environment variable not defined.")
        F90RNTM = `gfortran -m32 -print-file-name=libgfortran.a`
        message("Fortran runtime set:")
        message($$F90RNTM)
    }

    exists($(HOME)/lib/libopenblas.so) {
        # prefer locally compiled OpenBLAS
        message(Using OpenBLAS in $(HOME)/lib)
        LIBS *= $(HOME)/lib/libopenblas.so 
        DEFINES += HAVE_OPENBLAS HAVE_LAPACK HAVE_LAPACKE
        INCLUDEPATH *= $(HOME)/include
    } else {
        # if there is no local OpenBLAS, check if there is a system version
        exists(/usr/lib/libopenblas.so) | exists(/usr/lib/libopenblas.so) {
            message(Using OpenBLAS in /usr/lib)
            DEFINES += HAVE_OPENBLAS HAVE_LAPACK
            LIBS += -llapack -lopenblas
        } else {
            LIBS += -llapack -lblas $$F90RNTM
        }
    }
  }

  qglviewer {
    DEFINES *= QGLVIEWER_STATIC
    INCLUDEPATH *= ../QGLViewer
    CONFIG(debug, debug|release) {
      LIBS *= -lQGLViewer
    } else {
      LIBS *= -lQGLViewer
    }
    QT += opengl xml
    LIBS += -lGLU
  }

  LIBS += -fPIC -lrt -lm -ldl
}

linux-icc | linux-icc-64 {

  BUILD_TAG = "icc-64"
  CONFIG *= sse3 target-64bit
  BASEFLAGS     = -m64 -Wno-unknown-pragmas
  TARGET_LIB_DIR = $$PREFIX/lib64
  QMAKE_LFLAGS *= -m64 -L/usr/local/lib64 -L$$TARGET_LIB_DIR
  DEFINES += _LP64

  #MKLROOT = $(MKLROOT)
  #isEmpty($$MKLROOT):MKLROOT = /opt/intel/composerxe/mkl
  DEFINES += _GLIBCXX_USE_C99_FP_MACROS_DYNAMIC BOOST_THREAD_USES_MOVE

  # always have MKL and tbb
  !no-mkl {
    CONFIG += mklpardiso
  }
  !no-tbb {
    CONFIG *= tbb
  }

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS -std=c++11

  gcc47 {
    QMAKE_CFLAGS *= -gcc-name=gcc-4.7
    QMAKE_CXXFLAGS *= -gxx-name=g++-4.7
  }

  exists(/opt/rh/devtoolset-2/root/usr/bin/g++) {
    QMAKE_CFLAGS *= -gcc-name=/opt/rh/devtoolset-2/root/usr/bin/gcc
    QMAKE_CXXFLAGS *= -gxx-name=/opt/rh/devtoolset-2/root/usr/bin/g++
    QMAKE_LFLAGS *= -gxx-name=/opt/rh/devtoolset-2/root/usr/bin/g++
  }

  tbb {
    QMAKE_CFLAGS *= -tbb
    QMAKE_CXXFLAGS *= -tbb
    QMAKE_LFLAGS *= -tbb
    DEFINES *= HAVE_TBB
    INCLUDEPATH += -I$(TBBROOT)/include
  }

  release {
    DEFINES    *= NDEBUG
    OPTFLAGS    = -O3 -no-prec-div
    ipoopt {
        OPTFLAGS += -ipo6
        QMAKE_LFLAGS += -ipo-jobs6
    }
  }

  profile {
    DEFINES      *= NDEBUG
    OPTFLAGS      = -debug minimal -O2 -no-prec-div
    QMAKE_LFLAGS   += -p
  }

  QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
  QMAKE_CFLAGS_RELEASE   += $$OPTFLAGS

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
    QMAKE_CFLAGS *= -qopenmp
    QMAKE_CXXFLAGS *= -qopenmp
    QMAKE_LFLAGS *= -qopenmp
  }

  hostopt {
    CONFIG -= sse2 sse3
    QMAKE_CFLAGS *= -xHost
    QMAKE_CXXFLAGS *= -xHost
  }

  sse2 {
    QMAKE_CFLAGS *= -msse2 -axSSE4.1 -diag-disable cpu-dispatch
    QMAKE_CXXFLAGS *= -msse2 -axSSE4.1 -diag-disable cpu-dispatch
    DEFINES *= ARCH_SSE2
  }

  sse3 {
    QMAKE_CFLAGS *= -xSSE3 -axAVX -diag-disable cpu-dispatch
    QMAKE_CXXFLAGS *= -xSSE3 -axAVX -diag-disable cpu-dispatch
    DEFINES *= ARCH_SSE3
  }

  mklpardiso | fastlapack | reflapack {
    DEFINES += HAVE_MKL HAVE_MKL_PARDISO MKL_DIRECT_CALL
    INCLUDEPATH *= $(MKLROOT)/include
    QMAKE_CFLAGS *= -qopenmp
    QMAKE_CXXFLAGS *= -qopenmp
    target-64bit {
      LIBS *=  -Wl,--start-group  $(MKLROOT)/lib/intel64/libmkl_intel_lp64.a \
                $(MKLROOT)/lib/intel64/libmkl_intel_thread.a \
                $(MKLROOT)/lib/intel64/libmkl_core.a -Wl,--end-group \
                -lpthread -lm
    } else {
      LIBS *= -Wl,--start-group $(MKLROOT)/lib/ia32/libmkl_intel.a \
              $(MKLROOT)/lib/ia32/libmkl_intel_thread.a \
              $(MKLROOT)/lib/ia32/libmkl_core.a -Wl,--end-group -lpthread -lm
    }
  }

  # put executable path into library search path
  # to allow bundling of compiler libs
  QMAKE_LFLAGS += '-Wl,-rpath,\'\$$ORIGIN/../lib\''
  QMAKE_LFLAGS += '-Wl,-rpath,\'\$$ORIGIN/../lib64\''

  # expat and zlib are system libraries, use them
  builtin_expat {
    LIBS *= -lz
  } else {
    LIBS *= -lz -lexpat
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
    LIBS += -lGLU
  }

  LIBS += -lrt
}

