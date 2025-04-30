
#include "unbalancedbvtree.h"

#include <genua/kdop.h>
#include <genua/point.h>
#include <genua/morton.h>
#include <genua/dvector.h>
#include <genua/svector.h>
#include <genua/timing.h>
#include <genua/parallel_algo.h>
#include <genua/mxelementtree.h>

#include <boost/chrono.hpp>

#include <iostream>

using namespace std;

typedef boost::chrono::duration<int64_t, boost::milli> milliseconds;
typedef boost::chrono::duration<int64_t, boost::micro> microseconds;

typedef boost::chrono::high_resolution_clock HRClock;
typedef HRClock::time_point HRTime;

static HRTime s_stamp;

void tick()
{
  s_stamp = HRClock::now();
}

void tock(const std::string &s)
{
  HRTime t = HRClock::now();
  microseconds ms = boost::chrono::duration_cast<microseconds>( t - s_stamp );
  cout << s << ms << endl;
}

/** Generate a triangle mesh covering a half-cylinder.
 * @param nr    Number of nodes in circumferential direction
 * @param nl    Number of nodes in axial direction
 * @param v     Node list
 * @param tri   Triangle vertex index list
 */
static void mesh_cylinder(int nr, int nl, PointList<3,float> &v, Indices &tri)
{
  const float R = 3.0f;
  const float L = 14.0f;
  Vct3f ax(0.0f, 0.0f, R);
  Vct3f ay(0.0f, R, 0.0f);
  Vct3f az(L, 0.0f, 0.0f);

  v.resize( nr*nl );
  float sphi, cphi;
  for (int i=0; i<nr; ++i) {
    sincosine( float(PI*i/(nr-1)), sphi, cphi );
    for (int j=0; j<nl; ++j) {
      v[i*nl+j] = az*(float(j)/(nl-1)) + sphi*ax + cphi*ay;
    }
  }

  const int ntri = (nr-1)*(nl-1)*2;
  tri.resize(3*ntri);
  int off = 0;
  for (int i=1; i<nr; ++i) {
    for (int j=1; j<nl; ++j) {
      uint p1 = (i-1)*nl + (j-1);
      uint p2 = (i-1)*nl + j;
      uint p3 = i*nl + j;
      uint p4 = i*nl + (j-1);

      tri[3*off+0] = p1;
      tri[3*off+1] = p3;
      tri[3*off+2] = p2;
      ++off;
      tri[3*off+0] = p1;
      tri[3*off+1] = p4;
      tri[3*off+2] = p3;
      ++off;
    }
  }
  assert(off == ntri);
}

template <class TreeType>
void visualize(const PointList<3,float> &pts, const Indices &tri,
               const TreeType &tree)
{
  MxMesh mx;
  mx.appendNodes( pts.begin(), pts.end() );
  mx.appendSection( Mx::Tri3, tri );

  // generate line elements between triangle centers
  const DVector<uint> & items( tree.sortedItems() );
  const int ne = items.size();
  cout << ne << " sorted triangles." << endl;
  uint voff = mx.nnodes();
  for (int i=0; i<ne; ++i) {
    const uint *vi = &tri[ 3*items[i] ];
    Vct3f c;
    for (int k=0; k<3; ++k)
      c += pts[vi[k]];
    mx.appendNode( Vct3( c/3.0f ) );
  }

  Indices lines;
  lines.reserve((items.size() - 1)*2 );
  for (int i=1; i<ne; ++i) {
    lines.push_back( voff + i - 1);
    lines.push_back( voff + i );
  }
  mx.appendSection( Mx::Line2, lines );

  mx.countElements();

  // generate one field with integer values for each tree level
  DVector<int> field( mx.nelements() );
  Indices nodes(1), tmp;
  nodes[0] = 0;

  for (int il=0; il<6; ++il) {

    tmp.clear();
    tmp.reserve( 2*nodes.size() );
    const int n = nodes.size();
    field = NotFound;
    for (int i=0; i<n; ++i) {
      uint ni = nodes[i];
      if (not tree.leaf(ni)) {
        tmp.push_back( tree.left(ni) );
        tmp.push_back( tree.right(ni) );
      }
      typename TreeType::ItemIterator itr, last = tree.end(ni);
      for (itr = tree.begin(ni); itr != last; ++itr)
        field[*itr] = ni;
      cout << "Level " << il << " Node " << ni
           << " size " << tree.size(ni) << endl;
    }
    mx.appendField( "Level "+str(il), field );
    tmp.swap(nodes);
  }

  mx.toXml(true).zwrite("tree.zml", 0);
}

int main(int argc, char *argv[])
{
  // produce about 500k triangles by default
  int nr = 1000;
  int nl = 250;
  if (argc > 2) {
    nr = atol( argv[1] );
    nl = atol( argv[2] );
  }

  PointList<3,float> vtx;
  Indices tri;
  mesh_cylinder(nr, nl, vtx, tri);

  const int nv = vtx.size();
  const int nt = tri.size() / 3;
  const int leafSize = 4;

  typedef UnbalancedBVTree<Dop3d3<float>, uint64_t> TreeType;
  typedef TriangleKeyFunctor<float> KeyFunctor;
  typedef TriangleBoxFunctor<float> BoxFunctor;

  Wallclock clk;
  clk.start();

  TreeType tree;
  tree.allocate( nt, leafSize );

  tick();
  KeyFunctor kf(&vtx, &tri[0]);
  tock("KeyFunctor initialization: ");

  tick();
  tree.sortKeys( kf );
  tock("Key sorting: ");

  tick();
  tree.createNodes();
  tock("Node creation: ");

  tick();
  BoxFunctor bf(&vtx, &tri[0]);
  tree.boundingVolumes( bf );
  tock("Bounding volumes: ");

  clk.stop();
  cout << "LBVH construction: " << clk.elapsed() << endl;

  if (nt < 10000)
    visualize(vtx, tri, tree);
  else
    cout << "Not writing visualization -- mesh too large." << endl;

  clk.start();
  MxTriTree btree(leafSize);
  btree.build( vtx, tri);
  clk.stop();
  cout << "Balanced binary tree construction: " << clk.elapsed() << endl;

  // test find-nearest correctness
  {
    const int ntest = 4;
    TriangleDistanceFunctor<float> fdst(&vtx, &tri[0]);
    for (int i=0; i<ntest; ++i) {
      const Vct3f & pt( vtx[lrand48() % vtx.size()] );
      uint iref = btree.nearestTriangle(pt);
      fdst.point( pt );
      uint inear = tree.nearest(fdst);
      cout << i << "TriTree: " << iref << '(' << fdst(iref) << ')'
           << " LBVH: " << inear << '(' << fdst(inear) << ')' << endl;
    }
  }


  // test lookup performance

  const int nlookup = 100;

  tick();
  TriangleDistanceFunctor<float> fdst(&vtx, &tri[0]);
  for (int i=0; i<nlookup; ++i) {
    fdst.point( vtx[ lrand48() % nv ] );
    uint inear = tree.nearest(fdst);
  }
  tock("Time for LBVH lookups: ");

  tick();
  for (int i=0; i<nlookup; ++i) {
    uint inear = btree.nearestTriangle( vtx[ lrand48() % nv ] );
  }
  tock("Time for MxTriTree lookups: ");




  return 0;
}

