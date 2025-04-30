
/* ------------------------------------------------------------------------
 * file:       sumo.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Surface modeler program : main widget
 * ------------------------------------------------------------------------ */

#include <QCloseEvent>
#include <QLocale>
#include <QDesktopWidget>
#include <QFileDialog>
#include <QLabel>
#include <QPushButton>
#include <QAction>
#include <QMenuBar>
#include <QMenu>
#include <QToolBar>
#include <QBoxLayout>
#include <QTabWidget>
#include <QMessageBox>
#include <QStatusBar>
#include <QSettings>
#include <QUrl>
#include <QInputDialog>
#include <QMimeData>
#include <QGLContext>
#include <QGLFormat>

#include <genua/xcept.h>
#include <genua/sysinfo.h>
#include <genua/mxmesh.h>

#include "util.h"
#include "frameeditor.h"
#include "renderview.h"
#include "trimeshview.h"
#include "splitter.h"
#include "wingmanagerwidget.h"
#include "dlgsavemesh.h"
#include "cseditorwidget.h"
#include "sectioneditor.h"
#include "exportrow.h"
#include "skeletonwidget.h"
#include "editbody.h"
#include "jetengineeditor.h"
#include "assemblytree.h"
#include "createassembly.h"
#include "exporttritet.h"
#include "dlgtetgen.h"
#include "meshoptions.h"
#include "mgenprogressctrl.h"
#include "csmgenerator.h"
#include "wavedragdlg.h"
#include "wingsectionfitdlg.h"
#include "nacellegeometrydlg.h"
#include "dlgglobaltransform.h"
#include "spacenav/spacemouseinterface.h"
#include "version.h"
#include "sumo.h"

using namespace std;
using namespace Qt;

SumoMain::SumoMain() : QMainWindow()
{
  // lazily constructed dialogs
  dlgTetgen = 0;
  dlgWaveDrag = 0;

  // construct OpenGL context
  QGLFormat fmt;
#if QT_VERSION >= QT_VERSION_CHECK(4,7,0)
  fmt.setVersion(2,1);
  fmt.setProfile(QGLFormat::CompatibilityProfile);
#endif
  renderContext = new QGLContext(fmt);
  meshContext = new QGLContext(fmt);

  // set window icon
  QMainWindow::setWindowIcon(QIcon(":/icons/bjet6.png"));
  QMainWindow::setAttribute(Qt::WA_DeleteOnClose, true);
  QMainWindow::setAcceptDrops(true);

  // create default assembly
  model = AssemblyPtr(new Assembly);
  
  initMainWidgets();
  initActions();
  initMenus();
  
  // create geometry tree
  asytree->build();
  
  // show main widget
  asytree->setFocus();

  // recover last directory visited
  QSettings settings;
  lastdir = settings.value("last-directory", QString()).toString();
  if (settings.contains("last-geometry"))
    resize( settings.value("last-geometry").toSize() );
}

SumoMain::~SumoMain()
{
  changeSetting("last-directory", lastdir);
  changeSetting("last-geometry", this->size());
  changeSetting("sumo-show-maximized", isMaximized());

  delete dlgTetgen;
}

void SumoMain::changeSetting(const QString & key, const QVariant & val)
{
  QSettings settings;
  settings.setValue(key, val);
}

QVariant SumoMain::setting(const QString & key, const QVariant & defval)
{
  QSettings settings;
  return settings.value(key, defval);
}

void SumoMain::initMainWidgets()
{
  // generate main window contents
  asytree = new AssemblyTree(this, model);
  maintab = new QTabWidget(this);

  // dialogs which must be alive on startup
  dlgFitWing = new WingSectionFitDlg(this);
  
  QFrame *tabFrame = new QFrame(this);
  QVBoxLayout *vbox = new QVBoxLayout;
  vbox->setContentsMargins(0, 8, 0, 0);
  vbox->addWidget(maintab);
  tabFrame->setLayout(vbox);

  QList<int> sl;
  sl << 100 << 500;

  splitter = new Splitter(Qt::Horizontal, this);
  splitter->addWidget(asytree);
  splitter->addWidget(tabFrame);
  splitter->setSizes(sl);
  setCentralWidget(splitter);

  // create skeleton editor for side and top view
  skewi = new SkeletonWidget(this);
  maintab->addTab(skewi, "Skeleton");
  skewi->setBody(model->body(0));
  skewi->fitView();
  
  // create frame editor for body frame editing
  fred = new FrameEditor(this);
  maintab->addTab(fred, "Frame");
  
  // create contexts
  renderContext->create();
  meshContext->create();

  // setup rendering
  rdv = new RenderView(renderContext, this, model);
  maintab->addTab(rdv, "Rendering");

  // connect frame projector
  fred->setProjector( rdv->frameProjector() );

  // setup mesh viewing tab
  mshview = new TriMeshView(meshContext, this);
  maintab->addTab(mshview, "Mesh");
  
  // try to connect to SpaceNavigator
  if (SpaceMouseInterface::connectDevice(rdv)) {
    connect( SpaceMouseInterface::globalInterface(),
             SIGNAL(axisMotion(const SpaceMouseMotionData&)),
             rdv, SLOT(multiAxisControl(const SpaceMouseMotionData&)) );
    connect( SpaceMouseInterface::globalInterface(),
             SIGNAL(buttonPressed(uint)),
             rdv, SLOT(multiAxisButtonPressed(uint)) );
    connect( SpaceMouseInterface::globalInterface(),
             SIGNAL(axisMotion(const SpaceMouseMotionData&)),
             mshview, SLOT(multiAxisControl(const SpaceMouseMotionData&)) );
    connect( SpaceMouseInterface::globalInterface(),
             SIGNAL(buttonPressed(uint)),
             mshview, SLOT(multiAxisButtonPressed(uint)) );
  }

  // store tab indices
  itab_skewi = maintab->indexOf(skewi);
  itab_fred = maintab->indexOf(fred);
  itab_rdv = maintab->indexOf(rdv);
  itab_mshview = maintab->indexOf(mshview);

  // pass status messages from tab widgets to status bar
  connect(skewi, SIGNAL(mptrPosition(const QString&)),
          statusBar(), SLOT(showMessage(const QString&)) );
  connect(fred, SIGNAL(postStatusMessage(const QString&)),
          statusBar(), SLOT(showMessage(const QString&)));
  connect(rdv, SIGNAL(mousePosMsg(const QString&)),
          statusBar(), SLOT(showMessage(const QString&)) );
  connect(mshview, SIGNAL(postStatusMessage(const QString&)),
          statusBar(), SLOT(showMessage(const QString&)));
  
  // process user interaction with tree pane
  connect( asytree, SIGNAL(itemSelected(ShTreeItem*)),
           this, SLOT(processTreeSelection(ShTreeItem*)) );
  connect( asytree, SIGNAL(rmbClicked( ShTreeItem*, const QPoint& )),
           this, SLOT(showTreeMenu( ShTreeItem*, const QPoint& )) );
  
  // update geomtry tree whenever skeleton geometry is modified
  connect( skewi, SIGNAL(topologyChanged()),
           asytree, SLOT(update()) );
  
  // update frame drawing if skeleton geometry was modified
  connect( skewi, SIGNAL(geometryChanged()),
           fred, SLOT(update()) );
  
  // update tree when frame changed (could be name change)
  connect( fred, SIGNAL(geometryChanged()),
           asytree, SLOT(update()) );

  // update skeleton drawing if frame geometry was modified
  connect( fred, SIGNAL(geometryChanged()),
           skewi, SLOT(reconstruct()) );
  
  // update rendering if frame geometry was modified
  connect( fred, SIGNAL(geometryChanged()),
           rdv, SLOT(updateGeometry()) );
  
  // redraw when active tab changed
  connect( maintab, SIGNAL(currentChanged(int)),
           this, SLOT(switchTab(int)) );

  // redraw when sections fitted to overlay
  connect( dlgFitWing, SIGNAL(geometryChanged()),
           rdv, SLOT(updateGeometry()) );
  connect( dlgFitWing, SIGNAL(indicatorChanged()),
           rdv, SLOT(repaint()) );
}

