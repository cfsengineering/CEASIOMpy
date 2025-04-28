
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
 
#include "mxelementtree.h"
#include "primitives.h"
#include "csrmatrix.h"
#include "timing.h"
#include <set>

using namespace std;

// ----------------- MxElementTree ------------------------------------------

namespace {

class AxialDivider
{
public:

  AxialDivider(MxElementTree & t) : tree(t), iax(0) {}

  // node division criterion
  template <class Iterator>
  bool divide(uint inode, Iterator nbegin, Iterator nend) {
    if (nend <= nbegin)
      return false;

    // TODO
    // Check whether it is more efficient to *not* collect vertices first,
    // but to fit the DOP directly while processing the list of elements
    // once -> duplicate computations but much less memory traffic

    // low/high BV limits
    Vct3 p1, p2;
    p1 =   std::numeric_limits<Real>::max();
    p2 = - std::numeric_limits<Real>::max();

    for (Iterator itr = nbegin; itr != nend; ++itr) {
      uint nv, isec;
      const uint *vi = tree.mappedElement(*itr, nv, isec);
      for (uint j=0; j<nv; ++j) {
        const Vct3 & q( tree.point(vi[j]) );
        MxElementTree::DopType::fit(q.pointer(), p1.pointer(), p2.pointer());
      }
    }

    /*

    // first, collect all element vertex indices
    assert(tree.mesh());
    uint isec, nv;
    std::set<uint> vix;
    for (Iterator itr = nbegin; itr != nend; ++itr) {
      const uint *vi = tree.mappedElement(*itr, nv, isec);
      assert(nv > 0);
      vix.insert(vi, vi+nv);
    }

    // low/high BV limits
    Vct3 p1, p2;
    p1 =   std::numeric_limits<Real>::max();
    p2 = - std::numeric_limits<Real>::max();

    // now, process all element vertices
    std::set<uint>::const_iterator itv, vlast = vix.end();
    for (itv = vix.begin(); itv != vlast; ++itv) {
      const Vct3 & q( tree.point(*itv) );
      MxElementTree::DopType::fit(q.pointer(), p1.pointer(), p2.pointer());
    }

    */

    MxElementTree::DopType & dop( tree.dop(inode) );
    dop.setCoef(p1.pointer(), p2.pointer());
    iax = dop.longestAxis();

    // leaf nodes must be processed to generate the bounding box,
    // but they do not need to be sorted
    return ( uint(std::distance(nbegin, nend)) > tree.minElemCount());
  }

  // sorting criterion : compare elements by center coordinate
  bool operator() (uint a, uint b) const {
    Real ca(0), cb(0);
    const uint *vi;
    uint nva, nvb, isec;
    vi = tree.mappedElement(a, nva, isec);
    for (uint i=0; i<nva; ++i)
      ca += tree.point( vi[i] )[iax];
    vi = tree.mappedElement(b, nvb, isec);
    for (uint i=0; i<nvb; ++i)
      cb += tree.point( vi[i] )[iax];
    return (nvb*ca) < (nva*cb);
  }

private:

  /// reference to point tree
  MxElementTree & tree;

  /// separating axis
  int iax;
};

}

//static inline Real lparm(const Vct3 & pt, const Vct3 & p1, const Vct3 & p2)
//{
//  Vct3 lnv(p2 - p1), dst(pt - p1);
//  return clamp(dot(lnv,dst)/sq(lnv), 0.0, 1.0);
//}

void MxElementTree::allocate(MxMeshPtr pm, uint mincount)
{
  pmx = pm;
  itree.init(pmx->nelements(), mincount);
  bvol.resize(itree.nnodes());

  // elix ends up as a 1:1 mapping
  const int n = pmx->nelements();
  elix.resize(n);
  for (int i=0; i<n; ++i)
    elix[i] = i;
}

void MxElementTree::allocateSections(MxMeshPtr pm, const Indices & sects,
                                     uint mincount)
{
  pmx = pm;

  // collect element indices to use
  uint nelm = 0;
  const int nsec = sects.size();
  for (int i=0; i<nsec; ++i)
    nelm += pmx->section(sects[i]).nelements();

  int elo = 0;
  elix.resize(nelm);
  for (int i=0; i<nsec; ++i) {
    const MxMeshSection & sec( pmx->section(sects[i]) );
    const uint offset = sec.indexOffset();
    const int ne = sec.nelements();
    for (int j=0; j<ne; ++j)
      elix[elo+j] = offset + j;
    elo += ne;
  }

  itree.init(elix.size(), mincount);
  bvol.resize(itree.nnodes());
}

