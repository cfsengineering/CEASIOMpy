
/* ------------------------------------------------------------------------
 * file:       frameeditor.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Widget for interactive modification of interpolation frames
 * ------------------------------------------------------------------------ */

#ifndef SUMO_FRAMEEDITOR_H
#define SUMO_FRAMEEDITOR_H

#ifndef Q_MOC_RUN
#include "forward.h"
#include "frameprojector.h"
#include "framepainter.h"
#endif
#include <QWidget>
#include <QFrame>

class QPolygonF;
class QMouseEvent;
class QWheelEvent;
class QResizeEvent;
class QPaintEvent;
class QKeyEvent;
class QMenu;
class QAction;
class QPixmap;

class EditFrameProperties;

/** FrameEditor is used to modify interpolation frames.

  This is a graphical editor for the frames from which surfaces are 
  interpolated. It enables to interactively modify the frame by moving 
  interpolated points, removing and inserting points. 

  Since version 1.0, the FrameEditor also displays the previous (green)
  and the following (red) frame in order to provide a better reference for 
  drawing.

  */
class FrameEditor : public QFrame
{
  Q_OBJECT

  public:

    /// default construction
    FrameEditor(QWidget *parent);

    /// check if frame is defined 
    bool hasFrame() const {return bool(bsp);}
    
    /// access currently referenced body
    const BodySkeletonPtr & currentBody() const {return bsp;}
    
    /// change frame to edit, along with its parent surface
    void setFrame(const BodySkeletonPtr & sp, int iframe);
    
    /// assign projector
    void setProjector(FrameProjectorPtr pp);

  public slots:

    /// initialize painters
    void build();
    
    /// fit drawing into view
    void fitView();
    
     /// jump back (+x) one frame
    void nextFrame();
    
    /// jump forward (-x) one frame
    void prevFrame();
    
    /// recreate drawing
    void updateDrawing();

    /// open dialog to modify frame properties
    bool editProperties();
    
    /// load background image from file 
    void loadBackgroundImage();
    
    /// switch background image on/off 
    void toggleBackgroundImage();
    
  private slots:
    
    /// insert interpolation point
    void insertPoint();
    
    /// remove interpolation point
    void removePoint();
    
    /// switch to control point display 
    void toggleControlPoints();
    
    /// eliminate frame constraint
    void eraseConstraint();
    
    /// project one interpolation point onto overlay CAD geometry
    void projectPoint();

    /// project all interpolation points onto overlay CAD geometry
    void projectPoints();

  signals:
    
    /// emitted for new status bar message
    void postStatusMessage(const QString & s);

    /// emitted whenever frame geometry has changed
    void geometryChanged();

  protected:
    
    /// select interpolation point to move
    void mousePressEvent(QMouseEvent *e);

    /// allow interactive movement of interpolation points
    void mouseMoveEvent(QMouseEvent *e);

    /// perform modifications if applicable
    void mouseReleaseEvent(QMouseEvent *e);

    /// zoom on mouse wheel
    void wheelEvent(QWheelEvent *e);
    
    /// repaint widget contents
    void paintEvent(QPaintEvent *e);

    /// change widget size
    void resizeEvent(QResizeEvent *e);
    
    /// change to previous/next frame with (+/-)
    void keyPressEvent(QKeyEvent *e);
    
  private:

    /// construct actions, menus
    void initActions();
    
    /// fetch handles and curve points 
    void fetch(uint i, QPolygonF & hdl, QPolygonF & cv) const;
    
    /// determine limit dimensions for frame i
    void frameDimensions(int i, Vct2 & yzmin, Vct2 & yzmax) const;
    
    /// adapt frame painters to current drawing scale 
    void displace();
    
    /// check for selected handle 
    int selectHandle();
    
    /// rebuild interpolation curve 
    void interpolate();
   
    /// post mouse position 
    void postMousePos();
    
    /// show context menu at mspress
    void contextMenu();
    
    /// transform background image (if any)
    void fitBackgroundImage(int w, int h);
    
    /// convert CAD-space line segments to model space
    void modelSpaceSegments();

  private:

    /// body which owns frames to display 
    BodySkeletonPtr bsp;

    /// overlay projector (may be null)
    FrameProjectorPtr pfpj;

    /// intersections of edited frame and overlay geometry
    FrameProjector::SegmentArray segments;

    /// editable frame on display 
    int iEdit, iFront, iBack, iSelect, iLastHandle;
    
    /// paint frames 
    FramePainter fpEdit, fpFront, fpBack;
    
    /// property dialog
    EditFrameProperties *efp;

    /// drawing origin
    QPointF dorg;
    
    /// drawing scale (pixel per meter)
    qreal ppm; 
    
    /// overlay painting data
    QVector<QPointF> opps;

    /// current action : pan, zoom, move handle
    enum {FePan, FeZoom, FeMove, FeNone} act;
    
    /// position of mouse press 
    QPoint mspress;
    
    /// context menu 
    QMenu *ctmenu;
    
    /// actions 
    QAction *actEditProp, *actInsertPoint, *actRemovePoint;
    QAction *actNextFrame, *actPrevFrame, *actCtrlPoints;
    QAction *actUnconstrain, *actLoadBgi, *actToggleBgi;
    QAction *actProjectPoint, *actProjectAll;

    /// optional background image, transformed version
    QPixmap *origim, *trfim;
    
    /// number of zooms performed
    int nzoom;
    
    /// decide if point motion is locked, ip or ctrl points 
    bool symlock, ctrlpts, drawbgi;
    
    /// used to monitor panning distance 
    double span;
};

#endif

