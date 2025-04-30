
#include <genua/triset.h>

#include <iostream>
#include <fstream>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/mxmesh.h>
#include <genua/defines.h>
#include <surf/delaunaycore.h>
#include <surf/dcgeometry.h>
// #include <surf/dcplanegeometry.h>

using namespace std;

class PlaneDelaunay
{
public:

  /// initialize empty set
  PlaneDelaunay(Real qmin, Real qmax) : geo(qmin,qmax), core(geo) {}

  /// number of valid faces
  uint nValidFaces() const {return core.nValidFaces();}

  /// assign existing mesh
  void assign(const PointList<2> & vtx, const Indices & tri) {
    core.clear();
    geo.assign(vtx);
    const int ntri = tri.size() / 3;
    for (int i=0; i<ntri; ++i)
      core.addFace(tri[3*i+0], tri[3*i+1], tri[3*i+2]);
    core.fixate();
  }

  // debug
  void flipEdge(uint s, uint t) {
    DcEdge *pe = core.findEdge(s, t);
    assert(pe != 0);
    core.flipEdge(pe);
  }

  /// test insertion
  int insertVertex(const Vct2 & p) {
    uint c = geo.stInsertVertex(p);
    return core.insertVertex(c);
  }

  /// test constraint insertion
  uint insertConstraint(const PointList<2> & cp) {
    const uint np = cp.size();
    assert(np > 1);
    Indices cc(np);
    for (uint i=0; i<np; ++i)
      cc[i] = geo.stInsertVertex(cp[i]);
    if (sq(cp.back() - cp.front()) < gmepsilon)
      cc.back() = cc.front();
    dump("cinserted.zml");
    return core.insertConstraint(cc);
  }

  /// eat hole starting at p
  uint eatHole(const Vct2 & p) {
    uint nearest, ip = geo.stInsertVertex(p);
    int flag = geo.locateTriangle(core, ip, nearest);
    if (flag != DcGeometry::Outside)
      return core.eatHole(nearest);
    else
      return 0;
  }

  //  /// test polygon triangulation
  //  void polygon(const PointList<2> & pts) {
  //    geo.assign(pts);
  //    const int np = pts.size();
  //    Indices c(np-2);
  //    for (int i=2; i<np; ++i)
  //      c[i-2] = i;
  //    core.triangulatePolygon(core.constructEdge(0,1), c.begin(), c.end());
  //  }

  /// export triangles
  void triangles(Indices & tri) const {
    core.triangles(tri);
  }

  /// export geo (debug)
  void dump(const std::string & fname) const
  {
    const PointList<2> & pts( geo.stVertices() );
    const int np = pts.size();
    PointList<3> p3(np);
    for (int i=0; i<np; ++i)
      p3[i] = vct(pts[i][0], pts[i][1], 0.0);

    MxMesh mx;
    mx.appendNodes(p3);

    Indices tri;
    core.triangles(tri);
    mx.appendSection(Mx::Tri3, tri);
    // geo.triSet().toMx(mx);
    mx.toXml(true).zwrite(fname);
  }

  /// generate from grid (testing utility)
  void fromGrid(int np) {
    PointGrid<2> pg(np,np);
    for (int j=0; j<np; ++j)
      for (int i=0; i<np; ++i)
        pg(i,j) = vct( Real(i)/(np-1), Real(j)/(np-1) );

    PointList<2> pts(pg.begin(), pg.end());
    Indices tri(6*(np-1)*(np-1));
    for (int i=0; i<np-1; ++i) {
      for (int j=0; j<np-1; ++j) {
        uint p1 = i + j*np;
        uint p2 = i+1 + j*np;
        uint p3 = i+1 + (j+1)*np;
        uint p4 = i + (j+1)*np;
        uint fi1 = 2*(np-1)*i + 2*j;
        uint fi2 = fi1 + 1;
        tri[3*fi1+0] = p1; tri[3*fi1+1] = p2; tri[3*fi1+2] = p3;
        tri[3*fi2+0] = p1; tri[3*fi2+1] = p3; tri[3*fi2+2] = p4;
      }
    }

    geo.quantRange(-0.1, 1.1);
    this->assign(pts, tri);
  }

  /// statistics
  void stats() const {
    cout << Real(geo.iterations())/geo.calls() << " iterations/call" << endl;
  }

private:

  /// geometry/vertices
  DcGeometry geo;

  /// connectivity/mesh
  DelaunayCore core;
};

