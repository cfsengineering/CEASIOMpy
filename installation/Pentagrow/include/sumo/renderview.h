
/* ------------------------------------------------------------------------
 * file:       renderview.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * 3D View widget for surfaces
 * ------------------------------------------------------------------------ */

#ifndef SUMO_RENDERVIEW_H
#define SUMO_RENDERVIEW_H

#include <QGLViewer/qglviewer.h>

#ifndef Q_MOC_RUN
#include "forward.h"
#include "assembly.h"
#include "productoverlay.h"
#include "frameprojector.h"
#endif

class QMouseEvent;
class QStringList;
class TransformationDialog;
class SpaceMouseMotionData;

/** OpenGL Rendering widget.

  RenderView shows a BodySkeleton object in a 3D view which
  can be navigated by mouse. It uses the QGLViewer library. 

  */
class RenderView : public QGLViewer
{
  Q_OBJECT
  
public:

  enum MvCamDirection {MvPosX, MvNegX, MvPosY, MvNegY,
                       MvPosZ, MvNegZ, MvTopLeftFwd};

  /// empty initialization
  RenderView(QGLContext *ctx, QWidget *parent, AssemblyPtr pm);

  /// clear OpenGL state
  ~RenderView();

  /// change model to draw
  void setModel(AssemblyPtr pm);

  /// try to identify file type and load automatically
  void loadAnyOverlay(const QStringList & files);

  /// load IGES file for background display
  void loadIgesOverlay(const QString & fname);

  /// load STEP file for background display
  void loadStepOverlay(const QString & fname);

  /// load multiple STL files
  void loadStlOverlay(const QStringList & files);

  /// import computational mesh as overlay
  void loadMeshOverlay(const QString &fname);

  /// retrieve overlay from XML representation
  void loadXmlOverlay(const QString & fname);

  /// access pointer to builtin projection object
  FrameProjectorPtr frameProjector() {return framePj;}

  /// access auxilliary object used to indicate capture rectangles for fitting
  FitIndicatorPtr fitIndicator() {return findic;}

public slots:

  /// recompute geometry to render
  void updateGeometry();

  /// save pixmap snapshot of current view
  void saveSnapshot();

  /// change view direction
  void changeCamDirection(MvCamDirection cd);

  /// enable/disable overlay display
  void showOverlay(bool flag);

  /// enable/disable wireframe overlay
  void wireframeOverlay(bool flag);

  /// save overlay file
  void saveOverlay();

  /// save overlay file, select filename
  void saveOverlayAs();

  /// open dialog for overlay transformation
  void trafoOverlay();

  /// fit display to scene
  void fitScreen();

  /// update geometry transformation for frame projector
  void updateProjector();

  /// interface for motion controller
  void multiAxisControl(const SpaceMouseMotionData &mdata);

  /// handle space mouse buttons
  void multiAxisButtonPressed(uint buttons);

signals:

  /// send message to main window
  void postStatusMsg(const QString & msg);

  /// post mouse click position message
  void mousePosMsg(const QString & s);

protected:

  /// initialize display
  void init();

  /// plot the current scene
  void draw();

  /// help string for Viewer's help window
  QString helpString() const;

  /// intercept clicks on rendered surfaces
  void mouseReleaseEvent(QMouseEvent *e);

  /// catch keys x,y,z to change view direction
  void keyPressEvent(QKeyEvent *e);

private:

  /// build display lists
  void buildDisplayList();

  /// compute scene properties
  void updateSceneDimensions();

  /// construct frame projector
  void buildProjector();

private:

  /// surfaces to render
  AssemblyPtr model;

  /// display list index
  uint iDisplayList;

  /// scene bounding box
  qglviewer::Vec vLo, vHi;

  /// display IGES model in background
  ProductOverlay ovldisp;

  /// frame projection object
  FrameProjectorPtr framePj;

  /// auxilliary painter for capture rectangles for section fitting
  FitIndicatorPtr findic;

  /// colors for drawing polygons and lines
  QColor cPolygon, cLine;

  /// string for help window
  QString shelp;

  /// overlay filename
  QString ovlFileName;

  /// overlay transformation dialog
  TransformationDialog *trafoDlg;

  /// make sure scene is centered on first call
  bool bShown;

  /// whether intialization succeeded
  bool bGlInitialized;
};

#endif