void MxElementTree::sort()
{
  AxialDivider cmp(*this);
  itree.sort(cmp);
}

uint MxElementTree::nearest(const Vct3 &p) const
{
  uint inear = elix[0];
  uint inode = 0;
  uint nnodes = bvol.size();

  Real ldst, rdst, best;
  best = elementDistance(p, 0);

  typedef std::pair<uint,Real> NodeDst;
  std::vector<NodeDst> opt;

  while (inode != NotFound) {

    uint left = itree.leftChild(inode);
    uint right = itree.rightChild(inode);

    if (left >= nnodes) {

      // inode is a leaf node, process contained elements
      uint ibegin, iend;
      itree.offsetRange(inode, ibegin, iend);
      for (uint i=ibegin; i<iend; ++i) {
        uint idx = itree.index(i);
        Real dst = elementDistance(p, idx);
        if (dst < best) {
          best = dst;
          inear = elix[idx];
        }
      }

      // early exit : will never get better than zero...
      if (best == 0)
        return inear;

      inode = NotFound;

    } else {

      ldst = rdst = std::numeric_limits<Real>::max();
      if (left < nnodes)
        ldst = bvol[left].pointDistance(p.pointer());
      if (right < nnodes)
        rdst = bvol[right].pointDistance(p.pointer());
      assert(std::isfinite(ldst) or std::isfinite(rdst));

      inode = NotFound;

      // If p is in left child box (ldst == 0) or at least closer to
      // the box than the smallest point distance computed yet, continue
      // loop with left child. However, if ldst *could* possibly contain
      // a closer match but rdst is smaller, continue with right child but
      // put ldst on the stack.

      if (ldst < best) {
        if (ldst <= rdst)
          inode = left;
        else
          opt.push_back( std::make_pair(left, ldst) );
      }

      if (rdst < best) {
        if (rdst < ldst)
          inode = right;
        else
          opt.push_back( std::make_pair(right, rdst) );
      }

    }

    // pick next candidate c off the stack : discard directly if distance of
    // p from box c is larger than the current best hit, proceed otherwise
    while (inode == NotFound) {
      if (opt.empty())
        break;
      NodeDst c = opt.back();
      opt.pop_back();
      if (c.second < best) {
        inode = c.first;
        break;
      }
    }
  }

  return inear;
}

bool MxElementTree::find(const Vct3 &p, Real radius, Indices &eix) const
{
  uint inode = 0;
  uint nnodes = bvol.size();

  Real ldst, rdst, rsq = sq(radius);
  std::vector<uint> opt;

  eix.clear();
  while (inode != NotFound) {

    uint left = itree.leftChild(inode);
    uint right = itree.rightChild(inode);

    if (left >= nnodes) {

      // inode is a leaf node, process contained elements
      uint ibegin, iend;
      itree.offsetRange(inode, ibegin, iend);
      for (uint i=ibegin; i<iend; ++i) {
        uint idx = itree.index(i);
        Real dst = elementDistance(p, idx);
        if (dst < rsq)
          eix.push_back( elix[idx] );
      }

      inode = NotFound;

    } else {

      ldst = rdst = std::numeric_limits<Real>::max();
      if (left < nnodes)
        ldst = bvol[left].pointDistance(p.pointer());
      if (right < nnodes)
        rdst = bvol[right].pointDistance(p.pointer());

      inode = NotFound;

      if (ldst < rsq)
        inode = left;

      if (rdst < rsq) {
        if (inode == NotFound)
          inode = right;
        else
          opt.push_back(right);
      }
    }

    // pick next candidate c off the stack
    while (inode == NotFound and (not opt.empty())) {
      inode = opt.back();
      opt.pop_back();
    }
  }

  return (not eix.empty());
}

