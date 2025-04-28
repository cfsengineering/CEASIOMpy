
/* ------------------------------------------------------------------------
 * file:       framepainter.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Draws frame curve plus editing handles
 * ------------------------------------------------------------------------ */

#ifndef SUMO_FRAMEPAINTER_H
#define SUMO_FRAMEPAINTER_H

#include <cassert>
#include <vector>
#include <QPointF>
#include <QColor>
#include <genua/defines.h>
#include "bezierpainter.h"

/**
*/
class FramePainter
{
  public:
    
    /// set minimum default settings 
    FramePainter();

    /// initialize geometry: handles and curve 
    void init(const QPolygonF & key, const QPolygonF & cv);
    
    /// set overlay segments to draw
    void setOverlay(const QVector<QPointF> & sgs);

    /// disable overlay display
    void clearOverlay();

    /// change editable state 
    void editable(bool flag) {bEditable = flag;}
    
    /// change control point mode 
    void drawEdges(bool flag) {bDrawEdges = flag;}
    
    /// change constraint state
    void shapeConstrained(bool flag) {bConstrained = flag;}
    
    /// number of handles drawn 
    uint nHandles() const {return hboxes.size();}
    
    /// set color to use for curve drawing 
    void setCurveColor(const QColor & c) {bzp.setColor(c);}
    
    /// adjust handle size 
    static void setHandleSize(double s);
    
    /// change offset or scaling 
    void replace(const QPointF & org, qreal pp);
    
    /// access the position of handle i 
    const QPointF & position(int i) const {
      assert(i < tkey.size());
      return tkey[i];
    }
    
    /// move the physical position of handle i  
    void move(int i, qreal dx, qreal dy) {
      if (not bConstrained) {
        tkey[i].rx() += dx;
        tkey[i].ry() += dy;
        dkey[i] = (tkey[i] - dorg)*ppm;
        hboxes[i] = QRectF(dkey[i].x()-0.5*hds, dkey[i].y()-0.5*hds, hds, hds);
      }
    }
    
    /// change curve data 
    void changePolygon(const QPolygonF & p) {bzp.changePolygon(p);}
    
    /// draw curve and handles (if editable) 
    void paint(QPainter *painter);
    
    /// check if p is in handle box (returns -1 if none) 
    int onHandle(const QPointF & p) const {
      const int nh(hboxes.size());
      for (int i=0; i<nh; ++i) {
        if (hboxes[i].contains(p))
          return i;
      }
      return -1;
    }
    
  private:
    
    /// interpolate bezier control points 
    void interpolate(const QPolygonF & p);

    /// construct handle boxes to draw 
    void makeBoxes();
    
  private:
    
    /// drawing offset from origin (x,z-plane)
    QPointF dorg;
    
    /// drawing scale: pixel-per-meter
    qreal ppm;
    
    /// handle positions, real and drawing space 
    QPolygonF tkey, dkey;
    
    /// curve to draw, real and drawing space 
    BezierPainter bzp;
    
    /// boxes for handles 
    std::vector<QRectF> hboxes;
    
    /// section of overlay geometry (linear segments)
    QVector<QPointF> tsgs, dsgs;

    /// flag to indicate whether to draw handles 
    bool bEditable, bDrawEdges, bConstrained;
    
    /// size of handle 
    static qreal hds;
};

#endif