Real rnd()
{
  return Real( rand() ) / RAND_MAX;
}

void random_triangles(uint nt, PointList<2> & vtx, Indices & tri)
{
  vtx.resize( 3*nt );
  tri.resize( 3*nt );

  const Real ds = sqrt(1.0 / nt);
  for (uint i=0; i<nt; ++i) {
    Vct2 ctr( vct(rnd(), rnd()) );
    for (int k=0; k<3; ++k) {
      vtx[3*i+k] = ctr + ds*vct(rnd(), rnd());
      tri[3*i+k] = 3*i+k;
    }
  }
}

// experimental data structure
template <int lgn, class Key, class HashFcn>
class HashTable
{
public:

  enum { NB = (1 << lgn) };

  typedef typename std::vector<Key> Array;
  typedef typename Array::iterator iterator;
  typedef typename Array::const_iterator const_iterator;

  const_iterator begin() const {return m_table[0].begin();}

  const_iterator end() const {return m_table[NB-1].end();}

  void insert(const Key & k) {
    Array & a( m_table[index(HashFcn()(k))] );
    a.insert( std::lower_bound(a.begin(), a.end(), k), k);
  }

  void erase(const Key & k) {
    HashFcn hf;
    Array & a( m_table[index(hf(k))] );
    a.erase( std::lower_bound(a.begin(), a.end(), k) );
  }

  const_iterator find(const Key & k) const {
    HashFcn hf;
    const Array & a( m_table[index(hf(k))] );
    typename Array::const_iterator pos;
    pos = std::lower_bound(a.begin(), a.end(), k);
    return ((pos != a.end()) and (*pos == k)) ? pos : end();
  }


private:

  uint index(uint hashValue) const {
    return hashValue - ((hashValue >> lgn) << lgn);
  }

private:

  std::vector<Key> m_table[NB];
};

struct EdgeHash
{
  uint operator() (const DcEdge & e) const
  {
    return murmur_hash(e.source(), e.target());
  }
};

uint edge_hash(const DcEdge & e)
{
  return murmur_hash(e.source(), e.target());
}

//class SortedEdgeArray
//{
//public:

//  typedef std::vector<DcEdge> Container;
//  typedef Container::iterator iterator;

//  void insert(const DcEdge & e) {
//    iterator pos = std::lower_bound(m_edges.begin(), m_edges.end(), e);
//    m_edges.insert(pos, e);
//  }

//  iterator begin() {return m_edges.begin();}
//  iterator end() {return m_edges.end();}

//  iterator find(const DcEdge & e) {
//    iterator pos = std::lower_bound(m_edges.begin(), m_edges.end(), e);
//    return ((pos != end()) and (*pos == e)) ? pos : end();
//  }

//private:

//  /// linear array of edges
//  std::vector<DcEdge> m_edges;
//};

uint64_t mortonKey(const PointList<2> &m_st, const uint vix[])
{
  // profile! could be vectorized (SSE2) if hotspot
  const Vct2 & p1( m_st[vix[0]] );
  const Vct2 & p2( m_st[vix[1]] );
  const Vct2 & p3( m_st[vix[2]] );
  const Real m_qoffset(-0.1);
  const Real m_qscale( std::numeric_limits<int32_t>::max() / 2.2 );
  const Real third(1.0 / 3.0);
  Real uc = (p1[0] + p2[0] + p3[0])*third;
  Real vc = (p1[1] + p2[1] + p3[1])*third;
  int64_t a( (uc - m_qoffset)*m_qscale );
  int64_t b( (vc - m_qoffset)*m_qscale );
  return interleave_bits<uint64_t, 32>(a, b);
}

size_t inspect_hash1(const DcEdge *pe)
{
  size_t seed = 0;
  boost::hash_combine(seed, pe->source());
  boost::hash_combine(seed, pe->target());
  return seed;
}

size_t inspect_hash2(const DcEdge *pe)
{
  size_t seed = pe->source();
  boost::hash_combine(seed, pe->target());
  return seed;
}

size_t inspect_hash3(const DcEdge *pe)
{
  return murmur_hash(pe->source(), pe->target());
}