Real MxElementTree::elementDistance(const Vct3 &p, uint k) const
{
  uint nv, isec;
  const uint *vi = mappedElement(k, nv, isec);
  Mx::ElementType et = pmx->section(isec).elementType();

  // decomposition pattern of non-simplex elements
  const uint vqd4[6] = {0,1,2, 0,2,3};
  const uint vqd8[12] = {0,4,7, 5,4,1, 7,6,3, 6,5,2};
  const uint vtr6[12] = {0,3,5, 5,3,4, 4,3,1, 4,2,5};

  switch (et) {
  case Mx::Point:
    return sq(p - pmx->node(vi[0]));
  case Mx::Tri3:
    return edTri3(p, vi);
  case Mx::Tri6:
    return edMultiTri3<4>(p, vtr6, vi);
  case Mx::Quad4:
    return edMultiTri3<2>(p, vqd4, vi);
  case Mx::Quad8:
    return edMultiTri3<4>(p, vqd8, vi);
  default:
    return std::numeric_limits<Real>::max();
  }
}

Real MxElementTree::edTri3(const Vct3 &p, const uint *vi) const
{
  Vct3 tri[3];
  for (int k=0; k<3; ++k)
    tri[k] = pmx->node( vi[k] );

  return adp_sqdistance(tri, p);
}

// ---------- MxTriTree ------------------------------------------------------

namespace {

class MxTriTreeDivider
{
public:

  MxTriTreeDivider(MxTriTree & t) : tree(t), iax(0) {}

  // node division criterion
  template <class Iterator>
  bool divide(uint inode, Iterator nbegin, Iterator nend) {
    if (nend <= nbegin)
      return false;

    // low/high BV limits
    Vct3f p1, p2;
    p1 =   std::numeric_limits<float>::max();
    p2 = - std::numeric_limits<float>::max();

    // although this loop does, on average, six times as much arithmetic
    // as strictly necessary when only processing the set of unique nodes,
    // it is still vastly faster than the index extraction and sorting
    // needed to avoid the additional computation
    for (Iterator itr = nbegin; itr != nend; ++itr) {
      const uint *vi = tree.vertices(*itr);
      for (int k=0; k<3; ++k)
        MxTriTree::DopType::fit(tree.vertex(vi[k]).pointer(),
                                p1.pointer(), p2.pointer());
    }

    MxTriTree::DopType & dop( tree.dop(inode) );
    dop.setCoef(p1.pointer(), p2.pointer());
    iax = dop.longestAxis();

    // leaf nodes must be processed to generate the bounding box,
    // but they do not need to be sorted
    return ( uint(std::distance(nbegin, nend)) > tree.minElemCount());
  }

  // compare elements by center coordinate
  bool operator() (uint a, uint b) const {
    float ca(0.0f), cb(0.0f);
    const uint *v = tree.vertices(a);
    for (int k=0; k<3; ++k)
      ca += tree.vertex(v[k])[iax];
    v = tree.vertices(b);
    for (int k=0; k<3; ++k)
      cb += tree.vertex(v[k])[iax];
    return ca < cb;
  }

private:

  /// reference to point tree
  MxTriTree & tree;

  /// separating axis
  int iax;
};

}

void MxTriTree::build(const MxMesh &msh)
{
  Indices sfsec;
  for (uint i=0; i<msh.nsections(); ++i) {
    if (msh.section(i).surfaceElements())
      sfsec.push_back(i);
  }

  if (not sfsec.empty())
    build(msh, sfsec);
}

void MxTriTree::build(const MxMesh &msh, const Indices &sections)
{
  if (sections.empty()) {
    build(msh);
    return;
  }

  clear();
  const int nsec = sections.size();
  if (nsec == 0)
    return;

  // first pass : collect all vertex indices referenced
  {
    uint nv = 0;
    for (int i=0; i<nsec; ++i) {
      const MxMeshSection & sec( msh.section(sections[i]) );
      nv += sec.nelements() * sec.nElementNodes();
    }

    Indices tmp;
    tmp.reserve(nv);
    for (int i=0; i<nsec; ++i) {
      const MxMeshSection & sec( msh.section(sections[i]) );
      const int nsv = sec.nelements() * sec.nElementNodes();
      const uint *v = sec.element(0);
      tmp.insert(tmp.end(), v, v+nsv);
    }
    std::sort(tmp.begin(), tmp.end());
    tmp.erase( std::unique(tmp.begin(), tmp.end()), tmp.end() );
    m_gnix.swap(tmp);
  }

  // second pass : extract vertices
  const int nv = m_gnix.size();
  m_vtx.resize(nv);
  for (int i=0; i<nv; ++i)
    m_vtx[i] = msh.node( m_gnix[i] );

  // third pass : split elements into triangles
  for (int i=0; i<nsec; ++i)
    splitElements(msh, sections[i]);

  sort();
}

