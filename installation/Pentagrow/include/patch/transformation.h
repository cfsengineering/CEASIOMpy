
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
 
// Geometric transformation - replacement for ancient trafo.h

#ifndef GENUA_TRANSFORMATION_H
#define GENUA_TRANSFORMATION_H

#include "forward.h"
#include "svector.h"
#include "smatrix.h"
#include "mvop.h"
#include "smallqr.h"
#include "xmlelement.h"

/** Geometric transformations.

  TrafoTpl provides static implementation utility functions which can
  be used to compute 4-by-4 transformation matrices. Furthermore, it
  can be used to store a canonical representation of a transformation
  sequence in terms of one rotation, one scaling operation and a single
  translation. In this way, it is possible to store a geometric
  transformation description to file and recover a user-editable
  representation.

  The canonical order of transformations applied is
  1. Apply coordinate scaling factors in the original frame.
  2. Rotate about the origin, first around x, then around the now
     rotated y-axis, then around the twice rotated z-axis (x-y'-z'').
  3. Translate.

  Using reconstruct, the canonical representation of the above three operations
  can be extracted from any affine transformation matrix that was constructed by
  any sequence of these transformations. \b Note: TrafoTpl implements the
  construction of reflections as well, but not (yet) their reconstruction.

  \ingroup geometry

*/
template <typename FloatType>
class TrafoTpl
{
public:

  typedef SVector<3,FloatType> TrafoVct;
  typedef SMatrix<4,4,FloatType> TrafoMtx;

  enum Flag {TrafoNone=0,
             TrafoReflect=1,
             TrafoScale=2,
             TrafoRotate=4,
             TrafoTranslate=8};

  /// create identity transformation
  TrafoTpl() { identity(); }

  /// access transformation components
  const TrafoVct & scaling() const {return m_scaling;}

  /// access transformation components
  const TrafoVct & rotation() const {return m_rotation;}

  /// access transformation components
  const TrafoVct & translation() const {return m_translation;}

  /// access rotation center
  const TrafoVct & pivot() const {return m_pivot;}

  /// reset transformation to identity
  void identity() {
    m_flag = TrafoNone;
    m_reflection = FloatType(0);
    m_scaling = FloatType(1);
    m_rotation = FloatType(0);
    m_pivot = FloatType(0);
    m_translation = FloatType(0);
  }

  /// reflect about plane through origin
  template <typename FType>
  void reflect(FType sx, FType sy, FType sz) {
    m_reflection[0] = sx;
    m_reflection[1] = sy;
    m_reflection[2] = sz;
    assert(sq(sx)+sq(sy)+sq(sz) > 0);
    normalize(m_reflection);
    m_flag |= TrafoReflect;
  }

  /// set translation vector
  template <typename FType>
  void translate(FType rx, FType ry, FType rz) {
    m_translation[0] = rx;
    m_translation[1] = ry;
    m_translation[2] = rz;
    m_flag |= TrafoTranslate;
  }

  /// set translation vector
  template <typename FType>
  void translate(const SVector<3,FType> &trn) {
    m_translation = TrafoVct(trn);
    m_flag |= TrafoTranslate;
  }

  /// set scaling factors
  template <typename FType>
  void scale(FType sx, FType sy, FType sz) {
    m_scaling[0] = sx;
    m_scaling[1] = sy;
    m_scaling[2] = sz;
    m_flag |= TrafoScale;
  }

  /// set rotation angles
  template <typename FType>
  void rotate(FType rx, FType ry, FType rz) {
    m_rotation[0] = rx;
    m_rotation[1] = ry;
    m_rotation[2] = rz;
    m_flag |= TrafoRotate;
  }

  /// set rotation angles
  template <typename FType>
  void rotate(const SVector<3,FType> &rxyz) {
    m_rotation = TrafoVct(rxyz);
    m_flag |= TrafoRotate;
  }

  /// set center of rotation
  template <typename FType>
  void pivot(FType px, FType py, FType pz) {
    m_pivot[0] = px;
    m_pivot[1] = py;
    m_pivot[2] = pz;
  }

  /// set center of rotation
  template <typename FType>
  void pivot(const SVector<3,FType> &rxyz) {m_pivot = rxyz;}

