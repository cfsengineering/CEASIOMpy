
/* ------------------------------------------------------------------------
 * project:    scope
 * file:       scope.h
 * begin:      July 2005
 * copyright:  (c) 2005 by <dlr@kth.se>
 * ------------------------------------------------------------------------
 * main window for mesh data vizualization tool
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */


#include <QApplication>
#include <QDesktopWidget>
#include <QFileDialog>
#include <QAction>
#include <QMenu>
#include <QToolBar>
#include <QMessageBox>
#include <QStatusBar>
#include <QMenuBar>
#include <QSettings>
#include <QDragEnterEvent>
#include <QInputDialog>
#include <QUrl>
#include <QFrame>
#include <QMimeData>
#include <QBoxLayout>

#include "util.h"
#include "buildfluttermodedialog.h"
#include "displacementdialog.h"
#include "dlgmeshcut.h"
#include "transformdlg.h"
#include "planegriddialog.h"
#include "slicedlg.h"
#include "elementinfobox.h"
#include "nodeinfobox.h"
#include "addmodeshapedialog.h"
#include "editmeshdialog.h"
#include "longmaneuvdialog.h"
#include "directpmapdialog.h"
#include "inrelloaddialog.h"
#include "deformationmapdlg.h"
#include "transformationdialog.h"
#include "contourdialog.h"
#include "componentdialog.h"
#include "sectioncopydialog.h"
#include "meshqualitydialog.h"
#include "forcedisplaydialog.h"
#include "scope.h"
#include "sidebartree.h"
#include "sidebartreemodel.h"
#include "meshplotter.h"
#include "plotcontroller.h"
#include "version.h"
#include "spacenav/spacemouseinterface.h"

#include <genua/sysinfo.h>
#include <genua/timing.h>
#include <genua/mxsolutiontree.h>
#include <surf/rbfinterpolator.h>
#include <surf/flapspec.h>

#include <QGLFormat>
#include <QDesktopServices>

using namespace std;
using namespace Qt;

Scope::Scope() : QMainWindow()
{
  // set window icon
  QMainWindow::setWindowIcon(QIcon(":/icons/contours.png"));
  QMainWindow::setAttribute(Qt::WA_DeleteOnClose, true);
  QMainWindow::setAcceptDrops(true);

  // interface for mesh display
  plotControl = new PlotController;

  // create an empty data plotter
  view = new ViewManager(this);
  view->assign(plotControl);

  // try to connect to SpaceNavigator
  if (SpaceMouseInterface::connectDevice(view)) {
    connect( SpaceMouseInterface::globalInterface(),
             SIGNAL(axisMotion(const SpaceMouseMotionData&)),
             view, SLOT(multiAxisControl(const SpaceMouseMotionData&)) );
    connect( SpaceMouseInterface::globalInterface(),
             SIGNAL(buttonPressed(uint)),
             view, SLOT(multiAxisButtonPressed(uint)) );
  }

  // create tree model w/o assigned machine
  treeModel = new SidebarTreeModel(this);
  treeView = new SidebarTree(this);
  treeView->header()->setVisible(false);
  treeView->setModel( treeModel );

#ifdef Q_OS_MAC
  treeView->setFrameStyle(QFrame::NoFrame);
  treeView->setAttribute(Qt::WA_MacShowFocusRect, false);
  treeView->setAutoFillBackground(true);

  QPalette color_palette = this->palette();
  QColor macSidebarColor(231, 237, 246);
  if (SysInfo::osversion() > SysInfo::OSX_1060)
    macSidebarColor = QColor(220, 226, 232);
  QColor macSidebarHighlightColor(168, 183, 205);
  color_palette.setColor(QPalette::Base, macSidebarColor);
  color_palette.setColor(QPalette::Highlight, macSidebarHighlightColor);
  setPalette(color_palette);
#endif

  mwRightFrame = new QFrame(this);
  mwRightFrame->setFrameStyle( treeView->frameStyle() );
  mwRightFrame->setFrameShape( treeView->frameShape() );
  mwFrameLayout = new QBoxLayout(QBoxLayout::TopToBottom, mwRightFrame);
  mwFrameLayout->setContentsMargins(0, 0, 0, 0);
  mwFrameLayout->addWidget(view);

  // ... and a splitter to separate the two
  mwSplitter = new Splitter(Qt::Horizontal, this);
  mwSplitter->addWidget(treeView);
  mwSplitter->addWidget(mwRightFrame);

  initActions();
  initMenus();
  
  // connect status bar message to MeshView signal
  connect(view, SIGNAL(postStatusMessage(const QString&)),
          statusBar(), SLOT(showMessage(const QString&)));

  // switch animation button icon
  connect(view, SIGNAL(animationRunning(bool)),
          this, SLOT(togglePlayButton(bool)));

  // display element information
  connect(view, SIGNAL(elementPicked(int)),
          this, SLOT(elementInfo(int)));

  // display node information
  connect(view, SIGNAL(nodePicked(int)),
          this, SLOT(nodeInfo(int)));

  // update tree when mesh structure changed
  connect( plotControl, SIGNAL(structureChanged()),
           this, SLOT(updateTree()) );

  // stop animations when plotControl asked for that
  connect( plotControl, SIGNAL(animationDone()),
           view, SLOT(stopAnimation()) );

  // forward messages
  connect( plotControl, SIGNAL(postStatusMessage(QString)),
           statusBar(), SLOT(showMessage(QString)) );

  // update view on request
  connect( plotControl, SIGNAL(needRedraw()),
           view, SLOT(updateRepaint()) );

  // switch section/boco visibility on/off
  connect(treeView, SIGNAL(showSection(int, bool)),
          plotControl, SLOT(showSection(int, bool)));
  connect(treeView, SIGNAL(showBoco(int, bool)),
          plotControl, SLOT(showBoco(int, bool)));
  connect(treeView, SIGNAL(colorsChanged(int)),
          plotControl, SLOT(uploadSectionColor(int)));

  // display field using default settings when selected in sidebar
  connect(treeView, SIGNAL(plotField(int)),
          plotControl, SLOT(contourField(int)));

  // open settings dialog when requested from sidebar context menu
  connect(treeView, SIGNAL(editSection(int)),
          this, SLOT(editSection(int)));
  connect(treeView, SIGNAL(editBoco(int)),
          this, SLOT(editBoco(int)));
  connect(treeView, SIGNAL(editField(int)),
          this, SLOT(colorContours(int)) );

  view->setFocus();
  setCentralWidget(mwSplitter);
  statusBar()->showMessage( tr("Ready"), 2000 );

  // QRect sg = qApp->desktop()->screenGeometry();
  // resize( int(0.9*sg.width()), int(0.9*sg.height()) );

  // partition central widget between sidebar and main view
  const int splitterWidth = min(300, max(width()/5, 100));
  QList<int> spw;
  spw << splitterWidth << width() - splitterWidth;
  mwSplitter->setSizes(spw);

  // recover last directory visited
  QSettings settings;
  lastdir = settings.value("last-directory", QString()).toString();
  resize( setting("last-size", QSize(600,400)).toSize() );

  setUnifiedTitleAndToolBarOnMac(true);	
}

Scope::~Scope()
{
  SpaceMouseInterface::disconnectDevice();

  changeSetting("last-directory", lastdir);
  changeSetting("last-size", size());
  changeSetting("scope-mainwindow-maximized", isMaximized());

  delete dlgDisplace;
  delete dlgGrid;
  delete dlgSlice;
  delete elmInfoBox;
  delete nodeInfoBox;
  delete dlgLongLoads;
  delete dlgDirectPMap;
  delete dlgInrelLoads;
  delete dlgMeshQuality;
}

