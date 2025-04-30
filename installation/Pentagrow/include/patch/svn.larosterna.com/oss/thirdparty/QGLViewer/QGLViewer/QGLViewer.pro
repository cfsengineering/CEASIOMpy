# l i b Q G L V i e w e r
# C o m p i l a t i o n    c o n f i g u r a t i o n
# Run "qmake; make; make install" to compile and install the library on Unix systems.
# Optional arguments can tune install paths (as in "qmake PREFIX=$HOME"). See doc/download.html for details.
# If your Qt version is lower than 3.1 (look at $QTDIR/lib), you need to link with GLUT.
# Uncomment the following line:
# USE_GLUT = yes
# modified to always build static lib
QGLVIEWER_STATIC = 1
TEMPLATE = lib
TARGET = QGLViewer
VERSION = 2.3.1
CONFIG *= qt opengl staticlib thread rtti
include(../../config/rootconfig.pri)
DESTDIR = $$TARGET_LIB_DIR
CONFIG(debug, debug|release):TARGET = $$join(TARGET,,,_debug)
HEADERS = qglviewer.h \
    camera.h \
    manipulatedFrame.h \
    manipulatedCameraFrame.h \
    frame.h \
    constraint.h \
    keyFrameInterpolator.h \
    mouseGrabber.h \
    quaternion.h \
    vec.h \
    domUtils.h \
    config.h

SOURCES = qglviewer.cpp \
    camera.cpp \
    manipulatedFrame.cpp \
    manipulatedCameraFrame.cpp \
    frame.cpp \
    saveSnapshot.cpp \
    constraint.cpp \
    keyFrameInterpolator.cpp \
    mouseGrabber.cpp \
    quaternion.cpp \
    vec.cpp
DISTFILES *= qglviewer-icon.xpm
TRANSLATIONS = qglviewer_fr.ts
QT_VERSION = $$[QT_VERSION]

# settings for Qt4

QT *= xml opengl
FORMS *= ImageInterface.Qt4.ui

# settings for Qt5
contains( QT_VERSION, "^5.*" ) {
    QT *= widgets
}

!isEmpty( QGLVIEWER_STATIC ):CONFIG *= staticlib


# --  V e c t o r i a l   R e n d e r i n g  --
# In case of compilation troubles with vectorial rendering, uncomment this line
DEFINES *= NO_VECTORIAL_RENDER
contains( DEFINES, NO_VECTORIAL_RENDER ):message( Vectorial rendering disabled )
else { 
    FORMS *= VRenderInterface.Qt4.ui
    SOURCES *= VRender/BackFaceCullingOptimizer.cpp \
        VRender/BSPSortMethod.cpp \
        VRender/EPSExporter.cpp \
        VRender/Exporter.cpp \
        VRender/FIGExporter.cpp \
        VRender/gpc.cpp \
        VRender/ParserGL.cpp \
        VRender/Primitive.cpp \
        VRender/PrimitivePositioning.cpp \
        VRender/TopologicalSortMethod.cpp \
        VRender/VisibilityOptimizer.cpp \
        VRender/Vector2.cpp \
        VRender/Vector3.cpp \
        VRender/NVector3.cpp \
        VRender/VRender.cpp
    HEADERS *= VRender/AxisAlignedBox.h \
        VRender/Exporter.h \
        VRender/gpc.h \
        VRender/NVector3.h \
        VRender/Optimizer.h \
        VRender/ParserGL.h \
        VRender/Primitive.h \
        VRender/PrimitivePositioning.h \
        VRender/SortMethod.h \
        VRender/Types.h \
        VRender/Vector2.h \
        VRender/Vector3.h \
        VRender/VRender.h
}

