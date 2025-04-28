
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
 
#ifndef SUMO_FITINDICATOR_H
#define SUMO_FITINDICATOR_H

#include "forward.h"
#include <genua/point.h>
#include <genua/color.h>

/** Draw display hint for section fitting.

  Objects of this class draw rectangles to indicate the region covered
  by the section fit algorithms. This helps to determine whether the
  fitting will cover the intended space or whether it may interfere with
  unrelated bodies.

  \sa FrameProjector, WingSection
*/
class FitIndicator
{

public:

  /// construct empty object
  FitIndicator() : clr(0.7f, 0.7f, 1.0f) {}

  /// destroy
  virtual ~FitIndicator();

  /// assign assembly
  void assign(AssemblyPtr asy) {pasy = asy; clear();}

  /// draw rectangles around the specivied wing section, or all sections
  void markWingSection(uint iwing, uint isection = NotFound,
                       Real rChord = 1.5, Real rThick = 0.5);

  /// clear out all stored rectangles
  void clear();

  /// draw rectangles, if any are present
  void draw() const;

private:

  /// draw primitives in immediate mode
  void drawQuads() const;

private:

  /// parent assembly
  AssemblyPtr pasy;

  /// list of rectangle vertices
  PointList<3,float> rects;

  /// color to use for all rectangles
  Color clr;
};

#endif // FITINDICATOR_H
