
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
 

#include "paver.h"
#include <genua/trimesh.h>

void Paver::nextRow(const PointList<2> & row)
{
  // last vertex of current top row
  loffset = hoffset;
  hoffset = ppt.size();

  // append vertices
  ppt.insert(ppt.end(), row.begin(), row.end());

  // cannot create triangles for the first row
  if (hoffset == 0)
    return;

  // walk along the row and add triangles
  uint nlo = hoffset - loffset;
  uint nhi = ppt.size() - hoffset;
  uint ihi(0), ilo(0), vi[3];
  while (ihi < nhi-1 or ilo < nlo-1) {
    vi[0] = hoffset + ihi;
    vi[1] = loffset + ilo;
    if (ilo == nlo-1) {
      ++ihi;
      vi[2] = hoffset + ihi;
    } else if (ihi == nhi-1) {
      ++ilo;
      vi[2] = loffset + ilo;
    } else {
      if (pickLow(ilo,ihi)) {
        ++ilo;
        vi[2] = loffset + ilo;
      } else {
        ++ihi;
        vi[2] = hoffset + ihi;
      }
    }
    itriangles.insert(itriangles.end(), vi, vi+3);
  }
}

void Paver::nextVRow(Real v, const Vector & up)
{
  const int n = up.size();
  PointList<2> qts(n);
  for (int i=0; i<n; ++i)
    qts[i] = vct(up[i], v);
  nextRow(qts);
}

void Paver::fan(const Vct2 & ctr)
{
  loffset = hoffset;     // base index to connect to ctr
  hoffset = ppt.size();  // index of ctr

  ppt.push_back(ctr);
  const int nv = hoffset - loffset;
  uint vi[3];
  vi[2] = hoffset;
  for (int i=1; i<nv; ++i) {
    vi[0] = loffset+i-1;
    vi[1] = loffset+i;
    itriangles.insert(itriangles.end(), vi, vi+3);
  }
}

bool Paver::pickLow(uint ilo, uint ihi) const
{
  // paving front mean tangent
  Vct3 pl0 = eval(loffset+ilo);
  Vct3 pl1 = eval(loffset+ilo+1);
  Vct3 ph0 = eval(hoffset+ihi);
  Vct3 ph1 = eval(hoffset+ihi+1);

  Vct3 tgl = (pl1-pl0);
  Vct3 tgh = (ph1-ph0);
  Vct3 tg = tgl.normalized() + tgh.normalized();

  Vct3 base = 0.5*(pl0 + ph0);

  return dot(tg,pl1-base) < dot(tg,ph1-base);
}

void Paver::exportMesh(TriMesh &msh)
{
  const int nv = ppt.size();
  PointList<3> pts(nv), nrm(nv);
  for (int i=0; i<nv; ++i) {
    Vct3 S, Su, Sv;
    srf.plane(ppt[i][0], ppt[i][1], S, Su, Sv);
    pts[i] = S;
    nrm[i] = cross(Su, Sv).normalized();
  }

  msh.importMesh(pts, nrm, triangles());
}
