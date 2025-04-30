

#include <genua/sysinfo.h>
#include <genua/point.h>
#include <genua/morton.h>
#include <genua/dvector.h>
#include <genua/svector.h>
#include <genua/timing.h>
#include <genua/parallel_algo.h>

#ifdef HAVE_TBB
#include <tbb/blocked_range.h>
#include <tbb/parallel_sort.h>
#include <tbb/parallel_for.h>
#endif

#include <boost/function.hpp>
#include <boost/lockfree/queue.hpp>
#include <boost/thread.hpp>
#include <boost/make_shared.hpp>
#include <boost/bind.hpp>
#include <boost/container/vector.hpp>
#include <boost/chrono.hpp>

#include <iostream>
#include <cstdlib>

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

struct MinMax
{
  MinMax() {
    xmin = std::numeric_limits<float>::max();
    xmax = -xmin;
  }

  void assign(float vmin, float vmax) {
    boost::unique_lock<boost::mutex> lock(guard);
    xmin = std::min(xmin, vmin);
    xmax = std::max(xmax, vmax);
  }

  float xmin, xmax;
  boost::mutex guard;
};

struct MortonCoder
{
  typedef void result_type;

  MortonCoder(const PointList<3,float> &v, const Indices &t,
              MinMax &mm, DVector<uint64_t> &c)
    : vtx(v), tri(t), codes(c), lmt(mm) {}

  void limits(int a, int b) {
    float plo = std::numeric_limits<float>::max();
    float phi = -plo;
    for (int i=a; i<b; ++i) {
      const Vct3f & p( vtx[i] );
      for (int k=0; k<3; ++k) {
        plo = std::min(plo, p[k]);
        phi = std::max(phi, p[k]);
      }
    }
    lmt.assign(plo, phi);
  }

  void operator() (int a, int b) { encode(a,b); }

  void encode(int a, int b) {
    float offset = lmt.xmin;
    float scale = float((1 << 21) - 1) / (lmt.xmax - lmt.xmin);
    for (int i=a; i<b; ++i) {
      const uint *vi = &tri[3*i];
      Vct3f pmin( std::numeric_limits<float>::max() );
      Vct3f pmax = -pmin;
      for (int j=0; j<3; ++j) {
        const Vct3f & p( vtx[vi[j]] );
        for (int k=0; k<3; ++k) {
          pmin[k] = std::min(pmin[k], p[k]);
          pmax[k] = std::max(pmax[k], p[k]);
        }
      }
      uint64_t pi[3];
      for (int k=0; k<3; ++k)
        pi[k] = (0.5*(pmin[k] + pmax[k]) - offset)*scale;
      codes[i] = interleave_bits<uint64_t, 21>( pi[0], pi[1], pi[2] );
    }
  }

  const PointList<3,float> & vtx;
  const Indices & tri;
  DVector<uint64_t> & codes;
  MinMax & lmt;
};

struct EncodeRangeFunctor
{
  typedef void result_type;

  EncodeRangeFunctor() {}

  EncodeRangeFunctor(const PointList<3,float> &v, const Indices &t,
                     const MinMax &mm, DVector<uint64_t> &c)
    : pvtx(&v), tri(&t[0]), codes(c.pointer()), plmt(&mm) {}

  void operator() (int a, int b) const {
    float offset = plmt->xmin;
    float scale = float((1 << 21) - 1) / (plmt->xmax - plmt->xmin);
    const PointList<3,float> & vtx( *pvtx );
    for (int i=a; i<b; ++i) {
      const uint *vi = &tri[3*i];
      Vct3f pmin( std::numeric_limits<float>::max() );
      Vct3f pmax = -pmin;
      for (int j=0; j<3; ++j) {
        const Vct3f & p( vtx[vi[j]] );
        for (int k=0; k<3; ++k) {
          pmin[k] = std::min(pmin[k], p[k]);
          pmax[k] = std::max(pmax[k], p[k]);
        }
      }
      uint64_t pi[3];
      for (int k=0; k<3; ++k)
        pi[k] = (0.5*(pmin[k] + pmax[k]) - offset)*scale;
      codes[i] = interleave_bits<uint64_t, 21>( pi[0], pi[1], pi[2] );
    }
  }

#ifdef HAVE_TBB

  void operator() (const tbb::blocked_range<int> &r) const {
    (*this)(r.begin(), r.end());
  }

#endif

  const PointList<3,float> *pvtx;
  const uint *tri;
  mutable uint64_t *codes;
  const MinMax *plmt;
};

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

