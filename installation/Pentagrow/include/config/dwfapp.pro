# qmake settings for applications
# use library settings
include(dwfroot.pro)

# define CONFIG options for genua, cgns, zip, etc
unix:QMAKE_LFLAGS += -L$$PREFIX_LIB
libgenua:LIBS += -lgenua \
    -lboost_components \
    -lexpat
minizip:LIBS += -lminizip
cgns:LIBS += -lcgns
qglviewer { 
    DEFINES += QGLVIEWER_STATIC
    INCLUDEPATH += ../QGLViewer
    LIBS += -lQGLViewer
    QT += opengl \
        xml
    win32:LIBS += -lopengl32 \
        -lglu32
}

# to add in local expat, use this
# not needed for Qt apps on Linux, where Qt pulls in fontconfig,
# which uses expat anyway
# LIBS += $$PREFIX/lib/libexpat.a
# ## configuration dependent
# Note on libs:
# Lapack can be statically linked against compiler fortran runtime
# Use the localqt CONFIG variable to link with a local Qt installation
linux-g++-32 { 
    # use static libs whenever possible to avoid too many
    # dependencies in the final package
    QMAKE_FLAGS += -m32
    INCLUDEPATH += /usr/include/GL
    
    # set this config option when compiling against a locally
    # compiled version of Qt
    localqt { 
        QT -= core \
            gui \
            xml \
            opengl
        QTDIR = /opt/Qt-4.4.3/32bit/
        INCLUDEPATH += $$QTDIR/include/QtCore \
            $$QTDIR/include/QtGui \
            $$QTDIR/include/QtXml \
            $$QTDIR/include/QtOpenGL
        LIBS += $$QTDIR/lib/libQtOpenGL.a \
            $$QTDIR/lib/libQtGui.a \
            $$QTDIR/lib/libQtXml.a \
            $$QTDIR/lib/libQtCore.a
    }
    
    # link against atlas lapack
    fastlapack:LIBS += /usr/local/lib/libfastlapack.a \
        `gcc \
        -m32 \
        -print-file-name=libgfortran.a`
    
    # link against reference fortran lapack
    reflapack:LIBS += /usr/local/lib/libreflapack.a \
        `gcc \
        -m32 \
        -print-file-name=libgfortran.a`
}
linux-g++-64 { 
    INCLUDEPATH += /usr/include/GL
    
    # set this config option when compiling against a locally
    # compiled version of Qt
    localqt { 
        QT -= core \
            gui \
            xml \
            opengl
        QTDIR = /opt/Qt-4.4.3/64bit/
        INCLUDEPATH += $$QTDIR/include/QtCore \
            $$QTDIR/include/QtGui \
            $$QTDIR/include/QtXml \
            $$QTDIR/include/QtOpenGL
        LIBS += $$QTDIR/lib/libQtOpenGL.a \
            $$QTDIR/lib/libQtGui.a \
            $$QTDIR/lib/libQtXml.a \
            $$QTDIR/lib/libQtCore.a
    }
    
    # link against atlas lapack
    fastlapack:LIBS += /usr/local/lib64/libfastlapack.a \
        `gcc \
        -m64 \
        -print-file-name=libgfortran.a`
    
    # link against reference fortran lapack
    reflapack:LIBS += /usr/local/lib64/libreflapack.a \
        `gcc \
        -m64 \
        -print-file-name=libgfortran.a`
}
linux-icc { 
    reflapack:LIBS += /usr/local/lib64/libreflapack.a \
        `gcc \
        -m64 \
        -print-file-name=libgfortran.a`
    fastlapack:LIBS += /usr/local/lib64/libfastlapack.a \
        `gcc \
        -m64 \
        -print-file-name=libgfortran.a`
    mkl { 
        MKLPATH = /opt/intel/Compiler/11.0/069/mkl/lib/em64t
        LIBS += -openmp \
            -L$$MKLPATH \
            -lmkl_lapack \
            -lmkl \
            -lpthread
    }
}
macx { 
    QMAKE_LFLAGS += -headerpad_max_install_names
    LIBS += -framework \
        vecLib \
        -framework \
        CoreFoundation \
        -framework \
        IOKit
}
win32-g++ { 
    posix_threads:LIBS += -lpthread.dll
    debug:CONFIG += console
    reflapack|fastlapack:LIBS += -llapack_win32 \
        -lblas_win32
    LIBS += -lIphlpapi
}
win32-msvc2005|win32-msvc2008 { 
    QMAKE_LFLAGS += -LIBPATH:$$PREFIX_LIB
    LIBS += -lIphlpapi
}
