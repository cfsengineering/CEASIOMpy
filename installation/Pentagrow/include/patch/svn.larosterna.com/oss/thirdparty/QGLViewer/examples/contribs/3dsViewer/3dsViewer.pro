# The LGPL lib3ds library is used to load and display a 3ds scene.

# You need to install the lib3ds library (version 1.2) in order to compile this file.
# See <a href="http://lib3ds.sourceforge.net/">http://lib3ds.sourceforge.net/</a>.

# The current version (Version 1.2, Dec 2002) of the lib3ds library is flawed and results in :
# <pre>3dsViewer.cpp:62: `lib3ds_file_bounding_box' undeclared (first use this function)</pre>

# A patched version is available on the <a href="../installUnix.html">Unix installation page</a>.
# You can alternately add this line in the file that uses <code>lib3ds_file_bounding_box()</code>
# (or in <code>lib3ds/file.h</code>) :
# <pre>extern "C" { LIB3DSAPI void lib3ds_file_bounding_box(Lib3dsFile *file, Lib3dsVector min, Lib3dsVector max); }</pre>

# This example is simply a translation of a lib3ds example. Although it uses display lists, the
# rendering speed does not seem to be as good as with other 3ds libraries (10 factor speed up). Note
# however that this is due to the lib3ds library and not QGLViewer.

# Press '<b>L</b>' (load) to load a new 3DS scene.

TEMPLATE = app
TARGET   = 3dsViewer

# Set these paths according to your configuration
# Use qmake 3DS_INCLUDE_DIR=... 3DS_LIB_DIR=...
!isEmpty( 3DS_INCLUDE_DIR ) {
  INCLUDEPATH *= $${3DS_INCLUDE_DIR}
}
!isEmpty( 3DS_LIB_DIR ) {
  LIBS *= -L$${3DS_LIB_DIR}
}
!isEmpty( 3DS_LIB_A ) {
  LIBS *= $${3DS_LIB_A}
} else {
  LIBS *= -l3ds
}

# win32:LIBS  *= C:\code\lib\lib3ds.lib

HEADERS  = 3dsViewer.h
SOURCES  = 3dsViewer.cpp main.cpp

DISTFILES += *.3DS

QT *= xml opengl

CONFIG -= debug debug_and_release
CONFIG += release qt opengl warn_on thread rtti console embed_manifest_exe

# --------------------------------------------------------------------------------------

# The remaining of this configuration tries to automatically detect the library paths.
# In your applications, you can probably simply use (see doc/compilation.html for details) :

#INCLUDEPATH *= C:/Users/debunne/Documents/libQGLViewer-2.3.1
#LIBS *= -LC:/Users/debunne/Documents/libQGLViewer-2.3.1/QGLViewer -lQGLViewer2

# Change these paths according to your configuration.

# --------------------------------------------------------------------------------------


### Unix configuration ###
unix|win32-g++ {
  isEmpty( PREFIX ) {
    # Try same INCLUDE_DIR and LIB_DIR parameters than for the make install.
    PREFIX=/usr
  }

  # INCLUDE_DIR
  isEmpty( INCLUDE_DIR ) {
    INCLUDE_DIR = $${PREFIX}/include

    !exists( $${INCLUDE_DIR}/QGLViewer/qglviewer.h ) {
      exists( ../../../QGLViewer/qglviewer.h ) {
        message( Using ../../.. as INCLUDE_DIR )
        INCLUDE_DIR = ../../..
      }
    }
  }

  !exists( $${INCLUDE_DIR}/QGLViewer/qglviewer.h ) {
    message( Unable to find QGLViewer/qglviewer.h in $${INCLUDE_DIR} )
    error( Use qmake INCLUDE_DIR=Path/To/QGLViewer )
  }

  # LIB_NAME
  LIB_NAME = libQGLViewer*.so*
  macx|darwin-g++ {
    LIB_NAME = libQGLViewer*.$${QMAKE_EXTENSION_SHLIB}
  }
  hpux {
    LIB_NAME = libQGLViewer*.sl*
  }
  win32-g++ {
    LIB_NAME = libQGLViewer*.a
  }

  !isEmpty( QGLVIEWER_STATIC ) {
    LIB_NAME = libQGLViewer*.a
  }

  # LIB_DIR
  isEmpty( LIB_DIR ) {
    LIB_DIR = $${PREFIX}/lib

    !exists( $${LIB_DIR}/$${LIB_NAME} ) {
      exists( ../../../QGLViewer/$${LIB_NAME} ) {
        message( Using ../../../QGLViewer as LIB_DIR )
        LIB_DIR = ../../../QGLViewer
      }
    }  
  }

  !exists( $${LIB_DIR}/$${LIB_NAME} ) {
    message( Unable to find $${LIB_NAME} in $${LIB_DIR} )
    error( You should run qmake LIB_DIR=Path/To/$${LIB_NAME} )
  }

      
  contains( LIB_DIR, ".." ) {
    macx|darwin-g++ {
      message( You should add the path to "$${LIB_DIR}" to your DYLD_LIBRARY_PATH variable )
    } else {
      message( You should add the path to "$${LIB_DIR}" to your LD_LIBRARY_PATH variable )
    }
    message( See doc/compilation.html for details )
  }

  # Paths were correctly detected
  INCLUDEPATH *= $${INCLUDE_DIR}
  DEPENDPATH  *= $${INCLUDE_DIR}
  isEmpty( QGLVIEWER_STATIC ) {
    LIBS *= -L$${LIB_DIR} -lQGLViewer
  } else {
    LIBS *= $${LIB_DIR}/$${LIB_NAME}
  }

  macx {
    LIBS *= -lobjc
    CONFIG -= thread
  }

  # Remove debugging options
  release:QMAKE_CFLAGS_RELEASE -= -g
  release:QMAKE_CXXFLAGS_RELEASE -= -g

  # Intermediate files are created in an hidden folder
  MOC_DIR = .moc
  OBJECTS_DIR = .obj
}



### Windows configuration ###
win32 {
  MOC_DIR = moc
  OBJECTS_DIR = obj
}

!win32-g++ {
win32 {
  # Use the Qt DLL version. Only needed with Qt3
  DEFINES *= QT_DLL QT_THREAD_SUPPORT

  !isEmpty( QGLVIEWER_STATIC ) {
    DEFINES *= QGLVIEWER_STATIC
  }

  # Compilation from zip file : libQGLViewer is located in ../../..
  exists( ../../../QGLViewer ) {
    exists( ../../../QGLViewer/qglviewer.h ) {
      INCLUDEPATH *= ../../..
    }
    
    LIB_FILE = QGLViewer*.lib

    exists( ../../../QGLViewer/$${LIB_FILE} ) {
      LIB_PATH = ../../../QGLViewer
    }
  }

  LIBS *= -L$${LIB_PATH} -lQGLViewer2
}}