void SumoMain::initActions()
{
  //
  // File menu
  //
  newMainAct = new QAction( QIcon(":/icons/new_window.png"),
                            tr("&New window"), this );
  newMainAct->setShortcut(tr("Ctrl+N"));
  newMainAct->setIconText(tr("New"));
  newMainAct->setStatusTip(tr("Open a new sumo window"));
  connect( newMainAct, SIGNAL(triggered()), this, SLOT(newView()) );

  // close main window
  closeMainAct = new QAction( QIcon(":/icons/close_window.png"),
                              tr("&Close window"), this );
  closeMainAct->setShortcut(tr("Ctrl+W"));
  closeMainAct->setIconText(tr("Close"));
  closeMainAct->setStatusTip(tr("Close this sumo window"));
  connect( closeMainAct, SIGNAL(triggered()), this, SLOT(close()) );

  // file operations
  openAct = new QAction( QIcon(":/icons/fileopen.png"),
                         tr("&Open file..."), this );
  openAct->setIconText(tr("Open"));
  openAct->setShortcut(tr("Ctrl+O"));
  openAct->setStatusTip(tr("Load assembly from file"));
  connect( openAct, SIGNAL(triggered()), this, SLOT(loadAndReplace()) );
  
  openAddAct = new QAction( QIcon(":/icons/fileopen.png"),
                            tr("Load &components..."), this );
  openAddAct->setStatusTip(tr("Load components from file"));
  connect( openAddAct, SIGNAL(triggered()), this, SLOT(loadAndAppend()) );
  
  importCsmAct = new QAction( QIcon(":/icons/fileopen.png"),
                              tr("Import CEASIOM file..."), this );
  importCsmAct->setStatusTip(tr("Import CEASIOM geometry definition xml file"));
  connect( importCsmAct, SIGNAL(triggered()), this, SLOT(importCsm()) );

  saveAct = new QAction( QIcon(":/icons/filesave.png"),
                         tr("&Save assembly..."), this );
  saveAct->setIconText(tr("Save"));
  saveAct->setShortcut(tr("Ctrl+S"));
  saveAct->setStatusTip(tr("Save assembly to file"));
  connect( saveAct, SIGNAL(triggered()), this, SLOT(save()) );
  
  saveAsAct = new QAction( QIcon(":/icons/filesaveas.png"),
                           tr("Save assembly &as..."), this );
  saveAsAct->setIconText(tr("Save As"));
  saveAsAct->setStatusTip(tr("Save assembly to file"));
  connect( saveAsAct, SIGNAL(triggered()), this, SLOT(saveAs()) );
  
  revertAct = new QAction( QIcon(":/icons/revert.png"),
                           tr("&Revert..."), this );
  revertAct->setStatusTip(tr("Reload from disk"));
  revertAct->setIconText(tr("Revert"));
  revertAct->setShortcut(tr("Ctrl+Z"));
  connect( revertAct, SIGNAL(triggered()), this, SLOT(revert()) );
  
  exportGridAct = new QAction( QIcon(":/icons/filesave.png"),
                               tr("Export point &grid..."), this );
  exportGridAct->setStatusTip(tr("Export point grid"));
  connect( exportGridAct, SIGNAL(triggered()), this, SLOT(exportGrid()) );
  
  exportIgesAct = new QAction( QIcon(":/icons/filesave.png"),
                               tr("Export to &IGES..."), this );
  exportIgesAct->setStatusTip(tr("Export geometry to IGES file"));
  connect( exportIgesAct, SIGNAL(triggered()), this, SLOT(exportIges()) );
  
  importGridAct = new QAction( QIcon(":/icons/fileopen.png"),
                               tr("&Import point grid..."), this );
  importGridAct->setStatusTip(tr("Import point grid"));
  connect( importGridAct, SIGNAL(triggered()), this, SLOT(importGrid()) );
  
  snapshotAct = new QAction( QIcon(":/icons/snapshot.png"),
                             tr("Save snapshot..."), this );
  snapshotAct->setIconText(tr("Snapshot"));
  snapshotAct->setShortcut(tr("Ctrl+P"));
  snapshotAct->setStatusTip(tr("Save snapshot of 3D view to file"));
  connect( snapshotAct, SIGNAL(triggered()), this, SLOT(saveSnapshot()) );
  
  aboutAct = new QAction( tr("About sumo"), this );
  connect( aboutAct, SIGNAL(triggered()), this, SLOT(about()) );
  
  quitAct = new QAction( QIcon(":/icons/exit.png"),
                         tr("&Quit"), this );
  quitAct->setShortcut(tr("Ctrl+Q"));
  quitAct->setStatusTip(tr("Exit"));
  connect( quitAct, SIGNAL(triggered()), this, SLOT(close()) );
  
  //
  // Edit menu
  //
  
  newAsmAct = new QAction( QIcon(":/icons/filenew.png"),
                           tr("&New assembly..."), this );
  newAsmAct->setStatusTip(tr("Create new assembly"));
  // newAsmAct->setShortcut(tr("Ctrl+N"));
  newAsmAct->setIconText(tr("New"));
  connect( newAsmAct, SIGNAL(triggered()), this, SLOT(newAssembly()) );
  
  addBodyAct = new QAction( QIcon(":/icons/addfuselage.png"),
                            tr("Create &body surface..."), this );
  addBodyAct->setStatusTip(tr("Create new body surface"));
  addBodyAct->setIconText(tr("Body"));
  connect( addBodyAct, SIGNAL(triggered()), this, SLOT(newBody()) );
  
  addWingAct = new QAction( QIcon(":/icons/addwings.png"),
                            tr("Create &wing surface..."), this );
  addWingAct->setStatusTip(tr("Create new wing surface"));
  addWingAct->setIconText(tr("Wing"));
  connect( addWingAct, SIGNAL(triggered()), this, SLOT(newWing()) );
  
  transformGloballyAct = new QAction( tr("Transform assembly..."), this );
  transformGloballyAct->setStatusTip(tr("Apply global transform factor to"
                                    " entire geometry"));
  transformGloballyAct->setIconText(tr("Transform"));
  connect( transformGloballyAct, SIGNAL(triggered()),
           this, SLOT(globalTransform()) );

  editCsAct = new QAction( tr("Edit &control system..."), this );
  editCsAct->setStatusTip(tr("Edit control system specification"));
  connect( editCsAct, SIGNAL(triggered()), this, SLOT(editControlSystem()) );
  
  editJeAct = new QAction( tr("Edit &jet engine properties..."), this );
  editJeAct->setStatusTip(tr("Edit jet engine specification"));
  connect( editJeAct, SIGNAL(triggered()), this, SLOT(editJetEngines()) );
  
  editObjAct = new QAction( QIcon(":/icons/edit.png"),
                            tr("&Edit selected object..."), this );
  editObjAct->setStatusTip(tr("Edit selected object"));
  editObjAct->setShortcut(tr("Ctrl+E"));
  connect( editObjAct, SIGNAL(triggered()), this, SLOT(editObject()) );
  
  rmObjAct = new QAction( QIcon(":/icons/editdelete.png"),
                          tr("&Delete selected object..."), this );
  rmObjAct->setStatusTip(tr("Delete selected object"));
  rmObjAct->setShortcut(tr("Ctrl+D"));
  connect( rmObjAct, SIGNAL(triggered()), this, SLOT(removeObject()) );
  
  cpObjAct = new QAction( QIcon(":/icons/editcopy.png"),
                          tr("&Copy selected object..."), this );
  cpObjAct->setStatusTip(tr("Copy selected object"));
  cpObjAct->setShortcut(tr("Ctrl+C"));
  connect( cpObjAct, SIGNAL(triggered()), this, SLOT(copyObject()) );
  
  xzmObjAct = new QAction( QIcon(":/icons/editcopy.png"),
                           tr("Create &mirror copy..."), this );
  xzmObjAct->setStatusTip(tr("Copy and mirror about the xz-plane"));
  connect( xzmObjAct, SIGNAL(triggered()), this, SLOT(mirrorObject()) );

  nacGeoAct = new QAction( tr("Edit &nacelle geometry..."), this );
  nacGeoAct->setStatusTip(tr("Change geometry settings for engine nacelle inlets."));
  connect( nacGeoAct, SIGNAL(triggered()), this, SLOT(editNacelleGeometry()) );

  fitSectionsAct = new QAction( tr("Wing sections from overlay..."), this );
  fitSectionsAct->setStatusTip(tr("Fit all present wing sections to overlay geometry."));
  connect( fitSectionsAct, SIGNAL(triggered()),
           this, SLOT(fitWingSections()) );
  fitSectionsAct->setEnabled(false);

  //
  // Tree context menu
  //

  showObjAct = new QAction( tr("Show object"), this );
  showObjAct->setStatusTip( tr("Toggle visibility of surface object on/off") );
  showObjAct->setCheckable(true);
  showObjAct->setChecked(true);
  connect( showObjAct, SIGNAL(toggled(bool)), this, SLOT(showObject(bool)) );

  //
  //  View menu
  //

  loadOverlayAct = new QAction( QIcon(":/icons/fileopen.png"),
                                tr("Load overlay geometry..."), this );
  loadOverlayAct->setStatusTip(tr("Display IGES/STEP geometry as overlay."));
  connect( loadOverlayAct, SIGNAL(triggered()), this, SLOT(loadOverlay()) );

  saveOverlayAct = new QAction( QIcon(":/icons/filesave.png"),
                                tr("Save overlay geometry"), this );
  saveOverlayAct->setStatusTip(tr("Save currently shown overlay geometry to file."));
  saveOverlayAct->setEnabled(false);
  connect( saveOverlayAct, SIGNAL(triggered()), rdv, SLOT(saveOverlay()) );

  saveOverlayAsAct = new QAction( QIcon(":/icons/filesave.png"),
                                  tr("Save overlay geometry as..."), this );
  saveOverlayAsAct->setStatusTip(tr("Select filename for currently shown "
                                    "overlay geometry and save."));
  saveOverlayAsAct->setEnabled(false);
  connect( saveOverlayAsAct, SIGNAL(triggered()), rdv, SLOT(saveOverlayAs()) );

  trafoOverlayAct = new QAction(
        tr("Transform overlay..."), this );
  trafoOverlayAct->setStatusTip(tr("Apply geometric transformation to 3D "
                                   "overlay display."));
  connect( trafoOverlayAct, SIGNAL(triggered()), rdv, SLOT(trafoOverlay()) );
  trafoOverlayAct->setEnabled(false);

  showOverlayAct = new QAction(
        tr("Show overlay..."), this );
  showOverlayAct->setCheckable(true);
  showOverlayAct->setChecked(true);
  showOverlayAct->setStatusTip(tr("Enable/disable display of current "
                                  " overlay geometry."));
  connect(showOverlayAct, SIGNAL(triggered(bool)), rdv, SLOT(showOverlay(bool)) );
  showOverlayAct->setEnabled(false);

  outlineOverlayAct = new QAction(
        tr("Wireframe overlay..."), this );
  outlineOverlayAct->setCheckable(true);
  outlineOverlayAct->setChecked(false);
  outlineOverlayAct->setStatusTip(tr("Enable/disable display of current "
                                     " overlay geometry."));
  connect(outlineOverlayAct, SIGNAL(triggered(bool)), rdv, SLOT(wireframeOverlay(bool)) );
  outlineOverlayAct->setEnabled(false);

  fitScreenAct = new QAction( QIcon(":/icons/fullscreen.png"),
                              tr("Fit scene to screen"), this );
  fitScreenAct->setIconText(tr("Fit Scene"));
  fitScreenAct->setStatusTip(tr("Scale display to show entire scene."));
  connect(fitScreenAct, SIGNAL(triggered()), this, SLOT(fitScreen()) );

  //
  // mesh operations
  //

  generateMeshAct = new QAction( QIcon(":/icons/gear.png"),
                                 tr("Generate surface &mesh..."), this );
  generateMeshAct->setIconText(tr("Mesh"));
  generateMeshAct->setShortcut(tr("Ctrl+M"));
  generateMeshAct->setStatusTip(tr("Generate surface mesh"));
  connect( generateMeshAct, SIGNAL(triggered()), this, SLOT(generateMesh()) );
  
  mvOptionsAct = new QAction( QIcon(":/icons/configure.png"),
                              tr("Mesh view options..."), this );
  mvOptionsAct->setStatusTip(tr("Change mesh view options"));
  mvOptionsAct->setIconText(tr("Mesh View"));
  connect( mvOptionsAct, SIGNAL(triggered()), this, SLOT(showMeshDrawOptions()) );
  
  saveSurfMeshAct = new QAction( QIcon(":/icons/filesave.png"),
                                 tr("&Save surface mesh..."), this );
  saveSurfMeshAct->setStatusTip(tr("Save surface mesh to file"));
  connect( saveSurfMeshAct, SIGNAL(triggered()), this, SLOT(saveSurfaceMesh()) );
  
  saveVolMeshAct = new QAction( QIcon(":/icons/filesave.png"),
                                tr("&Save volume mesh..."), this );
  saveVolMeshAct->setStatusTip(tr("Save volume mesh to file"));
  connect( saveVolMeshAct, SIGNAL(triggered()), this, SLOT(saveVolumeMesh()) );
  
  meshCutAct = new QAction( tr("Wave Drag Estimation..."), this );
  meshCutAct->setStatusTip(tr("Estimate supersonic volume wave drag using "
                              "longitudinal area distribution."));
  connect( meshCutAct, SIGNAL(triggered()), this, SLOT(waveDrag()) );
  
  xpTritetAct = new QAction( QIcon(":/icons/filesave.png"),
                             tr("Export boundary mesh..."), this );
  xpTritetAct->setStatusTip(tr("Export boundary mesh for tritet or tetgen"));
  connect( xpTritetAct, SIGNAL(triggered()), this, SLOT(exportBoundary()) );
  
  genVolMeshAct = new QAction(tr("Generate volume mesh..."), this );
  genVolMeshAct->setStatusTip(tr("Create tetrahedral or hybrid volume mesh"));
  connect( genVolMeshAct, SIGNAL(triggered()), this, SLOT(generateVolMesh()) );
  
  // initially, there is no mesh, hence the related actions are inactive
  mvOptionsAct->setEnabled(false);
  saveSurfMeshAct->setEnabled(false);
  saveVolMeshAct->setEnabled(false);
  xpTritetAct->setEnabled(false);
  genVolMeshAct->setEnabled(false);
  meshCutAct->setEnabled(false);
  nacGeoAct->setEnabled(false);
  
  // furthermore, the 3D geometry has not been computed, hence no snapshot
  snapshotAct->setEnabled(false);
}

