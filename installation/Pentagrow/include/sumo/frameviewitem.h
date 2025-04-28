
/* ------------------------------------------------------------------------
 * file:       frameviewitem.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Modification handle for skeleton editor
 * ------------------------------------------------------------------------ */

#ifndef SUMO_FRAMEHANDLE_H
#define SUMO_FRAMEHANDLE_H

#include <vector>
#include <QRectF>
#include <QPointF>

class QPainter;

/** Frame handle for skeleton editor.
  */
class FrameHandle
{
  public:
  
    /// create view item 
    FrameHandle(const QPointF & pos, qreal h) : tpos(pos), th(h) {}
    
    /// access current (true) position 
    const QPointF & position() const {return tpos;}
    
    /// access current true height 
    qreal height() const {return th;}
    
    /// compute position and size 
    void place(const QPointF & dorg, qreal ppm, 
               const QPointF & pos, qreal h);
    
    /// change offset or scaling 
    void replace(const QPointF & dorg, qreal ppm) {
      ctr = (tpos - dorg)*ppm;
      mh = th*ppm;
      makeBoxes();
    }
    
    /// move the physical origin 
    void move(qreal dx, qreal dy) {
      tpos.rx() += dx;
      tpos.ry() += dy;
    }
    
    /// move top node by physical offset  
    void moveTop(qreal dy) {
      tpos.ry() += 0.5*dy;
      th += dy;
    }
    
    /// move top node by physical offset  
    void moveBot(qreal dy) {
      tpos.ry() += 0.5*dy;
      th -= dy;
    }
    
    /// access handle size 
    static double handleSize() {return hds;}
    
    /// change handle size (for all items)
    static void setHandleSize(double s) {hds = s;}

    /// draw the item 
    void paint(QPainter *painter) const;
  
    /// true if p in center box 
    bool inCenterBox(const QPointF & p) const {
      return cbox.contains(p);
    }
    
    /// true if p in top box 
    bool inTopBox(const QPointF & p) const {
      return tbox.contains(p);
    }
    
    /// true if p in top box 
    bool inBotBox(const QPointF & p) const {
      return bbox.contains(p);
    }
    
    /// text position (drawing coordinates)
    QPointF textPos() const {return tbox.topLeft();}
    
  private:
    
    /// reconstructs handle boxes 
    void makeBoxes() {
      qreal r = 0.5*hds;
      qreal x = ctr.x();
      qreal y = ctr.y();
      cbox = QRectF(x-r, y-r, hds, hds);
      tbox = QRectF(x-r, y+0.5*mh-r, hds, hds);
      bbox = QRectF(x-r, y-0.5*mh-r, hds, hds);
    }
    
  private:
    
    /// center position (drawing & true)
    QPointF ctr, tpos;
    
    /// vertical size (drawing & true)
    qreal mh, th;
    
    /// rectangles for handles 
    QRectF cbox, tbox, bbox;
    
    /// handle size 
    static qreal hds;
};

typedef std::vector<FrameHandle> FrameHandleArray;

#endif