void MxTriTree::build(const MxMesh &msh, const SubsetArray &sba)
{
  clear();
  const int nsec = sba.size();
  if (nsec == 0)
    return;

  // first pass : collect all vertex indices referenced
  {
    uint nv = 0;
    for (int i=0; i<nsec; ++i) {
      const MxMeshSection & sec( msh.section(sba[i].isection) );
      nv += sba[i].elementList.size() * sec.nElementNodes();
    }

    Indices tmp;
    tmp.reserve(nv);
    for (int i=0; i<nsec; ++i) {
      const MxMeshSection & sec( msh.section(sba[i].isection) );
      const int nsel = sba[i].elementList.size();
      const int npe = sec.nElementNodes();
      for (int j=0; j<nsel; ++j) {
        const uint *v = sec.element(sba[i].elementList[j]);
        tmp.insert(tmp.end(), v, v+npe);
      }
    }
    std::sort(tmp.begin(), tmp.end());
    tmp.erase( std::unique(tmp.begin(), tmp.end()), tmp.end() );
    m_gnix.swap(tmp);
  }

  // second pass : extract vertices
  const int ngv = m_gnix.size();
  m_vtx.resize(ngv);
  for (int i=0; i<ngv; ++i)
    m_vtx[i] = msh.node( m_gnix[i] );

  // third pass : split elements into triangles
  for (int i=0; i<nsec; ++i)
    splitElements(msh, sba[i].isection, sba[i].elementList);

  sort();
}

void MxTriTree::build(const PointList<3, float> &pts, const Indices &tri)
{
  // find set of vertices used by triangles
  m_gnix = tri;
  sort_unique(m_gnix);

  const int nv = m_gnix.size();
  m_vtx.resize(nv);
  for (int i=0; i<nv; ++i)
    m_vtx[i] = pts[m_gnix[i]];

  const int ntri = tri.size() / 3;
  m_gelix.resize(ntri);
  m_tri.resize( tri.size() );
  for (int i=0; i<ntri; ++i) {
    m_gelix[i] = i;
    for (int k=0; k<3; ++k)
      m_tri[3*i+k] = sorted_index( m_gnix, tri[3*i+k] );
  }

  sort();
}

void MxTriTree::build(const PointList<3, double> &pts, const Indices &tri)
{
  // find set of vertices used by triangles
  m_gnix = tri;
  sort_unique(m_gnix);

  const int nv = m_gnix.size();
  m_vtx.resize(nv);
  for (int i=0; i<nv; ++i)
    m_vtx[i] = Vct3f( pts[m_gnix[i]] );

  const int ntri = tri.size() / 3;
  m_gelix.resize(ntri);
  m_tri.resize( tri.size() );
  for (int i=0; i<ntri; ++i) {
    m_gelix[i] = i;
    for (int k=0; k<3; ++k)
      m_tri[3*i+k] = sorted_index( m_gnix, tri[3*i+k] );
  }

  sort();
}

