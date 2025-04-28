
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
 
// ANCIENT CODE, NEEDS TO BE REWORKED

#ifndef GENUA_TRAFO_H
#define GENUA_TRAFO_H

#include <math.h>

#include "smatrix.h"
#include "point.h"

extern "C" {

  // Low-level function for coordinate transformation
  // these are kept separately for the day they are reimplemented in SSE...
  void vertex_transform_4d(int npt, const double T[], const double A[], double B[]);
  void vertex_transform_4f(int npt, const float T[], const float A[], float B[]);
  void vertex_transform_3d(int npt, const double T[], const double A[], double B[]);
  void vertex_transform_3f(int npt, const float T[], const float A[], float B[]);
}

/// plain code 4x4 vertex transform template
template <class Type>
inline void vertex_transform_4(int npt, const Type T[], const Type A[], Type B[])
{
  Type A0, A1, A2, A3;
  const int nb = npt/4;
  for (int jb=0; jb<nb; ++jb) {
    
    int j = 4*jb;
    A0 = A[4*j+0];
    A1 = A[4*j+1];
    A2 = A[4*j+2];
    A3 = A[4*j+3];
    B[4*j+0] = T[0]*A0 + T[4]*A1 + T[ 8]*A2 + T[12]*A3;
    B[4*j+1] = T[1]*A0 + T[5]*A1 + T[ 9]*A2 + T[13]*A3;
    B[4*j+2] = T[2]*A0 + T[6]*A1 + T[10]*A2 + T[14]*A3;
    B[4*j+3] = T[3]*A0 + T[7]*A1 + T[11]*A2 + T[15]*A3;
  
    ++j;
    A0 = A[4*j+0];
    A1 = A[4*j+1];
    A2 = A[4*j+2];
    A3 = A[4*j+3];
    B[4*j+0] = T[0]*A0 + T[4]*A1 + T[ 8]*A2 + T[12]*A3;
    B[4*j+1] = T[1]*A0 + T[5]*A1 + T[ 9]*A2 + T[13]*A3;
    B[4*j+2] = T[2]*A0 + T[6]*A1 + T[10]*A2 + T[14]*A3;
    B[4*j+3] = T[3]*A0 + T[7]*A1 + T[11]*A2 + T[15]*A3;
    
    ++j;
    A0 = A[4*j+0];
    A1 = A[4*j+1];
    A2 = A[4*j+2];
    A3 = A[4*j+3];
    B[4*j+0] = T[0]*A0 + T[4]*A1 + T[ 8]*A2 + T[12]*A3;
    B[4*j+1] = T[1]*A0 + T[5]*A1 + T[ 9]*A2 + T[13]*A3;
    B[4*j+2] = T[2]*A0 + T[6]*A1 + T[10]*A2 + T[14]*A3;
    B[4*j+3] = T[3]*A0 + T[7]*A1 + T[11]*A2 + T[15]*A3;
    
    ++j;
    A0 = A[4*j+0];
    A1 = A[4*j+1];
    A2 = A[4*j+2];
    A3 = A[4*j+3];
    B[4*j+0] = T[0]*A0 + T[4]*A1 + T[ 8]*A2 + T[12]*A3;
    B[4*j+1] = T[1]*A0 + T[5]*A1 + T[ 9]*A2 + T[13]*A3;
    B[4*j+2] = T[2]*A0 + T[6]*A1 + T[10]*A2 + T[14]*A3;
    B[4*j+3] = T[3]*A0 + T[7]*A1 + T[11]*A2 + T[15]*A3;
  }
  
  for (int j=4*nb; j<npt; ++j) {
    A0 = A[4*j+0];
    A1 = A[4*j+1];
    A2 = A[4*j+2];
    A3 = A[4*j+3];
    B[4*j+0] = T[0]*A0 + T[4]*A1 + T[ 8]*A2 + T[12]*A3;
    B[4*j+1] = T[1]*A0 + T[5]*A1 + T[ 9]*A2 + T[13]*A3;
    B[4*j+2] = T[2]*A0 + T[6]*A1 + T[10]*A2 + T[14]*A3;
    B[4*j+3] = T[3]*A0 + T[7]*A1 + T[11]*A2 + T[15]*A3;
  }
} 

