#ifndef PENTA_H
#define PENTA_H

#include <genua/point.h>
#include <genua/dvector.h>
#include <genua/smatrix.h>

typedef SMatrix<3,4,float> RbTransform;

struct Trajectory
{
  Trajectory(uint nstep) : time(nstep), transform(nstep) {}
  DVector<float> time;
  std::vector<RbTransform> transform;
};

struct Penta
{
  /// determine vertex coordinates from triangle and trajectory
  void assign(const PointList<3,float> &vtx, const uint tri[],
              const Trajectory &tj, int step1, int step2)
  {
    for (int k=0; k<3; ++k) {
      const Vct3f & p = vtx[tri[k]];
      pts[k+0] = Penta::map( p, tj, step1 );
      pts[k+3] = Penta::map( p, tj, step2 );
    }
  }

  /// compute 4D vertex
  static Vct4f map(const Vct3f &p, const Trajectory &tj, int step) {
    Vct4f q;
    const RbTransform &t( tj.transform[step] );
    for (int k=0; k<3; ++k)
      q[k] = t(k,0)*p[0] + t(k,1)*p[1] + t(k,2)*p[2] + t(k,3);
    q[3] = tj.time[step];
    return q;
  }

  /// access vertex map
  static int index(int itri, int jvx) {
    assert(itri < 8);
    assert(jvx < 3);
    const int m[8*3] = {  0,1,2,
                          3,4,5,
                          0,1,4,
                          0,4,3,
                          1,2,5,
                          1,5,4,
                          0,3,5,
                          0,5,2 };
    return m[3*itri + jvx];
  }

  /// 0,1,2 are lower, 3,4,5 upper triangle nodes
  Vct4f pts[6];
};

int scalar_intersection(const Penta &pa, const Penta &pb);
int sse_intersection(const Penta &pa, const Penta &pb);
int avx_intersection(const Penta &pa, const Penta &pb);
// int unrolled_intersection(const Penta &pa, const Penta &pb);

#endif // PENTA_H