  /// set rotation angles from quaternion
  template <typename Quat>
  void fromQuaternion(const Quat & q) {
    quat2rxyz(q, m_rotation);
    m_flag |= TrafoRotate;
  }

  /// apply another transformation to this one (premultiply)
  void prepend(const TrafoTpl<FloatType> & a) {
    TrafoMtx t1, t2;
    this->matrix(t1);
    a.matrix(t2);
    t1 = t2 * t1;
    reconstruct(t1);
  }

  /// compute the resulting transformation matrix
  template <class MatrixType>
  void matrix(MatrixType & m) const {
    unity(m);
    MatrixType tmp;
    if (m_flag & TrafoReflect) {
      reflectionMatrix(m_reflection, m);
    }
    if (m_flag & TrafoScale) {
      scalingMatrix(m_scaling, tmp);
      m = tmp*m;
    }
    if (m_flag & TrafoRotate) {
      if (m_rotation[0] != 0) {
        xRotationMatrix(m_rotation[0], tmp);
        m = tmp*m;
      }
      if (m_rotation[1] != 0) {
        yRotationMatrix(m_rotation[1], tmp);
        m = tmp*m;
      }
      if (m_rotation[2] != 0) {
        zRotationMatrix(m_rotation[2], tmp);
        m = tmp*m;
      }
      if (sq(m_pivot) != 0)
        shiftPivot(m_pivot, m);
    }
    if (m_flag & TrafoTranslate) {
      unity(tmp);
      for (int i=0; i<3; ++i)
        tmp(i,3) = m_translation[i];
      m = tmp*m;
    }
  }

  /// convenience interface: return 4x4 matrix
  SMatrix<4,4,FloatType> matrix() const {
    SMatrix<4,4,FloatType> m;
    this->matrix(m);
    return m;
  }

  /// apply the current transformation to a point list
  template <class PtList>
  void transformList(PtList & pts) {
    TrafoMtx m;
    this->matrix(m);
    TrafoTpl<FloatType>::transformList(m, pts);
  }

  /// apply the current transformation to a 6D point list (force/moment pairs)
  template <class FloatT>
  void transformList6D(PointList<6,FloatT> & pts) {
    TrafoMtx m;
    this->matrix(m);
    TrafoTpl<FloatType>::transformList6D(m, pts);
  }

  /// apply the current transformation to a point (inefficient)
  template <class VectorType>
  void transformPoint(VectorType & p) {
    TrafoMtx m;
    this->matrix(m);
    TrafoTpl<FloatType>::transformPoint(m, p);
  }

  /// apply the current transformation to a direction (inefficient)
  template <class VectorType>
  void transformDirection(VectorType & p) {
    TrafoMtx m;
    this->matrix(m);
    TrafoTpl<FloatType>::transformDirection(m, p);
  }

  /// reconstruct from 4x4 matrix (assuming no reflection)
  void reconstruct(const TrafoMtx & m) {
    m_flag = TrafoNone;
    m_reflection = FloatType(0);
    m_pivot = FloatType(0);
    m_scaling = FloatType(0);
    for (int i=0; i<3; ++i) {
      m_translation[i] = m(i,3);
      for (int j=0; j<3; ++j)
        m_scaling[i] += sq(m(j,i));
      m_scaling[i] = std::sqrt(m_scaling[i]);
    }
    TrafoMtx mrot;
    for (int j=0; j<3; ++j)
      for (int i=0; i<3; ++i)
        mrot(i,j) = m(i,j) / m_scaling[j];
    findRotation(mrot, m_rotation);
    canonical();
  }

  /// print for debugging and testing
  void prettyprint(std::ostream &os) const {
    if (m_flag & TrafoRotate)
      os << "Rotate: [" << deg(m_rotation[0]) << ", " << deg(m_rotation[1])
          << ", " << deg(m_rotation[2]) << "]"  << std::endl;
    if (sq(m_pivot) != 0)
      os << "Pivot: [" << m_pivot[0] << ", "
         << m_pivot[1] << ", "<< m_pivot[2] << "]" << std::endl;
    if (m_flag & TrafoScale)
      os << "Scale: [" << m_scaling[0] << ", " << m_scaling[1] << ", "
         << m_scaling[2] << "]" << std::endl;
    if (m_flag & TrafoReflect)
      os << "Reflect: [" << m_reflection[0] << ", " << m_reflection[1] << ", "
         << m_reflection[2] << "]" << std::endl;
    if (m_flag & TrafoTranslate)
      os << "Translate: [" << m_translation[0] << ", "
         << m_translation[1] << ", "<< m_translation[2] << "]" << std::endl;
  }

