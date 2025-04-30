
/* ------------------------------------------------------------------------
 * project:    scope
 * file:       view.h
 * copyright:  (c) 2009 by <dlr@kth.se>
 * ------------------------------------------------------------------------
 * Interface to QGLViewer
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#ifndef SCOPE_VIEW_H
#define SCOPE_VIEW_H

#include <QGLViewer/qglviewer.h>
#ifndef Q_MOC_RUN
#include <genua/point.h>
#include <genua/smatrix.h>
#include "planegrid.h"
#include "forward.h"
#endif

typedef enum {MvPosX, MvNegX, MvPosY, MvNegY,
              MvPosZ, MvNegZ, MvTopLeftFwd} MvCamDirection;

/** Main 3D View widget.
 *
 * This is the main 3D view handling object which processes user interaction
 * and animation control by means of the QGLViewer base class. OpenGL
 * drawing is not handled here but by MeshPlotter and friends managed by the
 * PlotController class.
 *
 * \sa PlotController, MeshPlotter
 */
class ViewManager  : public QGLViewer
{
  Q_OBJECT

public:

  /// generate empty view widget
  ViewManager(QWidget *parent);

  /// save internal settings
  ~ViewManager();

  /// figure out whether this is a high-resolution display
  bool ishidpi() const;

  /// connect to plot controller
  void assign(PlotController *plc);

  /// access scene dimensions
  const Vct3f & lowCorner() const {return lobox;}

  /// access scene dimensions
  const Vct3f & highCorner() const {return hibox;}

  /// access plane grid display aid
  const PlaneGrid & planeGrid(uint k) const {
    assert(k < 3);
    return aidGrid[k];
  }

  /// access plane grid display aid
  PlaneGrid & planeGrid(uint k) {
    assert(k < 3);
    return aidGrid[k];
  }

  /// true if animation is running
  bool animating() const {return bAnimating;}

  /// globally set animation time scaling (default 1/2048)
  static void animationTimeScale(float f) { s_animation_tscale = f; }

  /// access global time scale
  static float animationTimeScale() { return s_animation_tscale; }

public slots:

  /// clear view window
  void clear();

  /// save screenshot
  void saveSnapshot();

  /// change view direction
  void changeCamDirection(MvCamDirection cd);

  /// toggle perspective projection
  void togglePerspective(bool flag);

  /// use current geometry
  void updateDrawing();

  /// update and repaint then
  void updateRepaint();

  /// compute scene properties
  void updateSceneDimensions();

  /// overloaded animation start
  void startAnimation();

  /// overloaded animation stop
  void stopAnimation();

  /// toggle element picking mode
  void togglePickElement(bool flag);

  /// toggle element picking mode
  void togglePickNode(bool flag);

  /// use perspectiv projection?
  void enablePerspectiveProjection(bool flag);

  /// interface for motion controller
  void multiAxisControl(const SpaceMouseMotionData &mdata);

  /// handle space mouse buttons
  void multiAxisButtonPressed(uint buttons);

signals:

  /// emitted for new status bar message
  void postStatusMessage(const QString & s);

  /// posted when animation starts/stops
  void animationRunning(bool flag);

  /// fired when element picked
  void elementPicked(int k);

  /// fired when element picked
  void nodePicked(int k);

protected:

  /// initialize display
  void init();

  /// call display list
  void draw();

  /// plot the current scene immediately
  void drawNow();

  /// motion animation
  void animate();

  /// retrieve point under mouse position
  bool pointUnderPixel(const QPoint & pscreen, Vct3f & pos) const;

  /// catch keys x,y,z to change view direction
  void keyPressEvent(QKeyEvent *e);

  /// display current 3D position when mouse button released
  void mouseReleaseEvent(QMouseEvent* e);

private:

  /// plot controller
  PlotController *plotControl;

  /// timer for animation
  QTime animtime;

  /// visual aid : plane grids
  PlaneGrid aidGrid[3];

  /// object movement matrix extracted from SpaceNavigator, if present
  Mtx44 viewTransform;

  /// scene bounding box
  Vct3f lobox, hibox;

  /// determine whether animating, mesh cut displayed
  bool bAnimating;

  /// picking modes
  bool bPickElement, bPickNode;

  /// whether GL has been successfully initialized
  bool bGlInitialized;

  /// whether blended anti-aliasing is enabled
  bool bBlendedAA;

  /// whether to pick point on each mouse release
  bool bPickOnMouseRelease;

  /// static application setting
  static float s_animation_tscale;
};

#endif // VIEW_H