void Scope::initActions()
{
  QSettings settings;

  // action groups
  pickActions = new QActionGroup(this);

  // open new (empty) window
  newMainAct = new QAction( QIcon(":/icons/new_window.png"),
                            tr("&New view"), this );
  newMainAct->setShortcut(tr("Ctrl+N"));
  newMainAct->setIconText(tr("New"));
  newMainAct->setStatusTip(tr("Open a new scope view"));
  connect( newMainAct, SIGNAL(triggered()), this, SLOT(newView()) );

  // close main window
  closeMainAct = new QAction( QIcon(":/icons/close_window.png"),
                              tr("&Close"), this );
  closeMainAct->setShortcut(tr("Ctrl+W"));
  closeMainAct->setIconText(tr("Close"));
  closeMainAct->setStatusTip(tr("Close this view"));
  connect( closeMainAct, SIGNAL(triggered()), this, SLOT(close()) );

  //
  // file operations
  //
  openAct = new QAction( QIcon(":/icons/fileopen.png"),
                         tr("&Open file..."), this );
  openAct->setShortcut(tr("Ctrl+O"));
  openAct->setIconText(tr("Open"));
  openAct->setStatusTip(tr("Open new data file"));
  connect( openAct, SIGNAL(triggered()), this, SLOT(choose()) );
  
  loadTjAct = new QAction( QIcon(":/icons/fileopen.png"),
                           tr("Load &trajectory..."), this );
  loadTjAct->setShortcut(tr("Ctrl+T"));
  loadTjAct->setStatusTip(tr("Open plain text trajectory data file"));
  connect( loadTjAct, SIGNAL(triggered()), this, SLOT(loadTrajectory()) );

  snapshotAct = new QAction( QIcon(":/icons/snapshot.png"),
                             tr("Save screenshot..."), this );
  snapshotAct->setStatusTip(tr("Save current view to file"));
  snapshotAct->setIconText(tr("Snapshot"));
  connect( snapshotAct, SIGNAL(triggered()), view, SLOT(saveSnapshot()) );
  
  saveAct = new QAction( QIcon(":/icons/filesaveas.png"),
                         tr("&Save file as..."), this );
  saveAct->setShortcut(tr("Ctrl+S"));
  saveAct->setIconText(tr("Export"));
  saveAct->setStatusTip(tr("Save visualization file"));
  connect( saveAct, SIGNAL(triggered()), this, SLOT(save()) );
  
  embedNoteAct = new QAction( QIcon(":/icons/fileopen.png"),
                              tr("&Embed annotation..."), this );
  embedNoteAct->setStatusTip(tr("Embed annotation from xml/zml file."));
  connect( embedNoteAct, SIGNAL(triggered()), this, SLOT(embedNote()) );

  helpAct = new QAction( tr("User Manual"), this );
  connect( helpAct, SIGNAL(triggered()), this, SLOT(openHelp()) );

  aboutAct = new QAction( tr("About scope"), this );
  connect( aboutAct, SIGNAL(triggered()), this, SLOT(about()) );
  
  quitAct = new QAction( QIcon(":/icons/exit.png"),
                         tr("&Quit"), this );
  quitAct->setShortcut(tr("Ctrl+Q"));
  quitAct->setStatusTip(tr("Exit"));
  connect( quitAct, SIGNAL(triggered()), this, SLOT(close()) );

  //
  // View operations
  //

  fitScreenAct = new QAction( QIcon(":/icons/fullscreen.png"),
                              tr("&Fit display to screen"), this );
  fitScreenAct->setStatusTip(tr("Scale active display object to fit window size"));
  fitScreenAct->setIconText(tr("Fit Screen"));
  connect( fitScreenAct, SIGNAL(triggered()), this, SLOT(fitScreen()) );

  surfContoursAct = new QAction( QIcon(":/icons/contours.png"),
                                 tr("Surface &color contours..."), this );
  surfContoursAct->setStatusTip(tr("Change surface color contours"));
  surfContoursAct->setIconText(tr("Fields"));
  connect( surfContoursAct, SIGNAL(triggered()), this, SLOT(colorContours()) );

  componentsAct = new QAction( QIcon(":/icons/configure.png"),
                               tr("Mesh &section display"), this );
  componentsAct->setStatusTip(tr("Switch mesh section display on/off"));
  componentsAct->setIconText(tr("Components"));
  connect( componentsAct, SIGNAL(triggered()), this, SLOT(editSection()) );

  dispSettingsAct = new QAction( QIcon(":/icons/modeshape.png"),
                                 tr("Mesh &deformation settings..."), this );
  dispSettingsAct->setStatusTip(tr("Select mesh deformation options"));
  dispSettingsAct->setIconText(tr("Deformation"));
  connect( dispSettingsAct, SIGNAL(triggered()),
           this, SLOT(deformationSettings()) );

  plotHedgehogAct = new QAction(
        tr("&Hedgehog plot..."), this );
  plotHedgehogAct->setStatusTip(tr("Display vector fields using line overlay"));
  connect( plotHedgehogAct, SIGNAL(triggered()),
           plotControl, SLOT(openHedgehogDialog()) );

  plotStreamlinesAct = new QAction(
        tr("Stream&line plot..."), this );
  plotStreamlinesAct->setStatusTip(tr("Display vector fields using line overlay"));
  connect( plotStreamlinesAct, SIGNAL(triggered()),
           plotControl, SLOT(openStreamlineDialog()) );

  meshQualityAct = new QAction(
        tr("Mesh &quality display..."), this );
  meshQualityAct->setStatusTip(tr("Display bad volume elements"));
  connect( meshQualityAct, SIGNAL(triggered()), this, SLOT(meshQuality()) );

  toggleGridAct = new QAction(
        tr("Display &grid planes"), this );
  toggleGridAct->setStatusTip(tr("Display coordinate grid planes"));
  connect( toggleGridAct, SIGNAL(triggered()), this, SLOT(gridPlanes()) );

  elemInfoAct = new QAction( QIcon(":/icons/triangle.png"),
                             tr("Element information"), this );
  elemInfoAct->setStatusTip(tr("Display information about picked element"));
  elemInfoAct->setCheckable(true);
  elemInfoAct->setIconText(tr("Element"));
  connect( elemInfoAct, SIGNAL(toggled(bool)), view, SLOT(togglePickElement(bool)) );
  pickActions->addAction(elemInfoAct);

  nodeInfoAct = new QAction( QIcon(":/icons/node.png"),
                             tr("Node information"), this );
  nodeInfoAct->setStatusTip(tr("Display information about picked node"));
  nodeInfoAct->setCheckable(true);
  nodeInfoAct->setIconText(tr("Node"));
  connect( nodeInfoAct, SIGNAL(toggled(bool)), view, SLOT(togglePickNode(bool)) );
  pickActions->addAction(nodeInfoAct);

  integPressureAct = new QAction(tr("Integrate pressure"), this);
  integPressureAct->setStatusTip(tr("Integrate pressure field "
                                    "over mesh sections."));
  connect(integPressureAct, SIGNAL(triggered()),
          this, SLOT(integratePressure()));

  bool usePerspective = settings.value("scope-perspective-projection",
                                       true).toBool();
  perspAct = new QAction(
        tr("Perspective projection"), this );
  perspAct->setStatusTip(tr("Switch between perspective and"
                            " orthographic projection"));
  perspAct->setCheckable(true);
  perspAct->setChecked( usePerspective );
  perspAct->setIconText(tr("Perspective"));
  connect( perspAct, SIGNAL(toggled(bool)),
           view, SLOT(enablePerspectiveProjection(bool)) );

  bool enableaa = settings.value("scope-enable-fsaa", true).toBool();
  fsaaAct = new QAction(tr("Enable multisampling"), this );
  fsaaAct->setStatusTip(tr("Enable full-scene multisampling anti-aliasing on "
                           "program startup"));
  fsaaAct->setCheckable(true);
  fsaaAct->setChecked( enableaa );
  connect( fsaaAct, SIGNAL(toggled(bool)),
           this, SLOT(enableMultisampling(bool)) );

  bool enable_blend= settings.value("scope-enable-blendaa",
                                    (not view->ishidpi())).toBool();
  blendAct = new QAction(tr("Enable blended anti-aliasing"), this );
  blendAct->setStatusTip(tr("Enable polygon and line anti-aliasing by"
                            "alpha blending on program startup"));
  blendAct->setCheckable(true);
  blendAct->setChecked( enable_blend );
  connect( blendAct, SIGNAL(toggled(bool)),
           this, SLOT(enableBlending(bool)) );

  //
  // Edit operations
  //

  meshInfoAct = new QAction(
        tr("Mesh info..."), this );
  meshInfoAct->setStatusTip(tr("Display and change mesh properties"));
  connect( meshInfoAct, SIGNAL(triggered()), this, SLOT(meshInfo()) );
  meshInfoAct->setEnabled(false);

  mergeMeshAct = new QAction(
        tr("Merge mesh..."), this );
  mergeMeshAct->setStatusTip(tr("Merge current mesh with mesh from file"));
  connect( mergeMeshAct, SIGNAL(triggered()), this, SLOT(mergeMesh()) );

  copySectionAct = new QAction(
        tr("Miror copy sections..."), this );
  copySectionAct->setStatusTip(tr("Create a mirror copy of "
                                  "existing mesh sections"));
  connect( copySectionAct, SIGNAL(triggered()), this, SLOT(copySection()) );
  copySectionAct->setEnabled(false);

  rmIdleNodesAct = new QAction(
        tr("Remove unused nodes..."), this );
  rmIdleNodesAct->setStatusTip(tr("Eliminate nodes which are no longer" " "
                                  "referenced by any mesh section."));
  connect( rmIdleNodesAct, SIGNAL(triggered()), this, SLOT(rmIdleNodes()) );
  rmIdleNodesAct->setEnabled(false);

  meshCutAct = new QAction( QIcon(":/icons/meshcut.png"),
                            tr("Show &plane mesh cut..."), this );
  meshCutAct->setIconText(tr("Volume Slice"));
  meshCutAct->setStatusTip(tr("Compute a slice through volume elements"));
  connect( meshCutAct, SIGNAL(triggered()), this, SLOT(cutMesh()) );

  meshQualityAct = new QAction(
        tr("Mesh &quality display..."), this );
  meshQualityAct->setStatusTip(tr("Display mesh quality"));
  connect( meshQualityAct, SIGNAL(triggered()), this, SLOT(meshQuality()) );

  meshTrafoAct = new QAction(
        tr("&Transform nodes..."), this );
  meshTrafoAct->setStatusTip(tr("Geometric transformations on mesh nodes."));
  connect( meshTrafoAct, SIGNAL(triggered()), this, SLOT(meshTrafo()) );

  surfSliceAct = new QAction( QIcon(":/icons/dataslice.png"),
                              tr("Slice surface data"), this );
  surfSliceAct->setIconText(tr("Surface Slice"));
  surfSliceAct->setStatusTip(tr("Generate a plane slice through surface mesh."));
  connect( surfSliceAct, SIGNAL(triggered()), this, SLOT(surfaceSlice()) );

  addModeAct = new QAction(
        tr("Add rigid-body modeshapes"), this );
  addModeAct->setStatusTip(tr("Generate artificial rigid-body modes and append to mesh."));
  connect(addModeAct, SIGNAL(triggered()), this, SLOT(addRigidMode()) );
  addModeAct->setEnabled(false);

  genFlapDisp = new QAction( tr("Flap displacements..."), this );
  genFlapDisp->setStatusTip( tr("Generate element groups and displacement "
                                "fields from flap specifications.") );
  connect(genFlapDisp, SIGNAL(triggered()),
          this, SLOT(generateFlapDisplacements()));
  genFlapDisp->setEnabled(false);

  // start/stop animation
  toggleAnimAct = new QAction( QIcon(":/icons/play.png"),
                               tr("Toggle &animation"), this );
  toggleAnimAct->setStatusTip(tr("Switch animation on/off"));
  toggleAnimAct->setIconText(tr("Animation"));
  connect( toggleAnimAct, SIGNAL(triggered()), this, SLOT(toggleAnimation()) );

  //
  // Solver interfaces, heavy work actions
  //

  // map single pressure field to structural loads
  directMap = new QAction( tr("Map pressure field..."), this );
  directMap->setStatusTip(tr("Generate structural loads from single "
                             "pressure field."));
  connect( directMap, SIGNAL(triggered()), this, SLOT(mapDirect()) );

  // generate loads for longitudinal maneuver
  longLoadMap = new QAction( tr("Longitudinal maneuver..."), this );
  longLoadMap->setStatusTip(tr("Map structural loads for "
                               "longitudinal maneuver"));
  connect( longLoadMap, SIGNAL(triggered()), this, SLOT(mapLongMLoad()) );

  // generate loads for state history stored in plain text file
  tdlMap = new QAction( tr("Time-domain inertial relief loads..."), this );
  tdlMap->setStatusTip(tr("Generate loads from simulated "
                          "motion state history"));
  connect( tdlMap, SIGNAL(triggered()), this, SLOT(mapTdlLoads()) );

  // generate harmonic loads for frequency-response analysis
  frfMap = new QAction( tr("Frequency domain MA loads..."), this );
  frfMap->setStatusTip(tr("Map structural loads for "
                          "frequency domain mode acceleration analysis"));
  connect( frfMap, SIGNAL(triggered()), this, SLOT(mapFRFLoads()) );

  //  // open dwfs frontend dialog
  //  callDwfsAct = new QAction( tr("Call dwfs..."), this );
  //  callDwfsAct->setStatusTip(tr("Generate input file and call dwfs potential flow solver"));
  //  connect( callDwfsAct, SIGNAL(triggered()), this, SLOT(callDwfs()) );

  // map beam model displacements to wetted surface of aerodynamic mesh
  mapStrDeform = new QAction( tr("Map structural deformation..."), this );
  mapStrDeform->setStatusTip( tr("Interpolate structural model displacements to "
                                 "selected aerodynamic surfaces") );
  connect( mapStrDeform, SIGNAL(triggered()), this, SLOT(mapDisplacements()) );
  mapStrDeform->setEnabled(false);

  // generate new fields containing the maximum values across multiple subcases
  genCaseMaxAct = new QAction( tr("Generate max value field..."), this );
  genCaseMaxAct->setStatusTip(tr("Create a new data field containing the maximum "
                                 "value taken across multiple sub-cases."));
  connect( genCaseMaxAct, SIGNAL(triggered()), this, SLOT(genCaseMax()) );

  buildFlutterAct = new QAction( tr("Manualy define flutter mode..."), this );
  buildFlutterAct->setStatusTip(tr("Generate a flutter mode from modal "
                                       "participation factors"));
  connect( buildFlutterAct, SIGNAL(triggered()),
           this, SLOT(buildFlutterMode()) );

  // at startup, there is no data
  loadTjAct->setEnabled(false);
  saveAct->setEnabled(false);
  componentsAct->setEnabled(false);
  surfContoursAct->setEnabled(false);
  dispSettingsAct->setEnabled(false);
  meshCutAct->setEnabled(false);
  mergeMeshAct->setEnabled(false);
  meshTrafoAct->setEnabled(false);
  meshQualityAct->setEnabled(false);
  surfSliceAct->setEnabled(false);
  buildFlutterAct->setEnabled(false);

  elemInfoAct->setEnabled(false);
  nodeInfoAct->setEnabled(false);
  plotHedgehogAct->setEnabled(false);
  plotStreamlinesAct->setEnabled(false);
  toggleAnimAct->setEnabled(false);
  // callDwfsAct->setEnabled(false);
}