void MxTriTree::splitElements(const MxMesh &msh, uint isec, const Indices &elix)
{
  // mapping between element nodes and triangle vertices
  const int map_tri3[] = { 0,1,2 };
  const int map_tri6[] = { 0,3,5, 5,3,4, 4,3,1, 4,2,5 };
  const int map_quad4[] = { 0,1,2, 2,3,0 };
  const int map_quad8[] = { 0,4,7, 4,5,7, 1,5,4,
                            2,6,5, 5,6,7, 3,7,6 };
  const int map_tet4[] =  { 0,1,2, 1,3,2, 0,2,3, 0,3,1 };
  const int map_hexa8[] = { 0,1,2, 0,2,3,
                            2,6,7, 3,2,7,
                            2,5,6, 1,2,5,
                            4,7,6, 4,6,5,
                            0,4,1, 1,4,5,
                            0,3,7, 0,7,4 };

  const MxMeshSection & sec( msh.section(isec) );
  const int nsel = sec.nelements();
  const int npe = sec.nElementNodes();
  const int *map(0);
  int ntri(0);
  switch (sec.elementType()) {
  case Mx::Tri3:
    map = map_tri3;
    ntri = 1;
    break;
  case Mx::Tri6:
    map = map_tri6;
    ntri = 4;
    break;
  case Mx::Quad4:
    map = map_quad4;
    ntri = 2;
    break;
  case Mx::Quad8:
    map = map_quad8;
    ntri = 6;
    break;
  case Mx::Tet4:
    map = map_tet4;
    ntri = 4;
    break;
  case Mx::Hex8:
    map = map_hexa8;
    ntri = 12;
    break;
  default:
    return;
  }

  // construct default element list (all) if list empty
  Indices elx(elix);
  if (elx.empty()) {
    elx.resize(nsel);
    for (int i=0; i<nsel; ++i)
      elx[i] = i;
  }
  const int nel = elx.size();

  Indices stri(ntri*nel*3), sgel(ntri*nel);
  uint gvi[8], offset(0);
  for (int j=0; j<nel; ++j) {
    const uint *v = sec.element(elx[j]);
    for (int k=0; k<npe; ++k) {
      gvi[k] = sorted_index(m_gnix, v[k]);
      assert(gvi[k] != NotFound);
    }
    for (int k=0; k<ntri; ++k) {
      stri[offset+0] = gvi[map[3*k+0]];
      stri[offset+1] = gvi[map[3*k+1]];
      stri[offset+2] = gvi[map[3*k+2]];
      sgel[j*ntri+k] = sec.indexOffset() + elx[j];
      offset += 3;
    }
  }
  m_tri.insert(m_tri.end(), stri.begin(), stri.end());
  m_gelix.insert(m_gelix.end(), sgel.begin(), sgel.end());
}

float MxTriTree::tridist(uint itri, const Vct3f &pf) const
{
  Vct3f tri[3];
  const uint *v = vertices(itri);
  for (int k=0; k<3; ++k)
    tri[k] = m_vtx[v[k]];
  return qr_sqdistance(tri, pf);
}

uint MxTriTree::nearestTriangle(const Vct3f &pf) const
{
  uint inear = 0;
  uint inode = 0;
  uint nnodes = m_dop.size();

  float ldst, rdst, best;
  best = tridist(0, pf);

  typedef std::pair<uint,Real> NodeDst;
  std::vector<NodeDst> opt;

  while (inode != NotFound) {

    uint left = leftChild(inode);
    uint right = rightChild(inode);

    if (left >= nnodes) {

      // inode is a leaf node, process contained elements
      uint ibegin, iend;
      offsetRange(inode, ibegin, iend);
      for (uint i=ibegin; i<iend; ++i) {
        uint idx = triangleIndex(i);
        float dst = tridist(idx, pf);
        if (dst < best) {
          best = dst;
          inear = idx;
        }
      }

      // early exit : will never get better than zero...
      if (best == 0)
        return inear;

      inode = NotFound;

    } else {

      ldst = rdst = std::numeric_limits<float>::max();
      if (left < nnodes)
        ldst = dop(left).pointDistance(pf.pointer());
      if (right < nnodes)
        rdst = dop(right).pointDistance(pf.pointer());
      assert(std::isfinite(ldst) or std::isfinite(rdst));

      inode = NotFound;

      // If p is in left child box (ldst == 0) or at least closer to
      // the box than the smallest point distance computed yet, continue
      // loop with left child. However, if ldst *could* possibly contain
      // a closer match but rdst is smaller, continue with right child but
      // put ldst on the stack.

      if (ldst < best) {
        if (ldst <= rdst)
          inode = left;
        else
          opt.push_back( std::make_pair(left, ldst) );
      }

      if (rdst < best) {
        if (rdst < ldst)
          inode = right;
        else
          opt.push_back( std::make_pair(right, rdst) );
      }
    }

    // pick next candidate c off the stack : discard directly if distance of
    // p from box c is larger than the current best hit, proceed otherwise
    while (inode == NotFound) {
      if (opt.empty())
        break;
      NodeDst c = opt.back();
      opt.pop_back();
      if (c.second < best) {
        inode = c.first;
        break;
      }
    }
  }

  return inear;
}

