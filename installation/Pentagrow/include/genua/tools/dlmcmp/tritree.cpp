#include "tritree.h"
#include "lntree.h"
#include "treetraverse.h"
#include "moeller.h"
#include <genua/cgmesh.h>
#include <genua/smallqr.h>
#include <genua/primitives.h>
#include <set>
#include <iostream>

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
    //return divideLongest(inode, nbegin, nend);
    return divideBBoxCenter(inode, nbegin, nend);
  }

  // sorting criterion : compare elements bounding box center
  bool operator() (uint a, uint b) const {
    //return cmpElementCenter(a,b);
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

      // for each triangle, extend node box bounds to fit all vertices
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
                 const Indices &tri, uint leafCount, bool lazySort)
  : m_vtx(vtx), m_tri(tri), m_mincount(leafCount)
{
  if (lazySort)
    sortNode(0);
  else
    sort();
}

TriTree::TriTree(const CgMesh & cgm, uint leafCount, bool lazySort)
  : m_mincount(leafCount)
{
  init(cgm, lazySort);
}

void TriTree::init(const CgMesh & cgm, bool lazySort)
{
  m_vtx = cgm.vertices();
  m_tri.clear();
  cgm.toTriangles(m_tri);
  if (lazySort)
    sortNode(0);
  else
    sort();
}

void TriTree::init(PointList<3, float> &vtx, Indices &tri, bool lazySort)
{
  m_vtx.swap(vtx);
  m_tri.swap(tri);
  if (lazySort)
    sortNode(0);
  else
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

void TriTree::sortNode(uint k)
{
  // precondition is that parent node is sorted
  assert((k == 0) or isSorted(k/2));

  if (k == 0) {
    const int ntri = m_tri.size() / 3;
    m_itree.init( ntri, m_mincount );
    m_dop.resize( m_itree.nnodes() );
  }

  // sort and create bounding volumes
  TriTreeDivider axd(*this);
  m_itree.sortNode(axd, k);
}

void TriTree::clear()
{
  m_vtx.clear();
  m_tri.clear();
  m_itree = LazyTree();
  m_dop.clear();
}

// -------------- triangle - triangle -------------------------------------

void TriTree::intersect(TriTree &other, IndexPairArray &pairs,
                        bool parallel)
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

// ------------------ triangle - line -------------------------------------

// compute intersection point, does not check if intersection is inside
static inline float intersectTriangleLine(const Vct3f tri[], const Vct3f ln[],
                                          Vct3f & is)
{
  Mtx33f A;
  Vct3f b(tri[0] - ln[0]);
  for (int i=0; i<3; ++i) {
    A(i, 0) = ln[1][i] - ln[0][i];
    A(i, 1) = tri[0][i] - tri[1][i];
    A(i, 2) = tri[0][i] - tri[2][i];
  }

  qrlls<3,3>(A.pointer(), b.pointer());
  is = ln[0] + b[0]*(ln[1] - ln[0]);
  return b[0];
}

void TriTree::intersect(LnTree &other, IndexPairArray &pairs,
                        bool parallel)
{
  if (parallel)
    detail::parallel_traverse(*this, other, pairs);
  else
    detail::serial_traverse(*this, other, pairs);
}

void TriTree::testLeaves(const TriTree & a, uint anode,
                         const LnTree & b, uint bnode,
                         IndexPairArray & isec)
{
  uint aBegin(a.begin(anode)), aEnd(a.end(anode));
  uint bBegin(b.begin(bnode)), bEnd(b.end(bnode));

  for (uint ati=aBegin; ati != aEnd; ++ati) {

    // extract triangle from a
    uint ida = a.elementIndex(ati);
    const uint *va = a.vertices( ida );
    const Vct3f & tp0( a.vertex(va[0]) );
    const Vct3f & tp1( a.vertex(va[1]) );
    const Vct3f & tp2( a.vertex(va[2]) );

    // check against lines
    for (uint bti=bBegin; bti != bEnd; ++bti) {
      uint idb = b.elementIndex(bti);
      Vct3f ldir = b.target(idb) - b.source(idb);
      if ( mt_line_triangle<false>(b.source(idb).pointer(), ldir.pointer(),
                                  tp0.pointer(), tp1.pointer(), tp2.pointer()) )
        isec.push_back( make_pair(ida,idb) );
    }
  }
}

float TriTree::intersection(const LnTree &other,
                            const IndexPair &p, Vct3f &isp) const
{
  Vct3f ap[3];
  const uint *va = this->vertices( p.first );
  for (int k=0; k<3; ++k)
    ap[k] = this->vertex(va[k]);

  Vct3f bp[2];
  other.vertices( p.second, bp[0], bp[1] );
  return intersectTriangleLine(ap, bp, isp);
}

// --------------------- point search ------------------------

bool TriTree::project(uint tix, const Vct3f &pt, Vct3f &pj) const
{
  if (3*tix >= m_tri.size())
    return false;

  const uint *vix = &m_tri[3*tix];
  const Vct3f & p1( m_vtx[vix[0]] );
  const Vct3f & p2( m_vtx[vix[1]] );
  const Vct3f & p3( m_vtx[vix[2]] );

  SMatrix<3,2,float> A;
  Vct3f r;
  for (int i=0; i<3; ++i) {
    A(i,0) = p2[i] - p1[i];
    A(i,1) = p3[i] - p1[i];
    r[i] = pt[i] - p1[i];
  }
  bool flag = qrlls<3,2>(A.pointer(), r.pointer());
  pj = (1.0f-r[0]-r[1])*p1 + r[0]*p2 + r[1]*p3;
  return flag;
}

float TriTree::elementDistance(const Vct3f &p, uint tix) const
{
  Vct3f pj;
  if (project(tix, p, pj))
    return norm(pj - p);
  else
    return std::numeric_limits<float>::max();
}

uint TriTree::nearest(const Vct3f &p) const
{
  if (ntriangles() == 0)
    return 0;

  uint inear = 0;
  uint inode = 0;
  uint nnodes = m_dop.size();

  float ldst, rdst, best;
  best = elementDistance(p, 0);

  typedef std::pair<uint,float> NodeDst;
  std::vector<NodeDst> opt;

  while (inode != NotFound) {

    uint left = m_itree.leftChild(inode);
    uint right = m_itree.rightChild(inode);

    if (left >= nnodes) {

      // inode is a leaf node, process contained elements
      uint ibegin, iend;
      m_itree.offsetRange(inode, ibegin, iend);
      for (uint i=ibegin; i<iend; ++i) {
        uint idx = m_itree.index(i);
        Real dst = elementDistance(p, idx);
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
        ldst = m_dop[left].pointDistance(p.pointer());
      if (right < nnodes)
        rdst = m_dop[right].pointDistance(p.pointer());
      assert(isfinite(ldst) or isfinite(rdst));

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