void Scope::initMenus()
{
  // setup drop-down menus

  fileMenu = menuBar()->addMenu(tr("&File"));
  fileMenu->addAction(openAct);
  fileMenu->addAction(loadTjAct);
  fileMenu->addAction(saveAct);
  fileMenu->addAction(embedNoteAct);
  fileMenu->addAction(snapshotAct);
  fileMenu->addSeparator();
  fileMenu->addAction(newMainAct);
  fileMenu->addAction(closeMainAct);
  fileMenu->addSeparator();
  fileMenu->addAction(helpAct);
  fileMenu->addAction(aboutAct);
  fileMenu->addAction(quitAct);
  
  viewMenu = menuBar()->addMenu(tr("&View"));
  viewMenu->addAction(meshInfoAct);
  viewMenu->addAction(fitScreenAct);
  viewMenu->addAction(surfContoursAct);
  viewMenu->addAction(plotHedgehogAct);
  viewMenu->addAction(plotStreamlinesAct);
  viewMenu->addAction(componentsAct);
  viewMenu->addAction(dispSettingsAct);
  viewMenu->addAction(meshQualityAct);
  viewMenu->addAction(toggleGridAct);
  viewMenu->addAction(elemInfoAct);
  viewMenu->addAction(nodeInfoAct);
  viewMenu->addAction(integPressureAct);
  viewMenu->addAction(perspAct);
  viewMenu->addAction(fsaaAct);
  viewMenu->addAction(blendAct);

  editMenu = menuBar()->addMenu(tr("&Edit"));
  editMenu->addAction(mergeMeshAct);
  editMenu->addAction(copySectionAct);
  editMenu->addAction(rmIdleNodesAct);
  editMenu->addAction(meshCutAct);
  editMenu->addAction(surfSliceAct);
  editMenu->addAction(meshTrafoAct);
  editMenu->addAction(addModeAct);
  editMenu->addAction(genFlapDisp);

  loadsMenu = menuBar()->addMenu(tr("&Loads"));
  loadsMenu->addAction(mapStrDeform);
  loadsMenu->addAction(directMap);
  loadsMenu->addAction(longLoadMap);
  loadsMenu->addAction(tdlMap);
  loadsMenu->addAction(frfMap);
  loadsMenu->addAction(genCaseMaxAct);
  loadsMenu->addAction(buildFlutterAct);

  //  solveMenu = menuBar()->addMenu(tr("&Solve"));
  //  solveMenu->addAction(callDwfsAct);
  
  // setup toolbars

  fileTools = addToolBar(tr("File"));
  fileTools->setToolButtonStyle( Qt::ToolButtonTextUnderIcon );
  fileTools->addAction(openAct);
  fileTools->addAction(saveAct);
  fileTools->addAction(snapshotAct);
  fileTools->addAction(quitAct);
  
  viewTools = addToolBar(tr("View"));
  viewTools->setToolButtonStyle( Qt::ToolButtonTextUnderIcon );
  viewTools->addAction(fitScreenAct);
  viewTools->addAction(surfContoursAct);
  viewTools->addAction(componentsAct);
  viewTools->addAction(dispSettingsAct);
  viewTools->addAction(meshCutAct);
  viewTools->addAction(toggleAnimAct);
  viewTools->addAction(elemInfoAct);
  viewTools->addAction(nodeInfoAct);
  viewTools->addAction(surfSliceAct);

#ifdef Q_OS_MACX

#if QT_VERSION >= QT_VERSION_CHECK(5,0,0)
  const char tbStyle[] =
      "QToolBar:!active"
      "{ border: 0px; background-color: qlineargradient(x1: 0, y1: 0, "
      "x2: 0, y2: 1, stop: 0 #F0F0F0, stop: 1 #E8E8E8 ); }"
      " QToolBar:active"
      "{ border: 0px; background-color: qlineargradient(x1: 0, y1: 0, "
      "x2: 0, y2: 1, stop: 0 #D9D9D9, stop: 1 #A5A5A5 ); }";
  fileTools->setStyleSheet(tbStyle);
  viewTools->setStyleSheet(tbStyle);
#endif

  fileTools->setMovable(false);
  fileTools->setFloatable(false);
  viewTools->setMovable(false);
  viewTools->setFloatable(false);
#endif
}