  /// create xml representation
  XmlElement toXml() const {
    XmlElement xe("Trafo3");
    if (m_flag & TrafoReflect)
      xe["reflection"] = str(m_reflection);
    if (m_flag & TrafoScale)
      xe["scaling"] = str(m_scaling);
    if (m_flag & TrafoRotate) {
      xe["rotation"] = str(m_rotation);
      if (sq(m_pivot) != 0)
        xe["pivot"] = str(m_pivot);
    }
    if (m_flag & TrafoTranslate)
      xe["translation"] = str(m_translation);
    return xe;
  }

  /// reconstruct from xml representation
  void fromXml(const XmlElement & xe) {
    assert(xe.name() == "Trafo3");
    identity();
    xe.fromAttribute("reflection", m_reflection);
    xe.fromAttribute("scaling", m_scaling);
    xe.fromAttribute("rotation", m_rotation);
    xe.fromAttribute("translation", m_translation);
    xe.fromAttribute("pivot", m_pivot);
    canonical();
  }

  /// utility : convert from homogeneous to physical coordinates
  static void h2p(const FloatType hp[], FloatType pp[]) {
    FloatType iw = FloatType(1.0) / hp[3];
    pp[0] = iw*hp[0];
    pp[1] = iw*hp[1];
    pp[2] = iw*hp[2];
  }

  /// utility : convert from homogeneous to physical coordinates
  static SVector<3,FloatType> h2p(const SVector<4,FloatType> & hp) {
    SVector<3,FloatType> pp;
    h2p(hp.pointer(), pp.pointer());
    return pp;
  }

  /// utility : find any 3D unit vector perpendicular to a
  template <typename FloatT>
  static SVector<3,FloatT> perpendicular(const SVector<3,FloatT> &a) {
    FloatT ax = std::fabs(a[0]);
    FloatT ay = std::fabs(a[1]);
    FloatT az = std::fabs(a[2]);
    SVector<3,FloatT> b;
    if ((ax <= ay) and (ax <= az))
      b[0] = 1;
    else if ((ay <= ax) and (ay <= az))
      b[1] = 1;
    else
      b[2] = 1;
    b -= (dot(b,a)/sq(a)) * a;
    normalize(b);
    return b;
  }

  /// utility : generate reflection
  template <typename VectorType, class MatrixType>
  static void reflectionMatrix(const VectorType & rfl, MatrixType & m) {
    unity(m);
    for (int j=0; j<3; ++j)
      for (int i=0; i<3; ++i)
        m(i,j) -= 2*rfl[i]*rfl[j];
  }

  /// utility : generate scaling
  template <typename VectorType, class MatrixType>
  static void scalingMatrix(const VectorType & x, MatrixType & m) {
    unity(m);
    for (int j=0; j<3; ++j)
      m(j,j) = x[j];
  }

  /// utility : generate rotation about first coordinate axis
  template <typename FType, class MatrixType>
  static void xRotationMatrix(FType phi, MatrixType & m) {
    unity(m);
    FType s, c;
    sincosine(phi, s, c);
    m(1,1) = m(2,2) = c;
    m(1,2) = -s;
    m(2,1) = +s;
  }

  /// utility : generate rotation about first coordinate axis
  static SMatrix<3,3,FloatType> xRotationMatrix(FloatType phi) {
    SMatrix<3,3,FloatType> m;
    TrafoTpl<FloatType>::xRotationMatrix(phi, m);
    return m;
  }

  /// utility : generate rotation about second coordinate axis
  template <typename FType, class MatrixType>
  static void yRotationMatrix(FType phi, MatrixType & m) {
    unity(m);
    FType s, c;
    sincosine(phi, s, c);
    m(0,0) = m(2,2) = c;
    m(0,2) = +s;
    m(2,0) = -s;
  }