int main(int argc, char *argv[])
{

  try {

//    // test morton code functions
//    {
//      uint32_t a[2], b[2];
//      MortonLess<uint32_t, 2> iless;
//      for (int j=0; j<50000; ++j) {
//        a[0] = 90000 + rand() % 1200000;
//        a[1] = 90000 + rand() % 1200000;
//        b[0] = 90000 + rand() % 1200000;
//        b[1] = 90000 + rand() % 1200000;
//        uint64_t za = interleave_bits<uint64_t,32>(a[0], a[1]);
//        uint64_t zb = interleave_bits<uint64_t,32>(b[0], b[1]);
//        if ( (za < zb) != iless(a,b) ) {
//          cout << "Conflict: " << endl;
//          cout << "a = " << a[0] << ", " << a[1] << " za = " << za << endl;
//          cout << "b = " << b[0] << ", " << b[1] << " zb = " << zb << endl;
//        }
//      }
//      cout << "*** Morton code testing completed." << endl;
//    }

//    // test hash map implementations
//    {
//      // generate many edges
//      const int ne = 100000;
//      const int nlook = 16*ne;
//      std::vector<DcEdge> edges(ne);
//      for (int i=0; i<ne; ++i) {
//        uint src = rand() % ne;
//        uint trg = src + 1 + (rand() % 100);
//        edges[i] = DcEdge(src,trg);
//      }

//      Wallclock clk;
//      {
//        clk.start();
//        DcEdgeHash hashMap;
//        for (int i=0; i<ne; ++i)
//          hashMap.insert( &edges[i] );
//        clk.stop();
//        cout << "unordered_set construction: "
//             << 1e-6*ne/clk.elapsed() << "M/sec" << endl;

//        clk.start();
//        for (int i=0; i<nlook; ++i) {
//          DcEdge & edg( edges[lrand48() % ne] );
//          hashMap.find( &edg );
//        }
//        clk.stop();
//        cout << "unordered_set lookup: " << 1e-6*nlook/clk.elapsed()
//             << "M/sec" << endl;
//      }

//      {
//        typedef HashTable<18, DcEdge, EdgeHash> EdgeTable;
//        EdgeTable table;
//        clk.start();
//        for (int i=0; i<ne; ++i)
//          table.insert( edges[i] );
//        clk.stop();
//        cout << "static hash table construction: " << 1e-6*ne/clk.elapsed()
//             << "M/sec" << endl;

//        clk.start();
//        for (int i=0; i<nlook; ++i) {
//          const DcEdge & edg( edges[lrand48() % ne] );
//          table.find( edg );
//        }
//        clk.stop();
//        cout << "static hash table lookup: " << 1e-6*nlook/clk.elapsed()
//             << "M/sec" << endl;
//      }

//      {
//        SortedEdgeArray table;
//        clk.start();
//        for (int i=0; i<ne; ++i)
//          table.insert( edges[i] );
//        clk.stop();
//        cout << "sorted array construction: " << 1e-6*ne/clk.elapsed()
//             << "M/sec" << endl;

//        clk.start();
//        for (int i=0; i<nlook; ++i) {
//          const DcEdge & edg( edges[lrand48() % ne] );
//          table.find( edg );
//        }
//        clk.stop();
//        cout << "sorted array lookup: " << 1e-6*nlook/clk.elapsed()
//             << "M/sec" << endl;
//      }

//    }

    int ntri = 16;
    if (argc > 2) {
      cerr << argv[0] << " ntriangles" << endl;
      return -2;
    } else if (argc == 2) {
      ntri = atoi(argv[1]);
    }

    PointList<2> vtx;
    Indices tri;
    random_triangles( ntri, vtx, tri );

    // test lookup accuracy
    {
      cout << "*** Test triangle lookup" << endl;
      TriSet tset;
      tset.qrange(-0.1, 2.1);
      tset.assign(vtx, tri);

      // compare ordering
      DcIndexMap imap;
      for (int i=0; i<ntri; ++i) {
        size_t key = mortonKey(vtx, &tri[3*i]);
        imap.insert( key, i );
      }

      TriSet::const_iterator itset = tset.begin();
      DcIndexMap::iterator itimap = imap.begin();
      for (int i=0; i<ntri; ++i) {
        uint itri = imap.triangle(itimap);
        size_t mapkey = mortonKey(vtx, &tri[3*itri]);
        cout << i << " TriSet: " << tset.triangle(itset)
             << " IndexMap: " << itri << " Key: \t" << mapkey << endl;
        ++itset;
        ++itimap;
      }

      // pick random triangles
      const int ntest = 5;
      for (int i=0; i<ntest; ++i) {
        const uint it = rand() % ntri;
        const uint *v = &tri[3*it];
        Vct2 p;
        for (int k=0; k<3; ++k)
          p += vtx[ v[k] ];
        p /= 3.0;

        uint ilo(0), ihi(0);
        tset.nearest(p, ilo, ihi);
        cout << "Triset " << it << " lo " << ilo << " hi " << ihi << endl;
      }
    }

    Wallclock clk;
    {
      cout << "*** Time TriSet::assign()" << endl;
      clk.start();
      TriSet tset;
      tset.qrange(-0.1, 2.1);
      tset.assign(vtx, tri);
      clk.stop();
      cout << "Assign: " << ntri/clk.elapsed() << " tri/s" << endl;
    }
    
    {
      cout << "*** Time TriSet::insert()" << endl;
      clk.start();
      TriSet tset;
      tset.qrange(-0.1, 2.1);
      for (int i=0; i<ntri; ++i)
        tset.insert(vtx, &tri[3*i], i);
      clk.stop();
      cout << "Insert: " << ntri/clk.elapsed() << " tri/s" << endl;

      // test lookup performance
      clk.start();
      const int m = std::max(4, ntri / 16);
      uint ilo, ihi, nfound(0);
      for (int i=0; i<m; ++i) {
        const uint k = rand() % vtx.size();
        tset.nearest(vtx[k], ilo, ihi);
        nfound += ilo != NotFound;
        nfound += ihi != NotFound;
      }
      clk.stop();
      cout << "Lookup: " << m/clk.elapsed() << " points/s" << endl;
    }

    // test with a grid mesh
    const int np = (int) sqrt( double(ntri) );

    cout << "*** Create mesh from grid" << endl;
    PlaneDelaunay pd(-0.1, 1.1);
    pd.fromGrid(np);
    pd.dump("pre.zml");

    cout << "*** Test insertVertex()" << endl;
    Vct2 pt1 = vct(0.62, 0.5);
    if ( pd.insertVertex(pt1) )
      cout << "Insertion succeeded." << endl;
    else
      cout << "Insertion failed." << endl;

    pt1 = vct(1./3., 1./6.);
    if ( pd.insertVertex(pt1) )
      cout << "Insertion succeeded." << endl;
    else
      cout << "Insertion failed." << endl;

    cout << "*** Test constraint insertion" << endl;
    const int ncp = 13;
    PointList<2> pcon(ncp);
    for (int i=0; i<ncp; ++i) {
      // const Real r = 0.15 + 0.05*(i & 0x1);
      const Real r = 0.2;
      Real sphi, cphi, phi = 2*M_PI * i / (ncp - 1);
      sincosine(phi, sphi, cphi);
      pcon[i][0] = 0.5 + r*cphi;
      pcon[i][1] = 0.5 + r*sphi;
    }
    uint nic = pd.insertConstraint(pcon);
    if (nic == pcon.size())
      cout << "Constraint insertion successful." << endl;
    else
      cout << "Constraint insertion returned " << nic << endl;
    pd.dump("constrained.zml");

    cout << "*** Time random insertions" << endl;
    clk.start();
#ifdef NDEBUG
    const int ni = 800000;
#else
    const int ni = 100;
#endif
    for (int i=0; i<ni; ++i) {
      pt1[0] = rnd();
      pt1[1] = rnd();
      int flag = pd.insertVertex(pt1);
#ifndef NDEBUG
      if (flag == DelaunayCore::NotInserted)
        cout << "Insertion failed: " << pt1 << endl;
#endif
    }

    clk.stop();
    cout << ni/clk.elapsed() << " insertions/s" << endl;
    pd.stats();

    cout << "*** Test hole punching" << endl;
    uint neaten = pd.eatHole(vct(0.5, 0.5));
    cout << "Hole eater deleted " << neaten
         << " triangles, " << pd.nValidFaces() << " left." << endl;

    pd.dump("post.zml");

    // simplest possible case for overlapping edges
    cout << "*** Test boundary constraint insertion" << endl;
    PlaneDelaunay pdc(-0.1, 1.1);
    pdc.fromGrid(5);
    pdc.dump("cpre.zml");

    pcon.resize(3);
    pcon[0] = Vct2( 0.0, 0.5 );
    pcon[1] = Vct2( 1.0, 0.5 );
    pcon[2] = Vct2( 1.0, 0.0 );
    nic = pdc.insertConstraint( pcon );
    if (nic == pcon.size())
      cout << "Colinear constraint insertion successful." << endl;
    else
      cout << "Colinear constraint insertion returned " << nic << endl;
    pdc.dump("colinear.zml");

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
