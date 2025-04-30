# A clipping plane is manipulated using a ManipulatedFrame

# The standard OpenGL <i>GL_CLIP_PLANE</i> feature is used to add an additionnal clipping
# plane in the scene, which position and orientation are set by a <b>ManipulatedFrame</b>.

# Hold the <b>Control</b> key pressed down while using the mouse to modify the plane orientation (left button)
# and position (right button) and to interactively see the clipped result.

# Since the plane equation is defined with respect to the current modelView matrix, a constant equation (normal
# along the Z axis) can be used since we transformed the coordinates system using the <b>matrix()</b> method.

TEMPLATE = app
TARGET   = clippingPlane

HEADERS  = clippingPlane.h
SOURCES  = clippingPlane.cpp main.cpp

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
      exists( ../../QGLViewer/qglviewer.h ) {
        message( Using ../.. as INCLUDE_DIR )
        INCLUDE_DIR = ../..
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
      exists( ../../QGLViewer/$${LIB_NAME} ) {
        message( Using ../../QGLViewer as LIB_DIR )
        LIB_DIR = ../../QGLViewer
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

  # Compilation from zip file : libQGLViewer is located in ../..
  exists( ../../QGLViewer ) {
    exists( ../../QGLViewer/qglviewer.h ) {
      INCLUDEPATH *= ../..
    }
    
    LIB_FILE = QGLViewer*.lib

    exists( ../../QGLViewer/$${LIB_FILE} ) {
      LIB_PATH = ../../QGLViewer
    }
  }

  LIBS *= -L$${LIB_PATH} -lQGLViewer2
}}
