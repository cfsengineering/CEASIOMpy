
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
 
#include "tritree.h"
#include "treetraverse.h"
#include <surf/guige.h>
#include <genua/cgmesh.h>
#include <genua/smallqr.h>
#include <set>

using namespace std;

// ------------------- local scope --------------------------------------

namespace {

class TriTreeDivider
{
public:

  TriTreeDivider(TriTree & t) : tree(t), iax(0) {}

  // node division criterion
  template <class Iterator>
  bool divide(uint inode, Iterator nbegin, Iterator nend) {
    // return divideLongest(inode, nbegin, nend);
    return divideBBoxCenter(inode, nbegin, nend);
  }

  // sorting criterion : compare elements bounding box center
  bool operator() (uint a, uint b) const {
    // return cmpElementCenter(a,b);
    return cmpBBoxCenter(a, b);
  }

private:

  // node division criterion
  template <class Iterator>
  bool divideLongest(uint inode, Iterator nbegin, Iterator nend) {
    if (nend <= nbegin)
      return false;

    // first, collect all element vertex indices
    std::set<uint> vix;
    for (Iterator itr = nbegin; itr != nend; ++itr) {
      const uint *vi = tree.vertices(*itr);
      vix.insert(vi, vi+3);
    }

    // low/high BV limits
    Vct3f p1, p2;
    p1 =   std::numeric_limits<float>::max();
    p2 = - std::numeric_limits<float>::max();

    // now, process all element vertices
    std::set<uint>::const_iterator itv, vlast = vix.end();
    for (itv = vix.begin(); itv != vlast; ++itv)
      TriTree::DopType::fit(tree.vertex(*itv).pointer(),
                            p1.pointer(), p2.pointer());

    TriTree::DopType & dop( tree.dop(inode) );
    dop.setCoef(p1.pointer(), p2.pointer());
    iax = dop.longestAxis();

    // leaf nodes must be processed to generate the bounding box,
    // but they do not need to be sorted
    return ( uint(std::distance(nbegin, nend)) > tree.minElemCount());
  }

  // node division criterion
  template <class Iterator>
  bool divideBBoxCenter(uint inode, Iterator nbegin, Iterator nend) {
    if (nend <= nbegin)
      return false;

    // limits of the node bounding box
    Vct3f nbp1, nbp2;
    nbp1 =   std::numeric_limits<float>::max();
    nbp2 = - std::numeric_limits<float>::max();

    // determine split direction from box around *triangle bbox centers*
    Vct3f cbp1(nbp1), cbp2(nbp2);

    for (Iterator itr = nbegin; itr != nend; ++itr) {
      const uint *vi = tree.vertices(*itr);

      // establish bounding box for triangle
      Vct3f p1, p2;
      p1 =   std::numeric_limits<float>::max();
      p2 = - std::numeric_limits<float>::max();
      for (int k=0; k<3; ++k) {
        const float *pk = tree.vertex(vi[k]).pointer();
        TriTree::DopType::fit(pk, p1.pointer(), p2.pointer());
      }

      // for each triangle, extend node box bounds to fitt al vertices,
      TriTree::DopType::fit(p1.pointer(), nbp1.pointer(), nbp2.pointer());
      TriTree::DopType::fit(p2.pointer(), nbp1.pointer(), nbp2.pointer());

      // p1 = center of bounding box, cbp1/2 corners of box around centers
      p1 = 0.5f*(p1 + p2);
      TriTree::DopType::fit(p1.pointer(), cbp1.pointer(), cbp2.pointer());
    }

    TriTree::DopType & dop( tree.dop(inode) );
    dop.setCoef(nbp1.pointer(), nbp2.pointer());

    // look at the side lengths of the bounding box around the centers of the
    // triangle boxes and pick the longest of these as a split direction
    TriTree::DopType cdop;
    cdop.setCoef(cbp1.pointer(), cbp2.pointer());
    iax = cdop.longestAxis();

    // leaf nodes must be processed to generate the bounding box,
    // but they do not need to be sorted
    return ( uint(std::distance(nbegin, nend)) > tree.minElemCount());
  }

  // compare elements by center coordinate
  bool cmpElementCenter(uint a, uint b) const {
    float ca(0.0f), cb(0.0f);
    const uint *v = tree.vertices(a);
    for (int k=0; k<3; ++k)
      ca += tree.vertex(v[k])[iax];
    v = tree.vertices(b);
    for (int k=0; k<3; ++k)
      cb += tree.vertex(v[k])[iax];
    return ca < cb;
  }

  // compare elements by center coordinate
  bool cmpBBoxCenter(uint a, uint b) const {
    float amin, amax, bmin, bmax;
    amin = bmin =   std::numeric_limits<float>::max();
    amax = bmax = - std::numeric_limits<float>::max();
    const uint *v = tree.vertices(a);
    for (int k=0; k<3; ++k) {
      float x = tree.vertex(v[k])[iax];
      amin = std::min(amin, x);
      amax = std::max(amax, x);
    }
    v = tree.vertices(b);
    for (int k=0; k<3; ++k) {
      float x = tree.vertex(v[k])[iax];
      bmin = std::min(bmin, x);
      bmax = std::max(bmax, x);
    }
    return (amin+amax) < (bmin+bmax);
  }

private:

  /// reference to point tree
  TriTree & tree;

