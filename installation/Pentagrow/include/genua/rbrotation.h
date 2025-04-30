
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
 
#ifndef GENUA_RBROTATION_H
#define GENUA_RBROTATION_H

#include "defines.h"
#include "trigo.h"

/** Rigid-body rotation
 *
 * Computes the rigid-body rotation matrix for three attitude angles. This
 * form corresponds to flight mechanics conventions.
 *
 * @param x[0] Roll angle phi
 * @param x[1] Pitch angle theta
 * @param x[2] Yaw angle psi
 * @param r    3x3 Rotation matrix stored in column-major order
 *
 *
 */
inline void rbrotation(const Real x[], Real r[])
{
  // extract angles
  // x[0] = phi, roll
  // x[1] = theta, pitch
  // x[2] = psi, yaw
  Real cphi, sphi, ctheta, stheta, cpsi, spsi;
  sincosine(x[0], sphi, cphi);
  sincosine(x[1], stheta, ctheta);
  sincosine(x[2], spsi, cpsi);

#undef R
#define R(i,j)  r[3*(j)+(i)]

  // rotation matrix body-to-earth coordinates
  R(0,0) = cpsi*ctheta;
  R(0,1) = sphi*stheta*cpsi - cphi*spsi;
  R(0,2) = cpsi*stheta*cphi + spsi*sphi;

  R(1,0) = spsi*ctheta;
  R(1,1) = spsi*stheta*sphi + cpsi*cphi;
  R(1,2) = spsi*stheta*cphi - cpsi*sphi;

  R(2,0) = -stheta;
  R(2,1) = ctheta*sphi;
  R(2,2) = ctheta*cphi;

#undef R
}

/** Rigid-body rotation and time derivatives.
 *
 * Computes the rigid-body rotation matrix for three attitude angles. This
 * version computes both the rotation matrices and (optionally) the first and
 * second time derivatives.
 *
 * @param x[0] Roll angle phi
 * @param x[1] Pitch angle theta
 * @param x[2] Yaw angle psi
 * @param xdot First time derivatives of the attitude angles, only referenced
 *             if rdot != nullptr
 * @param xddot Second time derivatives of the attitude angles, only referenced
 *             if rddot != nullptr
 * @param r    3x3 Rotation matrix stored in column-major order
 * @param rdot First time derivative of rotation matrix (can be nullptr)
 * @param rdot Second time derivative of rotation matrix (can be nullptr)
 *
 */
