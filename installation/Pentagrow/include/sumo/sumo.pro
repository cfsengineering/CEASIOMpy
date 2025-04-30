# qmake project file for sumo
TEMPLATE = app
INCLUDEPATH += ..
TARGET = dwfsumo
CONFIG += warn_on thread exceptions stl rtti qglviewer fastlapack openmp

win32 { 
  CONFIG += mkl
  LIBS += -lAdvapi32
}
macx:CONFIG += netcdf

greaterThan(QT_MAJOR_VERSION, 4) {
    QT += core gui xml opengl printsupport widgets
} else {
    QT += core gui xml opengl svg 	
}

DEFINES += GLEW_STATIC XML_STATIC

CONFIG(debug, debug|release) { 
    TARGET = $$join(TARGET,,,-debug)
    LIBS += -lsurf_debug -lpredicates_debug -lgenua_debug -lboost_components_debug
    # LIBS += -lsurf_debug -lgenua -lboost_components
}
else:LIBS += -lsurf -lpredicates -lgenua -lboost_components
include(../config/appconfig.pri)
DESTDIR = $$TARGET_BIN_DIR



macx:ICON += icons/bjet6.icns

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

FORMS += dlgairfoil.ui \
    dlgcreateassembly.ui \
    dlgdefinecontrol.ui \
    dlgdrawoptions.ui \
    dlgeditbody.ui \
    dlgeditframe.ui \
    dlgeditjetengine.ui \
    dlgeditsection.ui \
    dlgeditwing.ui \
    dlgframeshapes.ui \
    dlgmeshoptions.ui \
    dlgsavemesh.ui \
    dlgtetgen.ui \
    dlgexportrow.ui \
    dlgxptritet.ui \
    wingstat.ui \
    nacellegeometrydlg.ui \
    endcapdlg.ui \
    transformationdialog.ui \
    wavedragdlg.ui \
    wingsectionfitdlg.ui \
    dlgglobaltransform.ui

HEADERS +=  spacenav/spacemouseinterface.h \
    aabb.h \
    qcustomplot.h \
    assembly.h \
    assemblytree.h \
    bezierpainter.h \
    bodyframe.h \
    bodyskeleton.h \
    component.h \
    componentlibrary.h \
    createassembly.h \
    cseditorwidget.h \
    csmbody.h \
    csmcomponent.h \
    csmcontroldef.h \
    csmfairing.h \
    csmgenerator.h \
    csmwing.h \
    ctpattern.h \
    ctsurface.h \
    ctsystem.h \
    dlgairfoil.h \
    dlgsavemesh.h \
    dlgtetgen.h \
    editbody.h \
    editframeproperties.h \
    exportrow.h \
    exporttritet.h \
    frameeditor.h \
    framepainter.h \
    frameshapes.h \
    frameshapeconstraint.h \
    frameviewitem.h \
    jetengineeditor.h \
    jetenginespec.h \
    meshdrawoptions.h \
    meshoptions.h \
    mgenprogressctrl.h \
    pool.h \
    renderview.h \
    sectioneditor.h \
    shelltreeitems.h \
    skeletonview.h \
    skeletonwidget.h \
    sumo.h \
    trimeshview.h \
    wingmanagerwidget.h \
    wingsection.h \
    wingskeleton.h \
    nacellegeometrydlg.h \
    glew.h \
    glxew.h \
    wglew.h \
    endcapdlg.h \
    splitter.h \
    transformationdialog.h \
    qsciencespinbox.h \
    cgpainter.h \
    productpainter.h \
    productoverlay.h \
    tritree.h \
    treetraverse.h \
    frameprojector.h \
    wavedragdlg.h \
    forward.h \
    version.h \
    wingsectionfitdlg.h \
    fitindicator.h \
    batchrun.h \
    reportingpentagrow.h \
    util.h \
    dlgglobaltransform.h

SOURCES += spacenav/spacemouseinterface.cpp \
    qcustomplot.cpp \
    assembly.cpp \
    assemblytree.cpp \
    batchrun.cpp \
    bezierpainter.cpp \
    bodyframe.cpp \
    bodyskeleton.cpp \
    component.cpp \
    componentlibrary.cpp \
    createassembly.cpp \
    cseditorwidget.cpp \
    csmbody.cpp \
    csmcomponent.cpp \
    csmcontroldef.cpp \
    csmfairing.cpp \
    csmgenerator.cpp \
    csmwing.cpp \
    ctpattern.cpp \
    ctsurface.cpp \
    ctsystem.cpp \
    dlgairfoil.cpp \
    dlgsavemesh.cpp \
    dlgtetgen.cpp \
    editbody.cpp \
    editframeproperties.cpp \
    exportrow.cpp \
    exporttritet.cpp \
    frameeditor.cpp \
    framepainter.cpp \
    frameshapeconstraint.cpp \
    frameshapes.cpp \
    frameviewitem.cpp \
    jetengineeditor.cpp \
    jetenginespec.cpp \
    main.cpp \
    meshdrawoptions.cpp \
    meshoptions.cpp \
    mgenprogressctrl.cpp \
    pool.cpp \
    renderview.cpp \
    sectioneditor.cpp \
    shelltreeitems.cpp \
    skeletonview.cpp \
    skeletonwidget.cpp \
    sumo.cpp \
    trimeshview.cpp \
    wingmanagerwidget.cpp \
    wingsection.cpp \
    wingskeleton.cpp \
    nacellegeometrydlg.cpp \
    glew.c \
    endcapdlg.cpp \
    splitter.cpp \
    transformationdialog.cpp \
    qsciencespinbox.cpp \
    cgpainter.cpp \
    productpainter.cpp \
    productoverlay.cpp \
    tritree.cpp \
    frameprojector.cpp \
    wavedragdlg.cpp \
    wingsectionfitdlg.cpp \
    fitindicator.cpp \
    reportingpentagrow.cpp \
    dlgglobaltransform.cpp

RESOURCES += icons.qrc \
    smxtemplates.qrc \
    smxcomponents.qrc \
    airfoillib.qrc
RC_FILE += sumo_appicon.rc













