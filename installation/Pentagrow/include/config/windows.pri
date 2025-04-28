
# configure detected/selected components
spacenav {
  DEFINES += HAVE_SPACENAV
}

win32-g++ | win32-g++-4.6 {

  # architecture defaults to 64bit
  !contains(CONFIG,x86) {
    CONFIG *= x86_64
  }

  CONFIG(x86) {
    BUILD_TAG = "gcc-32"
    message("Building with GCC for 32bit")
    TARGET_LIB_DIR = $$PREFIX/lib
    QMAKE_LFLAGS += -m32 -L$$TARGET_LIB_DIR
    BASEFLAGS = -m32
    # CONFIG -= sse2 sse3
  }

  CONFIG(x86_64) {
    BUILD_TAG = "gcc-64"
    message("Building with GCC for 64bit")
    TARGET_LIB_DIR = $$PREFIX/lib64
    QMAKE_LFLAGS += -m64 -L$$TARGET_LIB_DIR
    BASEFLAGS = -m64
  }

  CONFIG(debug, debug|release) {
    CONFIG *= console
  } else {
    CONFIG -= console
  }

  QMAKE_CFLAGS_RELEASE =
  QMAKE_CXXFLAGS_RELEASE =
  QMAKE_CXXFLAGS_DEBUG =

  # prevent windows.h from defining all kinds of generic
  # names as macros
  DEFINES *= WIN32_LEAN_AND_MEAN NOMINMAX

  # we are aware that we cannot std::copy to 0x0.
  DEFINES *= _CRT_SECURE_NO_WARNINGS

  release {
    OPTFLAGS  = -O3 -DNDEBUG -funroll-loops -fomit-frame-pointer \
                -march=core2 -ffinite-math-only -fno-math-errno
  } else {
    # necessary because PE/COFF object file format limits number of
    # object file sections which is too large with -g
    QMAKE_CXXFLAGS_DEBUG = -g1 -O1
  }

  profile {
    OPTFLAGS  = -O2 -DNDEBUG -funroll-loops  \
                -march=core2 -ffinite-math-only -fno-math-errno
    BASEFLAGS += -g -pg
    QMAKE_LFLAGS   += -pg
  }

  staticlib {
    DESTDIR = $$TARGET_LIB_DIR
    QMAKE_CFLAGS_STATIC_LIB  -= -fPIC
    QMAKE_CXXFLAGS_STATIC_LIB  -= -fPIC
  }


  # the GNU OpenMP implementation is built on top of
  # the pthread library, so we need to use pthreads
  openmp {
    CONFIG += posix_threads
    BASEFLAGS += -fopenmp
    QMAKE_LFLAGS += -fopenmp
  }

  sse2 {
    DEFINES += ARCH_SSE2
    BASEFLAGS += -march=k8 -mtune=core2 -msse2
  }

  sse3 {
    DEFINES += ARCH_SSE3
    BASEFLAGS += -march=core2 -msse3
  }

  sse41 {
    DEFINES += ARCH_SSE41
    BASEFLAGS += -march=core2 -mtune=corei7 -msse4.1
  }

  avx {
    DEFINES += ARCH_AVX
    BASEFLAGS += -march=corei7-avx -mavx
  }

  avx2 {
    DEFINES += ARCH_AVX2
    BASEFLAGS += -march=core-avx2 -mavx2 -ffp-contract=fast
  }

  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS --std=c++11
  QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
  QMAKE_CFLAGS_RELEASE += $$OPTFLAGS

  QMAKE_LFLAGS += -L$$TARGET_LIB_DIR
  LIBS += -lIphlpapi

  reflapack|fastlapack {
    LIBS += -llapack -lblas
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
    LIBS += -lopengl32 -lglu32
  }
}

