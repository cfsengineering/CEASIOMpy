/* ------------------------------------------------------------------------
 * file:       framepainter.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Draws frame curve plus editing handles
 * ------------------------------------------------------------------------ */

#include <iostream>
#include <QPainter>

#include "framepainter.h"

using namespace std;

qreal FramePainter::hds = 10.0;

FramePainter::FramePainter()
{
  bEditable = false;
  bDrawEdges = false;
  bConstrained = false;
  dorg = QPointF(0.0, 0.0);
  ppm = 100.0;
}

void FramePainter::init(const QPolygonF & key, const QPolygonF & cv)
{
  tkey = key;
  dkey.resize(key.size());
  bzp.changePolygon(cv);
  clearOverlay();
}

void FramePainter::setOverlay(const QVector<QPointF> & sgs)
{
  tsgs = sgs;
  dsgs.resize(tsgs.size());
}

void FramePainter::clearOverlay()
{
  tsgs.clear();
  dsgs.clear();
}

void FramePainter::replace(const QPointF & org, qreal pp)
{
  dorg = org;
  ppm = pp;
  if (bEditable) {
    const int nh(tkey.size());
    for (int i=0; i<nh; ++i)
      dkey[i] = (tkey[i] - dorg)*ppm;
    makeBoxes();
    const int ns = tsgs.size();
    for (int i=0; i<ns; ++i)
      dsgs[i] = (tsgs[i] - dorg)*ppm;
  }
  bzp.replace(org, pp);
}

void FramePainter::makeBoxes()
{
  const int nh(dkey.size());
  hboxes.resize(nh);
  for (int i=0; i<nh; ++i) {
    qreal x = dkey[i].x();
    qreal y = dkey[i].y();
    hboxes[i] = QRectF(x-0.5*hds, y-0.5*hds, hds, hds);
  }
}

void FramePainter::setHandleSize(double s)
{
  hds = s;
}

void FramePainter::paint(QPainter *painter)
{
  QPen fpen;

  // draw overlay, if present
  if (not dsgs.empty()) {
    fpen.setColor(Qt::gray);
    fpen.setWidth(2);
    painter->setPen(fpen);
    painter->drawLines(dsgs);
    fpen.setWidth(1);
  }

  // draw curve first 
  bzp.paint(painter);
  
  // draw handle points 
  if (bEditable) {
    
    painter->setPen(Qt::lightGray);
    if (bDrawEdges) 
      painter->drawPolyline(dkey);
    
    painter->setPen(Qt::black);
    if (bConstrained) {
      painter->setBrush(Qt::white);
      const int nh(hboxes.size());
      for (int i=0; i<nh; ++i) {
        painter->drawEllipse(hboxes[i]);  
      }
    } else {
      painter->setBrush(Qt::red);
      const int nh(hboxes.size());
      for (int i=0; i<nh; ++i) {
        painter->drawEllipse(hboxes[i]);  
      }
    }
  }
}

