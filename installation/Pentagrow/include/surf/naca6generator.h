
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
 
#ifndef SURF_NACA6GENERATOR_H
#define SURF_NACA6GENERATOR_H

#include "naca6.h"

/** Compute coordinates for NACA 6-series airfoils.

  Naca6Generator provides an interface to Ladson's program for NACA 6-series
  airfoils. It allows to specify up to ten mean camber lines for superposition.

  Thickness profiles 63-67 and 63A-65A are supported. The former is specified
  simply as an integer in the range 63 to 67, the latter as one between
  163 and 165. Camber profiles can be either standard (icamber 63...67) or
  modified (icamber 163...165). Thickness ratio toc is given as a fraction of
  chord.

  All functions returning int produce an error code as specified in naca6.h

  \ingroup geometry
  \sa Airfoil
  */
class Naca6Generator
{
public:

  /// set default values
  Naca6Generator();

  /// add another mean line specification (up to 10)
  int addMeanLine(double cli, double a);

  /// generate for multiple mean lines
  int generate(int iprof, int icamb, double toc);

  /// generate profile for single mean line
  int generate(int iprof, int icamb, double toc, double cli, double a);

  /// number of coordinates computed
  int ncoord() const {return mnout;}

  /// copy generated coordinates
  void copyCoordinates(double cx[], double cy[]) const;

  /// clear all data (start anew)
  void clear();

private:

  /// coordinates
  double mxyout[800];

  /// for superimposed mean lines
  double ma[10], mcli[10];

  /// array size parameters
  int mncmbl, mnout;
};

#endif

