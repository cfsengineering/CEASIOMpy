
// test penta intersection

#include "penta.h"
#include <genua/trimesh.h>
#include <boost/chrono.hpp>

#include <iostream>

using namespace std;

typedef boost::chrono::duration<int64_t, boost::milli> milliseconds;
typedef boost::chrono::duration<int64_t, boost::micro> microseconds;
typedef boost::chrono::duration<int64_t, boost::nano> nanoseconds;

typedef boost::chrono::high_resolution_clock HRClock;
typedef HRClock::time_point HRTime;

static HRTime s_stamp;

void tick()
{
  s_stamp = HRClock::now();
}

float tock(const std::string &s)
{
  HRTime t = HRClock::now();
  milliseconds ms = boost::chrono::duration_cast<milliseconds>( t - s_stamp );
  cout << s << ms << endl;
  return ms.count();
}

static void plain_test()
{
  Penta pa, pb;

  pa.pts[0] = Vct4f( 0.0f, 0.0f, 0.0f, 0.0f );
  pa.pts[1] = Vct4f( 1.0f, 0.0f, 0.0f, 0.0f );
  pa.pts[2] = Vct4f( 0.0f, 1.0f, 0.0f, 0.0f );

  for (int k=0; k<3; ++k)
    pa.pts[3+k] = pa.pts[k] + Vct4f( 0.0f, 0.0f, 1.0f, 1.0f );

  pb.pts[0] = Vct4f( 0.0f, 0.0f, 0.5f, 0.0f );
  pb.pts[1] = Vct4f( 1.0f, 0.0f, 0.5f, 0.0f );
  pb.pts[2] = Vct4f( 0.0f, 0.0f, 1.5f, 0.0f );

  for (int k=0; k<3; ++k)
    pb.pts[3+k] = pb.pts[k] + Vct4f( 0.0f, 1.0f, 0.0f, 1.0f );

  int mask = 0;

  tick();
  mask = 0;
  for (int i=0; i<10000; ++i)
    mask += scalar_intersection(pa, pb);
  tock("Scalar intersection test: ");

  // print result to avoid compiler optimization
  cout << "scalar pentahedra intersect: " << mask << endl;

  tick();
  mask = 0;
  for (int i=0; i<10000; ++i)
    mask += sse_intersection(pb, pa);
  tock("SSE intersection test: ");

  // print result to avoid compiler optimization
  cout << "sse pentahedra intersect: " << mask << endl;

  tick();
  mask = 0;
  for (int i=0; i<10000; ++i)
    mask += avx_intersection(pb, pa);
  tock("AVX intersection test: ");

  // print result to avoid compiler optimization
  cout << "avx pentahedra intersect: " << mask << endl;

  tick();
  mask = 0;
  for (int i=0; i<100; ++i)
    mask += scalar_intersection(pa, pb);
  tock("Scalar intersection test: ");

  // print result to avoid compiler optimization
  cout << "scalar pentahedra intersect: " << mask << endl;

  tick();
  mask = 0;
  for (int i=0; i<100; ++i)
    mask += sse_intersection(pb, pa);
  tock("SSE intersection test: ");

  // print result to avoid compiler optimization
  cout << "sse pentahedra intersect: " << mask << endl;

  tick();
  mask = 0;
  for (int i=0; i<100; ++i)
    mask += avx_intersection(pb, pa);
  tock("AVX intersection test: ");

  // print result to avoid compiler optimization
  cout << "avx pentahedra intersect: " << mask << endl;
}

static void generate_sphere(PointList<3,float> &vtx, Indices &tri)
{
  TriMesh tm;
  tm.icosahedron( Vct3(0.0,0.0,0.0), 0.2 );
  tm.quadSplit(3);

  vtx = PointList<3,float>( tm.vertices() );
  const int nf = tm.nfaces();
  tri.resize(3*nf);
  for (int i=0; i<nf; ++i) {
    const uint *vi = tm.face(i).vertices();
    for (int k=0; k<3; ++k)
      tri[3*i+k] = vi[k];
  }
}

static RbTransform translation(const Vct3f &to)
{
  RbTransform rbf;
  for (int k=0; k<3; ++k) {
    rbf(k,k) = 1.0;
    rbf(k,3) = to[k];
  }
  return rbf;
}

template <int N>
static int brute_force(const PointList<3,float> &vtx,
                        const Indices &tri,
                        const Trajectory &ta,
                        const Trajectory &tb)
{
  const int ntri = tri.size() / 3;
  int isec = 0;
  for (int i=0; i<ntri; ++i) {
    Penta pa;
    pa.assign(vtx, &tri[3*i], ta, 0, 1);
    for (int j=0; j<ntri; ++j) {
      Penta pb;
      pb.assign(vtx, &tri[3*j], tb, 0, 1);
      if (N == 1)
        isec += scalar_intersection(pa, pb);
      else if (N == 2)
        isec += sse_intersection(pa, pb);
      else if (N == 3)
        isec += avx_intersection(pa, pb);
      else if (N == 4)
        isec += unrolled_intersection(pa, pb);
    }
  }

  return isec;
}

int main()
{
  PointList<3,float> vtx;
  Indices tri;
  generate_sphere(vtx, tri);

  Trajectory tja(2), tjb(2);
  tja.time[0] = 0.0;
  tja.transform[0] = translation( Vct3f(-1.0,0.0,0.0) );
  tja.time[1] = 1.0;
  tja.transform[1] = translation( Vct3f(+1.0,0.0,0.0) );

  tjb.time[0] = 0.0;
  tjb.transform[0] = translation( Vct3f(0.0,-1.0,0.0) );
  tjb.time[1] = 1.0;
  tjb.transform[1] = translation( Vct3f(0.0,+1.0,0.0) );

  // floating-point ops per penta-penta test
  size_t ntri = tri.size() / 3;
  float t1, t2, t3, t4;
  float ppops = 64*438*ntri*ntri;
  cout << "Operation count: " << ppops << endl;

  tick();
  int is1 = brute_force<1>(vtx, tri, tja, tjb);
  t1 = tock("Scalar: ");

  tick();
  int is2 = brute_force<2>(vtx, tri, tja, tjb);
  t2 = tock("SSE:  ");

  tick();
  int is3 = brute_force<3>(vtx, tri, tja, tjb);
  t3 = tock("AVX: ");

  tick();
  int is4 = brute_force<4>(vtx, tri, tja, tjb);
  t4 = tock("Unrolled: ");

  cout << "Scalar checksum: " << is1 << ", " << 1e-6f*ppops/t1 << " GFlops" << endl;
  cout << "SSE checksum: " << is2 << ", " << 1e-6f*ppops/t2 << " GFlops" << endl;
  cout << "AVX checksum: " << is3 << ", " << 1e-6f*ppops/t3 << " GFlops" << endl;
  cout << "UNR checksum: " << is4 << ", " << 1e-6f*ppops/t4 << " GFlops" << endl;

  return 0;
}