void Scope::checkOpenGL()
{
  // see if this has been done before
  bool haveChecked = Scope::setting("startup-opengl-check", false).toBool();
  if (not haveChecked) {

    bool haveGL = QGLFormat::hasOpenGL();
    // bool have15 = QGLFormat::openGLVersionFlags() & QGLFormat::OpenGL_Version_1_5;
    if (not haveGL) {
      QString msg = tr("<b>OpenGL not present.</b>");
      msg += "<hr>";
      msg += tr("Scope requires OpenGL support to work properly, but your "
                "operating system does not support OpenGL. This problem may "
                "be alleviated by upgrading to a graphics driver provided "
                "by the manufacturer of your graphics adapter.");
      QString title = tr("OpenGL required.");
      QMessageBox::critical(this, title, msg);
      close();
    } else {
      Scope::changeSetting("startup-opengl-check", true);
    }
  }
}

void Scope::newView()
{
  Scope *newView = new Scope();
  newView->show();
}

void Scope::load(const QString & fname)
{
  QStringList fns;
  fns.append(fname);
  load(fns);
}

void Scope::load(const QStringList & fnames)
{
  checkOpenGL();

  // close all dialogs
  emit closeDialogs();
  closeAllDialogs();

  if ( not fnames.isEmpty() ) {

    QApplication::setOverrideCursor(Qt::WaitCursor);
    try {

      Wallclock clk;
      clk.start();
      if (fnames.size() == 1)
        plotControl->load( fnames.front() );
      else
        plotControl->loadFields(fnames);
      clk.stop();
      statusBar()->showMessage( tr("Load time: %1").arg(clk.elapsed()) );

      // enable actions
      switchActions();
      if (fnames.size() == 1) {
        lastfile = fnames.front();
        setWindowTitle( lastfile );
      }
      updateTree();
    } catch (Error & xcp) {
      QApplication::restoreOverrideCursor();
      QString title = tr("Loading aborted.");
      QString xmsg = qstr(xcp.what());
      QString text = tr("<b>Could not load %1</b><br><hr> %2").arg(fnames.front()).arg(xmsg);
      QMessageBox::information( this, title, text );
    }

    QApplication::restoreOverrideCursor();
  }

  view->update();
  view->showEntireScene();
}

void Scope::updateTree()
{
  MeshPlotterPtr plotter = plotControl->plotter();
  if (plotter != nullptr) {
    // plotter->rebuildSections();
    treeModel->construct( plotter );
    treeView->setModel( treeModel );
    treeView->expandToDepth(1);
    treeView->resizeColumnToContents(0);
  } else {
    // Hmm.
  }
}

void Scope::changeSetting(const QString & key, const QVariant & val)
{
  QSettings settings;
  settings.setValue(key, val);
}

QVariant Scope::setting(const QString & key, const QVariant & defval)
{
  QSettings settings;
  return settings.value(key, defval);
}

