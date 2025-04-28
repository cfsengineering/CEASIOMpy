
/* ------------------------------------------------------------------------
 * file:       skeletonview.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Used for body side- and top views
 * ------------------------------------------------------------------------ */

#ifndef SUMO_SKELETONVIEW_H
#define SUMO_SKELETONVIEW_H

#include <cassert>
#include <QWidget>
#include <QFrame>
#ifndef Q_MOC_RUN
#include "frameviewitem.h"
#include "bezierpainter.h"
#endif

class QResizeEvent;
class QPaintEvent;
class QMenu;
class QPixmap;

/** View and edit widget for side and top view.
  
  SkeletonView draws top- or side views of a body surface, including markers
  which indicate the location and size of interpolation frames. This class
  manages display and user interaction with the screen representation, while
  the parent object SkeletonWidget updates the underlying geometry whenever 
  needed. 

*/
class SkeletonView : public QFrame
{
  Q_OBJECT
  
  public:
    
    /// create view from scene 
    SkeletonView(QWidget *parent);
    
    /// remove all frames and outlines
    void clear();
    
    /// change coordinate names to display 
    void changeNames(const QString & x, const QString & y, const QString & h);
    
    /// add frame item h high, at pos  
    void addFrame(double x, double y, double h) {
      fhdl.push_back( FrameHandle(QPointF(x,y), h) );
    }
    
    /// modify frame geometry only 
    void changeFrame(uint i, double x, double y, double h) {
      assert(i < fhdl.size());
      fhdl[i].place(QPointF(xdorg,ydorg), ppm, QPointF(x,y), h);
    }
    
    /// add an outline curve
    void addOutline(const QPolygonF & pline, const QColor & c=Qt::darkBlue) 
    {
      otl.push_back( BezierPainter(pline, QPointF(xdorg,ydorg), ppm) );
      otl.back().setColor(c);
    }
    
    /// change polygon for outline 
    void changeOutline(uint i, const QPolygonF & pline) {
      assert(i < otl.size());
      otl[i].changePolygon(pline);
    }
    
    /// retrieve position and width of frame i 
    double fdim(uint i, QPointF & pos) const {
      assert(i < fhdl.size());
      pos = fhdl[i].position();
      return fhdl[i].height();
    }
    
    /// status of the symmetry lock
    bool symLock() const {return symlock;}
    
  public slots:
    
    /// switch symlock on/off
    void symLock(bool flag) {symlock = flag;}
    
    /// flip state of the symmetry lock
    void flipSymLock() {symlock = !symlock;}
    
    /// fit scene into view 
    void fitView();
    
    /// adapt handle positions 
    void displace();
    
    /// change x-position of frame i by dx
    void xMoveFrame(int i, double dx);
    
    /// insert frame at mouse pointer position 
    void insertFrame();
    
    /// remove frame nearest mouse pointer position 
    void removeFrame();
    
    /// open context menu (if applicable)
    bool contextMenu();
    
    /// load background image from file 
    void loadBackgroundImage();
    
    /// switch background image on/off 
    void toggleBackgroundImage();
    
  signals:
    
    /// notify that frame i moved by dx 
    void xFrameMoved(int i, double dx);
    
    /// emitted when frame modification ended
    void frameModified(int i);
    
    /// request frame insertion
    void sigInsertFrame(double x);
    
    /// request frame removal
    void sigRemoveFrame(double x);
    
    /// post mouse pointer position message 
    void mptrPosition(const QString & s);
    
  protected:
    
    /// overload resize event 
    void resizeEvent(QResizeEvent *e);
    
    /// overload paint event
    void paintEvent(QPaintEvent *e);
    
    /// register position of mouse press
    void mousePressEvent(QMouseEvent *e);
    
    /// move mouse for panning (RMB) and zooming (MMB) 
    void mouseMoveEvent(QMouseEvent *e);
    
    /// finalize mouse move action
    void mouseReleaseEvent(QMouseEvent *e);
    
    /// zoom on mouse wheel
    void wheelEvent(QWheelEvent *e);
    
    /// check if any frame is hit by mouse at mspress
    bool selectFrame();
    
    /// generate actions for context menu
    void initActions();
    
    /// post a message about the position of frame i 
    void postFramePosition(int i, double t);
    
    /// transform background image (if any)
    void fitBackgroundImage(int w, int h);
    
  private:
    
    /// frame handles to use 
    FrameHandleArray fhdl;
    
    /// outlines to draw 
    BezierPainterArray otl;
    
    /// origin of the drawing area in physical space 
    qreal xdorg, ydorg;
    
    /// extent of the current frames
    qreal xmin, xmax, ymin, ymax; 
    
    /// current scaling : pixel per meter
    qreal ppm;

    /// what to do in interactive mode 
    enum {SkvPan, SkvZoom, SkvMove, SkvModTop, SkvModBot, SkvNone} act;

    /// position of last mouse press 
    QPoint mspress;
    
    /// context menu 
    QMenu *ctmenu;
    
    /// actions for context menu 
    QAction *actFlipLock, *actInsert, *actRemove, *actLoadBgi, *actToggleBgi;

    /// original image and transformed version 
    QPixmap *origim, *trfim;
    
    /// names to use for coordinate output 
    QString xname, yname, hname;
    
    /// index of selected frame, number of user zoom/scales 
    int iselect, nzoom;
    
    /// allow non-symmetric motion? Draw background image?
    bool symlock, drawbgi;
    
    /// keep track of mouse motion (trigger context menu if span == 0)
    double span;
};

#endif

