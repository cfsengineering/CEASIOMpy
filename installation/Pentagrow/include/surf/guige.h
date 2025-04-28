
/* Interface definition for Guigue/Devillers' triangle-triangle
 * intersections routines (Journal of Graphics Tools)
 *
 * This file is in the public domain
 */

#ifndef SURF_GUIGE_H
#define SURF_GUIGE_H

#ifdef __cplusplus
extern "C" 
{
#endif
 
// Guige

int tri_tri_overlap_test_3d(const double p1[3], const double q1[3], const double r1[3], 
                            const double p2[3], const double q2[3], const double r2[3]);


int coplanar_tri_tri3d(const double  p1[3], const double  q1[3], const double  r1[3],
                       const double  p2[3], const double  q2[3], const double  r2[3],
                       const double  N1[3], const double  N2[3]);


int tri_tri_overlap_test_2d(const double p1[2], const double q1[2], const double r1[2], 
                            const double p2[2], const double q2[2], const double r2[2]);


int tri_tri_intersection_test_3d(const double p1[3], const double q1[3], const double r1[3], 
                                 const double p2[3], const double q2[3], const double r2[3],
                                 int * coplanar, 
                                 double source[3], double target[3]);

#ifdef __cplusplus
} // end extern "C"

#include <iostream>
#include <genua/triface.h>
#include <genua/trimesh.h>

// Moeller

int tri_tri_intersect(const double V0[3],const double V1[3],const double V2[3],
                      const double U0[3],const double U1[3],const double U2[3]);

int tri_tri_intersect_with_isectline(double V0[3], double V1[3], double V2[3],
                                     double U0[3], double U1[3], double U2[3],
                                     int *coplanar, double isectpt1[3],
                                     double isectpt2[3]);

int tri_tri_intersect(const float V0[3],const float V1[3],const float V2[3],
                      const float U0[3],const float U1[3],const float U2[3]);

int tri_tri_intersect_with_isectline(float V0[3], float V1[3], float V2[3],
                                     float U0[3], float U1[3], float U2[3],
                                     int *coplanar, float isectpt1[3],
                                     float isectpt2[3]);

             
inline bool guige_overlap(const TriFace & f1, const TriFace & f2)
{
  const uint *v1( f1.vertices() );
  const TriMesh & m1( *(f1.mesh()) );
  const Vct3 & p1( m1.vertex(v1[0]) );
  const Vct3 & q1( m1.vertex(v1[1]) );
  const Vct3 & r1( m1.vertex(v1[2]) );
  
  const uint *v2( f2.vertices() );
  const TriMesh & m2( *(f2.mesh()) );
  const Vct3 & p2( m2.vertex(v2[0]) );
  const Vct3 & q2( m2.vertex(v2[1]) );
  const Vct3 & r2( m2.vertex(v2[2]) );
  
  int r = tri_tri_overlap_test_3d(p1.pointer(), q1.pointer(), r1.pointer(),
                                  p2.pointer(), q2.pointer(), r2.pointer());
  return (r != 0);
}

inline bool guige_intersect(const TriFace & f1, const TriFace & f2,
                            Vct3 & isrc, Vct3 & itrg)
{
  const uint *v1( f1.vertices() );
  const TriMesh & m1( *(f1.mesh()) );
  const Vct3 & p1( m1.vertex(v1[0]) );
  const Vct3 & q1( m1.vertex(v1[1]) );
  const Vct3 & r1( m1.vertex(v1[2]) );
  
  const uint *v2( f2.vertices() );
  const TriMesh & m2( *(f2.mesh()) );
  const Vct3 & p2( m2.vertex(v2[0]) );
  const Vct3 & q2( m2.vertex(v2[1]) );
  const Vct3 & r2( m2.vertex(v2[2]) );
  
  int coplanar(0);
  int r = tri_tri_intersection_test_3d(p1.pointer(), q1.pointer(), r1.pointer(),
                                       p2.pointer(), q2.pointer(), r2.pointer(),
                                       &coplanar, 
                                       isrc.pointer(), itrg.pointer());
    
  return (r != 0 and coplanar != 1);
}

inline bool moeller_intersect(const Vct3 a[], const Vct3 b[])
{
  int r = tri_tri_intersect(a[0].pointer(), a[1].pointer(), a[2].pointer(),
                            b[0].pointer(), b[1].pointer(), b[2].pointer());
  return (r != 0);
}

inline bool moeller_intersect(const TriFace & f1, const TriFace & f2,
                              Vct3 & isrc, Vct3 & itrg)
{
  const uint *v1( f1.vertices() );
  const TriMesh & m1( *(f1.mesh()) );
  Vct3 p1( m1.vertex(v1[0]) );
  Vct3 q1( m1.vertex(v1[1]) );
  Vct3 r1( m1.vertex(v1[2]) );
  
  const uint *v2( f2.vertices() );
  const TriMesh & m2( *(f2.mesh()) );
  Vct3 p2( m2.vertex(v2[0]) );
  Vct3 q2( m2.vertex(v2[1]) );
  Vct3 r2( m2.vertex(v2[2]) );
  
  int coplanar(0);
  int r = tri_tri_intersect_with_isectline(p1.pointer(), q1.pointer(), r1.pointer(),
                                           p2.pointer(), q2.pointer(), r2.pointer(),
                                           &coplanar, isrc.pointer(), itrg.pointer());
    
  return (r != 0 and coplanar != 1);
}

#endif

#endif
