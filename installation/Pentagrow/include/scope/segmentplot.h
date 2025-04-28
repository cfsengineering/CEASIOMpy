
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
 
#ifndef SCOPE_SEGMENTPLOT_H
#define SCOPE_SEGMENTPLOT_H

#include "qcustomplot.h"
#include <genua/forward.h>
#include <genua/dvector.h>

/** Interface for plotting segmented data in QCustomPlot.
  */
class SegmentPlot : public QCPAbstractPlottable
{
public:

  /// construct plottable
  SegmentPlot(QCPAxis *keyAxis, QCPAxis *valueAxis);

  /// virtual destructor
  virtual ~SegmentPlot();

  /// assign data for a single input-output pair
  void assign(const MxMeshSlice & slice, uint xcol, uint ycol);

  /// remove all contents
  void clearData();

  /// test whether key/value is near plotted segments
  double selectTest(double key, double value) const;

protected:

  /// draw segments
  void draw(QPainter *painter) const;

  /// draw indicator for legend
  void drawLegendIcon(QPainter *painter, const QRect &rect) const;

  /// determine range of values for x-keys
  QCPRange getKeyRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;

  /// determine range of y-values
  QCPRange getValueRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;

private:

  /// utility
  bool valueInDomain(double v, SignDomain sd) const;

private:

  /// segmented data
  Vector xp, yp;

  /// lengths of segments
  Indices segLengths;
};

#endif // SEGMENTPLOT_H