void SumoMain::initMenus()
{
  // setup drop-down menus
  
  fileMenu = menuBar()->addMenu(tr("&File"));
  fileMenu->addAction(openAct);
  fileMenu->addAction(openAddAct);
  fileMenu->addAction(saveAct);
  fileMenu->addAction(saveAsAct);
  fileMenu->addAction(revertAct);

  importMenu = fileMenu->addMenu( tr("Import...") );
  importMenu->addAction(loadOverlayAct);
  importMenu->addAction(importCsmAct);
  importMenu->addAction(importGridAct);

  exportMenu = fileMenu->addMenu( tr("Export...") );
  exportMenu->addAction(exportIgesAct);
  exportMenu->addAction(saveOverlayAsAct);
  exportMenu->addAction(exportGridAct);
  exportMenu->addAction(saveSurfMeshAct);
  exportMenu->addAction(saveVolMeshAct);

  fileMenu->addAction(snapshotAct);
  fileMenu->addSeparator();
  fileMenu->addAction(newMainAct);
  fileMenu->addAction(closeMainAct);
  fileMenu->addSeparator();
  fileMenu->addAction(aboutAct);
  fileMenu->addAction(quitAct);
  
  editMenu = menuBar()->addMenu(tr("&Edit"));
  editMenu->addAction(newAsmAct);
  editMenu->addAction(addBodyAct);
  editMenu->addAction(addWingAct);
  editMenu->addAction(transformGloballyAct);
  editMenu->addAction(editCsAct);
  editMenu->addAction(editJeAct);
  editMenu->addAction(nacGeoAct);
  editMenu->addAction(fitSectionsAct);
  
  viewMenu = menuBar()->addMenu(tr("&View"));
  viewMenu->addAction(fitScreenAct);
  viewMenu->addSeparator();
  viewMenu->addAction(loadOverlayAct);
  viewMenu->addAction(saveOverlayAct);
  viewMenu->addAction(saveOverlayAsAct);
  viewMenu->addAction(showOverlayAct);
  viewMenu->addAction(outlineOverlayAct);
  viewMenu->addAction(trafoOverlayAct);

  meshMenu = menuBar()->addMenu(tr("&Mesh"));
  meshMenu->addAction(generateMeshAct);
  meshMenu->addAction(xpTritetAct);
  meshMenu->addAction(genVolMeshAct);
  meshMenu->addAction(mvOptionsAct);
  meshMenu->addAction(meshCutAct);
  meshMenu->addSeparator();
  meshMenu->addAction(saveSurfMeshAct);
  meshMenu->addAction(saveVolMeshAct);
  
  // context menu for tree view
  treeMenu = new QMenu(this);
  treeMenu->addAction(showObjAct);
  treeMenu->addAction(editObjAct);
  treeMenu->addAction(rmObjAct);
  treeMenu->addAction(cpObjAct);
  treeMenu->addAction(xzmObjAct);
  treeMenu->addAction(addBodyAct);
  treeMenu->addAction(addWingAct);
  treeMenu->addAction(exportGridAct);
  treeMenu->addAction(fitSectionsAct);

  // setup toolbars

  fileTools = addToolBar(tr("File"));
  fileTools->setToolButtonStyle( Qt::ToolButtonTextUnderIcon );
  fileTools->addAction(openAct);
  fileTools->addAction(saveAct);
  fileTools->addAction(saveAsAct);
  fileTools->addAction(revertAct);
  fileTools->addAction(snapshotAct);
  
  editTools = addToolBar(tr("Edit"));
  editTools->setToolButtonStyle( Qt::ToolButtonTextUnderIcon );
  editTools->addAction(newAsmAct);
  editTools->addAction(addBodyAct);
  editTools->addAction(addWingAct);
  editTools->addAction(fitScreenAct);
  
  meshTools = addToolBar(tr("Mesh"));
  meshTools->setToolButtonStyle( Qt::ToolButtonTextUnderIcon );
  meshTools->addAction(generateMeshAct);
  meshTools->addAction(mvOptionsAct);

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
  editTools->setStyleSheet(tbStyle);
  meshTools->setStyleSheet(tbStyle);
#endif

  fileTools->setFloatable(false);
  fileTools->setMovable(false);

  editTools->setFloatable(false);
  editTools->setMovable(false);

  meshTools->setFloatable(false);
  meshTools->setMovable(false);
  setUnifiedTitleAndToolBarOnMac(true);
#endif
}

