
#include <genua/judymap.h>
#include <genua/timing.h>
#include <genua/point.h>
#include <genua/morton.h>
#include <boost/unordered/unordered_set.hpp>

#include <cstdlib>
#include <vector>
#include <set>

using namespace std;

typedef JudyArray<size_t> JMap;
typedef std::pair<size_t, size_t> KV;
typedef std::vector<KV> Array;


bool compare_first(const KV & a, const KV &b)
{
  return a.first < b.first;
}

bool equal_first(const KV & a, const KV &b)
{
  return a.first == b.first;
}

void test_jmap(size_t nkey, bool io)
{
  Wallclock clk;
  Array kvs(nkey);
  for (size_t i=0; i<nkey; ++i) {
    kvs[i] = std::make_pair( lrand48(), lrand48() );
  }

  // make set unique with respect to key
  std::sort(kvs.begin(), kvs.end(), compare_first);
  kvs.erase( std::unique(kvs.begin(), kvs.end(), equal_first), kvs.end() );

  // shuffle elements again
  nkey = kvs.size();
  for (size_t i=0; i<nkey; ++i)
    std::swap( kvs[i], kvs[ lrand48()%nkey ] );

  cout << nkey/1000. << "k keys..." << endl;
  std::map<size_t, size_t> rbm;

  clk.start();
  JMap sm;
  for (size_t i=0; i<nkey; ++i) {
    JMap::pointer pos = sm.insert( kvs[i].first, kvs[i].second );
    if (io) {
      cout << "Inserted " << kvs[i].first << " check "
           << (*pos == kvs[i].second) << endl;
    } else {
      assert(pos != 0 and *pos == kvs[i].second);
    }
  }
  clk.stop();
  Real rj = 1e-6*nkey/clk.elapsed();

  clk.start();
  cout << "std::map: ";
  for (size_t i=0; i<nkey; ++i) {
    rbm.insert( kvs[i] );
  }
  clk.stop();
  Real rs = 1e-6*nkey/clk.elapsed();
  cout << "Insertion: " << rj << "M/sec vs " << rs << "M/sec" << endl;

  // lookup performance
  size_t sum(0);
  clk.start();
  cout << "JudyMap: ";
  size_t nlook = 8*nkey;
  for (size_t i=0; i<nlook; ++i) {
    size_t idx = lrand48() % nkey;
    JMap::iterator pos = sm.find( kvs[idx].first );
    assert(pos != 0 and *pos == kvs[idx].second);
    sum += (pos != 0) ? *pos : 0;
  }
  clk.stop();
  rj = 1e-6*nlook/clk.elapsed();

  clk.start();
  cout << "std::map: ";
  sum = 0;
  for (size_t i=0; i<nlook; ++i) {
    size_t idx = lrand48() % nkey;
    std::map<size_t,size_t>::iterator pos = rbm.find( kvs[idx].first );
    sum += (pos != rbm.end()) ? pos->second : 0;
  }
  clk.stop();
  rs = 1e-6*nlook/clk.elapsed();
  cout << "Find: " << rj << "M/sec vs " << rs << "M/sec" << endl;

  // precompute random numbers to look iup
  std::vector<size_t> lookup(nlook);
  for (size_t i=0; i<nlook; ++i)
    lookup[i] = lrand48();

  // iteration performance
  clk.start();
  sum = 0;
  for (size_t i=0; i<nlook; ++i) {
    JMap::pointer pos = sm.first( lookup[i] );
    sum += (pos != 0) ? *pos : 1;
  }
  clk.stop();
  rj = 1e-6*nlook/clk.elapsed();
  // cout << "Dummy : " << sum << endl;

  clk.start();
  cout << "std::map: ";
  sum = 0;
  for (size_t i=0; i<nlook; ++i) {
    std::map<size_t,size_t>::iterator pos = rbm.lower_bound(lookup[i]);
    sum += (pos != rbm.end()) ? pos->second : 1;
  }
  clk.stop();
  rs = 1e-6*nlook/clk.elapsed();
  cout << "Lower bound: " << rj << "M/sec vs " << rs << "M/sec" << endl;

  // cout << "Dummy : " << sum << endl;

  // check sorted iteration
  if (nkey < 100) {

    // sort array
    clk.start();
    std::sort(kvs.begin(), kvs.end(), compare_first);
    clk.stop();
    cout << "Array sorting: " << clk.elapsed() << endl;

    Array::const_iterator ai = kvs.begin();
    size_t key = 0;
    JMap::pointer pos = sm.first(key);
    while (pos != 0) {
      if (ai->first != key or ai->second != *pos) {
        cout << "Mismatch!"<< endl;
        exit(1);
      }
      ++ai;
      pos = sm.next(key);
    }
    clk.stop();
  }
}