  /// utility : generate rotation about second coordinate axis
  static SMatrix<3,3,FloatType> yRotationMatrix(FloatType phi) {
    SMatrix<3,3,FloatType> m;
    TrafoTpl<FloatType>::yRotationMatrix(phi, m);
    return m;
  }

  /// utility : generate rotation about third coordinate axis
  template <typename FType, class MatrixType>
  static void zRotationMatrix(FType phi, MatrixType & m) {
    unity(m);
    FType s, c;
    sincosine(phi, s, c);
    m(0,0) = m(1,1) = c;
    m(0,1) = -s;
    m(1,0) = +s;
  }

  /// utility : generate rotation about third coordinate axis
  static SMatrix<3,3,FloatType> zRotationMatrix(FloatType phi) {
    SMatrix<3,3,FloatType> m;
    TrafoTpl<FloatType>::zRotationMatrix(phi, m);
    return m;
  }

  /// utility : find inverse transformation using QR factorization
  static void inverse(const TrafoMtx & m, TrafoMtx & mi) {
    SMatrix<4,4,FloatType> qrf(m);
    FloatType tau[4];
    qr<4,4>(qrf.pointer(), tau);
    unity(mi);
    for (int i=0; i<4; ++i)
      qrsolve<4,4>(qrf.pointer(), tau, mi.colpointer(i));
  }

  /// utility : shift transformation to a given pivot point
  template <class VectorType, class MatrixType>
  static void shiftPivot(const VectorType &pivot, MatrixType &m) {
    MatrixType tpre, tpost;
    tpre = tpost = MatrixType::identity();
    for (int k=0; k<3; ++k) {
      tpre(k,3) = -pivot[k];
      tpost(k,3) = pivot[k];
    }
    m = tpost * m * tpre;
  }

  /// utility : shift by means of pretransform
  template <class MatrixType>
  static void shiftTrafo(const MatrixType &tp, MatrixType &m) {
    MatrixType tpm;
    TrafoTpl<FloatType>::inverse( tp, tpm );
    m = tp * m * tpm;
  }

  /// utility : apply affine transformation to 3D point
  template <class VectorType, class MatrixType>
  attr_always_inline static force_inline void transformPoint(const MatrixType & m, VectorType & p)  {
    VectorType t(p);
    p[0] = m(0,0)*t[0] + m(0,1)*t[1] + m(0,2)*t[2] + m(0,3);
    p[1] = m(1,0)*t[0] + m(1,1)*t[1] + m(1,2)*t[2] + m(1,3);
    p[2] = m(2,0)*t[0] + m(2,1)*t[1] + m(2,2)*t[2] + m(2,3);
    // typename VectorType::value_type wgt;
    // wgt  = m(3,0)*t[0] + m(3,1)*t[1] + m(3,2)*t[2] + m(3,3);
    // p *= 1.0 / wgt;
  }

  /// utility : apply affine transformation to 3D point
  template <class VectorType, class MatrixType>
  attr_always_inline static force_inline void transformPoint(const MatrixType & m, const VectorType &t, VectorType &p)  {
    p[0] = m(0,0)*t[0] + m(0,1)*t[1] + m(0,2)*t[2] + m(0,3);
    p[1] = m(1,0)*t[0] + m(1,1)*t[1] + m(1,2)*t[2] + m(1,3);
    p[2] = m(2,0)*t[0] + m(2,1)*t[1] + m(2,2)*t[2] + m(2,3);
    // typename VectorType::value_type wgt;
    // wgt  = m(3,0)*t[0] + m(3,1)*t[1] + m(3,2)*t[2] + m(3,3);
    // p *= 1.0 / wgt;
  }

  /// utility : apply affine transformation to 3D direction
  template <class VectorType, class MatrixType>
  attr_always_inline static force_inline void transformDirection(const MatrixType & m, VectorType & p)  {
    VectorType t(p);
    p[0] = m(0,0)*t[0] + m(0,1)*t[1] + m(0,2)*t[2];
    p[1] = m(1,0)*t[0] + m(1,1)*t[1] + m(1,2)*t[2];
    p[2] = m(2,0)*t[0] + m(2,1)*t[1] + m(2,2)*t[2];
    // typename VectorType::value_type wgt;
    // wgt  = m(3,0)*t[0] + m(3,1)*t[1] + m(3,2)*t[2];
    // p *= 1.0 / wgt;
  }