void SumoMain::newView()
{
  SumoMain *newView = new SumoMain();
  newView->show();
}

void SumoMain::useNewModel()
{
  asytree->changeAssembly( model );
  if (model->nbodies() > 0) {
    skewi->setBody( model->body(0) );
    fred->setFrame( model->body(0), 0 );
  }
  rdv->setModel( model );
  rdv->showEntireScene();
  switchTab( itab_rdv );
  rdv->repaint();
  
  // initially, there is no mesh, hence the related actions are inactive
  mshview->clear();
  mvOptionsAct->setEnabled(false);
  saveSurfMeshAct->setEnabled(false);
  saveVolMeshAct->setEnabled(false);
  xpTritetAct->setEnabled(false);
  genVolMeshAct->setEnabled(false);
  meshCutAct->setEnabled(false);
}

void SumoMain::load(const QString & fn)
{
  if ( !fn.isEmpty() ) {
    try {
      model->loadAndReplace( QFile::encodeName(fn).constData() );
    } catch (Error & xcp) {
      QString msg;
      msg  = tr("<b>Problem reading input file: '")+fn+"'.</b>\n";
      msg += tr("Error message: ")+qstr(xcp.what());
      QMessageBox::information( this, "sumo", msg);
      statusBar()->showMessage( tr("Loading aborted"), 2000 );
      return;
    }
    useNewModel();
    filename = fn;
    QString caption = QString("sumo ") + _sumo_qversion;
#ifndef NDEBUG
    caption += " (debug) ";
#endif
    caption += " : " + filename;
    this->setWindowTitle(caption);
  } else
    statusBar()->showMessage( tr("Loading aborted"), 2000 );
}

void SumoMain::loadAndReplace()
{
  QString caption = tr("Load assembly from file");
  QString filter = tr("Sumo models (*.smx);; All files (*)");
  QString fn = QFileDialog::getOpenFileName(this, caption, lastdir, filter);
  if ( !fn.isEmpty() ) {
    lastdir = QFileInfo(fn).absolutePath();
    try {
      XmlElement xe;
      xe.read(str(fn));
      model->clear();
      model->fromXml(xe);
      
    } catch (Error & xcp) {
      QString msg;
      msg  = tr("<b>Problem reading input file: '")+fn+"'.</b>\n";
      msg += tr("Error message: ")+qstr(xcp.what());
      QMessageBox::information( this, "sumo", msg);
      statusBar()->showMessage( tr("Loading aborted"), 2000 );
      return;
    }
    useNewModel();
    filename = fn;
    caption = QString("sumo ") + _sumo_qversion + " : " + filename;
    this->setWindowTitle(caption);
  } else
    statusBar()->showMessage( tr("Loading aborted"), 2000 );
}

void SumoMain::loadAndAppend()
{
  QString caption = tr("Append components from file");
  QString filter = tr("Sumo models (*.smx);; All files (*)");
  QString fn = QFileDialog::getOpenFileName(this, caption, lastdir, filter);
  if ( !fn.isEmpty() ) {
    lastdir = QFileInfo(fn).absolutePath();
    try {
      XmlElement xe;
      xe.read(str(fn));
      model->fromXml(xe);
    } catch (Error & xcp) {
      QString msg;
      msg  = tr("<b>Problem reading input file: '")+fn+"'.</b>\n";
      msg += tr("Error message: ")+qstr(xcp.what());
      QMessageBox::information( this, "sumo", msg);
      statusBar()->showMessage( tr("Loading aborted"), 2000 );
      return;
    }
    useNewModel();
    filename = "";
  } else
    statusBar()->showMessage( tr("Loading aborted"), 2000 );
}

