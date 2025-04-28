
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
 
#ifndef SURF_IGES124_H
#define SURF_IGES124_H

#include "igesentity.h"
#include <genua/smatrix.h>

/** IGES 124: Transformation matrix.

  \b Spec : IGES 5.3, page 142

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesTrafoMatrix : public IgesEntity
{
public:

  /// create undefined
  IgesTrafoMatrix() : IgesEntity(124) { rp(0,0)=rp(1,1)=rp(2,2)=1.0; }

  /// set pointer to rotation matrix and translation vector
  void setup(const double rot[], const double trans[]) {
    memcpy(rp.pointer(), rot, 9*sizeof(double));
    memcpy(tp.pointer(), trans, 3*sizeof(double));
  }

  /// access rotation matrix (column major)
  const double *rotation() const {return rp.pointer();}

  /// access translation vector
  const double *translation() const {return tp.pointer();}

  /// access rotation
  const double & rotation(uint i, uint j) const {return rp(i,j);}

  /// access translation
  const double & translation(uint i) const {return tp[i];}

  /// access rotation
  double & rotation(uint i, uint j) {return rp(i,j);}

  /// access translation
  double & translation(uint i) {return tp[i];}

  /// convert to 4x4 transformation matrix
  void toMatrix(Mtx44 & m) const {
    for (int j=0; j<3; ++j) {
      m(j,3) = tp[j];
      for (int i=0; i<3; ++i)
        m(i,j) = rp(i,j);
    }
    m(3,0) = m(3,1) = m(3,2) = 0.0;
    m(3,3) = 1.0;
  }

  /// convert to 3x4 transformation matrix
  void toMatrix(Mtx34 & m) const {
    for (int j=0; j<3; ++j) {
      m(j,3) = tp[j];
      for (int i=0; i<3; ++i)
        m(i,j) = rp(i,j);
    }
  }

  /// convert from 3x4 transformation matrix
  template <class MatrixType>
  void fromMatrix(const MatrixType & m) {
    for (int j=0; j<3; ++j) {
      tp[j] = m(j,3);
      for (int i=0; i<3; ++i)
        rp(i,j) = m(i,j);
    }
  }

  /// transform a single point
  Vct3 forward(const Vct3 & p) const {
    Vct3 t;
    t[0] = rp(0,0)*p[0] + rp(0,1)*p[1] + rp(0,2)*p[2] + tp[0];
    t[1] = rp(1,0)*p[0] + rp(1,1)*p[1] + rp(1,2)*p[2] + tp[1];
    t[2] = rp(2,0)*p[0] + rp(2,1)*p[1] + rp(2,2)*p[2] + tp[2];
    return t;
  }

  /// assemble definition
  void definition(IgesFile & file);

  /// fetch data from string, return number of parameter values used
  uint parse(const std::string & pds, const Indices & vpos);

public:

  /// rotation matrix
  SMatrix<3,3,double> rp;

  /// translation vector
  SVector<3,double> tp;
};

#endif // IGES124_H