# --  U n i x  --
unix { 
    # INCLUDE_DIR and LIB_DIR specify where to install the include files and the library.
    # Use qmake INCLUDE_DIR=... LIB_DIR=... , or qmake PREFIX=... to customize your installation.
    isEmpty( PREFIX ):PREFIX = /usr
    isEmpty( LIB_DIR ):LIB_DIR = $${PREFIX}/lib
    isEmpty( INCLUDE_DIR ):INCLUDE_DIR = $${PREFIX}/include
    isEmpty( DOC_DIR ):DOC_DIR = $${PREFIX}/share/doc
    
    # GLUT for Unix architecture
    !isEmpty( USE_GLUT ):QMAKE_LIBS_OPENGL *= -lglut
    #MOC_DIR = .moc
    #OBJECTS_DIR = .obj
    
    # Adds a -P option so that "make install" as root creates files owned by root and links are preserved.
    # This is not a standard option, and it may have to be removed on old Unix flavors.
    !hpux:QMAKE_COPY_FILE = $${QMAKE_COPY_FILE} \
        -P
    
    # Make much smaller libraries (and packages) by removing debugging informations
    QMAKE_CFLAGS_RELEASE -= -g
    QMAKE_CXXFLAGS_RELEASE -= -g
    
    # install header
    include.path = $${INCLUDE_DIR}/QGLViewer
    include.files = $${HEADERS} \
        qglviewer.cw \
        qglviewer_*.qm
    
    # install documentation html
    documentation.path = $${DOC_DIR}/QGLViewer
    documentation.files = ../doc/*.html \
        ../doc/*.css
    
    # install documentation images
    docImages.path = $${DOC_DIR}/QGLViewer/images
    docImages.files = ../doc/images/*
    
    # install documentation examples
    # docExamples.path = $${DOC_DIR}/QGLViewer/examples
    # docExamples.files = ../examples/*../examples/*/*
    # install documentation refManual
    docRefManual.path = $${DOC_DIR}/QGLViewer/refManual
    docRefManual.files = ../doc/refManual/*
    
    # install static library
    # staticlib.extra = make -f Makefile.Release staticlib
    # staticlib.path = $${LIB_DIR}
    # staticlib.files = lib$${TARGET}.a
    # install library
    target.path = $${LIB_DIR}
    
    # "make install" configuration options
    INSTALLS *= target \
        include \
        documentation \
        docImages \
        docRefManual
}

# --  S G I   I r i x  --
irix-cc|irix-n32 { 
    QMAKE_CFLAGS_RELEASE -= -O3 \
        -O2 \
        -OPT:Olimit=30000
    QMAKE_LFLAGS_RELEASE -= -O3 \
        -O2 \
        -OPT:Olimit=30000
    QMAKE_CXXFLAGS_RELEASE -= -O3 \
        -O2 \
        -OPT:Olimit=30000
    QMAKE_CFLAGS_RELEASE *= -IPA \
        -Ofast=IP35
    QMAKE_LFLAGS_RELEASE *= -IPA \
        -Ofast=IP35
    QMAKE_CXXFLAGS_RELEASE *= -IPA \
        -Ofast=IP35
    QMAKE_CFLAGS *= -LANG:std
    QMAKE_LFLAGS *= -LANG:std
    QMAKE_CXXFLAGS *= -LANG:std
    QMAKE_CFLAGS *= -woff \
        1424,3201,1110,1188
    QMAKE_CXXFLAGS *= -woff \
        1424,3201,1110,1188
    QMAKE_LIBS_OPENGL -= -lXi
    
    # GLUT for SGI architecture
    !isEmpty( USE_GLUT ) { 
        QMAKE_LIBDIR_OPENGL *= /usr/local/lib32
        QMAKE_INCDIR_OPENGL *= /usr/local/include
    }
}

# --  M a c O S X  --
macx|darwin-g++ { 
    CONFIG -= lib_bundle
    CONFIG -= debug_and_release
    
    # GLUT for Macintosh architecture
    !isEmpty( USE_GLUT ) { 
        QMAKE_LIBS_OPENGL -= -lglut
        QMAKE_LIBS_OPENGL *= -framework GLUT -lobjc
    }
}

# --  W i n d o w s  --
win32 { 
    staticlib:DEFINES *= QGLVIEWER_STATIC
    else:DEFINES *= CREATE_QGLVIEWER_DLL
    MOC_DIR = moc
    OBJECTS_DIR = obj
    
    # Use the DLL version of Qt (needed for Qt3 only)
    DEFINES *= QT_THREAD_SUPPORT
    CONFIG *= embed_manifest_dll
}