void Scope::choose()
{
  QString filter;
  filter = tr("Mesh files (*.cgns *.xml *.zml *.msh *.bmsh *.taumesh "
              "*.vtk *.stl *.ply *.su2 *.node *.gbf);; "
              "Nastran (*.blk *.bdf *.f06 *.dat *.pch);; "
              "Abaqus (*.inp);; "
              "All files (*)");

  // if there is already an existing mesh, allow loading EDGE result files
  MxMeshPtr pmx = plotControl->pmesh();
  QStringList fns;
  if (pmx and pmx->nnodes() > 0 and pmx->nelements() > 0) {
    filter.replace("*.bmsh", "*.bmsh *.bout *.bdis");

    // permit to open multiple data field files
    fns = QFileDialog::getOpenFileNames(this, tr("Select file to open"),
                                        lastdir, filter);
  } else {
    QString fn = QFileDialog::getOpenFileName(this,
                                              tr("Select file to open"),
                                              lastdir, filter);
    fns.append(fn);
  }

  if (not fns.isEmpty()) {
    const QString &fn( fns.back() );
    if (not fn.isEmpty())
      lastdir = QFileInfo(fn).absolutePath();
  }
  load(fns);
}

void Scope::loadTrajectory()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  QString filter;
  filter = tr("Text files (*.txt *.dat);;"
              " All files (*)");
  QString fn = QFileDialog::getOpenFileName(this,
                                            tr("Select trajectory file to open"),
                                            lastdir, filter);
  if (not fn.isEmpty()) {
    lastdir = QFileInfo(fn).absolutePath();
    try {
      pmx->appendTrajectory( str(fn) );
      dispSettingsAct->setEnabled(true);
    } catch (Error & xcp) {
      QString title = tr("Could not open trajectory file");
      QString msg = tr("Failed to load trajectory file '%1'.").arg(fn);
      msg += tr(" Library reported error: <br>%1").arg(qstr(xcp.what()));
      QMessageBox::warning(this, title, msg);
    }
  }
}

void Scope::save()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  QString filter, selfilter;
  filter = tr("Native (*.zml);;"
              "Plain XML (*.xml);;"
              "CGNS with BCs (*.cgns);;"
              "CGNS, BCs as sections (*.cgns);;"
              "EDGE (*.bmsh);;"
              "EDGE boundary displacements (*.bdis);;"
              "SU2 (*.su2);;"
            #if defined(HAVE_NETCDF)
              "TAU (*.taumesh);;"
            #endif
            #ifdef HAVE_HDF5
              "HDF5 (*.h5);;"
            #endif
              "Tetgen input (*.smesh);;"
              //             "Genua binary (*.gbf);;"
              "Ensight (*.case);;"
              "VTK Legacy (v2.0) (*.vtk);;"
              "VTK XML (*.vtu);;"
              "Nastran bulk data (*.blk);;"
              "Abaqus (*.inp);;"
              "Zipped XML (*.zml);;"
              "Binary STL (*.stl);;"
              "Plain-Text STL (*.txt);;"
              "Binary PLY (*.ply);;"
              "Plain-Text PLY (*.ply);;"
              "Nastran (*.blk *.bdf)");
  QString fn = QFileDialog::getSaveFileName(this,
                                            tr("Save file as"),
                                            lastdir, filter, &selfilter);
  if (not lastdir.isEmpty())
    lastdir = QFileInfo(fn).absolutePath();
  try {

    QApplication::setOverrideCursor(Qt::WaitCursor);

    if (not fn.isEmpty()) {
      if (selfilter == "Native (*.zml)") {
        string fname = append_suffix(str(fn), ".zml");
        XmlElement xe = pmx->toXml(true);
        xe.write(fname, XmlElement::Lz4Compressed);
      } else if (selfilter.contains("CGNS")) {
        bool bcAsSections = selfilter.contains("sections");
        pmx->writeCgns( append_suffix(str(fn), ".cgns"),
                        bcAsSections );
      } else if (selfilter == "Zipped XML (*.zml)") {
        string fname = append_suffix(str(fn), ".zml");
        pmx->toXml(true).zwrite(fname, 1);
      } else if (selfilter == "Plain XML (*.xml)") {
        pmx->toXml(true).write( append_suffix(str(fn), ".xml"),
                                XmlElement::PlainText );
      } else if (selfilter == "EDGE (*.bmsh)") {
        pmx->writeFFA( append_suffix(str(fn), ".bmsh") );
      } else if (selfilter == "EDGE boundary displacements (*.bdis)") {
        pmx->writeFieldsBdis(str(fn));
      } else if (selfilter.contains("SU2")) {
        pmx->writeSU2( append_suffix(str(fn), ".su2") );
#if defined(HAVE_NETCDF)
      } else if (selfilter == "TAU (*.taumesh)") {
        pmx->writeTau( append_suffix(str(fn), ".taumesh") );
#endif
#if defined(HAVE_HDF5)
      } else if (selfilter.contains("HDF5")) {
        pmx->writeHdf5( append_suffix(str(fn), ".h5") );
#endif
      } else if (selfilter == "Tetgen input (*.smesh)") {
        pmx->writeSmesh( append_suffix(str(fn), ".smesh") );
        //      } else if (selfilter == "Genua binary (*.gbf)") {
        //        pmx->gbfNode()->write( append_suffix(str(fn), ".gbf") );
      } else if (selfilter.contains("Ensight")) {
        pmx->writeEnsight( append_suffix(str(fn), ".case") );
      } else if (selfilter.contains("VTK Legacy")) {
        pmx->writeLegacyVtk( append_suffix(str(fn), ".vtk") );
      } else if (selfilter == "VTK XML (*.vtu)") {
        pmx->toVTK().write( append_suffix(str(fn), ".vtu"),
                            XmlElement::PlainText );
      } else if (selfilter == "Nastran bulk data (*.blk)") {
        pmx->writeNastran(append_suffix(str(fn), ".blk") );
      } else if (selfilter == "Abaqus (*.inp)") {
        pmx->writeAbaqus(append_suffix(str(fn), ".inp") );
      } else if (selfilter == "Binary STL (*.stl)") {
        pmx->writeSTL(append_suffix(str(fn), ".stl"), true);
      } else if (selfilter == "Plain-Text STL (*.txt)") {
        pmx->writeSTL(append_suffix(str(fn), ".stl"), false);
      } else if (selfilter == "Binary PLY (*.ply)") {
        pmx->writePLY(append_suffix(str(fn), ".ply"), true);
      } else if (selfilter == "Plain-Text PLY (*.ply)") {
        pmx->writePLY(append_suffix(str(fn), ".ply"), false);
      } else if (selfilter == "Nastran (*.blk *.bdf)") {
        pmx->writeNastran( append_suffix(str(fn), ".bdf") );
      }
    }

    QApplication::restoreOverrideCursor();

  } catch (Error & xcp) {
    QApplication::restoreOverrideCursor();
    QString title = tr("Could not save file");
    QString msg = tr("Class MxMesh could not be saved to in format '%1'.").arg(selfilter);
    msg += tr(" Library reported error: <br>%1").arg(qstr(xcp.what()));
    QMessageBox::warning(this, title, msg);
  }
}