  /// utility : apply affine transformation to 3D direction
  template <class VectorType, class MatrixType>
  attr_always_inline static force_inline void transformDirection(const MatrixType & m,
                                 const VectorType & t, VectorType & p)  {
    p[0] = m(0,0)*t[0] + m(0,1)*t[1] + m(0,2)*t[2];
    p[1] = m(1,0)*t[0] + m(1,1)*t[1] + m(1,2)*t[2];
    p[2] = m(2,0)*t[0] + m(2,1)*t[1] + m(2,2)*t[2];
    // typename VectorType::value_type wgt;
    // wgt  = m(3,0)*t[0] + m(3,1)*t[1] + m(3,2)*t[2];
    // p *= 1.0 / wgt;
  }


  /// utility : apply affine transformation to 6D point (force/moment pair)
  template <class FloatT, class MatrixType>
  static void transformPoint6D(const MatrixType & m, SVector<6,FloatT> & p) {
    SVector<6,FloatT> t(p);
    p[0] = m(0,0)*t[0] + m(0,1)*t[1] + m(0,2)*t[2] + m(0,3);
    p[1] = m(1,0)*t[0] + m(1,1)*t[1] + m(1,2)*t[2] + m(1,3);
    p[2] = m(2,0)*t[0] + m(2,1)*t[1] + m(2,2)*t[2] + m(2,3);
    p[3] = m(0,0)*t[3] + m(0,1)*t[4] + m(0,2)*t[5] + m(0,3);
    p[4] = m(1,0)*t[3] + m(1,1)*t[4] + m(1,2)*t[5] + m(1,3);
    p[5] = m(2,0)*t[3] + m(2,1)*t[4] + m(2,2)*t[5] + m(2,3);
  }

  /// utility : apply affine transformation to list of 3D points
  template <class MatrixType, class PtList>
  static void transformList(const MatrixType & m, PtList & pts) {
    const int n = pts.size();
    for (int i=0; i<n; ++i)
      transformPoint(m, pts[i]);
  }

  /// utility : apply affine transformation to list of 3D vectors
  template <class MatrixType, class PtList>
  static void transformDirections(const MatrixType & m, PtList & pts) {
    const int n = pts.size();
    for (int i=0; i<n; ++i)
      transformDirection(m, pts[i]);
  }

  /// utility : apply affine transformation to list of 6D points
  template <class MatrixType, typename FloatT>
  static void transformList6D(const MatrixType & m, PointList<6,FloatT> & pts) {
    const int n = pts.size();
    for (int i=0; i<n; ++i)
      transformPoint6D(m, pts[i]);
  }

  /** Find rotation angles from rotation matrix. Since the extraction of
  Euler angles is under-determined when the absolute value of the sine of the
  middle rotation is one, it is possible to pass a hint for the third rotation
  angle which will be used in that particular case (r[2] = rzhint). **/
  template <class MatrixType, class VectorType>
  static void findRotation(const MatrixType & m, VectorType & r,
                           FloatType rzhint = 0.0f) {
    r[1] = std::asin( -m(2,0) );
    if (std::fabs(m(2,0)) < 1) {
      // if |sin(r[1])| != 1, then cos(r[1]) != 0, and the below is well-defined
      r[0] = std::atan2( m(2,1), m(2,2) );
      r[2] = std::atan2( m(1,0), m(0,0) );
    } else if (m(2,0) == -1) {
      // sin(r[1]) == 1
      // only the difference (rx - rz) is determined; convention rz = 0
      r[2] = rzhint;
      r[0] = rzhint + std::atan2(m(0,1), m(0,2));
    } else {
      // sin(r[1]) == -1
      r[2] = rzhint;
      r[0] = -rzhint + std::atan2(m(0,1), m(0,2));
    }
  }

  /// Identify rotation angles for the sequence RZ-RY-RX
  template <class MatrixType, class VectorType>
  static void findRotationYPR(const MatrixType & m, VectorType & r,
                           FloatType rzhint = 0.0f)
  {
    findRotation(m.transposed(), r, rzhint);
    r = -r;
  }