void SumoMain::loadOverlay()
{
  QString caption = tr("Import overlay geometry");
  QString filter = tr("Supported formats (*.igs *.iges *.stp *.step "
                      "*.zml *.stl *.txt *.cgns *.bmsh);;"
                      "IGES files (*.igs *.iges);;"
                      "STEP files (*.stp *.step);;"
                      "Multiple STL files (*.stl *.txt);;"
                      "Compressed XML (*.zml *.xml);;"
                      "CGNS/EDGE mesh (*.cgns *.bmsh);;"
                      "All files (*)");
  QString selfilter;
  QStringList fn = QFileDialog::getOpenFileNames(this, caption, lastdir,
                                                 filter, &selfilter);
  if (fn.isEmpty())
    return;

  lastdir = QFileInfo(fn[0]).absolutePath();
  try {

    // try to load file; enable actions on success
    if (selfilter.contains("IGES") or fn.endsWith(".IGS")
        or fn.endsWith(".igs"))
      rdv->loadIgesOverlay( fn[0] );
    else if (selfilter.contains("STEP") or fn.endsWith(".STP")
             or fn.endsWith(".stp"))
      rdv->loadStepOverlay( fn[0] );
    else if (selfilter.contains("STL") or fn.endsWith(".STL")
             or fn.endsWith(".stl"))
      rdv->loadStlOverlay( fn );
    else if (selfilter.contains("Compressed XML") or fn.endsWith("*.ZML")
             or fn.endsWith("*.zml"))
      rdv->loadXmlOverlay( fn[0] );
    else if (selfilter.contains("CGNS") or fn.endsWith(".CGNS")
             or fn.endsWith(".cgns"))
      rdv->loadMeshOverlay( fn[0] );
    else
      rdv->loadAnyOverlay( fn );

    saveOverlayAct->setEnabled(true);
    saveOverlayAsAct->setEnabled(true);
    showOverlayAct->setEnabled(true);
    trafoOverlayAct->setEnabled(true);
    outlineOverlayAct->setEnabled(true);
    fitSectionsAct->setEnabled(true);
    maintab->setCurrentWidget( rdv );

    // update projector settings
    fred->setProjector( rdv->frameProjector() );

  } catch (Error & xcp) {
    QString msg;
    msg  = tr("<b>Problem reading verlay file: '")+fn[0]+"'.</b>\n";
    msg += tr("Error message: ")+qstr(xcp.what());
    QMessageBox::information( this, "sumo", msg);
    statusBar()->showMessage( tr("Overlay import aborted"), 2000 );
    return;
  }
}

void SumoMain::revert()
{
  if (filename == "" or filename.isEmpty())
    return;
  
  try {
    XmlElement xe;
    xe.read(str(filename));
    model->clear();
    model->fromXml(xe);
  } catch (Error & xcp) {
    QString msg;
    msg  = tr("<b>Problem reading input file: '")+filename+"'.</b>\n";
    msg += tr("Error message: ")+qstr(xcp.what());
    QMessageBox::information( this, "sumo", msg);
    statusBar()->showMessage( tr("Revert aborted"), 2000 );
    return;
  }
  useNewModel();
}

void SumoMain::save()
{
  if ( filename.isEmpty() ) {
    saveAs();
    return;
  }
  XmlElement xm( model->toXml() );
  xm.write( append_suffix( filename, ".smx"), XmlElement::PlainText );
  statusBar()->showMessage( tr( "File %1 saved" ).arg( filename ), 2000 );
}

void SumoMain::saveAs()
{
  QString caption = tr("Save assembly to file");
  QString filter = tr("Sumo models (*.smx);; Raw surface data (*.xml);; "
                      "All files (*)");
  QString fn = QFileDialog::getSaveFileName(this, caption, lastdir, filter);
  if ( !fn.isEmpty() ) {
    lastdir = QFileInfo(fn).absolutePath();
    if (fn.contains(".xml")) {
      XmlElement xe(model->collectionXml());
      xe.write( str(fn), XmlElement::PlainText  );
    } else {
      filename = fn;
      save();
      caption = QString("sumo ") + _sumo_qversion + " : " + filename;
      this->setWindowTitle(caption);
    }
  } else {
    statusBar()->showMessage( tr("Saving aborted"), 2000 );
  }
}

void SumoMain::generateMesh()
{
  // mesh generation options
  MeshOptions dlg(this, *model);
  if (dlg.exec() != QDialog::Accepted)
    return;
  
  // run mesh generation
  MGenProgressPtr mpg(new MGenProgressCtrl(this, *model));
  try {

    // must force complete remeshing because re-use of refined
    // and intersected previous mesh is not robust
    for (uint i=0; i<model->ncomponents(); ++i)
      model->component(i)->surfaceChanged();

    model->processSurfaceMesh(mpg);
    model->ctsystem().updateGeometry();
    
    // bail out if process was interrupted by user
    if (mpg->interrupt())
      return;
    
  } catch (Error & xcp) {
    QString msg;
    msg  = tr("<h2>Surface mesh generation failed. </h2><hr>\n");
    msg += tr("<p>Error message: <br>") + QString::fromStdString(xcp.what());
    msg += tr("</p>");
    msg += tr("<p>This usually means that the mesh in the vicinity of the "
              "intersection is too coarse to represent the actual intersection "
              "line geometry accurately enough. Reducing the edge length parameters "
              "can help in this case.</p>");
    QMessageBox::information( this, tr("Mesh generation failed"), msg);
    statusBar()->showMessage( tr("Mesh generation aborted"), 2000 );
    return;
  }
  
  // destroy progress indicator
  mpg.reset();
  
  // show mesh if successfull
  if (model->mesh().nfaces() > 0) {
    
    mshview->display( &(model->mesh()) );
    switchTab( itab_mshview );

    // enable mesh-related actions
    mvOptionsAct->setEnabled(true);
    saveSurfMeshAct->setEnabled(true);
    saveVolMeshAct->setEnabled(false);
    xpTritetAct->setEnabled(true);
    genVolMeshAct->setEnabled(true);
    meshCutAct->setEnabled(true);

    askMeshSave();
  }
}

void SumoMain::askMeshSave() 
{
  DlgSaveMesh *dlg = new DlgSaveMesh(this, model->mesh());
  dlg->show();
}

void SumoMain::saveSurfaceMesh() 
{
  QString caption = tr("Save mesh to file");
  QString selfilter, filter;

  // check whether we can support tetgen output
  if (model->volumeMesh().nfaces() == 0) {
    filter = tr("Native (*.zml);;"
                "Standard CGNS (*.cgns);;"
                "dwfs mesh (*.msh);;"
                "STL (*.stl);;"
                "All files (*)");
  } else {
    filter = tr("dwfs mesh (*.msh);;"
                "STL (*.stl);;"
                "Tetgen (*.smesh);;"
                "All files (*)");
  }

  QString fn = QFileDialog::getSaveFileName(this, caption, lastdir,
                                            filter, &selfilter);
  if (not fn.isEmpty()) {
    lastdir = QFileInfo(fn).absolutePath();
    statusBar()->showMessage(tr("Writing surface mesh to ")+fn);
    qApp->processEvents();
    if (selfilter.contains(".zml")) {
      MxMesh mx;
      mx.appendSection(model->mesh());
      BinFileNodePtr bfp = mx.toXml(true).toGbf(true);
      bfp->write( append_suffix(str(fn), ".zml"),
                  BinFileNode::CompressedLZ4 );
    } else if (selfilter.contains("CGNS")) {
      MxMesh mx;
      mx.appendSection(model->mesh());
      mx.writeCgns( append_suffix(str(fn), ".cgns") );
    } else if (selfilter.contains("STL")) {
      model->mesh().writeAsciiSTL(str(fn));
    } else if (selfilter.contains("Tetgen")) {
      model->volumeMesh().writeSmesh( append_suffix(str(fn), ".smesh") );
    } else {
      model->toDwfsMesh().write( append_suffix(str(fn), ".msh"),
                                 XmlElement::PlainText  );
    }
  } else {
    statusBar()->showMessage(tr("Mesh not saved."));
  }
}