class TestFace1
{
public:
  TestFace1() {}
  explicit TestFace1(uint a, uint b, uint c) { vix[0]=a; vix[1]=b; vix[2]=c; }
  uint vix[3];
  // uint pad;
};

class TestFace2
{
public:
  TestFace2() {}
  explicit TestFace2(uint a, uint b, uint c) { vix[0]=a; vix[1]=b; vix[2]=c; }
  uint vix[3];
  size_t key;

  bool operator== (const TestFace2 &a) const {
    return key == a.key;
  }

  bool operator< (const TestFace2 &a) const {
    return key < a.key;
  }
};

class MortonKey
{
public:
  MortonKey(const PointList<2> &pts) : vtx(pts) {
    qmin = -0.1;
    qscale = Real( UINTPTR_MAX ) / 1.2;
  }

  template <class FaceType>
  size_t operator()(const FaceType &f) const {
    Vct2 ctr = 0.3333333333333*( vtx[f.vix[0]] + vtx[f.vix[1]] + vtx[f.vix[2]] );
    return key(ctr);
  }

  size_t key(const Vct2 & p) const {
    size_t a = qscale*(p[0] - qmin);
    size_t b = qscale*(p[1] - qmin);
    const int NB = sizeof(void*) * 4;
    return interleave_bits<size_t,NB>(a, b);
  }

private:
  const PointList<2> & vtx;
  Real qmin, qscale;
};

typedef JudyMap<TestFace1> JFaceMap;
typedef std::set<TestFace2> SFaceMap;

void test_facemap(int nkey)
{
  const int np = nkey/2;
  const int nlook = 4*nkey;
  PointList<2> vtx(np);
  for (int i=0; i<np; ++i) {
    vtx[i][0] = drand48();
    vtx[i][1] = drand48();
  }

  // vertex indices
  std::vector<uint> tri(3*nkey);
  for (int i=0; i<3*nkey; ++i)
    tri[i] = lrand48() % np;

  Real rsi, rsl, rst, rji, rjl, rjt;
  Wallclock clk, clt;
  size_t jsum(0), ssum(0);
  srand48(1);
  clt.start();
  {
    JFaceMap jfm;
    MortonKey kf(vtx);

    clk.start();
    jfm.reserve(nkey);
    for (int i=0; i<nkey; ++i) {
      TestFace1 fi( tri[3*i+0], tri[3*i+1], tri[3*i+2] );
      jfm.appendValue( kf(fi), fi );
    }
    clk.stop();
    rji = 1e-6*nkey/clk.elapsed();

    clk.start();

    for (int i=0; i<nlook; ++i) {
      const Vct2 & pi( vtx[ i%np ] );
      size_t key = kf.key(pi);
      size_t idx = jfm.lowerBound( key );
      if (idx != jfm.npos) {
        const TestFace1 & f(jfm[idx]);
        jsum += f.vix[0];
      }
    }
    clk.stop();
    rjl = 1e-6*nlook/clk.elapsed();
  }
  clt.stop();
  rjt = clt.elapsed();

  srand48(1);
  clt.start();
  {
    SFaceMap sfm;
    MortonKey kf(vtx);

    clk.start();
    for (int i=0; i<nkey; ++i) {
      TestFace2 fi( tri[3*i+0], tri[3*i+1], tri[3*i+2] );
      fi.key = kf(fi);
      sfm.insert(fi);
    }
    clk.stop();
    rsi = 1e-6*nkey/clk.elapsed();

    clk.start();
    SFaceMap::iterator pos;
    for (int i=0; i<nlook; ++i) {
      const Vct2 & pi( vtx[ i%np ] );
      TestFace2 fi;
      fi.key = kf.key(pi);
      pos = sfm.lower_bound(fi);
      if (pos != sfm.end())
        ssum += pos->vix[0];
    }
    clk.stop();
    rsl = 1e-6*nlook/clk.elapsed();
  }
  clt.stop();
  rst = clt.elapsed();

  cout << "Insert: " << rji << "M/sec vs " << rsi << "M/sec; Search "
       << rjl << "M/sec vs " << rsl << "M/sec" << endl;

  cout << "Checksum " << jsum << ", " << ssum << endl;
}

