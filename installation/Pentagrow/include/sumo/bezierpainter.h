
/* ------------------------------------------------------------------------
 * file:       bezierpainter.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Generate and draw bezier segments 
 * ------------------------------------------------------------------------ */

#ifndef SUMO_BEZIERPAINTER_H
#define SUMO_BEZIERPAINTER_H

#include <vector>
#include <QPointF>
#include <QPolygonF>
#include <QColor>

class QPainter;

/** Creates and draws Bezier segemnts.

  BezierPainter takes a point set which contains alternating curve points and 
  tangents and computes cubic Bezier control points from these. The paint()
  member draws the curve with the specified color and transformation. 
*/
class BezierPainter
{
  public:

    /// empty painter
    BezierPainter() : lnc(Qt::darkBlue), bDirty(true) {}

    /// initialize with curve and transformation 
    BezierPainter(const QPolygonF & p, const QPointF & org, qreal pp);
    
    /// change origin and scale 
    void replace(const QPointF & org, qreal pp) {
      dorg = org;
      ppm = pp;
      bDirty = true;
    }
    
    /// interpolate points: even indices are points, odd are tangents  
    void changePolygon(const QPolygonF & p) {
      interpolate(p);
      bDirty = true;
    }
    
    /// change color to paint with 
    void setColor(const QColor & c) {lnc = c;}
    
    /// draw line 
    void paint(QPainter *painter);
    
  private:
    
    /// transform to Bezier points 
    void interpolate(const QPolygonF & p);
    
  private:
    
    /// bezier control points (true and transformed space)
    QPolygonF tcp, dcp;
    
    /// current origin 
    QPointF dorg;
    
    /// color to draw outline 
    QColor lnc;
    
    /// drawing scale 
    qreal ppm;

    /// indicates whether a new transformation is necessary 
    bool bDirty;
};

typedef std::vector<BezierPainter> BezierPainterArray;

#endif