void SumoMain::saveVolumeMesh() 
{
  QString caption = tr("Save volume mesh to file");
  QString selfilter, filter = tr("Native (*.zml);;"
                                 "EDGE (*.bmsh);;"
                                 "CGNS, standard BCs (*.cgns);;"
                                 "CGNS, BCs as sections (*.cgns);;"
                                 "SU2 (*.su2);;"
                               #if defined(HAVE_NETCDF)
                                 "TAU (*.taumesh);;"
                               #endif
                                 //                   "Tetgen (*.ele *.node);;"
                                 "All files (*)");
  QString fn = QFileDialog::getSaveFileName(this, caption, lastdir, filter, &selfilter);
  if (not fn.isEmpty()) {
    lastdir = QFileInfo(fn).absolutePath();
    statusBar()->showMessage(tr("Writing volume mesh to ")+fn);
    qApp->processEvents();

    try {

      const MxMesh & mx( model->mxMesh() );

      if (selfilter.contains(".zml")) {
        BinFileNodePtr bfp = mx.toXml(true).toGbf(true);
        bfp->write( append_suffix(str(fn), ".zml"),
                    BinFileNode::CompressedLZ4 );
      } else if (selfilter.contains(".bmsh")) {
        mx.writeFFA( str(fn) );
        // model->volumeMesh().writeMsh( append_suffix(str(fn), ".bmsh"));
        // model->volumeMesh().writeBoc( append_suffix(str(fn), ".aboc"));
#if defined(HAVE_NETCDF)
      } else if (selfilter.contains("TAU")) {
        // MxMesh mx;
        // model->volumeMesh().toMx(mx);
        mx.writeTau( append_suffix(str(fn), ".taumesh") );
#endif
      } else if (selfilter.contains("CGNS")) {
        bool bcAsSections = selfilter.contains("sections");
        // model->volumeMesh().writeCgns( append_suffix(str(fn), ".cgns"),
        //                                bcAsSections );
        mx.writeCgns(append_suffix(str(fn), ".cgns"), bcAsSections);
      } else if (selfilter.contains("SU2")) {
        // MxMesh mx;
        // model->volumeMesh().toMx(mx);
        mx.writeSU2( append_suffix(str(fn), ".su2") );
        //      } else if (selfilter.contains("Tetgen")) {
        //        model->volumeMesh().writeTetgen(str(fn));
      }

    } catch (Error & xcp) {
      QString msg;
      msg  = tr("<h2>Cannot save volume mesh. </h2><hr>\n");
      msg += tr("<p>Error message: <br>") + QString::fromStdString(xcp.what());
      msg += tr("</p>");
      QMessageBox::information( this, tr("File cannot be saved."), msg);
      return;
    }

  } else {
    statusBar()->showMessage(tr("Mesh not saved."));
  }
}

void SumoMain::about()
{
  QString s;
  s  = tr("<center><h2>sumo</h2></center>");
  s += tr("<p><center>Version ") + _sumo_qversion + "</center></p>";
  s += tr("<p>Surface modeling tool for aircraft configurations.<br>");
  s += tr("For more information, visit <p><center><b>http://www.larosterna.com</b></center></p>");
  s += tr("<p>This program is free software; you can redistribute it and/or modify"
          "it under the terms of the GNU General Public License, version 2,"
          "as published by the Free Software Foundation.</p>");
  s += tr("<p>Copyright 2007-2014 by david@larosterna.com</p>");

  // system information
  // std::string hwa = SysInfo::primaryHardwareAddress();
  s += tr("<hr><center><h3> System Information </h3></center><p>");
  // s += tr("Primary MAC: ") + QString::fromStdString(hwa) + "<br>";
  s += tr("Physical RAM: %1 MByte<br>").arg( SysInfo::physMemory() );
  s += tr("Processors: %1<br>").arg( SysInfo::nproc() );

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
  s += "</p>";
  
  QMessageBox::about( this, tr("sumo"), s);
}

void SumoMain::newAssembly()
{
  CreateAssembly dlg(this);
  dlg.setLastDir( lastdir );
  if (dlg.exec() == QDialog::Accepted) {
    if (dlg.useTemplate()) {
      AssemblyPtr ptr = dlg.create();
      if (ptr) {
        model = ptr;
        useNewModel();
      }
    } else {
      load(dlg.file());
    }
  }
}

void SumoMain::newWing()
{
  WingSkeletonPtr wsp(new WingSkeleton);
  wsp->rename("Wing"+str(model->nwings()));
  model->addWing(wsp);

  WingManagerWidget *wedit = new WingManagerWidget(this, wsp);
  connect(wedit, SIGNAL(geometryChanged()),
          rdv, SLOT(updateGeometry()));
  connect(wedit, SIGNAL(geometryChanged()),
          asytree, SLOT(update()));
  wedit->exec();

  asytree->update();
}

void SumoMain::newBody()
{
  BodySkeletonPtr bsp(new BodySkeleton);
  bsp->rename("Body"+str(model->nbodies()));
  model->addBody(bsp);
  asytree->update();
  
  skewi->setBody(bsp);
}

void SumoMain::globalScaling()
{
  QString title(tr("Enter global geometry scaling factor"));
  QString label(tr("Scaling factor"));
  bool ok(true);
  double f = QInputDialog::getDouble(this, title, label,
                                     1.0, 0.0, 1e12, 6, &ok);
  if (ok and (f > 1e-12) and (f < 1e12)) {
    model->globalScale(f);
    rdv->updateGeometry();
    rdv->repaint();
  }
}

void SumoMain::globalTransform()
{
  if (model == nullptr)
    return;

  if (dlgGlobalTrafo == nullptr) {
    dlgGlobalTrafo = new DlgGlobalTransform(this);
  }

  if (dlgGlobalTrafo->exec() == QDialog::Accepted) {
    model->globalScale( dlgGlobalTrafo->scale() );
    model->globalTranslation( dlgGlobalTrafo->translation() );
    fred->build();
    rdv->updateGeometry();
    rdv->repaint();
  }
}

void SumoMain::editControlSystem()
{
  // show the control system
  model->ctsystem().updateGeometry();
  model->ctsystem().toggleVisible(true);
  rdv->updateGeometry();
  
  CsEditorWidget *cse = new CsEditorWidget(this, *model);
  connect(cse, SIGNAL(geometryChanged()), rdv, SLOT(updateGeometry()));
  cse->setModal(false);
  cse->show();
}

void SumoMain::editJetEngines()
{
  JetEngineEditor jee(this, *model);
  jee.exec();
}

void SumoMain::removeObject()
{
  QTreeWidgetItem *itm = asytree->currentItem();

  ShBodyItem *bi = dynamic_cast<ShBodyItem*>(itm);
  if (bi) {
    uint idx = model->find(bi->geometry()->name());
    if (idx != NotFound) {
      
      ComponentPtr cp = model->sumoComponent(idx);
      
      model->erase(idx);
      asytree->update();
      rdv->updateGeometry();
      
      if (cp.get() == skewi->currentBody().get())
        skewi->setBody(  BodySkeletonPtr() );
      
      if (cp.get() == fred->currentBody().get())
        fred->setFrame( BodySkeletonPtr(), -1 );
      
    }
    return;
  }

  ShWingItem *wi = dynamic_cast<ShWingItem*>(itm);
  if (wi) {
    uint idx = model->find(wi->geometry()->name());
    if (idx != NotFound) {
      model->erase(idx);
      asytree->update();
      rdv->updateGeometry();
    }
    return;
  }

  ShBFrameItem *bfi = dynamic_cast<ShBFrameItem*>(itm);
  if (bfi) {
    BodySkeletonPtr bsp = bfi->body();
    const Vct3 & org = bfi->geometry()->origin();
    bsp->removeFrame(org[0]);
    skewi->reconstruct();
    asytree->update();
    rdv->updateGeometry();
    return;
  }

  ShWSectionItem *afi = dynamic_cast<ShWSectionItem*>(itm);
  if (afi) {
    WingSkeletonPtr wsp = afi->wing();
    wsp->removeSection(afi->index());
    wsp->interpolate();
    asytree->update();
    rdv->updateGeometry();
    return;
  }
}

