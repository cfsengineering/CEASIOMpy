#
# qmake settings for all projects
#

contains(QT_MAJOR_VERSION, 5) { cache() }

PREFIX = $$PWD/../..

# if there is a local (site-) config file, pull it in first
exists(local.pri) {
  include(local.pri)
}

# configuration presets for particular packages
preset-vzm {
  message(Configuration presets for vzm)
  CONFIG *= builtin_yaml builtin_rply spacenav
  CONFIG *= no-netcdf no-mesquite no-spooles no-fftw no-spqr no-mtmetis
  CONFIG *= no-arpack no-scotch no-metis no-metis5 no-metis4 no-lapack no-mkl
  CONFIG *= no-jrstriangle nlopt-nolgpl
  !unix {
     CONFIG *= builtin_expat builtin_zlib 
  }
  DEFINES *= HAVE_RPLY
}

preset-sumo {
  CONFIG *= builtin_expat builtin_judy builtin_yaml spacenav
  CONFIG *= no-arpack no-scotch no-mesquite no-mtmetis
}

TARGET_BIN_DIR = $$PREFIX/bin
INCLUDEPATH += $$PWD/.. $$PWD/../boost $$PREFIX/include

CONFIG(debug, debug|release) {
  CONFIG *= debug
  CONFIG -= release
  # OBJECTS_DIR = ./build-$$BUILD_TAG-debug
} else {
  CONFIG += release
  CONFIG -= debug
  # OBJECTS_DIR = ./obj_release
  # OBJECTS_DIR = ./build-$$BUILD_TAG-release
}

# system independent

!contains(CONFIG, no-eigen) {
# compile the eeigen headers without parallelization because its internal
# parallelization interferes with higher level parallelization in the caller
    exists(../eigen/eeigen/Core) {
        DEFINES += HAVE_EIGEN EIGEN_DONT_PARALLELIZE
        INCLUDEPATH *= $$PWD/../eigen
    }
}

no-lapack {
  message(Compiling without LAPACK support)
  DEFINES += HAVE_NO_LAPACK
}

# system dependencies

unix {

    mac {
      pkgconf = /usr/local/bin/pkg-config
    } else {
      pkgconf = pkg-config
    }

    judy {
        DEFINES *= HAVE_JUDY 
        target-64bit { 
            DEFINES += JU_64BIT 
        }
        system_judy {
            message("Using external libJudy")
            INCLUDEPATH *= $$PREFIX/include
            LIBS *= -lJudy
        } else {
            message("libJudy compiled into libgenua")
            CONFIG *= builtin_judy
            INCLUDEPATH *= $$PWD/../genua/judy/src
        }
    }
}

win32 {
    netcdf {
        # netcdf.h installed locally
        # from package at 
        # http://www.unidata.ucar.edu/software/netcdf/win_netcdf/
        INCLUDEPATH *= ../../include
        LIBS *= -lnetcdf
    }
}

unix {
!mac {
    include(linux.pri)
}
}

mac {
    include(mac.pri)
}

win32 {
    include(windows.pri)
}

posix_threads {
  DEFINES += USE_PTHREADS
} else {
  DEFINES -= USE_PTHREADS
}

CONFIG(debug, debug|release) {
  OBJECTS_DIR = ./build-$$BUILD_TAG-debug
} else {
  OBJECTS_DIR = ./build-$$BUILD_TAG-release
}

MOC_DIR = $$OBJECTS_DIR
UI_DIR = $$OBJECTS_DIR
RCC_DIR = $$OBJECTS_DIR
