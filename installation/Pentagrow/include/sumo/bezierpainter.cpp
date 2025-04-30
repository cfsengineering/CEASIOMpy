
/* ------------------------------------------------------------------------
 * file:       bezierpainter.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Generate and draw bezier segments 
 * ------------------------------------------------------------------------ */

#include <iostream>
#include <cassert>
#include <QPainter>
#include <QPainterPath>
#include <genua/defines.h>
#include "bezierpainter.h"

using namespace std;

BezierPainter::BezierPainter(const QPolygonF & p, 
                             const QPointF & org, qreal pp) : 
    lnc(Qt::darkBlue), bDirty(true)
{
  changePolygon(p);
  replace(org, pp);
}

void BezierPainter::paint(QPainter *painter)
{
  const int ncp(dcp.size());
  if (ncp < 4)
    return;
  
  // transform manually - this could be done inside QPainter as well
  if (bDirty) {
    for (int i=0; i<ncp; ++i)
      dcp[i] = (tcp[i] - dorg) * ppm;
    bDirty = false;
  }
  
  QPainterPath path;
  path.moveTo(dcp[0]);
  for (int i=1; i<ncp; i+=3) 
    path.cubicTo(dcp[i], dcp[i+1], dcp[i+2]);
  painter->strokePath(path, QPen(lnc));
}

void BezierPainter::interpolate(const QPolygonF & p)
{
  const int np(p.size());
  assert(np%2 == 0);
  
  // number of Bezier segments 
  const int nbs(np/2 - 1);

  // number of Bezier points 
  const int nbp(3*nbs + 1);
  tcp.resize(nbp);
  dcp.resize(nbp);
  qreal slen, t1len, t2len;
  for (int i=0; i<nbs; ++i) {
    const QPointF & p1( p[2*i] );
    const QPointF & t1( p[2*i + 1] );
    t1len = sqrt( sq(t1.x()) + sq(t1.y()) ); 
    const QPointF & p2( p[2*i + 2] );
    const QPointF & t2( p[2*i + 3] );
    t2len = sqrt( sq(t2.x()) + sq(t2.y()) );
    slen = sqrt( sq(p2.x()-p1.x()) + sq(p2.y()-p1.y()) ) / 3.;    
    tcp[3*i] = p1;
    tcp[3*i + 1] = p1 + slen/t1len * t1;
    tcp[3*i + 2] = p2 - slen/t2len * t2;
  }
  tcp[nbp-1] = p[np-2];
}