void SumoMain::editObject()
{
  QTreeWidgetItem *itm = asytree->currentItem();

  ShBodyItem *bi = dynamic_cast<ShBodyItem*>(itm);
  if (bi) {
    BodySkeletonPtr bsp = bi->geometry();
    DlgEditBody *dlg = new DlgEditBody(this, bsp);
    connect(dlg, SIGNAL(geometryChanged()),
            skewi, SLOT(update()));
    connect(dlg, SIGNAL(geometryChanged()),
            asytree, SLOT(update()) );
    connect(dlg, SIGNAL(geometryChanged()),
            rdv, SLOT(updateGeometry()));
    dlg->show();
    return;
  }

  ShWingItem *wi = dynamic_cast<ShWingItem*>(itm);
  if (wi) {
    WingSkeletonPtr wsp = wi->geometry();
    WingManagerWidget *wedit = new WingManagerWidget(this, wsp);
    connect( wedit, SIGNAL(geometryChanged()),
             rdv, SLOT(updateGeometry()));
    connect( wedit, SIGNAL(geometryChanged()),
             asytree, SLOT(update()));
    wedit->setModal(false);
    wedit->show();
    return;
  }

  ShBFrameItem *bfi = dynamic_cast<ShBFrameItem*>(itm);
  if (bfi) {
    uint fix = bfi->index();
    if (fix != NotFound)
      fred->setFrame(bfi->body(), fix);
    else
      fred->setFrame(bfi->body(), 0);
    if (fred->editProperties()) {
      skewi->update();
      asytree->update();
      rdv->updateGeometry();
    }
    return;
  }
  
  ShWSectionItem *afi = dynamic_cast<ShWSectionItem*>(itm);
  if (afi) {
    bool ok;
    WingSectionPtr afp(afi->geometry());
    WingSkeletonPtr wsp(afi->wing());
    SectionEditor dlg(this, afp);
    if (dlg.exec() == QDialog::Accepted) {
      ok = dlg.process();
      if (ok) {
        wsp->interpolate();
        asytree->update();
        rdv->updateGeometry();
      }
    }
  }
}

void SumoMain::copyObject()
{
  QTreeWidgetItem *itm = asytree->currentItem();

  ShBodyItem *bi = dynamic_cast<ShBodyItem*>(itm);
  if (bi) {
    BodySkeletonPtr bsp = bi->geometry()->clone();
    bsp->rename(bi->geometry()->name()+"Copy");
    model->addBody(bsp);
    asytree->update();
    rdv->updateGeometry();
    return;
  }

  ShWingItem *wi = dynamic_cast<ShWingItem*>(itm);
  if (wi) {
    WingSkeletonPtr wsp = wi->geometry()->clone();
    wsp->rename(wi->geometry()->name()+"Copy");
    model->addWing(wsp);
    asytree->update();
    rdv->updateGeometry();
    return;
  }
}

void SumoMain::mirrorObject()
{
  QTreeWidgetItem *itm = asytree->currentItem();

  ShBodyItem *bi = dynamic_cast<ShBodyItem*>(itm);
  if (bi) {
    BodySkeletonPtr bsp = bi->geometry()->xzMirrorCopy();
    model->addBody(bsp);
    asytree->update();
    rdv->updateGeometry();
    return;
  }

  ShWingItem *wi = dynamic_cast<ShWingItem*>(itm);
  if (wi) {
    WingSkeletonPtr wsp = wi->geometry()->xzMirrorCopy();
    model->addWing(wsp);
    asytree->update();
    rdv->updateGeometry();
    return;
  }
}

void SumoMain::showObject(bool flag)
{
  QTreeWidgetItem *itm = asytree->currentItem();

  ShBodyItem *bi = dynamic_cast<ShBodyItem*>(itm);
  if (bi) {
    BodySkeletonPtr bsp = bi->geometry()->clone();
    bsp->visible( flag );
    rdv->updateGeometry();
    cerr << bsp->name() << (flag ? (" visible ") : (" hidden ")) << endl;
    return;
  }

  ShWingItem *wi = dynamic_cast<ShWingItem*>(itm);
  if (wi) {
    WingSkeletonPtr wsp = wi->geometry()->clone();
    wsp->visible( flag );
    rdv->updateGeometry();
    cerr << wsp->name() << (flag ? (" visible ") : (" hidden ")) << endl;
    return;
  }
}

void SumoMain::fitWingSections()
{
  if (not rdv)
    return;
  if (not model)
    return;

  dlgFitWing->assign( model, rdv->frameProjector(), rdv->fitIndicator() );
  if (selectedWing != NotFound)
    dlgFitWing->selectSection(selectedWing, selectedWingSection);

  dlgFitWing->show();
}

void SumoMain::fitScreen()
{
  if (maintab->currentWidget() == rdv) {
    rdv->fitScreen();
  } else if (maintab->currentWidget() == mshview) {
    mshview->fitScreen();
  }
}

void SumoMain::switchTab(int itab)
{
  maintab->setCurrentIndex(itab);
  if (itab == itab_rdv) {
    statusBar()->showMessage(tr("Rendering all surfaces "
                                "(this may take a while)"), 2000);
    rdv->updateGeometry();
    rdv->repaint();
    snapshotAct->setEnabled(true);
  } else if (itab == itab_skewi) {
    skewi->update();
    snapshotAct->setEnabled(false);
    statusBar()->showMessage("Middle button/wheel zooms, right button pans.");
  } else if (itab == itab_fred) {
    if (not fred->hasFrame()) {
      if (model->nbodies() > 0)
        fred->setFrame(model->body(0), 0);
      fred->setProjector( rdv->frameProjector() );
    }
    QString msg("Middle button/wheel zooms, right button pans. ");
    msg += " +/- move to next (+x) or previous (-x) frame.";
    statusBar()->showMessage(msg);
    snapshotAct->setEnabled(false);
  } else if (itab == itab_mshview) {
    snapshotAct->setEnabled(true);
  }
}

void SumoMain::processTreeSelection(ShTreeItem *item)
{
  selectedBody = NotFound;
  selectedBodyFrame = NotFound;
  selectedWing = NotFound;
  selectedWingSection = NotFound;

  ShBodyItem *bi = dynamic_cast<ShBodyItem*>(item);
  if (bi != 0) {
    selectedBody = bi->index();
    skewi->setBody(bi->geometry());
    maintab->setCurrentIndex( itab_skewi );
    nacGeoAct->setEnabled(true);
    return;
  } else {
    nacGeoAct->setEnabled(false);
  }
  
  ShWingItem *wi = dynamic_cast<ShWingItem*>(item);
  if (wi != 0) {
    selectedWing = wi->index();
    return;
  }

  ShBFrameItem *bfi = dynamic_cast<ShBFrameItem*>(item);
  if (bfi != 0) {
    selectedBody = bfi->parent();
    uint idx = bfi->index();
    if (idx != NotFound) {
      selectedBodyFrame = idx;
      fred->setFrame(bfi->body(), idx);
    } else {
      fred->setFrame(bfi->body(), 0);
    }
    maintab->setCurrentIndex( itab_fred );
    return;
  }

  ShWSectionItem *wsi = dynamic_cast<ShWSectionItem*>(item);
  if (wsi != 0) {
    selectedWing = wsi->parent();
    selectedWingSection = wsi->index();
  }
}

void SumoMain::showTreeMenu(ShTreeItem *item, const QPoint & p)
{
  selectedBody = NotFound;
  selectedBodyFrame = NotFound;
  selectedWing = NotFound;
  selectedWingSection = NotFound;

  ShBodyItem *bi = dynamic_cast<ShBodyItem*>( item );
  ShWingItem *wi = dynamic_cast<ShWingItem*>( item );
  if (bi or wi) {

    showObjAct->setEnabled(true);
    cpObjAct->setEnabled(true);
    // treeMenu->addAction(cpObjAct);

    exportGridAct->setEnabled(true);
    // treeMenu->addAction(exportGridAct);

    xzmObjAct->setEnabled(true);
    // treeMenu->addAction(xzmObjAct);

    if (bi) {
      selectedBody = bi->index();
      nacGeoAct->setEnabled(true);
      // treeMenu->addAction(nacGeoAct);
      showObjAct->setChecked( bi->geometry()->visible() );

    } else if (wi) {
      selectedWing = wi->index();
      nacGeoAct->setEnabled(false);
      // treeMenu->removeAction(nacGeoAct);
      showObjAct->setChecked( wi->geometry()->visible() );
    }

  } else {

    ShBFrameItem *bfi = dynamic_cast<ShBFrameItem*>(item);
    ShWSectionItem *wsi = dynamic_cast<ShWSectionItem*>(item);

    if (bfi) {
      selectedBody = bfi->parent();
      selectedBodyFrame = bfi->index();
    } else if (wsi) {
      selectedWing = wsi->parent();
      selectedWingSection = wsi->index();
    }

    showObjAct->setEnabled(false);
    cpObjAct->setEnabled(false);
    // treeMenu->removeAction(cpObjAct);
    exportGridAct->setEnabled(false);
    // treeMenu->removeAction(exportGridAct);
    xzmObjAct->setEnabled(false);
    // treeMenu->removeAction(xzmObjAct);
  }
  treeMenu->exec(p);
}