static void check_results(const DVector<uint64_t> &scodes,
                          const DVector<uint64_t> &pcodes)
{
  // check for consistent results
  for (uint i=0; i<pcodes.size(); ++i) {
    if (pcodes[i] != scodes[i]) {
      cout << "Triangle " << i << ": " << endl;
      cout << "Serial: " << scodes[i] << " Parallel: " << pcodes[i] << endl;
      abort();
    }
  }
  cout << "--------- Results OK --------" << endl;
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
  DVector<uint64_t> scodes(nt), pcodes(nt);
  MinMax lmt;

#if defined(HAVE_TBB)
  cout << "Using Thread Building Blocks." << endl;
#elif defined(HAVE_PPL)
  cout << "Using Microsoft PPL" << endl;
#elif defined(HAVE_PARALLEL_LIBCXX)
  cout << "Using OpenMP + parallel libstdc++" << endl;
#endif

  cout << "Nodes: " << nv << " Triangles: " << nt << endl;

  cout << "---------- Serial -------------" << endl;

  // serial loop
  {
    tick();
    MortonCoder mc(vtx, tri, lmt, scodes);
    mc.limits(0, nv);
    tock("Serial limits: ");

    tick();
    mc.encode(0, nt);
    tock("Serial encoding: ");
  }

  cout << "---------- Pure OpenMP -------------" << endl;

  // OpenMP loop
  {
    pcodes = 0;

    tick();
    MortonCoder mc(vtx, tri, lmt, pcodes);
#pragma omp parallel for
    for (int i=0; i<nt; ++i)
      mc.encode(i, i+1);
    tock("OpenMP encoding, default: ");

    pcodes = 0;

    tick();
#pragma omp parallel for schedule(dynamic, 2048)
    for (int i=0; i<nt; ++i)
      mc.encode(i, i+1);
    tock("OpenMP encoding, chunk = 2048: ");
  }

  check_results(scodes, pcodes);

  cout << "---------- TBB encoding --------------------" << endl;

#ifdef HAVE_TBB

  pcodes = 0;
  {
    for (int chunk=64; chunk<nt/16; chunk*=2) {
      tick();
      EncodeRangeFunctor func(vtx, tri, lmt, pcodes);
      tbb::parallel_for( tbb::blocked_range<int>(0,nt,chunk), func );
      tock("TBB encoding, chunk = "+str(chunk)+": ");
    }
    tick();
    EncodeRangeFunctor func(vtx, tri, lmt, pcodes);
    tbb::parallel_for( tbb::blocked_range<int>(0,nt), func );
    tock("TBB encoding, default: ");
  }

  check_results(scodes, pcodes);

#endif

  pcodes = 0;
  cout << "---------- genua/parallel_algo -------------" << endl;
  {
    for (int chunk=64; chunk<nt/16; chunk*=2) {
      tick();
      EncodeRangeFunctor func(vtx, tri, lmt, pcodes);
      parallel::block_loop( func, 0, nt, chunk );
      tock("block_loop, chunk = "+str(chunk)+": ");
    }
  }
  check_results(scodes, pcodes);

  cout << "----- Sorting -----------" << endl;

  Indices perm(nt);
  for (int i=0; i<nt; ++i)
    perm[i] = i;

  IndirectLess<DVector<uint64_t> > cmp(pcodes);
  tick();
  std::sort(perm.begin(), perm.end(), cmp);
  tock("Serial sort: ");

  for (int i=0; i<nt; ++i)
    perm[i] = i;

#ifdef HAVE_TBB
  tick();
  tbb::parallel_sort(perm.begin(), perm.end(), cmp);
  tock("tbb::parallel_sort: ");
#else // use whatever we have in genua/parallel_algo
  tick();
  parallel::sort(perm.begin(), perm.end(), cmp);
  tock("genua/parallel_sort: ");
#endif

  Indices tp(nt);
  for (int i=0; i<nt; ++i)
    tp[i] = i;

#ifdef HAVE_GENUA_PARALLEL_ALGO

  cout << " ----------- Test detail::split_range -------------" << endl;
  {
    Indices tmp(nt);
    std::generate(tmp.begin(), tmp.end(), rand);
    uint estMedian = parallel::detail::median3(tmp.front(), tmp[nt/2],
                                     tmp.back(), std::less<uint>());
    cout << "front:   " << tmp.front() << endl;
    cout << "mid  :   " << tmp[nt/2] << endl;
    cout << "back :   " << tmp.back() << endl;
    cout << "Estimated 3-way median: " << estMedian << endl;
    cout << "Estimated 9-way median: " << parallel::detail::median9(tmp.begin(),
                                                          tmp.end(), std::less<uint>()) << endl;

    tick();
    Indices::iterator pivot;
    pivot = parallel::detail::split_range(tmp.begin(), tmp.end(), std::less<uint>());

    tock("serial split_range: ");

    // cout << "pivot value: " << *pivot << endl;
    cout << "left size: " << std::distance(tmp.begin(), pivot) << endl;
    cout << "right size: " << std::distance(pivot, tmp.end()) << endl;

    // test post-condition
    assert(pivot != tmp.end());
    for (Indices::iterator itr=tmp.begin(); itr != pivot; ++itr)
      assert( *itr < estMedian );
    for (Indices::iterator itr=pivot; itr != tmp.end(); ++itr)
      assert( estMedian <= *itr );
    cout << "split_range verified." << endl;

    // simulate recursion
    std::sort(tmp.begin(), pivot);
    std::sort(pivot, tmp.end());
    for (int i=1; i<nt; ++i)
      assert(tmp[i-1] <= tmp[i]);
    cout << "Recursive sort verified." << endl;
    cout << "Actual median: " << tmp[nt/2] << endl;
  }

  // test parallel sort
  tick();
  uint *pbegin = &tp[0];
  uint *pend = pbegin + tp.size();
  parallel::genua_sort(pbegin, pend, cmp);
  tock("test_sort: ");

  for (int i=1; i<nt; ++i) {
    if ( pcodes[tp[i]] < pcodes[tp[i-1]] ) {
      cout << "Sort error at " << i << endl
           << " key[i-1] = " << pcodes[tp[i-1]] << endl
           << " key[i]   = " << pcodes[tp[i]] << endl;
      abort();
    }
  }
  cout << "------------ Sort result OK." << endl;

#endif

  return 0;
}
