
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
 #include "topoisecsegment.h"
#include "topology.h"
#include "sides.h"
#include <genua/mxmesh.h>
#include <genua/trimesh.h>
#include <genua/smallqr.h>

static inline Vct2 bary_project(const TriMesh &t, uint fi, const Vct3 &p)
{
  const PointList<3> & vtx( t.vertices() );
  const uint *v = t.face(fi).vertices();
  SMatrix<3,2,Real> A;
  Vct3 b;
  for (int i=0; i<3; ++i) {
    A(i,0) = vtx[v[1]][i] - vtx[v[0]][i];
    A(i,1) = vtx[v[2]][i] - vtx[v[0]][i];
    b[i] = p[i] - vtx[v[0]][i];
  }

  qrlls<3,2>(A.pointer(), b.pointer());
  return Vct2(b[0], b[1]);
}

static inline Vct2 bary_eval(const PointList<2> &q,
                             const uint vi[], const Vct2 &pj)
{
  Real bu = pj[0];
  Real bv = pj[1];
  Real bw = 1.0 - bu - bv;

  Vct2 qp = bw*q[vi[0]] + bu*q[vi[1]] + bv*q[vi[2]];
  qp[0] = clamp(qp[0], 0.0, 1.0);
  qp[1] = clamp(qp[1], 0.0, 1.0);
  forceNearBnd(gmepsilon, qp);
  return qp;
}

TopoIsecSegment::TopoIsecSegment(uint fa, uint fb, const IndexPairArray &pairs,
                                 const PointList<3> &pts, uint ip)
{
  m_iface[0] = fa;
  m_iface[1] = fb;
  m_tri[0] = pairs[ip].first;
  m_tri[1] = pairs[ip].second;
  m_pts[0] = pts[2*ip+0];
  m_pts[1] = pts[2*ip+1];
}

void TopoIsecSegment::uvMap(const Topology &topo)
{
  const TopoFace & fa( topo.face(m_iface[0]) );
  const TopoFace & fb( topo.face(m_iface[1]) );
  const TriMesh & ma( fa.mesh() );
  const TriMesh & mb( fb.mesh() );

  Vct2 psa = bary_project(ma, m_tri[0], m_pts[0]);
  Vct2 pta = bary_project(ma, m_tri[0], m_pts[1]);
  Vct2 psb = bary_project(mb, m_tri[1], m_pts[0]);
  Vct2 ptb = bary_project(mb, m_tri[1], m_pts[1]);

  const PointList<2> & uva( fa.uvVertices() );
  const PointList<2> & uvb( fb.uvVertices() );
  const uint *va = ma.face( m_tri[0] ).vertices();
  const uint *vb = mb.face( m_tri[1] ).vertices();

  // evaluate location in (u,v) space
  m_uva[0] = bary_eval(uva, va, psa);
  m_uva[1] = bary_eval(uva, va, pta);
  m_uvb[0] = bary_eval(uvb, vb, psb);
  m_uvb[1] = bary_eval(uvb, vb, ptb);
}

void TopoIsecSegment::append(uint fa, uint fb, const IndexPairArray &pairs,
                             const PointList<3> &pts, TopoIsecArray &segm)
{
  const int np = pairs.size();
  const int offset = segm.size();
  segm.resize( offset + np );
  for (int i=0; i<np; ++i)
    segm[offset+i] = TopoIsecSegment(fa, fb, pairs, pts, i);
}

uint TopoIsecSegment::asLines(const TopoIsecArray &segm, MxMesh &mx)
{
  // add each segment as a separate line
  const int nis = segm.size();
  const int voff = mx.nnodes();
  PointList<3> pts(2*nis);
  Indices lns(2*nis);
  for (int i=0; i<nis; ++i) {
    pts[2*i+0] = segm[i].psource();
    pts[2*i+1] = segm[i].ptarget();
    lns[2*i+0] = voff + 2*i + 0;
    lns[2*i+1] = voff + 2*i + 1;
  }

  mx.appendNodes(pts);
  return mx.appendSection(Mx::Line2, lns);
}