void SumoMain::showMeshDrawOptions()
{
  if (mshview != 0)
    mshview->dlgDrawOptions();
}

void SumoMain::importGrid()
{
  // pick file
  QString caption = tr("Import body from grid file");
  QString filter = tr("Text files (*.txt);; All files (*)");
  QString fn = QFileDialog::getOpenFileName(this, caption, lastdir, filter);
  if (not fn.isEmpty()) {
    try {
      BodySkeletonPtr bsp(new BodySkeleton);
      bsp->rename("Body"+str(model->nbodies()));
      bsp->importSections(str(fn));
      model->addBody(bsp);
      skewi->setBody(bsp);
      asytree->update();
      rdv->updateGeometry();
      rdv->showEntireScene();
      rdv->repaint();
    } catch (Error & xcp) {
      QString msg;
      msg  = tr("<b>Problem reading grid file: '")+fn+"'.</b>\n";
      msg += tr("Error message: ")+qstr(xcp.what());
      QMessageBox::information( this, "sumo", msg);
      statusBar()->showMessage( tr("Loading aborted"), 2000 );
      return;
    }
  }
}

void SumoMain::exportGrid()
{
  uint nsf(model->nbodies() + model->nwings());
  if (nsf == 0) {
    QString title( tr("No surface to export") );
    QString text;
    text = tr("There is no surface to export yet.");
    QMessageBox::information(this, title, text);
    return;
  }
  
  // fetch index of selected surface, if any
  QTreeWidgetItem *itm = asytree->currentItem();

  uint idx(NotFound);
  ShBodyItem *bi = dynamic_cast<ShBodyItem*>(itm);
  ShWingItem *wi = dynamic_cast<ShWingItem*>(itm);
  if (bi) {
    idx = model->find( bi->geometry()->name() );
  } else if (wi) {
    idx = model->find( wi->geometry()->name() );
  }
  
  // open export dialog
  ExportRow dlg(*model, this);
  if (idx == NotFound) {
    uint nstore(0);
    nsf = model->ncomponents();
    while (dlg.exec() == QDialog::Accepted and nstore < nsf) {
      dlg.store();
      ++nstore;
      nsf = model->ncomponents();
      dlg.setSelected(nstore%nsf);
    }
  } else {
    dlg.setSelected(idx);
    if (dlg.exec() == QDialog::Accepted)
      dlg.store();
  }
}

void SumoMain::saveSnapshot()
{
  int itab = maintab->currentIndex();
  if (itab == itab_mshview) {
    if (mshview != 0)
      mshview->saveSnapshot();
  } else if (itab == itab_rdv) {
    if (rdv != 0)
      rdv->saveSnapshot();
  } else
    statusBar()->showMessage(tr("Snapshots are only taken from 3D views"), 2000);
}

void SumoMain::exportBoundary()
{
  ExportTritet xpt(this, *model);
  xpt.execute( lastdir );
}

void SumoMain::generateVolMesh()
{
  if (dlgTetgen == 0) {
    dlgTetgen = new DlgTetgen(this);
    // needs update for hybrid mesh -> use code from scope
    // connect(dlgTetgen, SIGNAL(volumeMeshAvailable(bool)),
    //        this, SLOT(showMeshCut(bool)));
    connect(dlgTetgen, SIGNAL(volumeMeshAvailable(bool)),
            saveVolMeshAct, SLOT(setEnabled(bool)));
  }

  dlgTetgen->assign(model);
  dlgTetgen->show();
}

void SumoMain::showMeshCut(bool flag)
{
  if (flag) {
    mshview->displayCut( &(model->volumeMesh()) );
    mshview->repaint();
  }
}

void SumoMain::exportIges()
{
  QString caption = tr("Export assembly to IGES file");
  QString filter = tr("IGES files (*.igs);;"
                      "All files (*)");
  QString fn = QFileDialog::getSaveFileName(this, caption, lastdir, filter);
  if ( !fn.isEmpty() ) {
    lastdir = QFileInfo(fn).absolutePath();
    model->exportIges( QFile::encodeName(fn).constData() );
  } else {
    statusBar()->showMessage( tr("Saving aborted"), 2000 );
  }
}

void SumoMain::importCsm()
{
  QString caption = tr("Import CEASIOM geometry from XML file");
  QString filter = tr("XML files (*.xml);; All files (*)");
  QString fn = QFileDialog::getOpenFileName(this, caption, lastdir, filter);
  if (not fn.isEmpty()) {
    lastdir = QFileInfo(fn).absolutePath();
    loadCsm(fn);
  }
}

void SumoMain::loadCsm(const QString & fn)
{
  try {
    CsmGenerator csg;
    csg.read( str(fn) );
    model = csg.create();
    useNewModel();

    // display import warning messages
    QString msg(QString::fromStdString(CsmGenerator::msg()));
    if (not msg.isEmpty()) {
      QString box = tr("<b>CEASIOM import messages:</b><hr/>");
      box += msg;
      QMessageBox::information( this, "CEASIOM Import", box);
    }

  } catch (Error & xcp) {
    QString msg;
    msg  = tr("<b>Problem reading CEASIOM file: '")+fn+"'.</b>\n";
    msg += "<b/><hr/>";
    msg += tr("Error message: ")+qstr(xcp.what());
    QMessageBox::information( this, "CEASIOM Import", msg);
    statusBar()->showMessage( tr("Loading aborted"), 2000 );
    return;
  }
}

void SumoMain::waveDrag()
{
  if (dlgWaveDrag == 0)
    dlgWaveDrag = new WaveDragDlg(this);

  Indices intakeTags;
  const int njet = model->njet();
  for (int i=0; i<njet; ++i) {
    const JetEngineSpec & js( model->jetEngine(i) );
    const int nin = js.nintake();
    for (int j=0; j<nin; ++j)
      js.intakeRegion(j).insertTag( intakeTags );
  }
  std::sort(intakeTags.begin(), intakeTags.end());

  dlgWaveDrag->assign( model->mesh(), intakeTags );
  dlgWaveDrag->show();
}

void SumoMain::editNacelleGeometry()
{
  if (NacelleGeometryDlg::showing())
    return;

  ShBodyItem *bi = dynamic_cast<ShBodyItem *>(asytree->currentItem());
  if (bi != 0) {
    NacelleGeometryDlg *dlg = new NacelleGeometryDlg(this, *(bi->geometry()));
    connect( dlg, SIGNAL(geometryChanged()), rdv, SLOT(updateGeometry()) );
    connect( dlg, SIGNAL(geometryChanged()), skewi, SLOT(update()) );
    dlg->show();
  }
}

void SumoMain::dragEnterEvent(QDragEnterEvent *event)
{
  if (event->mimeData()->hasFormat("text/uri-list"))
    event->acceptProposedAction();
}

void SumoMain::dropEvent(QDropEvent *event)
{
  QString uri( event->mimeData()->data("text/uri-list") );

  // extract just the first filename
  uri = uri.left( uri.indexOf('\n') ).simplified();
  if (not uri.isEmpty()) {
    load( QUrl(uri).toLocalFile() );
    event->acceptProposedAction();
  }
}