  /// utility : Rx-Ry-Rz rotation angles from quaternion
  template <class VectorType>
  static void quat2rxyz(const VectorType & q, VectorType & rxyz) {
    rxyz[0] = std::atan2( 2*(q[0]*q[1] + q[2]*q[3]), 1 - 2*(sq(q[1]) + sq(q[2])) );
    rxyz[1] = std::asin( 2*(q[0]*q[2] - q[3]*q[1]) );
    rxyz[2] = std::atan2( 2*(q[0]*q[3] + q[1]*q[2]), 1 - 2*(sq(q[2]) + sq(q[3])) );
  }

  /// utility : 3x3 rotation matrix from axis and angles
  template <class VectorType, class MatrixType>
  static void axis2matrix(FloatType phi, const VectorType & ax,
                          MatrixType & m)
  {
    FloatType cp, sp;
    sincosine(phi, sp, cp);
    FloatType ux = ax[0];
    FloatType uy = ax[1];
    FloatType uz = ax[2];

    m(0,0) = cp + sq(ux)*(1 - cp);
    m(1,0) = uy*ux*(1 - cp) + uz*sp;
    m(2,0) = uz*ux*(1 - cp) - uy*sp;

    m(0,1) = ux*uy*(1 - cp) - uz*sp;
    m(1,1) = cp + sq(uy)*(1 - cp);
    m(2,1) = uz*uy*(1 - cp) + ux*sp;

    m(0,2) = ux*uz*(1 - cp) + uy*sp;
    m(1,2) = uy*uz*(1 - cp) - ux*sp;
    m(2,2) = cp + sq(uz)*(1 - cp);
  }

  /// utility : identify rotation axis and angle from 3x3 rotation matrix.
  /// returns a positive angle in (0,pi), will swap direction of the axis to
  /// produce the opposite rotation
  template <class VectorType, class MatrixType>
  static FloatType findAxis(const MatrixType & m, VectorType & ax)
  {
    // will fail if m is not a rotation matrix
    ax[0] = m(2,1) - m(1,2);
    ax[1] = m(0,2) - m(2,0);
    ax[2] = m(1,0) - m(0,1);
    FloatType sp2 = norm(ax);
    if (sp2 > 0) {
      // sin(phi) > 0, phi != 0, pi, ...
      ax /= sp2;
      return std::asin(clamp(0.5*sp2, 0.0, 1.0));
    } else {
      // sin(phi) = 0, can be phi = 0 or phi = +/- PI
      FloatType cp = 0.5*(m(0,0) + m(1,1) + m(2,2) - 1);
      if (cp < 0) {
        // phi = PI, find axis component magnitudes
        ax[0] = std::sqrt(clamp(0.5*(m(0,0) + 1), 0.0, 1.0));
        ax[1] = std::sqrt(clamp(0.5*(m(1,1) + 1), 0.0, 1.0));
        ax[2] = std::sqrt(clamp(0.5*(m(2,2) + 1), 0.0, 1.0));
        // find canonical signs, ax[0] > 0
        ax[1] *= -sign(m(1,0));
        ax[2] *= -sign(m(2,0));
        return PI;
      } else {
        // phi = 0, rotation axis is arbitrary
        ax[0] = 1.0;
        ax[1] = 0.0;
        ax[2] = 0.0;
        return 0.0;
      }
    }
  }

  /// angular interpolation between rotations
  static void angularIpol(const SMatrix<3,3,FloatType> & m0,
                          const SMatrix<3,3,FloatType> & m1,
                          FloatType t, SMatrix<3,3,FloatType> & mt)
  {
    // transition m0 -> m1
    SMatrix<3,3,FloatType> T = m1 * m0.transposed();
    if (T != SMatrix<3,3,FloatType>::identity()) {
      SVector<3,FloatType> axs;
      FloatType phi = findAxis(T, axs);
      axis2matrix(t*phi, axs, T);
      mt = T*m0;
    } else {
      mt = m1;
    }
  }

  /// utility : 3x3 rotation matrix which turns a into b
  template <class MatrixType>
  static void fan2matrix(const SVector<3,FloatType> & a,
                         const SVector<3,FloatType> & b,
                         MatrixType & m)
  {
    assert(sq(a) > 0);
    assert(sq(b) > 0);
    const SVector<3,FloatType> an = a.normalized();
    const SVector<3,FloatType> bn = b.normalized();
    SVector<3,FloatType> rax = cross(an, bn);
    if (sq(rax) > 0) {
      FloatType sphi = normalize(rax);
      axis2matrix(std::asin(sphi), rax, m);
    } else if ( dot(an,bn) < 0 ) {
      // a and b point in opposite directions since |cross(an,bn)| == 0
      SVector<3,FloatType> c = perpendicular(a);
      axis2matrix(FloatType(M_PI), c, m);
    } else {
      unity(m);
    }
  }

