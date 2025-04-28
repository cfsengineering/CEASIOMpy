
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

#ifndef SCOPE_H
#define SCOPE_H

#include <QVariant>
#include <QMainWindow>
#include "forward.h"
#include "view.h"
#include "splitter.h"

class QAction;
class QMenu;
class QToolBar;
class QSettings;
class QActionGroup;
class QFrame;
class QBoxLayout;

/** Main window.

  Scope manages actions, menus and dialogs and contains the
  main data elements.

  */
class Scope : public QMainWindow
{
  Q_OBJECT

public:

  /// default construction and child widget setup
  Scope();

  /// cleanup
  ~Scope();

  /// change app settings
  static void changeSetting(const QString & key, const QVariant & val);

  /// retrieve app settings
  static QVariant setting(const QString & key,
                          const QVariant & defval = QVariant());

signals:

  /// emitted when dialogs keeping state should be closed
  void closeDialogs();

public slots:

  /// load file by name
  void load(const QString &fname);

  /// load file by name
  void load(const QStringList &fnames);

  /// show message box and quit if OpenGL is not supported
  void checkOpenGL();

protected:

  /// accept file name URI
  void dragEnterEvent(QDragEnterEvent *event);

  /// try to load dropped filename
  void dropEvent(QDropEvent *event);

private slots:

  /// open new view window
  void newView();

  /// show file selection dialog for loading
  void choose();

  /// load trajectory file
  void loadTrajectory();

  /// save viz data
  void save();

  /// update sidebar tree
  void updateTree();

  /// change currently used directory
  void userPath(const QString &pth) { lastdir = pth; }

  /// show small info window
  void about();

  /// open user manual
  void openHelp(const QString &link = "");

  /// embed annotation from file
  void embedNote();

  /// fit display into window
  void fitScreen();

  /// enable/disable full-scene antialiasing
  void enableMultisampling(bool flag);

  /// enable/disable blended antialiasing
  void enableBlending(bool flag);

  /// surface color contour settings
  void colorContours(int ifield = -1);

  /// change display settings for specific mesh section (forwarding)
  void editSection(int isec = -1) {
      editComponent(isec, -1);
  }

  /// change display settings for element group (forwarding)
  void editBoco(int iboco = -1) {
      editComponent(-1, iboco);
  }

  /// edit display settings for mesh components
  void editComponent(int isec = -1, int iboco = -1);

  /// show mesh deformation dialog
  void deformationSettings();

  /// dialog controlling plane volume mesh slice
  void cutMesh();

  /// mesh transformation dialog
  void meshTrafo();

  /// display mesh properties
  void meshInfo();

  /// integrate pressures
  void integratePressure();

  /// merge with another mesh
  void mergeMesh();

  /// copy a mesh section
  void copySection();

  /// eliminate unused nodes (after removing sections, for example)
  void rmIdleNodes();

  /// dialog to display mesh quality
  void meshQuality();

  /// slice dialog
  void surfaceSlice();

  /// add artificial modeshape
  void addRigidMode();

  /// generate displacements from flap specifications
  void generateFlapDisplacements();

  /// display element info box
  void elementInfo(int k);

  /// switch element picking off
  void uncheckPickElement();

  /// display node info box
  void nodeInfo(int k);

  /// switch element picking off
  void uncheckPickNode();

  /// start/stop animation
  void toggleAnimation();

  /// change animation play/stop button
  void togglePlayButton(bool flag);
  
  /// open plane grid dialog
  void gridPlanes();

  /// direct mapping of cp field to NASTRAN loads
  void mapDirect();

  /// steady longitudinal maneuver load mapping
  void mapLongMLoad();

  /// frequency-domain mode acceleration
  void mapFRFLoads();

  /// time-domain inertial relief maneuver loads
  void mapTdlLoads();

  /// interpolate displacements using RBFs or shell projection
  void mapDisplacements();

  /// generate new field containing the maximum value over subcases
  void genCaseMax();

  /// manually assemble flutter mode shape
  void buildFlutterMode();

  /// enable/disable actions depending on mesh data
  void switchActions();

private:

  /// create main window actions
  void initActions();

  /// create main window menus (using actions)
  void initMenus();

  /// close dialogs before loading
  void closeAllDialogs();

private:

  /// proxy model for the tree view
  SidebarTreeModel *treeModel;

  /// left sidebar tree view
  SidebarTree *treeView;

  /// splitter separating the two main widgets
  Splitter *mwSplitter;

  /// main window layout
  QFrame *mwRightFrame;

  /// main window layout
  QBoxLayout *mwFrameLayout;