/// plain code 3x3 vertex transform template
template <class Type>
inline void vertex_transform_3(int npt, const Type T[], const Type A[], Type B[])
{
  Type A0, A1, A2;
  const int nb = npt/4;
  for (int jb=0; jb<nb; ++jb) {
    
    int j = 4*jb;
    A0 = A[3*j+0];
    A1 = A[3*j+1];
    A2 = A[3*j+2];
    B[3*j+0] = T[0]*A0 + T[3]*A1 + T[6]*A2;
    B[3*j+1] = T[1]*A0 + T[4]*A1 + T[7]*A2;
    B[3*j+2] = T[2]*A0 + T[5]*A1 + T[8]*A2;
    
    ++j;
    A0 = A[3*j+0];
    A1 = A[3*j+1];
    A2 = A[3*j+2];
    B[3*j+0] = T[0]*A0 + T[3]*A1 + T[6]*A2;
    B[3*j+1] = T[1]*A0 + T[4]*A1 + T[7]*A2;
    B[3*j+2] = T[2]*A0 + T[5]*A1 + T[8]*A2;
     
    ++j;
    A0 = A[3*j+0];
    A1 = A[3*j+1];
    A2 = A[3*j+2];
    B[3*j+0] = T[0]*A0 + T[3]*A1 + T[6]*A2;
    B[3*j+1] = T[1]*A0 + T[4]*A1 + T[7]*A2;
    B[3*j+2] = T[2]*A0 + T[5]*A1 + T[8]*A2;
    
    ++j;
    A0 = A[3*j+0];
    A1 = A[3*j+1];
    A2 = A[3*j+2];
    B[3*j+0] = T[0]*A0 + T[3]*A1 + T[6]*A2;
    B[3*j+1] = T[1]*A0 + T[4]*A1 + T[7]*A2;
    B[3*j+2] = T[2]*A0 + T[5]*A1 + T[8]*A2;
  }
  
  for (int j=4*nb; j<npt; ++j) {
    A0 = A[3*j+0];
    A1 = A[3*j+1];
    A2 = A[3*j+2];
    B[3*j+0] = T[0]*A0 + T[3]*A1 + T[6]*A2;
    B[3*j+1] = T[1]*A0 + T[4]*A1 + T[7]*A2;
    B[3*j+2] = T[2]*A0 + T[5]*A1 + T[8]*A2;
  }
} 

// derived convenience functions -- assumes that B has enough space
inline void vertex_transform(const Mtx44 & T, const PointList<4> & A, PointList<4> & B)
{
  assert(A.size() == B.size());
  vertex_transform_4(A.size(), T.pointer(), &(A[0][0]), &(B[0][0]));
}

// derived convenience functions -- assumes that B has enough space
inline void vertex_transform(const Mtx33 & T, const PointList<3> & A, PointList<3> & B)
{
  assert(A.size() == B.size());
  vertex_transform_3(A.size(), T.pointer(), &(A[0][0]), &(B[0][0]));
}

/** Rotation in space.
  */
class Rotation
{
  public:

    /// construction
    Rotation();

    /// rotate further
    const Mtx33 & rotate(const Vct3 & a, Real beta);

    /// shortcut - rotation about origin
    const Mtx33 & rotate(Real ax, Real ay, Real az);

    /// apply rotation to vector
    Vct3 forward(const Vct3 & v) const
      {return mat*v;}

    /// apply to homogeneous matrix
    void forward(SMatrix<4,4> & hm) const;

    /// apply backward transformation
    Vct3 backward(const Vct3 & v) const
      {return mat.transposed()*v;}

    /// apply to homogeneous matrix
    void backward(SMatrix<4,4> & hm) const;

    /** Convert representation.
        Compute the axis and angle of the current rotation into
        a rotation about an axis v with norm(v) = 1 and an angle beta.
        The return value is the axis scaled with beta. */
    Vct3 axis() const;

    /// reset to unit matrix
    void clear();

  private:

    /// rotation matrix
    SMatrix<3,3> mat;
};

/** Reference Frame.

  Every geometric entity inherits its own local reference frame which
  provides methods to translate and rotate the body with respect
  to a global reference. All transformation operations modify the reference
  frame. When multiple rotations are specified, they will be performed in axes
  order, i.e. (1.) Rotation about x-Axis, (2) about y-Axis, (3) about z-Axis.

  An object which inherits from RFrame must provide a method
  \verbatim
    void apply();
  \endverbatim
  which implements the homogeneous transform for the objects using the
  protected 4x4 transformation matrix 'mat'. A example transformation sequence
  would look like:
  \verbatim
    Surface surf;
    [...]
    surf.scale(3.0);
    surf.rotate(0.2, 0, 0);
    surf.translate(3.0, 4.0, -2.5);
    surf.apply();
  \endverbatim

 */
class RFrame
{
  public:

    /// default construction
    RFrame();

    /// virtual destructor
    virtual ~RFrame() {}

    /// this method must be provided by childs
    virtual void apply() = 0;
    
    /// apply should finally call this method to clear transformation matrix
    void clear();

    /// return the position of the current frame relative to global origin
    Vct3 getOrigin() const;

    /// move reference frame by translation vector
    void translate(const Vct3 & v);

    /// move reference by (dx,dy,dz)
    void translate(Real dx, Real dy, Real dz);

    /// rotate by (betax, bety, betaz) around origin axis
    void rotate(Real betax, Real betay, Real betaz);

    /// rotate by angle around axis
    void rotate(const Vct3 & rotax, Real angle);

    /// scales in three dimensions by the factors given
    void scale(Real xf, Real yf, Real zf);

    /// scale in all directions
    void scale(Real f)
      {scale(f,f,f);}

    /// mirror about plane - parameter is mirror plane normal
    void mirror(const Vct3 & normal);

    /// return transformation matrix
    const SMatrix<4,4> & trafoMatrix() const
      {return mat;}

    /// set transformation matrix 
    void setTrafoMatrix(const SMatrix<4,4> & m)
      {mat = m;}
      
    /// coordinate-transform vector
    Vct3 forward(const Vct3 & a) const;

    /// coordinate-transform vector backwards
    // Vct3 backward(const Vct3 & a) const;
    
    void forward(const PointList<4> & a, PointList<4> & b) const {
      vertex_transform(mat, a, b); 
    }
    
  protected:

    /// transformation matrix
    SMatrix<4,4> mat;
};

class Transformer : public RFrame
{
  public:
    void apply() {}
};

 



#endif