bool MxTriTree::projection(const Vct3 &p, uint nodes[], float coef[]) const
{
  uint itri = nearestTriangle(p);
  const uint *vi = vertices(itri);
  for (uint k=0; k<3; ++k)
    nodes[k] = m_gnix[vi[k]];

  Vct3f tri[3], pf(p);
  for (int k=0; k<3; ++k)
    tri[k] = m_vtx[vi[k]];

  Vct2f uv;
  bool inside = qr_project_point(tri, pf, uv);

  if (inside) {

    coef[0] = 1.0f - uv[0] - uv[1];
    coef[1] = uv[0];
    coef[2] = uv[1];

  } else {

    float lp, dl, dmin = std::numeric_limits<float>::max();

    // project on line tri[0] - tri[2]
    if (uv[0] <= 0) {
      lp = detail::lparm(pf, tri[0], tri[2]);
      dl = sq(pf - (1-lp)*tri[0] - lp*tri[2]);
      if (dl < dmin) {
        dmin = dl;
        coef[0] = 1-lp;
        coef[1] = 0.0f;
        coef[2] = lp;
      }
    }

    // project on line tri[0] - tri[1]
    if (uv[1] <= 0) {
      lp = detail::lparm(pf, tri[0], tri[1]);
      dl = sq(pf - (1-lp)*tri[0] - lp*tri[1]);
      if (dl < dmin) {
        dmin = dl;
        coef[0] = 1-lp;
        coef[1] = lp;
        coef[2] = 0.0f;
      }
    }

    // project on line tri[1] - tri[2]
    if (1-uv[0]-uv[1] <= 0) {
      lp = detail::lparm(pf, tri[1], tri[2]);
      dl = sq(pf - (1-lp)*tri[1] - lp*tri[2]);
      if (dl < dmin) {
        dmin = dl;
        coef[0] = 0.0f;
        coef[1] = 1-lp;
        coef[2] = lp;
      }
    }

  }

  return inside;
}

void MxTriTree::projection(const PointList<3> &vtx, const Indices &imap,
                           CsrMatrix<float,1> &op, uint ncol) const
{
  const int nr = imap.size();
  DVector<float> val(3*nr);
  Indices inds(3*nr);

#pragma omp parallel for schedule(static,128)
  for (int i=0; i<nr; ++i) {
    uint nds[3];
    float cf[3];
    projection( vtx[imap[i]], nds, cf );

    // sorting required for sorted spty
    if ( nds[0] > nds[2] ) {
      std::swap( nds[0], nds[2] );
      std::swap( cf[0], cf[2] );
    }
    if ( nds[0] > nds[1] ) {
      std::swap( nds[0], nds[1] );
      std::swap( cf[0], cf[1] );
    }
    if ( nds[1] > nds[2] ) {
      std::swap( nds[1], nds[2] );
      std::swap( cf[1], cf[2] );
    }

    // disjoint access
    for (int k=0; k<3; ++k) {
      inds[3*i+k] = nds[k];
      val[3*i+k] = cf[k];
    }
  }

  ConnectMap spty;
  for (int i=0; i<nr; ++i) {
    const uint *itr = &inds[3*i];
    spty.appendRow(itr, itr+3);
  }

  op = CsrMatrix<float,1>( spty, val, ncol );
}

void MxTriTree::sort()
{
  // allocate space
  const int ntri = m_tri.size() / 3;
  m_itree.init( ntri, m_mincount );
  const int nnd = m_itree.nnodes();
  m_dop.resize(nnd);

  // cout << ntri << " triangles, " << nnd << " tree nodes." << endl;

  // sort and create bounding volumes
  MxTriTreeDivider axd(*this);
  m_itree.sort(axd);
}

void MxTriTree::clear()
{
  m_vtx.clear();
  m_tri.clear();
  m_gnix.clear();
  m_gelix.clear();
  m_itree = ImplicitTree();
  m_dop.clear();
}

void MxTriTree::dump(const string &fname) const
{
  MxMesh mx;
  PointList<3> pts(m_vtx);
  mx.appendNodes(pts.begin(), pts.end());
  mx.appendSection(Mx::Tri3, m_tri);
  mx.toXml(true).zwrite(fname);
}
