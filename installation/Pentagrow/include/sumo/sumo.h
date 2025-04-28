
/* ------------------------------------------------------------------------
 * file:       sumo.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Surface modeler program : main widget
 * ------------------------------------------------------------------------ */

#ifndef SUMO_SUMOMAIN_H
#define SUMO_SUMOMAIN_H

#include <QVariant>
#include <QMainWindow>

#ifndef Q_MOC_RUN
#include "forward.h"
#include "assembly.h"
#include "splitter.h"
#endif

class QAction;
class QMenu;
class QToolBar;
class QTabWidget;
class QSettings;
class QGLContext;

/** Surface modeler : Main application window
 
  */
class SumoMain: public QMainWindow
{
  Q_OBJECT

  public:

    /// initialize main widget
    SumoMain();
    
    /// destroy main window
    virtual ~SumoMain();

    /// change app settings
    static void changeSetting(const QString & key, const QVariant & val);
    
    /// retrieve app settings
    static QVariant setting(const QString & key, 
                            const QVariant & defval = QVariant());
    
  public slots:
    
    /// load assembly on startup
    void load(const QString & fn);

    /// import ceasiom xml
    void loadCsm(const QString & fn);
  
    /// create new assembly
    void newAssembly();
    
  protected:

    /// accept file name URI
    void dragEnterEvent(QDragEnterEvent *event);
  
    /// try to load dropped filename
    void dropEvent(QDropEvent *event);

  private slots:

    /// new window
    void newView();

    /// save assembly to file 
    void save();
  
    /// ask for filename and save
    void saveAs();
  
    /// export point grid 
    void exportGrid();
    
    /// import point grid 
    void importGrid();
    
    /// import ceasiom geometry file 
    void importCsm();
    
    /// load IGES/STL geometry as background display
    void loadOverlay();

    /// export IGES file 
    void exportIges();
    
    /// show mesh info box and save optionally
    void askMeshSave();
    
    /// save current surface mesh to file
    void saveSurfaceMesh();
    
    /// save current volume mesh to file
    void saveVolumeMesh();
    
    /// revert to disk version
    void revert();
    
    /// show 'About' box
    void about();
  
    /// generate mesh and save to file
    void generateMesh();
    
    /// load and replace existing assembly
    void loadAndReplace();
  
    /// load and replace existing assembly
    void loadAndAppend();
    
    /// create new wing object
    void newWing();
  
    /// create new body object
    void newBody();
  
    /// apply a global scaling factor to entire geometry
    void globalScaling();

    /// apply a global transformation to entire geometry
    void globalTransform();

    /// edit control system properties
    void editControlSystem();
  
    /// edit jet engine properties 
    void editJetEngines();
    
    /// edit settings for nacelle geometry
    void editNacelleGeometry();

    /// remove the currently selected object
    void removeObject();
  
    /// edit the currently selected object
    void editObject();
  
    /// copy the currently selected object
    void copyObject();

    /// toggle object visibility
    void showObject(bool flag);

    /// generate a xz-mirror copy 
    void mirrorObject();
    
    /// fit all wing sections to reference geometry
    void fitWingSections();

    /// update rendering geometry (if visible)
    void switchTab(int itab);
  
    /// process item selection 
    void processTreeSelection(ShTreeItem *item);
    
    /// show context menu in tree view 
    void showTreeMenu(ShTreeItem *item, const QPoint & p);
    
    /// fit scene to screen
    void fitScreen();

    /// open mesh view drawing options dialog
    void showMeshDrawOptions();
    
    /// save a screenshot of the 3D scene or mesh  
    void saveSnapshot();
    
    /// export boundary mesh
    void exportBoundary();
    
    /// generate volume mesh using tetgen 
    void generateVolMesh();
    
    /// show volume mesh in mesh display
    void showMeshCut(bool flag);
    
    /// compute area distribution by cutting the mesh
    void waveDrag();

  private:
    
    /// create top-level widgets
    void initMainWidgets();
    
    /// initialize menu and toolbar actions 
    void initActions();
    
    /// initialize menus and toolbars 
    void initMenus();
    
    /// notify editors that a new model is in use
    void useNewModel();
  
  private:
  
    /// top-level splitter pane (tree/tab)
    Splitter *splitter;
    
    /// left pane: entity tree
    AssemblyTree *asytree;
    
    /// right pane: tabe widget for editors 
    QTabWidget *maintab;
    
    /// widget indices 
    int itab_skewi, itab_fred, itab_rdv, itab_mshview;
    
    /// skeleton editor 
    SkeletonWidget *skewi;
    
    /// editor for frame
    FrameEditor *fred;

    /// OpenGL context for render and mesh view
    QGLContext *renderContext, *meshContext;

    /// 3D View object
    RenderView *rdv;
    
    /// mesh viewing tool
    TriMeshView *mshview;
    
    /// Geometry data
    AssemblyPtr model;

    /// dialog controlling tetgen execution
    DlgTetgen *dlgTetgen = nullptr;
    
    /// dialog for wave drag estimation
    WaveDragDlg *dlgWaveDrag = nullptr;

    /// wing fitting dialog
    WingSectionFitDlg *dlgFitWing = nullptr;

    /// transformation dialog
    DlgGlobalTransform *dlgGlobalTrafo = nullptr;

    // -- selected properties etc

    /// filename for saving and directory last visisted
    QString filename, lastdir;

    /// body skeleton selected from tree
    uint selectedBody;

    /// body frame selected in tree
    uint selectedBodyFrame;

    /// wing skeleton selected from tree
    uint selectedWing;

    /// wing section selected from tree
    uint selectedWingSection;
    
    // -- actions

    /// new view/close view
    QAction *newMainAct, *closeMainAct;

    /// file menu and toolbar actions
    QAction *openAct, *openAddAct, *saveAct, *saveAsAct, *revertAct, *exportGridAct;
    QAction *importGridAct, *importCsmAct;
    QAction *snapshotAct, *aboutAct, *quitAct, *exportIgesAct;

    /// load IGES file for background display
    QAction *loadOverlayAct;

    /// apply (display) transformation to IGES overlay
    QAction *trafoOverlayAct;

    /// show/hide overlay display
    QAction *showOverlayAct;
    
    /// display overlay as wireframe outline
    QAction *outlineOverlayAct;

    /// save overlay including current transformation etc.
    QAction *saveOverlayAct, *saveOverlayAsAct;

    /// apply global scaling factor to all geometry
    QAction *transformGloballyAct;

    /// fit wing sections to overlay geometry
    QAction *fitSectionsAct;

    /// fit current display to screen
    QAction *fitScreenAct;

    /// edit menu actions
    QAction *newAsmAct, *addBodyAct, *addWingAct, *editCsAct, *editJeAct;
    QAction *nacGeoAct;
    
    /// actions on objects
    QAction *editObjAct, *rmObjAct, *cpObjAct, *xzmObjAct, *showObjAct;
    
    /// mesh menu actions 
    QAction *generateMeshAct, *saveSurfMeshAct, *saveVolMeshAct;
    QAction *xpTritetAct, *mvOptionsAct, *genVolMeshAct, *meshCutAct;
    
    /// main window menus
    QMenu *fileMenu, *editMenu, *viewMenu, *meshMenu, *treeMenu;
    
    /// sub-menus
    QMenu *importMenu, *exportMenu;

    /// main window toolbars
    QToolBar *fileTools, *editTools, *meshTools;
};

#endif
