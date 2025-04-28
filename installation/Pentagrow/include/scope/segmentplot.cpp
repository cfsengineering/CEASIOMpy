
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#include "segmentplot.h"
#include <genua/mxmeshslice.h>
#include <QPainter>
#include <QPolygonF>
#include <QDebug>

SegmentPlot::SegmentPlot(QCPAxis *keyAxis, QCPAxis *valueAxis)
  : QCPAbstractPlottable(keyAxis, valueAxis) {}

SegmentPlot::~SegmentPlot() {}

void SegmentPlot::assign(const MxMeshSlice &slice, uint xcol, uint ycol)
{
  Matrix m;
  const int nseg = slice.nsegments();
  if (nseg == 0) {
    clearData();
    return;
  }

  segLengths.clear();
  segLengths.reserve(nseg);
  xp.clear();
  yp.clear();
  for (int i=0; i<nseg; ++i) {
    slice.sliceData(i, m);
    if (xcol >= m.ncols() or ycol >= m.ncols()) {
      clearData();
      return;
    }
    const uint nrow = m.nrows();
    qDebug("Segment %d, nrows %d", i, nrow);
    if (nrow == 0)
      continue;
    segLengths.push_back(nrow);
    const Real *xcp = m.colpointer(xcol);
    const Real *ycp = m.colpointer(ycol);
    xp.insert(xp.end(), xcp, xcp+nrow);
    yp.insert(yp.end(), ycp, ycp+nrow);
  }

  qDebug("SegmentPlot: %zu",xp.size());
  if (xp.size() > 0)
    qDebug("x0 = %f, y0 = %f", xp[0], yp[0]);
  if (xp.size() > 1)
    qDebug("x1 = %f, y1 = %f", xp[1], yp[1]);

  // adapt axes
  bool goodRange = true;
  QCPRange range = getKeyRange(goodRange);
  if (goodRange)
    keyAxis()->setRange( range );
  range = getValueRange(goodRange);
  if (goodRange)
    valueAxis()->setRange(range);
}

void SegmentPlot::clearData()
{
  segLengths.clear();
  xp.clear();
  yp.clear();
}

double SegmentPlot::selectTest(double, double) const
{
  return -1.0;
}

void SegmentPlot::draw(QPainter *painter) const
{
  if (segLengths.empty())
    return;
  if (mPen.style() == Qt::NoPen or mPen.color().alpha() == 0)
    return;

  painter->setRenderHint(QPainter::Antialiasing,
           mParentPlot->antialiasedElements().testFlag(QCustomPlot::aeGraphs));
  painter->setPen(mPen);
  painter->setBrush(Qt::NoBrush);

  QPolygonF poly;
  const int nseg = segLengths.size();
  int offset(0);
  for (int i=0; i<nseg; ++i) {
    const int nsp = segLengths[i];
    poly.clear();
    for (int j=0; j<nsp; ++j)
      poly.append( coordsToPixels( xp[offset+j], yp[offset+j] ) );
    if (poly.size() > 1)
      painter->drawPolyline( poly );
    else
      painter->drawEllipse( poly.at(0), 4, 4 );
    offset += nsp;

    if (i == 0)
      qDebug() << "Polyline length: " << poly.size();
  }
}

void SegmentPlot::drawLegendIcon(QPainter *painter, const QRect &rect) const
{
  // draw fill
  if (mBrush.style() != Qt::NoBrush)
  {
    painter->setRenderHint(QPainter::Antialiasing,
             mParentPlot->antialiasedElements().testFlag(QCustomPlot::aeGraphs));
    painter->fillRect(rect.left(), rect.top()+rect.height()/2.0,
                      rect.width(), rect.height()/3.0, mBrush);
  }

  // draw line vertically centered:
  if (mPen.style() != Qt::NoPen and mPen.color().alpha() != 0)
  {
    painter->setRenderHint(QPainter::Antialiasing,
             mParentPlot->antialiasedElements().testFlag(QCustomPlot::aeGraphs));
    painter->setPen(mPen);

    // +5 on x2 else last segment is missing from dashed/dotted pens
    painter->drawLine(rect.left(), rect.top()+rect.height()/2.0,
                      rect.right()+5, rect.top()+rect.height()/2.0);
  }
}

bool SegmentPlot::valueInDomain(double v, SignDomain sd) const
{
  if (sd == sdBoth)
    return true;
  else if ( sd == sdPositive )
    return v >= 0;
  else if ( sd == sdNegative )
    return v <= 0;
  return true;
}

QCPRange SegmentPlot::getKeyRange(bool &validRange,
                                  SignDomain inSignDomain) const
{
  if (xp.empty()) {
    validRange = false;
    return QCPRange();
  }

  validRange = true;
  const int np = xp.size();
  Real xmin = std::numeric_limits<Real>::max();
  Real xmax = -xmin;
  for (int i=0; i<np; ++i) {
    Real v = xp[i];
    if (valueInDomain(v, inSignDomain)) {
      xmin = std::min(xmin, v);
      xmax = std::max(xmax, v);
    }
  }

  Real dx = xmax - xmin;
  xmin -= 0.02*dx;
  xmax += 0.02*dx;

  return QCPRange(xmin, xmax);
}

QCPRange SegmentPlot::getValueRange(bool &validRange,
                                    SignDomain inSignDomain) const
{
  if (yp.empty()) {
    validRange = false;
    return QCPRange();
  }

  validRange = true;
  const int np = yp.size();
  Real xmin = std::numeric_limits<Real>::max();
  Real xmax = -xmin;
  for (int i=0; i<np; ++i) {
    Real v = yp[i];
    if (valueInDomain(v, inSignDomain)) {
      xmin = std::min(xmin, v);
      xmax = std::max(xmax, v);
    }
  }

  Real dx = xmax - xmin;
  xmin -= 0.02*dx;
  xmax += 0.02*dx;

  return QCPRange(xmin, xmax);
}
