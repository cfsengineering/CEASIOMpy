
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
 
#include <iostream>
#include <genua/xcept.h>

#include "wingtipcap.h"

using namespace std;

WingtipCap::WingtipCap(const PointList<3> & bnd)
{
  // identify upper and lower side
  uint mid;
  mid = bnd.size() / 2;

  if (bnd.size()%2 == 1) {
    upper.resize(mid+1);
    lower.resize(mid+1);
    for (uint i=0; i<=mid; i++) {
      upper[i] = bnd[i];
      lower[i] = bnd[bnd.size()-1-i];
    }
  }
  else {
    upper.resize(mid);
    lower.resize(mid);
    for (uint i=0; i<mid; i++) {
      upper[i] = bnd[i];
      lower[i] = bnd[bnd.size()-1-i];
    }
  }
  
  
//   cout << "Boundary:" << endl;
//   for (uint i=0; i<lower.size(); ++i)
//     cout << lower[i] << upper[i] << endl;

  // rotation axis
  ax = bnd[mid] - 0.5*(bnd.front() + bnd.back());
  ax /= norm(ax);
}

const PointGrid<3> & WingtipCap::makeCap(uint nv, Real rout)
{
  // right/lower/fwd tip cap
  Vct3 ctr, ry, rx;
  Real phi;
  pg.resize(upper.size(), nv);
  for (uint i=0; i<upper.size(); i++) {
    ctr = 0.5*(upper[i]+lower[i]);
    ry = upper[i] - ctr;
    rx = cross(ax, ry);
    rx *= rout*norm(ry)/norm(rx);
    // rx = norm(ry)*cross(ax, ry).normalized();
    if (norm(ry) > gmepsilon) {
      for (uint j=0; j<nv; j++) {
        phi = PI* Real(j)/(nv-1);
        pg(i,j) = ctr + rx*sin(PI-phi) + ry*cos(PI-phi);
      }
    }
    else {
      for (uint j=0; j<nv; j++)
        pg(i,j) = ctr;
    }
  }
  return pg;
}

void WingtipCap::writeOogl(std::ostream & os) const
{
  // OOGL output for geomview
  if (pg.size() == 0)
    throw Error("Call WingtipCap::make*() before generating output.");

  os << "{ MESH " << endl;
  os << "  " << pg.nrows() << "  " << pg.ncols() << endl;

  for (uint j=0; j < pg.ncols(); j++) {
    for (uint i=0; i < pg.nrows(); i++) {
      os << "  " << pg(i,j) << "  ";
    }
    os << endl;
  }
  os << "}" << endl;
}

