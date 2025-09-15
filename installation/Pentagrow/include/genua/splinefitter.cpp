
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

#include "splinefitter.h"
#include "splinebasis.h"
#include "dmatrix.h"
#include "ndarray.h"
#include "parallel_loop.h"
#include "xcept.h"
#include <eeigen/Core>
#include <eeigen/Sparse>
#include <eeigen/SparseLU>

typedef eeigen::SparseMatrix<Real, eeigen::ColMajor> SpMatrixType;
typedef eeigen::Matrix<Real, eeigen::Dynamic, eeigen::Dynamic> DenseType;
typedef eeigen::Map<const DenseType, eeigen::Aligned> DenseMap;
typedef eeigen::Triplet<Real, int> Triplet;
typedef std::vector<Triplet> TripletArray;

void SplineFitter::fitCubicCurve(const SplineBasis &basis, const Vector &up,
                                 const Vector &b, Vector &cp) const
{
  Matrix mb(b), mcp(b.size(), 1);
  fitCubicCurve(basis, up, mb, mcp);
  cp.allocate(mcp.nrows());
  memcpy(cp.pointer(), mcp.pointer(), mcp.size() * sizeof(Real));
}

void SplineFitter::fitCubicCurve(const SplineBasis &basis, const Vector &up,
                                 const Matrix &b, Matrix &cp) const
{
  const int P(3);
  const int np = up.size();

  // assemble coefficient matrix using triplets
  SpMatrixType a;
  {
    TripletArray triplets;
    triplets.resize((P + 1) * np);
    for (int i = 0; i < np; ++i)
    {
      SVector<P + 1> bp;
      int span = int(basis.eval(up[i], bp)) - P;
      for (int k = 0; k < (P + 1); ++k)
        triplets[(P + 1) * i + k] = Triplet(i, span + k, bp[k]);
    }
    a.setFromTriplets(triplets.begin(), triplets.end());
  }
  a.makeCompressed();

  // solve for control points
  assert(b.nrows() == uint(np));
  eeigen::SparseLU<SpMatrixType> solver;
  solver.compute(a);
  DenseMap mb(b.pointer(), b.nrows(), b.ncols());
  DenseType mx = solver.solve(mb);

  cp.allocate(np, b.ncols());
  memcpy(cp.pointer(), mx.data(), cp.size() * sizeof(Real));
}

void SplineFitter::fitBicubicSurface(const SplineBasis &ubasis,
                                     const Vector &up,
                                     const SplineBasis &vbasis,
                                     const Vector &vp,
                                     const SplineFitter::Array3D &b,
                                     SplineFitter::Array3D &cp) const
{
  const int P(3);
  if (b.size(0) != up.size())
    throw Error("First dimension of point data must match u-parameter count.");
  if (b.size(1) != vp.size())
    throw Error("Second dimension of point data must match v-parameter count.");

  // dimension of point data
  const int nrhs = b.size(2);
  const int nu = up.size();
  const int nv = vp.size();

  SpMatrixType a;
  {
    TripletArray triplets;
    triplets.reserve(size_t((P + 1) * nu) * size_t((P + 1) * nv));
    SVector<P + 1> bu, bv;
    for (int j = 0; j < nv; ++j)
    {
      int vspan = int(vbasis.eval(vp[j], bv)) - P;
      for (int i = 0; i < nu; ++i)
      {
        int row = j * nu + i;
        int uspan = int(ubasis.eval(up[i], bu)) - P;
        for (int kv = 0; kv < (P + 1); ++kv)
        {
          for (int ku = 0; ku < (P + 1); ++ku)
          {
            int col = (vspan + kv) * nu + (uspan + ku);
            triplets.push_back(Triplet(row, col, bu[ku] * bv[kv]));
          }
        }
      }
    }
    a.setFromTriplets(triplets.begin(), triplets.end());
  }
  a.makeCompressed();

  // because the up-index is the fastest running, the memory layout of
  // b(i,j,k) is already the same as a the required mb(i+j*nu,k)
  DenseMap mb(b.pointer(), nu * nv, nrhs);

  eeigen::SparseLU<SpMatrixType> solver;
  solver.compute(a);
  DenseType mx = solver.solve(mb);

  cp.resize(nu, nv, nrhs);
  memcpy(cp.pointer(), mx.data(), cp.size() * sizeof(Real));
}
