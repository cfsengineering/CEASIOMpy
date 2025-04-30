# qmake settings for applications

# use library settings
include(rootconfig.pri)

CONFIG(zip):DEFINES += HAVE_ZIP
CONFIG(cgns):DEFINES += HAVE_CGNS
CONFIG(scotch):LIBS += -lscotch -lscotcherr

linux-g++-64 { 

   QMAKE_LFLAGS += -m64 -L$$TARGET_LIB_DIR
   fftw3:LIBS += -lfftw3

   # expat and zlib are system libraries, use them
   builtin_expat {
    LIBS *= -lz
   } else {
    LIBS *= -lz -lexpat
   }

  qglviewer {
    LIBS *= -lGLU
  }
}

linux-g++-32 { 

   QMAKE_LFLAGS += -m32 -L$$TARGET_LIB_DIR
   fftw3:LIBS += -lfftw3

   # expat and zlib are system libraries, use them
   !CONFIG(builtin_expat):LIBS += -lexpat
   !CONFIG(builtin_zlib):LIBS += -lz
   
  qglviewer {
    LIBS *= -lGLU
  }
}

macx-g++ | macx-g++42 | macx-clang {

   gcc47 {
     QMAKE_LINK = /opt/gcc/4.7.1/bin/g++-4.7.1
     QMAKE_LFLAGS += -static-libstdc++
     QMAKE_LFLAGS -= -Xarch_x86_64
   }

   fftw3 {
     QMAKE_LFLAGS *= -L/usr/local/lib
     LIBS += -lfftw3
   }

   QMAKE_LFLAGS += -L$$TARGET_LIB_DIR -headerpad_max_install_names
   LIBS += -framework CoreFoundation -framework IOKit

   # expat and zlib are system libraries, use them
   LIBS *= -lz -lexpat
}

macx-icc {

   reflapack {
       QMAKE_LFLAGS += -L/usr/local/lib64
       LIBS += -lreflapack `/sw/bin/gfortran -m64 -print-file-name=libgfortran.a`
   }

   reflapack | fastlapack {
     MKLROOT = /opt/intel/mkl
     QMAKE_LIBS  *= $$MKLROOT/lib/libmkl_intel_lp64.a \
                    $$MKLROOT/lib/libmkl_intel_thread.a \
                    $$MKLROOT/lib/libmkl_core.a -openmp -lpthread
   }

   fftw3 {
     QMAKE_LFLAGS *= -L/usr/local/lib64
     LIBS += -lfftw3
   }

   mklpardiso {

     MKLROOT = /opt/intel/mkl

      # MKL version 10
     exists($$MKLROOT/lib/libmkl_solver_lp64.a) {
       QMAKE_LIBS  *= $$MKLROOT/lib/libmkl_solver_lp64.a
     }

      # MKL version 11
      QMAKE_LIBS *=  $$MKLROOT/lib/libmkl_intel_lp64.a \
                     $$MKLROOT/lib/libmkl_intel_thread.a \
                     $$MKLROOT/lib/libmkl_core.a -openmp -lpthread -lm
   }

   ipo {
     QMAKE_LFLAGS += -ipo
   }

   ippz {
     QMAKE_LFLAGS *= -ipp
     LIBS -= -lz
     LIBS *= -lippz
   } else {
     LIBS *= -lz
   }

   QMAKE_LFLAGS += -L$$TARGET_LIB_DIR -headerpad_max_install_names
   LIBS += -framework CoreFoundation -framework IOKit

   # use system libexpat
   LIBS *= -lexpat
}