void Scope::embedNote()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  // pull in xml element from file and attach as note
  QString filter;
  filter = tr("XML files (*.xml *.zml);;"
              " All files (*)");
  QString fn = QFileDialog::getOpenFileName(this,
                                            tr("Select XML content to embed"),
                                            lastdir, filter);
  if (not fn.isEmpty()) {
    lastdir = QFileInfo(fn).absolutePath();
    try {

      XmlElement xe;
      xe.read(str(fn));

      QString tag;
      tag = QInputDialog::getText( this, tr("Annotation"),
                                   tr("Enter tag for annotation") );

      if (tag.isEmpty()) {
        pmx->annotate(xe);
      } else {
        XmlElement note( str(tag) );
        note.append(xe);
        pmx->annotate(note);
      }

    } catch (Error & xcp) {
      QString title = tr("Could not open trajectory file");
      QString msg = tr("Failed to load trajectory file '%1'.").arg(fn);
      msg += tr(" Library reported error: <br>%1").arg(qstr(xcp.what()));
      QMessageBox::warning(this, title, msg);
    }
  }
}

void Scope::about()
{
  QString s;
  s  = tr("<center><h2>Scope</h2></center>");
  s += tr("<p><center>Version ") + _scope_qversion + "</center></p>";
  s += tr("<p>Mesh and motion visualization for aeroelasticity and flight dynamics,");
  s += tr("graphical frontend for dwfs potential flow solver. ");
  s += tr("For more information, visit <p><center><b>http://www.larosterna.com</b></center></p>");
  s += tr("<p>This program is free software; you can redistribute it and/or modify"
          "it under the terms of the GNU General Public License, version 2,"
          "as published by the Free Software Foundation.</p>");
  s += tr("<p>Copyright 2009 by david@larosterna.com</p>");
  s += "<hr/>";
  s += tr("Rendering model: ");
  if (MeshPlotter::vboSupported())
    s += tr("Vertex buffer objects (OpenGL >= 1.5)<br>");
  else
    s += tr("Display list/vertex array (OpenGL 1.1)<br>");

  // build information
  QString compiler;
#if defined(__ICC)
  compiler = QString("Intel C++ %1 (%2bit)")
      .arg(__ICC/100)
      .arg(sizeof(void *)*8);
#elif defined(__ICL)
  compiler = QString("Intel C++ %1 (%2bit)")
      .arg(__ICL/100)
      .arg(sizeof(void *)*8);
#elif defined(__clang__)
  compiler = QString("clang %1.%2.%3 (%4 bit)")
      .arg(__clang_major__)
      .arg(__clang_minor__)
      .arg(__clang_patchlevel__)
      .arg(sizeof(void *)*8);
#elif defined(__GNUC__)
  compiler = QString("gcc %1.%2.%3 (%4 bit)")
      .arg(__GNUC__)
      .arg(__GNUC_MINOR__)
      .arg(__GNUC_PATCHLEVEL__)
      .arg(sizeof(void *)*8);
#elif defined(_MSC_VER)
  compiler = QString("Microsoft Visual C++ %1 (%2 bit)")
      .arg( _MSC_VER/100 )
      .arg(sizeof(void *)*8);
#endif

  if (compiler.isEmpty())
    s += tr("Compiled: %1 <br>").arg(__DATE__);
  else
    s += tr("Compiled: %1 using %2<br>").arg(__DATE__).arg(compiler);

  QMessageBox::about( this, tr("Scope"), s);
}

void Scope::openHelp(const QString &link)
{
#ifdef Q_OS_MAC
  const QString helpIndex = "file://" + QApplication::applicationDirPath()
      + "/../Documentation/";
#elif defined(Q_OS_LINUX)
  const QString helpIndex = QApplication::applicationDirPath()
      + "/../share/doc/dwfscope/";
#else
  const QString helpIndex = QApplication::applicationDirPath()
      + "/../userdoc/dwfscope/";
#endif

  QUrl helpUrl;
  if (link.isEmpty())
    helpUrl = helpIndex + "index.html";
  else
    helpUrl = helpIndex + link;
 
  statusBar()->showMessage(tr("Looking user manual in %1").arg(helpUrl.toString()));
  QDesktopServices::openUrl(helpUrl);
}

void Scope::fitScreen()
{
  view->updateSceneDimensions();
  view->showEntireScene();
}

void Scope::enableMultisampling(bool flag)
{
  QSettings settings;
  settings.setValue("scope-enable-fsaa", flag);
  QMessageBox::information(this, tr("Restart to apply."),
                           tr("This change requires the intialization of the"
                              "OpenGL context currently in use. Therefore,"
                              " it will come into effect on the next start "
                              "of the program."));
}

void Scope::enableBlending(bool flag)
{
  QSettings settings;
  settings.setValue("scope-enable-blendaa", flag);
  QMessageBox::information(this, tr("Restart to apply."),
                           tr("This change requires the intialization of the"
                              "OpenGL context currently in use. Therefore,"
                              " it will come into effect on the next start "
                              "of the program."));
  if (flag)
    qDebug("Enabled blending setting.");
  else
    qDebug("Disabled blending setting.");
}

void Scope::colorContours(int ifield)
{
  if (dlgContour == 0) {
    dlgContour = new ContourDialog(this);
    connect(this, SIGNAL(closeDialogs()), dlgContour, SLOT(close()));
    connect(treeView, SIGNAL(plotField(int)),
            dlgContour, SLOT(selectField(int)));
    disconnect(treeView, SIGNAL(plotField(int)),
               plotControl, SLOT(contourField(int)));
  }

  dlgContour->assign( plotControl );
  if (ifield >= 0)
    dlgContour->selectField(ifield);
  dlgContour->show();
}

void Scope::editComponent(int isec, int iboco)
{
  if (dlgComponent == 0) {
    dlgComponent = new ComponentDialog(this);
    connect(this, SIGNAL(closeDialogs()), dlgComponent, SLOT(close()));
    connect(dlgComponent, SIGNAL(sectionVisibilityChanged(int,bool)),
            treeModel, SLOT(markSectionVisible(int,bool)));
    connect(dlgComponent, SIGNAL(bocoVisibilityChanged(int,bool)),
            treeModel, SLOT(markBocoVisible(int,bool)));
    connect(dlgComponent, SIGNAL(needRedraw()),
            view, SLOT(repaint()));
  }

  dlgComponent->assign(plotControl);
  if (isec > -1)
    dlgComponent->selectSection(isec);
  if (iboco > -1)
    dlgComponent->selectBoco(iboco);
  dlgComponent->show();
}

void Scope::deformationSettings()
{
  if (dlgDisplace == 0) {
    dlgDisplace = new DisplacementDialog(this);
    connect(this, SIGNAL(closeDialogs()), dlgDisplace, SLOT(close()));
    connect(dlgDisplace, SIGNAL(needRedraw()), view, SLOT(repaint()) );
    connect(dlgDisplace, SIGNAL(startAnimation()),
            view, SLOT(startAnimation()));
    connect(dlgDisplace, SIGNAL(stopAnimation()),
            view, SLOT(stopAnimation()));
    connect(treeView, SIGNAL(plotField(int)),
            dlgDisplace, SLOT(selectField(int)));
  }

  dlgDisplace->assign(plotControl);
  dlgDisplace->show();
}

void Scope::cutMesh()
{
  if (dlgMeshCut == 0) {
    dlgMeshCut = new MeshCutDialog(this);
    connect( this, SIGNAL(closeDialogs()), dlgMeshCut, SLOT(close()) );
    connect( dlgMeshCut, SIGNAL(needRedraw()), view, SLOT(repaint()) );
  }

  dlgMeshCut->assign( plotControl );
  dlgMeshCut->show();
}

void Scope::meshTrafo()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  if (dlgTransform == 0) {
    dlgTransform = new TransformationDialog(this);
    connect( dlgTransform, SIGNAL(trafoChanged()),
             view, SLOT(reinitDrawing()) );
    connect( dlgTransform, SIGNAL(trafoChanged()),
             plotControl, SLOT(reload()) );
    connect( this, SIGNAL(closeDialogs()),
             dlgTransform, SLOT(close()) );
  }

  dlgTransform->assign( pmx );
  dlgTransform->show();
}

