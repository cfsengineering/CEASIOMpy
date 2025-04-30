
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
 
#include "triset.h"
#include <genua/mxmesh.h>

#include <iostream>
using namespace std;

void TriSet::qrange(Real qmin, Real qmax)
{
  qoff = qmin;
  // qscal = (1 << 30) / (qmax - qmin);
  qscal = std::numeric_limits<uint>::max() / (qmax - qmin);
  cout << "qmin " << qmin << " qmax " << qmax
       << " qoff " << qoff << " qscal " << qscal << endl;
}

void TriSet::qrange(const PointList<2> &pts)
{
  const int np = pts.size();
  Real qmin = std::numeric_limits<Real>::max();
  Real qmax = -qmin;
  for (int i=0; i<np; ++i) {
    for (int k=0; k<2; ++k) {
      qmin = std::min(qmin, pts[i][k]);
      qmax = std::max(qmax, pts[i][k]);
    }
  }

  // extend by 1/16 on each side
  Real qds = (qmax - qmin) / 16.;
  qrange( qmin-qds, qmax+qds );
}

void TriSet::assign(const PointList<2> &vtx, const Indices &tri)
{
  clear();
  const int n = tri.size() / 3;
  Node *pna = (Node *) nodePool.ordered_malloc(n);
  assert(pna != 0);
  for (int i=0; i<n; ++i) {
    QiPoint q = triangleCenter(vtx, &tri[3*i]);
    Node *pn = (new(&pna[i]) Node(q, i));  // placement new
    nodes.insert( *pn );
  }

  // debug
  Vct2 p = vct(0.4, 0.3);
  QiPoint q = quant(p);
  cout << "p " << p << " q " << q << " rq " << rquant(q) << endl;
}

void TriSet::toMx(MxMesh &mx) const
{
  // create line vertices
  PointList<3> lp;
  NodeSet::const_iterator it, last = nodes.end();
  for (it = nodes.begin(); it != last; ++it) {
    Vct2 p = rquant(it->ctr);
//    QiPoint ctr;
//    decodeMorton( it->zcode, ctr[0], ctr[1] );
//    Vct2 p = rquant( ctr );
    lp.push_back( vct(p[0], p[1], 0.0) );
  }

  const int np = lp.size();
  if (np == 0)
    return;

  Indices lns(2*(np-1));
  const uint off = mx.nnodes();
  for (int i=0; i<np-1; ++i) {
    lns[2*i+0] = off + i;
    lns[2*i+1] = off + i+1;
  }

  mx.appendNodes(lp);
  uint isec = mx.appendSection(Mx::Line2, lns);
  mx.section(isec).rename("ZOrder");
}

void TriSet::clear()
{
  nodes.clear();
  nodePool.purge_memory();
}