  /// utility : standard intrinsic roll-pitch-yaw sequence
  template <class MatrixType>
  static void rpyMatrix(const FloatType &psi, const FloatType &theta,
                        const FloatType &phi, MatrixType &m)
  {
    unity(m);
    xRotationMatrix(psi, m);
    MatrixType tmp;
    unity(tmp);
    yRotationMatrix(theta, tmp);
    m = tmp*m;
    zRotationMatrix(phi, tmp);
    m = tmp*m;
  }

  /// utility : standard intrinsic yaw-pitch-roll sequence (transpose of RPY)
  template <class MatrixType>
  static void yprMatrix(const FloatType &psi, const FloatType &theta,
                        const FloatType &phi, MatrixType &m)
  {
    unity(m);
    zRotationMatrix(psi, m);
    MatrixType tmp;
    unity(tmp);
    yRotationMatrix(theta, tmp);
    m = tmp*m;
    xRotationMatrix(phi, tmp);
    m = tmp*m;
  }

  /// utility : standard intrinsic z-x-z sequence
  template <class MatrixType>
  static void zxzMatrix(const FloatType &alpha, const FloatType &beta,
                        const FloatType &gamma, MatrixType &m)
  {
    unity(m);
    zRotationMatrix(alpha, m);
    MatrixType tmp;
    unity(tmp);
    yRotationMatrix(beta, tmp);
    m = tmp*m;
    zRotationMatrix(gamma, tmp);
    m = tmp*m;
  }

  /// utility: extract rotation block out of a 4x4 transformation
  template <typename FType, uint M>
  static SMatrix<3,3,FType> extractRotation(const SMatrix<M,4,FType> &tfm)
  {
    BOOST_STATIC_ASSERT(M > 2);
    SMatrix<3,3,FType> roma;
    std::copy_n(tfm.colpointer(0), 3, roma.colpointer(0));
    std::copy_n(tfm.colpointer(1), 3, roma.colpointer(1));
    std::copy_n(tfm.colpointer(2), 3, roma.colpointer(2));
    return roma;
  }

  /// utility: insert 3x3 rotation into a Mx4 transformation
  template <typename FType, uint M>
  static void injectRotation(const SMatrix<3,3,FType> &roma,
                             SMatrix<M,4,FType> &tfm)
  {
    BOOST_STATIC_ASSERT(M > 2);
    std::copy_n(roma.colpointer(0), 3, tfm.colpointer(0));
    std::copy_n(roma.colpointer(1), 3, tfm.colpointer(1));
    std::copy_n(roma.colpointer(2), 3, tfm.colpointer(2));
  }

protected:

  /// set flag according to values
  void canonical() {
    m_flag = TrafoNone;
    if (sq(m_reflection) != 0)
      m_flag |= TrafoReflect;
    if (m_scaling[0] != 1 or m_scaling[1] != 1 or m_scaling[2] != 1)
      m_flag |= TrafoScale;
    if (sq(m_rotation) != 0)
      m_flag |= TrafoRotate;
    if (sq(m_translation) != 0)
      m_flag |= TrafoTranslate;
  }

protected:

  /// plane about which to mirror
  TrafoVct m_reflection;

  /// scaling coefficients
  TrafoVct m_scaling;

  /// rotation angles
  TrafoVct m_rotation;

  /// pivot point for rotation
  TrafoVct m_pivot;

  /// translation vector
  TrafoVct m_translation;

  /// keep track of what should be applied
  uint m_flag;
};

template <typename FloatType>
std::ostream & operator<< (std::ostream &os, const TrafoTpl<FloatType> &tp)
{
  os << "Rotation " << tp.rotation() << std::endl;
  os << "Translation " << tp.translation() << std::endl;
  os << "Scaling " << tp.scaling() << std::endl;
  return os;
}


#endif // TRANSFORMATION_H