void Scope::meshInfo()
{
  MeshPlotterPtr pmx = plotControl->plotter();
  if (not pmx)
    return;

  if (dlgEditMesh == 0) {
    dlgEditMesh = new EditMeshDialog(this);
    connect(dlgEditMesh, SIGNAL(loadTrajectory()),
            this, SLOT(loadTrajectory()));
    connect(this, SIGNAL(closeDialogs()), dlgEditMesh, SLOT(close()));
    connect(plotControl, SIGNAL(needRedraw()),
            dlgEditMesh, SLOT(countPrimitives()) );
  }

  dlgEditMesh->assign( pmx );
  dlgEditMesh->show();
}

void Scope::integratePressure()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  if (dlgForceDisplay == nullptr) {
    dlgForceDisplay = new ForceDisplayDialog(this);
    connect( treeView, SIGNAL(plotField(int)),
             dlgForceDisplay, SLOT(selectField(int)) );
  }

  dlgForceDisplay->assign( pmx );
  dlgForceDisplay->lastDirectory( lastdir );
  dlgForceDisplay->show();
}

void Scope::mergeMesh()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  QString filter;
  filter = tr("Mesh files (*.xml *.zml *.cgns *.bmsh *.su2 *.taumesh *.stl);;");
  QString fn = QFileDialog::getOpenFileName(this,
                                            tr("Select file to open"),
                                            lastdir, filter);
  if (fn.isEmpty())
    return;

  lastdir = QFileInfo(fn).absolutePath();

  // ask for field merging option
  bool mergeFieldsByName = false;
  {
    QString title = tr("Choose field merge mode");
    QString text = tr("Should data fields from the imported file "
                      "be merged only if the field name matches the "
                      "name of a field already present in this mesh?");
    QMessageBox::StandardButton bclicked;
    bclicked = QMessageBox::question(this, title, text,
                                     QMessageBox::Yes | QMessageBox::No,
                                     QMessageBox::No);
    mergeFieldsByName = (bclicked == QMessageBox::Yes);
  }

  try {

    MxMesh toMerge;
    toMerge.loadAny(str(fn));

    qDebug("Before merge: %u sections", pmx->nsections());
    pmx->merge(toMerge, mergeFieldsByName);
    qDebug("Post merge: %u sections", pmx->nsections());
    plotControl->assign( pmx );
    updateTree();
    view->updateRepaint();

  } catch (Error & xcp) {
    QString title = tr("Merging aborted.");
    QString xmsg = qstr(xcp.what());
    QString text = tr("<b>Could not merge %1</b><br><hr> %2").arg(fn).arg(xmsg);
    QMessageBox::information( this, title, text );
  }
}

void Scope::copySection()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  if (dlgCopySection == 0) {
    dlgCopySection = new SectionCopyDialog(this);
    connect( this, SIGNAL(closeDialogs()), dlgCopySection, SLOT(close()) );
    connect( dlgCopySection, SIGNAL(meshChanged()),
             this, SLOT(updateTree()) );
    connect( dlgCopySection, SIGNAL(meshChanged()),
             plotControl, SLOT(reload()) );
  }

  dlgCopySection->assign(pmx);
  dlgCopySection->show();
}

void Scope::rmIdleNodes()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  uint ndrop = pmx->dropUnusedNodes();
  plotControl->assign(pmx);
  statusBar()->showMessage( tr("Eliminated %1 nodes").arg(ndrop) );
}

void Scope::meshQuality()
{
  if (dlgMeshQuality == 0) {
    dlgMeshQuality = new MeshQualityDialog(this);
    connect( this, SIGNAL(closeDialogs()), dlgMeshQuality, SLOT(close()) );
    connect( dlgMeshQuality, SIGNAL(requestRepaint()),
             view, SLOT(updateRepaint()) );
    connect( dlgMeshQuality, SIGNAL(postMessage(QString)),
             statusBar(), SLOT(showMessage(QString)) );
    dlgMeshQuality->assign(plotControl);
  }

  dlgMeshQuality->show();
}

void Scope::toggleAnimation()
{
  if (view->animating())
    view->stopAnimation();
  else
    view->startAnimation();
}

void Scope::togglePlayButton(bool flag)
{
  toggleAnimAct->setEnabled(true);
  if (flag) {
    toggleAnimAct->setIcon(QIcon(":/icons/stop.png"));
    toggleAnimAct->setIconText(tr("Stop"));
  } else {
    toggleAnimAct->setIcon(QIcon(":/icons/play.png"));
    toggleAnimAct->setIconText(tr("Play"));
  }
}

void Scope::gridPlanes()
{
  if (dlgGrid == 0) {
    dlgGrid = new PlaneGridDialog(this, view);
    connect(dlgGrid, SIGNAL(planesChanged()),
            view, SLOT(updateRepaint()));
  }

  dlgGrid->show();
}

void Scope::elementInfo(int k)
{
  if (elmInfoBox == 0) {
    elmInfoBox = new ElementInfoBox(this);
    connect(elmInfoBox, SIGNAL(rejected()),
            this, SLOT(uncheckPickElement()));
    connect(elmInfoBox, SIGNAL(requestNodeInfo(int)),
            this, SLOT(nodeInfo(int)));
  }

  elmInfoBox->assign( plotControl->pmesh() );
  elmInfoBox->showInfo(k);
  elmInfoBox->show();
}

void Scope::uncheckPickElement()
{
  elemInfoAct->setChecked(false);
}

void Scope::nodeInfo(int k)
{
  if (nodeInfoBox == 0) {
    nodeInfoBox = new NodeInfoBox(this);
    connect(nodeInfoBox, SIGNAL(rejected()),
            this, SLOT(uncheckPickNode()));
  }

  nodeInfoBox->assign(plotControl->pmesh());
  nodeInfoBox->showInfo(k);
  nodeInfoBox->show();
}

void Scope::uncheckPickNode()
{
  nodeInfoAct->setChecked(false);
}

void Scope::surfaceSlice()
{
  MeshPlotterPtr plt = plotControl->plotter();
  if (not plt)
    return;
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  if (dlgSlice == 0) {
    dlgSlice = new SliceDlg(this);
    connect(this, SIGNAL(closeDialogs()), dlgSlice, SLOT(close()));
    connect( treeView, SIGNAL(plotField(int)),
             dlgSlice, SLOT(assignCurrentField(int)) );
  }

  dlgSlice->attach(pmx, plt->lowCorner(), plt->highCorner());
  dlgSlice->lastDirectory(lastdir);
  dlgSlice->show();
}

void Scope::addRigidMode()
{
  if (dlgAddMode == 0) {
    dlgAddMode = new AddModeshapeDialog(this);
    connect(dlgAddMode, SIGNAL(addedModeshapes()),
            view, SLOT(initPlotter()));
    connect(dlgAddMode, SIGNAL(addedModeshapes()),
            this, SLOT(updateTree()));
    connect(this, SIGNAL(closeDialogs()), dlgAddMode, SLOT(close()) );
  }

  dlgAddMode->assign(plotControl->plotter());
  dlgAddMode->show();
}

