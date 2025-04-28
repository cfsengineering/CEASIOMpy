
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
 

// This is the small part of MxMesh which depends on LAPACK
// and hence requires that (fortran!) library. In order to avoid this link-time
// dependency for applications which do not need this but only MxMesh, it is
// pulled out into its own object file.

#include "mxmeshdeform.h"
#include "lu.h"
#include <string>

using namespace std;

void MxMeshDeform::buildSpline()
{
  const int nstep = ntime();
  Vector t(bptime);
  t -= t.front();
  t *= 1.0 / t.back();
  spl.init(3, t);

  // solve banded system for control points
  Vct4 b;
  const int ku(3);
  const int kl(3);
  Matrix bcf(2*kl+ku+1, nstep);
  for (int i=0; i<nstep; ++i) {
    int span = spl.eval(t[i], b);
    for (int j=0; j<4; j++) {
      int col = span-3+j;
      int row = kl+ku+i-col;
      bcf(row, col) = b[j];
    }
  }

  // build right-hand side
  const int nm = bpcoef.nrows();
  cpcoef.resize(nstep, nm);
  for (int i=0; i<nm; ++i)
    for (int j=0; j<nstep; ++j)
      cpcoef(j,i) = bpcoef(i,j);

  // solve banded system
  int stat = banded_lu_solve(kl, ku, bcf, cpcoef);
  if (stat != 0) {
    string msg("Lapack: Banded LU solve failed ");
    msg += "in MxMeshDeform::buildSpline ";
    if (stat < 0 and -stat-1 < 10) {
      const char *args[] = {"N", "KL", "KU", "NRHS", "AB", "LDAB",
        "IPIV", "B", "LDB", "INFO"};
        msg += "Argument '" + string(args[-stat-1]) + "' is illegal.";
    } else {
      msg += "Interpolation problem is singular in equation " + str(stat);
    }
    throw Error(msg);
  }
}

