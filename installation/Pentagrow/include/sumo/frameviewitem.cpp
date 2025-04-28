
/* ------------------------------------------------------------------------
 * file:       frameviewitem.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * GraphicsView item for skeleton views (side and top perspective)
 * ------------------------------------------------------------------------ */
 
#include "frameviewitem.h"

#include <iostream>
#include <QPainter>

using namespace std;

double FrameHandle::hds = 10;
    
void FrameHandle::place(const QPointF & dorg, qreal ppm, 
               const QPointF & pos, qreal h)
{
  tpos = pos;
  th = h;
  replace(dorg, ppm);
}
    
void FrameHandle::paint(QPainter *painter) const
{
  // line top to bottom 
  painter->setPen(Qt::gray);
  
  qreal x = ctr.x();
  qreal y = ctr.y();
  painter->drawLine(QPointF(x, y+0.5*mh), QPointF(x, y-0.5*mh));
 
  // circular handles top and bottom 
  painter->setPen(Qt::black);
  painter->setBrush(Qt::red);
  painter->drawEllipse(tbox);
  painter->drawEllipse(bbox);
  
  // rectangular handle in the center 
  painter->setBrush(Qt::darkGreen);
  painter->drawRect(cbox);
}