inline void rbrotation(const Real x[],
                       const Real xdot[],
                       const Real xddot[],
                       Real r[],
                       Real rdot[],
                       Real rddot[])
{
  // extract angles
  // x[0] = phi, roll
  // x[1] = theta, pitch
  // x[2] = psi, yaw
  Real cphi, sphi, ctheta, stheta, cpsi, spsi;
  sincosine(x[0], sphi, cphi);
  sincosine(x[1], stheta, ctheta);
  sincosine(x[2], spsi, cpsi);

#undef R
#define R(i,j)  r[3*(j)+(i)]

  // rotation matrix body-to-earth coordinates
  R(0,0) = cpsi*ctheta;
  R(0,1) = sphi*stheta*cpsi - cphi*spsi;
  R(0,2) = cpsi*stheta*cphi + spsi*sphi;

  R(1,0) = spsi*ctheta;
  R(1,1) = spsi*stheta*sphi + cpsi*cphi;
  R(1,2) = spsi*stheta*cphi - cpsi*sphi;

  R(2,0) = -stheta;
  R(2,1) = ctheta*sphi;
  R(2,2) = ctheta*cphi;

#undef R

  if (xdot != 0 and rdot != 0) {

    Real dphi = xdot[0];
    Real dtheta = xdot[1];
    Real dpsi = xdot[2];

#undef Rd
#define Rd(i,j)  rdot[3*(j)+(i)]

    Rd(0,0) = -cpsi*dtheta*stheta-ctheta*dpsi*spsi;
    Rd(0,1) = -dpsi*sphi*spsi*stheta+dphi*cphi*cpsi*stheta+dtheta*sphi*cpsi*ctheta+dphi*
              sphi*spsi-dpsi*cphi*cpsi;
    Rd(0,2) = -cphi*dpsi*spsi*stheta-cpsi*dphi*sphi*stheta+cphi*dphi*spsi
              +cpsi*dpsi*sphi+cphi*cpsi*ctheta*dtheta;

    Rd(1,0) = cpsi*ctheta*dpsi-dtheta*spsi*stheta;
    Rd(1,1) = cphi*dphi*spsi*stheta+cpsi*dpsi*sphi*stheta+ctheta*dtheta*sphi*spsi
              -cphi*dpsi*spsi-cpsi*dphi*sphi;
    Rd(1,2) = -dphi*sphi*spsi*stheta+cphi*cpsi*dpsi*stheta+dpsi*sphi*spsi
              +cphi*ctheta*dtheta*spsi-cphi*cpsi*dphi;

    Rd(2,0) = -ctheta*dtheta;
    Rd(2,1) = cphi*ctheta*dphi-dtheta*sphi*stheta;
    Rd(2,2) = -cphi*dtheta*stheta-ctheta*dphi*sphi;


#undef Rd

  }

  if (xddot != 0 and rddot != 0) {

    Real dphi(0.0), dtheta(0.0), dpsi(0.0);
    if (xdot != 0) {
      dphi = xdot[0];
      dtheta = xdot[1];
      dpsi = xdot[2];
    }

    Real ddphi = xddot[0];
    Real ddtheta = xddot[1];
    Real ddpsi = xddot[2];

#undef Rdd
#define Rdd(i,j)  rddot[3*(j)+(i)]

    Rdd(0,0) = 2*dpsi*dtheta*spsi*stheta-cpsi*ddtheta*stheta-ctheta*ddpsi*spsi
               -cpsi*ctheta*sq(dtheta)-cpsi*ctheta*sq(dpsi);
    Rdd(0,1) = sphi*cpsi*ctheta*ddtheta-sphi*cpsi*stheta*sq(dtheta)
               -2*sphi*spsi*dpsi*ctheta*dtheta+2*cphi*dphi*cpsi*ctheta*dtheta
               -sphi*spsi*ddpsi*stheta-sphi*cpsi*sq(dpsi)*stheta
               -2*cphi*dphi*spsi*dpsi*stheta+cphi*ddphi*cpsi*stheta
               -sphi*sq(dphi)*cpsi*stheta-cphi*cpsi*ddpsi+cphi*spsi*sq(dpsi)
               +2*sphi*dphi*cpsi*dpsi+sphi*ddphi*spsi+cphi*sq(dphi)*spsi;
    Rdd(0,2) = 2*dphi*dpsi*sphi*spsi*stheta-cphi*ddpsi*spsi*stheta
               -cpsi*ddphi*sphi*stheta
               -cphi*cpsi*sq(dtheta)*stheta
               -cphi*cpsi*sq(dpsi)*stheta
               -cphi*cpsi*sq(dphi)*stheta-sq(dpsi)*sphi*spsi
               -sq(dphi)*sphi*spsi
               -2*cphi*ctheta*dpsi*dtheta*spsi
               +cphi*ddphi*spsi
               -2*cpsi*ctheta*dphi*dtheta*sphi
               +cpsi*ddpsi*sphi+2*cphi*cpsi*dphi*dpsi
               +cphi*cpsi*ctheta*ddtheta;

    Rdd(1,0) = -ddtheta*spsi*stheta-2*cpsi*dpsi*dtheta*stheta-ctheta*sq(dtheta)*spsi
               -ctheta*sq(dpsi)*spsi+cpsi*ctheta*ddpsi;
    Rdd(1,1) = -sq(dtheta)*sphi*spsi*stheta-sq(dpsi)*sphi*spsi*stheta
               -sq(dphi)*sphi*spsi*stheta
               +cphi*ddphi*spsi*stheta
               +cpsi*ddpsi*sphi*stheta
               +2*cphi*cpsi*dphi*dpsi*stheta
               +2*dphi*dpsi*sphi*spsi
               +ctheta*ddtheta*sphi*spsi
               +2*cphi*ctheta*dphi*dtheta*spsi
               -cphi*ddpsi*spsi
               +2*cpsi*ctheta*dpsi*dtheta*sphi
               -cpsi*ddphi*sphi-cphi*cpsi*sq(dpsi)
               -cphi*cpsi*sq(dphi);
    Rdd(1,2) = -ddphi*sphi*spsi*stheta-cphi*sq(dtheta)*spsi*stheta
               -cphi*sq(dpsi)*spsi*stheta
               -cphi*sq(dphi)*spsi*stheta
               -2*cpsi*dphi*dpsi*sphi*stheta
               +cphi*cpsi*ddpsi*stheta
               -2*ctheta*dphi*dtheta*sphi*spsi+ddpsi*sphi*spsi
               +2*cphi*dphi*dpsi*spsi+cphi*ctheta*ddtheta*spsi
               +cpsi*sq(dpsi)*sphi+cpsi*sq(dphi)*sphi
               +2*cphi*cpsi*ctheta*dpsi*dtheta-cphi*cpsi*ddphi;

    Rdd(2,0) = sq(dtheta)*stheta-ctheta*ddtheta;
    Rdd(2,1) = -ddtheta*sphi*stheta-2*cphi*dphi*dtheta*stheta-ctheta*sq(dtheta)*sphi
               -ctheta*sq(dphi)*sphi+cphi*ctheta*ddphi;
    Rdd(2,2) = 2*dphi*dtheta*sphi*stheta-cphi*ddtheta*stheta-ctheta*ddphi*sphi
               -cphi*ctheta*sq(dtheta)-cphi*ctheta*sq(dphi);

#undef Rdd

  }
}

#endif // RBROTATION_H