size_t asm_inspect_jmap_first(const JFaceMap & map, size_t key)
{
  return map.lowerBound(key);
}

size_t asm_inspect_smap_first(const SFaceMap & map, size_t key)
{
  TestFace2 f2;
  f2.key = key;
  SFaceMap::const_iterator pos;
  pos = map.lower_bound(f2);
  return pos->vix[0];
}

class TestEdge
{
public:

  uint64_t key() const {
    uint64_t a(vix[0]), b(vix[1]);
    return a | (b << 32);
  }

  class Hasher {
  public:
    size_t operator() (const TestEdge *p) const {
      return (p != 0) ? p->key() : 0;
    }
  };

  class PtrEqual {
  public:
    bool operator() (const TestEdge *pa, const TestEdge *pb) const {
      return pa->key() == pb->key();
    }
  };

  uint vix[2];
  uint fix[2];
  uint flags;
  // uint pad[1];
};

typedef boost::unordered_set<TestEdge*, TestEdge::Hasher,
TestEdge::PtrEqual> EdgeHash;

void test_edgehash(int nedge)
{
  Wallclock clk;
  const int nv = nedge/8;
  const int nlook = 16*nedge;

  // allocate edges ahead of test
  std::vector<TestEdge> edges(nedge);
  for (int i=0; i<nedge; ++i) {
    edges[i].vix[0] = lrand48() % nv;
    edges[i].vix[1] = lrand48() % nv;
  }

  /*

  // test JudyHashTable
  Real rji, rjl, rsi, rsl;
  size_t jsum(0), ssum(0);
  srand48(1);
  {
    typedef JudyHashTable<TestEdge*, 8> JTable;
    JTable jht;

    clk.start();
    for (int i=0; i<nedge; ++i)
      jht.insert( edges[i].key(), &edges[i] );
    clk.stop();
    rji = 1e-6*nedge/clk.elapsed();

    clk.start();
    for (int i=0; i<nlook; ++i) {
      int idx = lrand48() % nedge;
      size_t key = edges[idx].key();
      JTable::pointer pos = jht.find(key);
      assert(pos != 0);
      jsum += (*pos)->vix[0];
    }
    clk.stop();
    rjl = 1e-6*nlook/clk.elapsed();
  }

  // test boost::unordered_set
  srand48(1);
  {
    EdgeHash hash;
    clk.start();
    for (int i=0; i<nedge; ++i)
      hash.insert( &edges[i] );
    clk.stop();
    rsi = 1e-6*nedge/clk.elapsed();

    clk.start();
    for (int i=0; i<nlook; ++i) {
      int idx = lrand48() % nedge;
      EdgeHash::iterator pos = hash.find( &edges[idx] );
      assert(pos != hash.end());
      ssum += (*pos)->vix[0];
    }
    clk.stop();
    rsl = 1e-6*nlook/clk.elapsed();
  }

  cout << "Insert: " << rji << "M/sec vs " << rsi << "M/sec; Search "
       << rjl << "M/sec vs " << rsl << "M/sec" << endl;
  cout << "Checksum " << jsum << ", " << ssum << endl;

  */
}

int main()
{
  cout.precision(3);
#ifndef NDEBUG
  cout << "*** Correctness check for JudyArray" << endl;
  test_jmap(128, true);
#endif

  cout << "*** Timing JudyArray" << endl;
  test_jmap(1 << 18, false);

  for (int i=12; i<19; ++i) {
    cout << "*** Timing ordered judy set: " << (1 << i)/1000 << "k" << endl;
    test_facemap(1 << i);
  }

  //  for (int i=12; i<21; ++i) {
  //    cout << "*** Timing hash map: " << (1 << i)/1000 << "k" << endl;
  //    test_edgehash(1 << i);
  //  }
}