void Scope::generateFlapDisplacements()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  QString fn, filter = tr("XML files (*.xml);; All files (*)");
  fn = QFileDialog::getOpenFileName(this, tr("Select FlapSpec XML file"),
                                    lastdir, filter);
  if (fn.isEmpty())
    return;

  try {

    XmlElement xe;
    xe.read( str(fn) );
    if (xe.name() == "FlapSpec") {
      FlapSpec spec;
      FlapSpec::NodeIndexSet iNodes;
      spec.fromXml(xe);
      spec.createBoco( *pmx, iNodes );
      spec.createDisplacement( *pmx, iNodes );
      updateTree();
    } else if (xe.name() == "FlapSpecSet") {
      FlapSpecSet specSet;
      specSet.fromXml(xe);
      specSet.createDisplacements( *pmx );
      updateTree();
    } else {
      QMessageBox::warning(this, tr("Flap spec not read"),
                           tr("Flap specification in file '%1' could not be "
                              "handled, format not recognized.").arg(fn));
    }

  } catch (Error & xcp) {
    QString msg = qstr(xcp.what());
    QMessageBox::warning(this, tr("Flap spec not read"),
                         tr("Flap specification in file '%1' could not be "
                            "handled correctly. Error message: %2").arg(fn).arg(msg));
    return;
  }
}

void Scope::mapDirect()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  if (dlgDirectPMap == 0) {
    dlgDirectPMap = new DirectPMapDialog(this);
    connect(dlgDirectPMap, SIGNAL(displayMesh(MxMeshPtr)),
            view, SLOT(swapMesh(MxMeshPtr)));
    connect(treeView, SIGNAL(plotField(int)),
            dlgDirectPMap, SLOT(changeSelectedField(int)));
    connect(this, SIGNAL(closeDialogs()), dlgDirectPMap, SLOT(close()));
  }

  if (dlgDirectPMap->assign( pmx ))
    dlgDirectPMap->show();
}

void Scope::mapLongMLoad()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  if (dlgLongLoads == 0) {
    dlgLongLoads = new LongManeuvDialog(this);
    connect(dlgLongLoads, SIGNAL(displayMesh(MxMeshPtr)),
            view, SLOT(swapMesh(MxMeshPtr)));
    connect(this, SIGNAL(closeDialogs()), dlgLongLoads, SLOT(close()));
  }

  if (dlgLongLoads->assign( pmx ))
    dlgLongLoads->show();
}

void Scope::mapFRFLoads()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  if (dlgInrelLoads == 0) {
    dlgInrelLoads = new InrelLoadDialog(this);
    connect(dlgInrelLoads, SIGNAL(statusMessage(QString)),
            statusBar(), SLOT(showMessage(QString)));
    connect(this, SIGNAL(closeDialogs()), dlgInrelLoads, SLOT(close()));
  }

  dlgInrelLoads->assignFrf( pmx );
  dlgInrelLoads->show();
}

void Scope::mapTdlLoads()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (not pmx)
    return;

  if (dlgInrelLoads == 0) {
    dlgInrelLoads = new InrelLoadDialog(this);
    connect(dlgInrelLoads, SIGNAL(statusMessage(QString)),
            statusBar(), SLOT(showMessage(QString)));
    connect(this, SIGNAL(closeDialogs()), dlgInrelLoads, SLOT(close()));
  }

  dlgInrelLoads->assignTdl( pmx );
  dlgInrelLoads->show();
}

void Scope::mapDisplacements()
{
  if (dlgMapDef == 0) {
    dlgMapDef = new DeformationMapDlg(this);
    connect(dlgMapDef, SIGNAL(userPathChanged(QString)),
            this, SLOT(userPath(QString)) );
    connect(dlgMapDef, SIGNAL(deformationsChanged(int)),
            this, SLOT(updateTree()) );
    connect(dlgMapDef, SIGNAL(deformationsChanged(int)),
            this, SLOT(switchActions()) );
    connect(this, SIGNAL(closeDialogs()),
            dlgMapDef, SLOT(close()) );
    connect(dlgMapDef, SIGNAL(requestHelp(QString)),
            this, SLOT(openHelp(QString)));
  }

  dlgMapDef->assign( plotControl->pmesh() );
  if ( not dlgMapDef->haveStructure() )
    dlgMapDef->loadStructure();
  dlgMapDef->show();
}

void Scope::genCaseMax()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (pmx != nullptr) {
    bool added = pmx->generateMaxFields(true);
    if (added) {
      plotControl->assign(pmx);
      updateTree();
    }
  }
}

void Scope::buildFlutterMode()
{
  MxMeshPtr pmx = plotControl->pmesh();
  if (pmx == nullptr)
    return;

  if (dlgBuildFlutterMode == nullptr) {
    dlgBuildFlutterMode = new BuildFlutterModeDialog(this);
    connect(dlgBuildFlutterMode, SIGNAL(flutterModeCreated()),
            plotControl, SLOT(reload()));
  }

  dlgBuildFlutterMode->assign(pmx);
  dlgBuildFlutterMode->exec();
}

void Scope::dragEnterEvent(QDragEnterEvent *event)
{
  if (event->mimeData()->hasFormat("text/uri-list"))
    event->acceptProposedAction();
}

void Scope::dropEvent(QDropEvent *event)
{
  QString uri( event->mimeData()->data("text/uri-list") );

  // extract just the first filename
  uri = uri.left( uri.indexOf('\n') ).simplified();
  if (not uri.isEmpty()) {
    load( QUrl(uri).toLocalFile() );
    event->acceptProposedAction();
  }
}

void Scope::closeAllDialogs()
{
  plotControl->closeAllDialogs();
  if (dlgAddMode)
    dlgAddMode->close();
  if (dlgDisplace)
    dlgDisplace->close();
  if (dlgGrid)
    dlgGrid->close();
  if (dlgSlice)
    dlgSlice->close();
  if (elmInfoBox)
    elmInfoBox->close();
  if (nodeInfoBox)
    nodeInfoBox->close();
}

void Scope::switchActions()
{
  bool hasElements = plotControl->hasElements();
  bool hasVolume = plotControl->hasVolume();
  bool hasFields = plotControl->hasFields();
  bool hasDisp = plotControl->hasDisplacements();
  bool hasVecFields = plotControl->hasVectorFields();

  qDebug() << "volume: " << hasVolume << " fields: " << hasFields
           << " disp: " << hasDisp << endl;

  meshInfoAct->setEnabled( plotControl->pmesh() != nullptr );
  copySectionAct->setEnabled( hasElements );
  rmIdleNodesAct->setEnabled( hasElements );
  saveAct->setEnabled( hasElements );
  surfContoursAct->setEnabled( hasFields );
  dispSettingsAct->setEnabled( hasDisp );
  componentsAct->setEnabled( hasElements );
  meshQualityAct->setEnabled( hasVolume );
  plotHedgehogAct->setEnabled( hasVecFields );
  plotStreamlinesAct->setEnabled( hasVecFields );
  elemInfoAct->setEnabled( hasElements );
  nodeInfoAct->setEnabled( hasElements );
  integPressureAct->setEnabled( hasFields );
  buildFlutterAct->setEnabled( hasDisp );

  toggleAnimAct->setEnabled( hasDisp );

  loadTjAct->setEnabled( hasElements );
  meshTrafoAct->setEnabled( hasElements );
  mergeMeshAct->setEnabled( hasElements );
  addModeAct->setEnabled( hasElements );
  genFlapDisp->setEnabled( hasElements );

  meshCutAct->setEnabled( hasVolume );
  surfSliceAct->setEnabled( hasElements );

  mapStrDeform->setEnabled( hasElements );

  MxMeshPtr pmx = plotControl->pmesh();
  if (pmx != nullptr) {
    MxSolutionTreePtr ptree = pmx->solutionTree();
    if (ptree != nullptr) {
      genCaseMaxAct->setEnabled( ptree->children() > 1 );
    } else
      genCaseMaxAct->setEnabled(false);
  } else {
    genCaseMaxAct->setEnabled(false);
  }

}