  /// separating axis
  int iax;
};

} // anonymous namespace

// ------------------- TriTree ------------------------------------------

TriTree::TriTree(const PointList<3,float> &vtx,
                 const Indices &tri) : m_vtx(vtx), m_tri(tri), m_mincount(16)
{
  sort();
}

TriTree::TriTree(const CgMesh & cgm) : m_mincount(16)
{
  m_vtx = cgm.vertices();
  m_tri.clear();
  cgm.toTriangles(m_tri);
  sort();
}

void TriTree::init(PointList<3, float> &vtx, Indices &tri)
{
  m_vtx.swap(vtx);
  m_tri.swap(tri);
  sort();
}

void TriTree::merge(const CgMesh &cgm)
{
  const uint voff = m_vtx.size();
  const PointList<3,float> & cgv( cgm.vertices() );
  m_vtx.insert(m_vtx.end(), cgv.begin(), cgv.end());

  Indices tmp;
  cgm.toTriangles(tmp);
  const int n = tmp.size();
  const uint toff = m_tri.size();
  m_tri.resize( toff + n );
  for (int i=0; i<n; ++i)
    m_tri[toff+i] = tmp[i] + voff;

  sort();
}

void TriTree::merge(const CgMesh &cgm, const Mtx44f & tfm)
{
  const uint voff = m_vtx.size();
  const PointList<3,float> & cgv( cgm.vertices() );
  if (cgv.empty())
    return;

  Indices tmp;
  cgm.toTriangles(tmp);
  if (tmp.empty())
    return;

  m_vtx.insert(m_vtx.end(), cgv.begin(), cgv.end());
  const int nv = m_vtx.size();
  for (int i=voff; i<nv; ++i) {
    Vct3f p( m_vtx[i] );
    for (int k=0; k<3; ++k)
      m_vtx[i][k] = tfm(k,0)*p[0] + tfm(k,1)*p[1] + tfm(k,2)*p[2] + tfm(k,3);
  }

  const int n = tmp.size();
  const uint toff = m_tri.size();
  m_tri.resize( toff + n );
  for (int i=0; i<n; ++i)
    m_tri[toff+i] = tmp[i] + voff;

  sort();
}

void TriTree::sort()
{
  // allocate space
  const int ntri = m_tri.size() / 3;
  m_itree.init( ntri, m_mincount );
  const int nnd = m_itree.nnodes();
  m_dop.resize(nnd);

  // sort and create bounding volumes
  TriTreeDivider axd(*this);
  m_itree.sort(axd);
}

void TriTree::clear()
{
  m_vtx.clear();
  m_tri.clear();
  m_itree = ImplicitTree();
  m_dop.clear();
}

// -------------- triangle - triangle -------------------------------------

void TriTree::intersect(const TriTree &other, IndexPairArray &pairs,
                        bool parallel) const
{
  if (parallel)
    detail::parallel_traverse(*this, other, pairs);
  else
    detail::serial_traverse(*this, other, pairs);
}

void TriTree::testLeaves(const TriTree & a, uint anode,
                         const TriTree & b, uint bnode,
                         IndexPairArray & isec)
{
  uint aBegin, aEnd, bBegin, bEnd;
  a.offsetRange(anode, aBegin, aEnd);
  b.offsetRange(bnode, bBegin, bEnd);

  for (uint ati=aBegin; ati != aEnd; ++ati) {
    Vct3 ap[3];
    uint ida = a.elementIndex(ati);
    const uint *va = a.vertices( ida );
    for (int k=0; k<3; ++k)
      ap[k] = Vct3( a.vertex(va[k]) );
    for (uint bti=bBegin; bti != bEnd; ++bti) {
      Vct3 bp[3];
      uint idb = b.elementIndex(bti);
      const uint *vb = b.vertices( idb );
      for (int k=0; k<3; ++k)
        bp[k] = Vct3( b.vertex(vb[k]) );
      if (moeller_intersect(ap, bp))
        isec.push_back( make_pair(ida,idb) );
    }

  }
}

bool TriTree::segment(const TriTree & other, const IndexPair & p,
                      Vct3f & src, Vct3f & trg) const
{
  Vct3 ap[3], bp[3];
  const uint *va = vertices( p.first );
  for (int k=0; k<3; ++k)
    ap[k] = Vct3( vertex(va[k]) );

  const uint *vb = other.vertices( p.second );
  for (int k=0; k<3; ++k)
    bp[k] = Vct3( other.vertex(vb[k]) );

  Vct3 s, t;
  int r(0), coplanar(0);
  r = tri_tri_intersect_with_isectline(ap[0].pointer(), ap[1].pointer(), ap[2].pointer(),
                                       bp[0].pointer(), bp[1].pointer(), bp[2].pointer(),
                                       &coplanar, s.pointer(), t.pointer());

  src = Vct3f(s);
  trg = Vct3f(t);

  return (r != 0 and coplanar != 1);
}

bool TriTree::segments(const TriTree & other, const IndexPairArray & p,
                       PointList<3,float> & segs) const
{
  Vct3f src, trg;
  const int np = p.size();
  segs.reserve(2*np);
  for (int i=0; i<np; ++i) {
    if (segment(other, p[i], src, trg)) {
      segs.push_back(src);
      segs.push_back(trg);
    }
  }

  return (not segs.empty());
}


