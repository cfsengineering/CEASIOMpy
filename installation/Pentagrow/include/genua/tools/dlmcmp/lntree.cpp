#include "lntree.h"
#include <deque>

using namespace std;

// ------------------- local scope --------------------------------------

namespace {

class LnTreeDivider
{
public:

  LnTreeDivider(LnTree & t) : tree(t), iax(0) {}

  // node division criterion
  template <class Iterator>
  bool divide(uint inode, Iterator nbegin, Iterator nend) {
    if (nend <= nbegin)
      return false;

    // low/high BV limits
    Vct3f p1, p2;
    p1 =   std::numeric_limits<float>::max();
    p2 = - std::numeric_limits<float>::max();

    // fit bounding volume to line vertices
    Vct3f lp1, lp2;
    for (Iterator itr = nbegin; itr != nend; ++itr) {
      tree.vertices(*itr, lp1, lp2);
      // lc = 0.5f*(lp1 + lp2);
      LnTree::DopType::fit(lp1.pointer(), p1.pointer(), p2.pointer());
      LnTree::DopType::fit(lp2.pointer(), p1.pointer(), p2.pointer());
    }

    LnTree::DopType & dop( tree.dop(inode) );
    dop.setCoef(p1.pointer(), p2.pointer());
    // iax = dop.longestAxis();

    float dx = fabsf(dop.maxCoef(0) - dop.minCoef(0));
    float dy = fabsf(dop.maxCoef(1) - dop.minCoef(1));
    if ( dx > dy )
      iax = 0;
    else
      iax = 1;

    // leaf nodes must be processed to generate the bounding box,
    // but they do not need to be sorted
    return ( uint(std::distance(nbegin, nend)) > tree.minElemCount());
  }

  // sorting criterion : compare lines by center
  bool operator() (uint a, uint b) const {
    return cmpElementCenter(a,b);
  }

private:

  // compare elements by center coordinate
  bool cmpElementCenter(uint a, uint b) const {
    Vct3f p1a, p2a, p1b, p2b;
    tree.vertices(a, p1a, p2a);
    tree.vertices(b, p1b, p2b);
    float ca = p1a[iax] + p2a[iax];
    float cb = p1b[iax] + p2b[iax];
    return ca < cb;
  }

private:

  /// reference to point tree
  LnTree & tree;

  /// separating axis
  int iax;
};

}
// ------------------- LnTree ------------------------------------------

LnTree::LnTree(const PointList<3,float> &vtx, bool lazy)
  : m_vtx(vtx), m_mincount(16)
{
  if (lazy)
    sortNode(0);
  else
    sort();
}

void LnTree::init(PointList<3, float> &vtx, bool lazy)
{
  m_vtx.swap(vtx);
  if (lazy)
    sortNode(0);
  else
    sort();
}

void LnTree::sortNode(uint k)
{
  if (k == 0) {
    m_itree.init( nlines(), m_mincount );
    m_dop.resize( m_itree.nnodes() );
  }

  LnTreeDivider axd(*this);
  m_itree.sortNode(axd, k);
}

void LnTree::sort()
{
  assert(m_vtx.size() % 2 == 0);

  // allocate space
  m_itree.init( nlines(), m_mincount );
  m_dop.resize( m_itree.nnodes() );

  // sort and create bounding volumes
  LnTreeDivider axd(*this);
  m_itree.sort(axd);
}