  /// main display widget
  ViewManager *view;

  /// display controller
  PlotController *plotControl;

  /// group for mouse pick actions
  QActionGroup *pickActions;

  /// open/close main window
  QAction *newMainAct, *closeMainAct;

  /// file operations
  QAction *openAct, *loadTjAct, *saveAct;

  /// auxilliary
  QAction *snapshotAct, *fitScreenAct, *quitAct, *aboutAct, *helpAct;

  // statistics

  /// display mesh properties
  QAction *meshInfoAct;

  /// pick nodal data
  QAction *nodeInfoAct;

  /// pick element data
  QAction *elemInfoAct;

  /// show integrated forces
  QAction *integPressureAct;

  // display

  /// surface coloring
  QAction *surfContoursAct;

  /// display of mesh sections/bocos
  QAction *componentsAct;

  /// mesh deformation and trajectories
  QAction *dispSettingsAct;

  /// highlight bad quality elements
  QAction *meshQualityAct;

  /// hedgehog plot
  QAction *plotHedgehogAct;

  /// streamline plot
  QAction *plotStreamlinesAct;

  /// display volume elements intersected by plane
  QAction *meshCutAct;

  /// display x-y plot of plane slice through surface elements
  QAction *surfSliceAct;

  /// visual aids : grid lines
  QAction *toggleGridAct;

  /// toggle animation status (start/stop)
  QAction *toggleAnimAct;

  // mesh modifications

  /// transform mesh nodes
  QAction *meshTrafoAct;

  /// embed xml annotation from file
  QAction *embedNoteAct;

  /// merge with another mesh
  QAction *mergeMeshAct;

  /// copy a mesh section
  QAction *copySectionAct;

  /// eliminate unused nodes
  QAction *rmIdleNodesAct;

  /// add rigid-body motion modeshape
  QAction *addModeAct;

  /// generate bocos and displacement fields from flap specs
  QAction *genFlapDisp;

  // mesh deformation and load generation

  /// deformation interpolation using RBFs or shell projection
  QAction *mapStrDeform;

  /// load interpolation, quasi-steady longitudinal
  QAction *longLoadMap, *directMap, *tdlMap, *frfMap;

  /// statistics and evaluation
  QAction *genCaseMaxAct;

  /// manually assemble flutter mode
  QAction *buildFlutterAct;

  /// view setup
  QAction *fsaaAct, *blendAct, *perspAct;

  /// main app menus
  QMenu *fileMenu, *viewMenu, *editMenu, *loadsMenu, *solveMenu;

  /// main app toolbar
  QToolBar *fileTools, *viewTools;

  /// remember location last visited
  QString lastdir, lastfile;

  /// surface contour settings dialog
  ContourDialog *dlgContour = nullptr;

  /// settings dialog for mesh components
  ComponentDialog *dlgComponent = nullptr;

  /// dialog to configure display of volume elements sliced by plane
  MeshCutDialog *dlgMeshCut = nullptr;

  /// mesh properties editor
  EditMeshDialog *dlgEditMesh = nullptr;

  /// copy a mesh section
  SectionCopyDialog *dlgCopySection = nullptr;

  /// node/field transformation dialog
  TransformationDialog *dlgTransform = nullptr;

  /// mesh displacement dialog
  DisplacementDialog *dlgDisplace = nullptr;

  /// grid plane dialog
  PlaneGridDialog *dlgGrid = nullptr;

  /// opens a dialog showing a slice through the mesh
  SliceDlg *dlgSlice = nullptr;

  /// box showing element data
  ElementInfoBox *elmInfoBox = nullptr;

  /// box showing node data
  NodeInfoBox *nodeInfoBox = nullptr;

  /// pressure integration dialog
  ForceDisplayDialog *dlgForceDisplay = nullptr;

  /// dialog for adding rigid-body modes
  AddModeshapeDialog *dlgAddMode = nullptr;

  /// longitudinal maneuver load interpolator
  LongManeuvDialog *dlgLongLoads = nullptr;

  /// direct pressure mapping dialog
  DirectPMapDialog *dlgDirectPMap = nullptr;

  /// load interpolation for frequency domain MA
  InrelLoadDialog *dlgInrelLoads = nullptr;

  /// interpolation of structural displacements
  DeformationMapDlg *dlgMapDef = nullptr;

  /// mesh quality dialog
  MeshQualityDialog *dlgMeshQuality = nullptr;

  /// build flutter mode dialog
  BuildFlutterModeDialog *dlgBuildFlutterMode = nullptr;
};


#endif
