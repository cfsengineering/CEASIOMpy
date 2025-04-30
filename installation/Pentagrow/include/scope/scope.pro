# qmake project file for scope

TEMPLATE = app
TARGET   = dwfscope
CONFIG  *= warn_on thread exceptions stl rtti openmp qglviewer fastlapack

# without a functional LAPACK implementation, the windows
# port requires that the Intel MKL is present
win32 { 
  CONFIG += mkl
  LIBS += -lAdvapi32
}

greaterThan(QT_MAJOR_VERSION, 4) {
    QT += core gui xml opengl printsupport widgets
} else {
    QT += core gui xml opengl svg 	
}

DEFINES += GLEW_STATIC
INCLUDEPATH += ..

CONFIG(debug, debug|release) {
  TARGET = $$join(TARGET,,,_debug)
  LIBS += -lsurf_debug -lgenua_debug -lpredicates
} else {
  LIBS += -lsurf -lgenua -lpredicates
}

include(../config/appconfig.pri)
DESTDIR = $$TARGET_BIN_DIR

macx:ICON += icons/scope.icns

unix {
  documentation.files = ./userdoc/scope-userdoc/site/*
  documentation.path = /usr/share/doc/dwfscope/
  target.path = /usr/bin
  INSTALLS += target documentation 
  LIBS += -lboost_components
}

win32 {

  # LIBS *= $$TARGET_LIB_DIR/mkl_sumo.lib

  spacenav {
    HEADERS += spacenav/I3dMouseParams.h \
               spacenav/Mouse3Dinput.h \
               spacenav/MouseParameters.h \
               spacenav/eventfilter.h
    SOURCES += spacenav/Mouse3DInput.cpp \
               spacenav/Mouseparameters.cpp \
               spacenav/eventfilter.cpp
  }
}

exists(../config/local.pri) { 
  include(../config/local.pri) 
}

message("LIBS: " $$LIBS)

FORMS += dlgmeshcut.ui \
    cfgeditor.ui \
    processmonitor.ui \
    streamlinedlg.ui \
    transformdlg.ui \
    planegriddialog.ui \
    slicedlg.ui \
    elementinfobox.ui \
    nodeinfobox.ui \
    addmodeshapedialog.ui \
    editmeshdialog.ui \
    longmaneuvdialog.ui \
    ploaddialog.ui \
    directpmapdialog.ui \
    transientloaddialog.ui \
    harmonicloaddialog.ui \
    transformationdialog.ui \
    inrelloaddialog.ui \
    deformationmapdlg.ui \
    xmldisplay.ui \
    contourdialog.ui \
    componentdialog.ui \
    displacementdialog.ui \
    sectioncopydialog.ui \
    meshqualitydialog.ui \
    splitridgedialog.ui \
    surfacestreamlinedialog.ui \
    forcedisplaydialog.ui \
    buildfluttermodedialog.ui

HEADERS += scope.h \
    view.h \
    dlgmeshcut.h \
    glew.h \
    wglew.h \
    glxew.h \
    cfgeditor.h \
    processmonitor.h \
    streamlinedlg.h \
    transformdlg.h \
    planegrid.h \
    planegriddialog.h \
    slicedlg.h \
    elementinfobox.h \
    nodeinfobox.h \
    addmodeshapedialog.h \
    qsciencespinbox.h \
    fielddatamodel.h \
    editmeshdialog.h \
    longmaneuvdialog.h \
    ploaddialog.h \
    directpmapdialog.h \
    transientloaddialog.h \
    harmonicloaddialog.h \
    transformationdialog.h \
    inrelloaddialog.h \
    frfspec.h \
    tdlspec.h \
    qcustomplot.h \
    segmentplot.h \
    deformationmapdlg.h \
    xmltreeitem.h \
    xmltreemodel.h \
    xmldisplay.h \
    xmlattrtablemodel.h \
    treeitem.h \
    treemodel.h \
    flightpath.h \
    sidebartreeitem.h \
    sidebartreemodel.h \
    sidebartree.h \
    splitter.h \
    sectionplotter.h \
    meshplotter.h \
    pathplotter.h \
    plotcontroller.h \
    forward.h \
    contourdialog.h \
    version.h \
    componentdialog.h \
    plotprimitives.h \
    displacementdialog.h \
    hedgehogplotter.h \
    spacenav/spacemouseinterface.h \
    sectioncopydialog.h \
    meshqualitydialog.h \
    util.h \
    signallinglogger.h \
    splitridgedialog.h \
    surfacestreamlinedialog.h \
    streamlineplotter.h \
    forcedisplaydialog.h \
    buildfluttermodedialog.h

SOURCES += main.cpp \
    scope.cpp \
    view.cpp \
    dlgmeshcut.cpp \
    glew.c \
    cfgeditor.cpp \
    processmonitor.cpp \
    streamlinedlg.cpp \
    transformdlg.cpp \
    planegrid.cpp \
    planegriddialog.cpp \
    slicedlg.cpp \
    elementinfobox.cpp \
    nodeinfobox.cpp \
    addmodeshapedialog.cpp \
    qsciencespinbox.cpp \
    fielddatamodel.cpp \
    editmeshdialog.cpp \
    longmaneuvdialog.cpp \
    ploaddialog.cpp \
    directpmapdialog.cpp \
    transientloaddialog.cpp \
    harmonicloaddialog.cpp \
    transformationdialog.cpp \
    inrelloaddialog.cpp \
    tdlspec.cpp \
    qcustomplot.cpp \
    segmentplot.cpp \
    deformationmapdlg.cpp \
    xmltreeitem.cpp \
    xmltreemodel.cpp \
    xmldisplay.cpp \
    xmlattrtablemodel.cpp \
    treeitem.cpp \
    treemodel.cpp \
    flightpath.cpp \
    sidebartreeitem.cpp \
    sidebartreemodel.cpp \
    sidebartree.cpp \
    splitter.cpp \
    sectionplotter.cpp \
    meshplotter.cpp \
    pathplotter.cpp \
    plotcontroller.cpp \
    contourdialog.cpp \
    componentdialog.cpp \
    displacementdialog.cpp \
    hedgehogplotter.cpp \
    spacenav/spacemouseinterface.cpp \
    sectioncopydialog.cpp \
    meshqualitydialog.cpp \
    signallinglogger.cpp \
    splitridgedialog.cpp \
    surfacestreamlinedialog.cpp \
    streamlineplotter.cpp \
    forcedisplaydialog.cpp \
    buildfluttermodedialog.cpp

RESOURCES = icons.qrc
RC_FILE += scope_appicon.rc