win32-msvc|win32-msvc2005|win32-msvc2008|win32-msvc2010|win32-msvc2012|win32-msvc2013 {

  MSVC_LOGO=$$system(cl)
  MSVC_TARGET_ARCH = $$(TARGET_CPU) $$(TARGET_ARCH)
  
  # message("qmake msvc version tag: " $$QMAKE_MSC_VER);
  MSABI_SUFFIX = "vc12"
  equals(QMAKE_MSC_VER, 1800) {
    message("Detected MSVC2013, MSC_VER: " $$QMAKE_MSC_VER);
    MSABI_SUFFIX = "vc12"
  }
  equals(QMAKE_MSC_VER, 1900) {
    message("Detected MSVC2015, MSC_VER: " $$QMAKE_MSC_VER);
    MSABI_SUFFIX = "vc14"
  }
  greaterThan(QMAKE_MSC_VER, 1909) {
    message("Detected MSVC2017, MSC_VER: " $$QMAKE_MSC_VER);
    MSABI_SUFFIX = "vc14"
  }

  contains(MSVC_TARGET_ARCH,x64)|contains(MSVC_TARGET_ARCH,intel64)|contains(MSVC_LOGO,x64)|contains(QMAKE_TARGET.arch, x86_64) {
    BUILD_TAG = "msvc-64"
    message( "Building with Visual C++ for 64 bit, " $$QMAKE_MSC_VER)
    CONFIG += intel64 sse2
    TARGET_BIN_DIR = $$PREFIX/bin64
    TARGET_LIB_DIR = $$PREFIX/lib64
  } else {
    message( "Building with Visual C++ for 32 bit, " $$MSVC_TARGET_ARCH)
    BUILD_TAG = "msvc-32"
    CONFIG += intel32 sse2
    TARGET_BIN_DIR = $$PREFIX/bin32
    TARGET_LIB_DIR = $$PREFIX/lib32
  }

  # check for TBB headers; if found, add LIB path etc
  !no-tbb {
    exists($$TARGET_LIB_DIR/../include/tbb/tbb.h) {
        message("Detected TBB")
        CONFIG *= tbb
        DEFINES += HAVE_TBB
        INCLUDEPATH *= $$TARGET_LIB_DIR/../include
        LIBS += -ltbb -ltbbmalloc -ltbbmalloc_proxy
        QMAKE_LFLAGS += -LIBPATH:$$TARGET_LIB_DIR/tbb-$$MSABI_SUFFIX
    }
  }

  # check for HDF headers; if found, add LIB path etc
  !no-hdf5 {
    exists($$TARGET_LIB_DIR/../include/hdf5/hdf5.h) {
        message("Detected HDF5")
        CONFIG *= hdf5
        DEFINES += HAVE_HDF5
        INCLUDEPATH *= $$TARGET_LIB_DIR/../include/hdf5
        LIBS += -llibhdf5_hl -llibhdf5 -llibszip
        QMAKE_LFLAGS += -LIBPATH:$$TARGET_LIB_DIR/hdf5-$$MSABI_SUFFIX
    }
  }

  #PDB_FNAME=$$TARGET_LIB_DIR/$$TARGET".pdb"
  #message("PDB location set to" $$PDB_FNAME)

  CONFIG += stl rtti exceptions

  # prevent windows.h from defining all kinds of generic
  # names as macros
  DEFINES *= WIN32_LEAN_AND_MEAN NOMINMAX

  # we are aware that we cannot std::copy to 0x0.
  DEFINES *= _CRT_SECURE_NO_WARNINGS _SCL_SECURE_NO_WARNINGS

  # using compiler attributes for SAL makes assert() unusable,
  # hence, use the (older) declspec version
  DEFINES *= _USE_DECLSPECS_FOR_SAL

  # target Windows 7 or later
  DEFINES *= WINVER=0x0601 _WIN32_WINNT=0x0601

  # Make sure to recompile *all* static libs when changing
  # anything here; the msvc build chain is extremely fragile

  BASEFLAGS = -wd4100 -wd4244 -wd4068 -wd4267

  aslr {
    QMAKE_LFLAGS += -DYNAMICBASE
  }

  profile {
    # put debug symbols into release build .pdb
    CONFIG *= release
    OPTFLAGS += -Gy -Zi -DEBUG -FS -GS- -bigobj
    QMAKE_LFLAGS += -DEBUG
    staticlib {
      #OPTFLAGS += -Fd\"$$PDB_FNAME\"
    }
  }

  release {
    mildopt {
      DEFINES += NDEBUG
      OPTFLAGS += -O1 -Gy
      QMAKE_LFLAGS *= -OPT:REF -OPT:ICF
    } else {
      # http://preshing.com/20110807/the-cost-of-_secure_scl/
      DEFINES *= _SECURE_SCL=0 _ITERATOR_DEBUG_LEVEL=0
      DEFINES += NDEBUG
      OPTFLAGS += -O2 -Gy -GS- -fp:fast
      QMAKE_LFLAGS *= -OPT:REF -OPT:ICF=4
      #QMAKE_LFLAGS += -LTCG
    }
  } else {
    debug {
      DEFINES *= _ITERATOR_DEBUG_LEVEL=1
      OPTFLAGS += -Od -bigobj -FS
      QMAKE_LFLAGS *= -OPT:NOICF
      staticlib {
        #OPTFLAGS += -Fd\"$$PDB_FNAME\"
      }
    }
  }

  sse3 {
    DEFINES += ARCH_SSE3
    intel32:OPTFLAGS += -arch:SSE2
  }

  sse2 {
    DEFINES += ARCH_SSE2
    intel32:OPTFLAGS += -arch:SSE2
  }
  
  avx {
    DEFINES += ARCH_AVX
    OPTFLAGS += -arch:AVX
  }
  
  avx2 {
    DEFINES += ARCH_AVX2
    OPTFLAGS += -arch:AVX2
  }

  openmp {
    BASEFLAGS += -openmp
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
  QMAKE_CXXFLAGS_DEBUG = -MDd -Zi -FS -Zo $$OPTFLAGS
  QMAKE_CFLAGS_DEBUG = -MDd -Zi -FS -Zo $$OPTFLAGS

  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
  QMAKE_CFLAGS_RELEASE += $$OPTFLAGS

  isEmpty(ICCROOT){
    exists("C:/Program Files (x86)/Intel/Composer XE") {
     ICCROOT=\"C:/Program Files (x86)/Intel/Composer XE
    }
    exists("D:/Program Files (x86)/Intel/Composer XE") {
      ICCROOT=\"D:/Program Files (x86)/Intel/Composer XE
    }
    exists("C:/Programme (x86)/Intel/Composer XE") {
     ICCROOT=\"C:/Programme (x86)/Intel/Composer XE
    }
  }

  message("Intel C++ root:" $$ICCROOT)

  intel64 {
    IPP_LIB_PATH=$$ICCROOT/ipp/lib/intel64\"
    ICC_LIB_PATH=$$ICCROOT/compiler/lib/intel64\"
    MKL_LIB_PATH=$$ICCROOT/mkl/lib/intel64\"
    MKL_LIBS = mkl_intel_lp64.lib mkl_core.lib mkl_sequential.lib
  } else {
    IPP_LIB_PATH=$$ICCROOT/ipp/lib/ia32\"
    ICC_LIB_PATH=$$ICCROOT/compiler/lib/ia32\"
    MKL_LIB_PATH=$$ICCROOT/mkl/lib/ia32\"
    MKL_LIBS = mkl_intel_c.lib mkl_core.lib mkl_sequential.lib
  }

  QMAKE_LFLAGS += -LIBPATH:$$TARGET_LIB_DIR
  LIBS += -lIphlpapi

  pgo_instrument {
    QMAKE_CXXFLAGS_RELEASE *= -GL -GS-
    QMAKE_LFLAGS *= -LTCG:PGI
  }

  pgo_optimize {
    QMAKE_CXXFLAGS_RELEASE *= -GL -GS-
    QMAKE_LFLAGS *= -LTCG:PGO
  }

  reflapack|fastlapack {
    mkl {
      QMAKE_LFLAGS += -LIBPATH:$$MKL_LIB_PATH -LIBPATH:$$ICC_LIB_PATH
      LIBS *= $$MKL_LIBS
    } else {
      # LIBS *= -llapack_win32_MT -lblas_win32_MT
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
    LIBS += -lopengl32 -lglu32
  }
}

win32-icc {

  # message("qmake msvc version tag: " $$QMAKE_MSC_VER);
  MSABI_SUFFIX = "vc12"
  equals(QMAKE_MSC_VER, 1800) {
    message("Detected MSVC2013, MSC_VER: " $$QMAKE_MSC_VER);
    MSABI_SUFFIX = "vc12"
  }
  equals(QMAKE_MSC_VER, 1900) {
    message("Detected MSVC2015, MSC_VER: " $$QMAKE_MSC_VER);
    MSABI_SUFFIX = "vc14"
  }
  greaterThan(QMAKE_MSC_VER, 1909) {
    message("Detected MSVC2017, MSC_VER: " $$QMAKE_MSC_VER);
    MSABI_SUFFIX = "vc14"
  }

  MSVC_TARGET_ARCH = $$(TARGET_CPU) $$(TARGET_ARCH)

  contains(MSVC_TARGET_ARCH,x64)|contains(MSVC_TARGET_ARCH,intel64)|contains(QMAKE_TARGET.arch,x86_64) {
    BUILD_TAG = "icc-64"
    message( "Building with Intel C++ for 64 bit, " $$MSVC_TARGET_ARCH)
    CONFIG += intel64
    TARGET_BIN_DIR = $$PREFIX/bin64
    TARGET_LIB_DIR = $$PREFIX/lib64
  } else {
    BUILD_TAG = "icc-32"
    message( "Building with Intel C++ for 32 bit, " $$MSVC_TARGET_ARCH)
    CONFIG += intel32
    TARGET_BIN_DIR = $$PREFIX/bin32
    TARGET_LIB_DIR = $$PREFIX/lib32
  }

  # Intel compiler - can assume that MKL is present
  !no-lapack {
    CONFIG *= mkl mklpardiso
  }

  !no-tbb {
    CONFIG *= tbb
  }
  
  !no-hdf5 {
    exists($$TARGET_LIB_DIR/../include/hdf5/hdf5.h) {
        message("Detected HDF5")
        CONFIG *= hdf5
        DEFINES += HAVE_HDF5
        INCLUDEPATH *= $$TARGET_LIB_DIR/../include/hdf5
        LIBS += -llibhdf5_hl -llibhdf5 -llibszip
        QMAKE_LFLAGS += -LIBPATH:$$TARGET_LIB_DIR/hdf5-$$MSABI_SUFFIX

        # STL in Visual C++ 2015 (.140.dll) is the same as in 2017
        #win32-msvc2015:QMAKE_LFLAGS += -LIBPATH:$$TARGET_LIB_DIR/hdf5-vc14
        #win32-msvc2017:QMAKE_LFLAGS += -LIBPATH:$$TARGET_LIB_DIR/hdf5-vc14
    }
  }
  
  # check for presence of netcdf3.lib in lib directory
  !no-netcdf {
	 exists($$TARGET_LIB_DIR/netcdf.lib) {
		CONFIG *= netcdf
	}
  }
 
  # root of the intel compiler installation
  ICCROOT = $$(ICPP_COMPILER19)
  isEmpty(ICCROOT) {
    ICCROOT = $$(ICPP_COMPILER18)
  }
  isEmpty(ICCROOT) {
    ICCROOT = $$(ICPP_COMPILER17)
  }
  isEmpty(ICCROOT) {
    ICCROOT = $$(ICPP_COMPILER16)
  }
  isEmpty(ICCROOT) {
    ICCROOT = $$(ICPP_COMPILER15)
  }
  isEmpty(ICCROOT) {
    ICCROOT = $$(ICPP_COMPILER14)
  }
  isEmpty(ICCROOT) {
    ICCROOT = $$(ICPP_COMPILER13)
  }
  
  isEmpty(ICCROOT){
    exists("C:/Program Files (x86)/Intel/Composer XE") {
      ICCROOT=\"C:/Program Files (x86)/Intel/Composer XE
    }
    exists("D:/Program Files (x86)/Intel/Composer XE") {
      ICCROOT=\"D:/Program Files (x86)/Intel/Composer XE
    }
    exists("C:/Programme (x86)/Intel/Composer XE") {
      ICCROOT=\"C:/Programme (x86)/Intel/Composer XE
    }
  }

  message("Intel C++ root:" $$ICCROOT)

  QMAKE_LINK = xilink
  QMAKE_LIB = xilib

  # still requires embedding the manifest manually using
  # mt -manifest dwfscope.exe.manifest -outputresource:dwfscope.exe;1

  CONFIG += embed_manifest_exe embed_manifest_dll
  CONFIG += stl rtti exceptions

  # prevent windows.h from defining all kinds of generic
  # names as macros
  DEFINES *= WIN32_LEAN_AND_MEAN NOMINMAX

  # we are aware that we cannot std::copy to 0x0.
  DEFINES *= _CRT_SECURE_NO_WARNINGS

  # using compiler attributes for SAL makes assert() unusable,
  # hence, use the (older) declspec version
  DEFINES *= _USE_DECLSPECS_FOR_SAL

  # path to MKL libs and PSTL includes
  INCLUDEPATH += "$$ICCROOT/compiler/include" "$$ICCROOT/pstl/include"
  MKLROOT = $$ICCROOT/mkl

  # Note : do not even think of anything -ipo: compiler crashes 
  #
  release {
    DEFINES *= NDEBUG ARCH_SSE2

    # http://preshing.com/20110807/the-cost-of-_secure_scl/
    DEFINES *= _SECURE_SCL=0 _ITERATOR_DEBUG_LEVEL=0

    OPTFLAGS = -O2 -Gy -Quse-intel-optimized-headers 
    
    profile {
      OPTFLAGS += -Zi -DEBUG -GS- -debug:inline-debug-info -debug:expr-source-pos
      QMAKE_LFLAGS += -DEBUG
    } else {
      DEFINES *= QT_NO_DEBUG_OUTPUT
    }
  } 

  # entirely thoeretical, since the pgogen binary is so slow that it cannot
  # be used with any meaningfull dataset
  PGODIR=$$TARGET_BIN_DIR/../pgodata
  pgogen {
    OPTFLAGS += -Qprof-dir:"$$PGODIR" -Qprof-gen:threadsafe
  }
  pgouse {
    OPTFLAGS += -Qprof-dir:"$$PGODIR" -Qprof-use:weighted -Qipo0 -Qipo-jobs:8
    QMAKE_LFLAGS += -Qipo -Qipo-jobs:8
  }

  sse3 {
    # adding -O3 here makes compiles times infinite
    DEFINES  *= ARCH_SSE3 
    OPTFLAGS *= -QxSSE3 -Qopt-matmul
  }
  
  sse41 {
    DEFINES  *= ARCH_SSE41
    OPTFLAGS -= -O2
    OPTFLAGS *= -O3 -QxSSE4.1 -Qopt-matmul
  }
  
  avx {
    DEFINES  *= ARCH_AVX
    OPTFLAGS -= -O2
    OPTFLAGS *= -O3 -QxAVX -Qopt-matmul
  }
  
  avx2 {
    DEFINES  *= ARCH_AVX2
    OPTFLAGS -= -O2
    OPTFLAGS *= -O3 -QxCORE-AVX2 -Qopt-matmul
  }

  staticlib {
    CONFIG += create_prl
  } else {
    CONFIG += link_prl
  }

  mklpardiso {
    DEFINES += HAVE_MKL_PARDISO
    INCLUDEPATH += "$$MKLROOT/include"
  }

  QMAKE_CFLAGS =
  QMAKE_CXXFLAGS = 
  BASEFLAGS = -Qwd161

  QMAKE_CFLAGS = $$BASEFLAGS
  QMAKE_CXXFLAGS = $$BASEFLAGS -Qstd=c++11 -Qcxx-features -EHsc
  QMAKE_CXXFLAGS_RELEASE = -MD
  QMAKE_CFLAGS_RELEASE = -MD
  QMAKE_CXXFLAGS_DEBUG = -MDd -Od -Zi -debug:full
  QMAKE_CFLAGS_DEBUG = -MDd -Od -Zi -debug:full
  QMAKE_CXXFLAGS_RELEASE += $$OPTFLAGS
  QMAKE_CFLAGS_RELEASE += $$OPTFLAGS

  openmp {
    QMAKE_CFLAGS += -Qopenmp
    QMAKE_CXXFLAGS += -Qopenmp
  }

  # linker options and libraries

  intel64 {
    ICC_ARCH=intel64
    QMAKE_LFLAGS += -LIBPATH:\"$$ICCROOT/compiler/lib/intel64\"
    QMAKE_LFLAGS += -LIBPATH:\"$$ICCROOT/ipp/lib/intel64\"
  } else {
    ICC_ARCH=ia32
    QMAKE_LFLAGS += -LIBPATH:\"$$ICCROOT/compiler/lib/ia32\"
    QMAKE_LFLAGS += -LIBPATH:\"$$ICCROOT/ipp/lib/ia32\"
  }

  QMAKE_LFLAGS += -OPT:REF -OPT:ICF=2
  QMAKE_LFLAGS += -LIBPATH:$$TARGET_LIB_DIR
  LIBS *= -lIphlpapi

  # use MKL
  reflapack | fastlapack | mkl {
    intel64 {
      QMAKE_LFLAGS += -LIBPATH:\"$$ICCROOT/mkl/lib/intel64\"
      LIBS *= mkl_intel_lp64.lib mkl_sequential.lib mkl_core.lib
      #LIBS *= mkl_intel_lp64_dll.lib mkl_core_dll.lib mkl_intel_thread_dll.lib
    } else {
      QMAKE_LFLAGS += -LIBPATH:\"$$ICCROOT/mkl/lib/ia32\"
      LIBS *= mkl_intel_c.lib mkl_sequential.lib mkl_core.lib
      #LIBS *= mkl_intel_c_dll.lib mkl_core_dll.lib mkl_intel_thread_dll.lib
    }
  }

  mklpardiso {
    # QMAKE_LFLAGS *= $$MKL_ROOT/lib/$$ICC_ARCH
    # LIBS *= mkl_intel_lp64.lib mkl_intel_thread.lib mkl_core.lib -Qopenmp
    # LIBS *= mkl_intel_lp64_dll.lib mkl_core_dll.lib mkl_intel_thread_dll.lib
  }

  ippz {
    QMAKE_CXXFLAGS *= -Qipp
    LIBS *= -lippz
  }

  tbb {
    DEFINES *= HAVE_TBB
    QMAKE_CXXFLAGS *= -Qtbb
    LIBS *= -ltbbmalloc
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
    LIBS += -lopengl32 -lglu32
  }
}

spooles {
    DEFINES *= HAVE_SPOOLES
    CONFIG(debug, debug|release) {
        LIBS += -lspooles_debug
    } else {
        LIBS += -lspooles
    }
}

netcdf {
    DEFINES *= HAVE_NETCDF
    INCLUDEPATH *= "../../include"
	LIBS += -lnetcdf
}
