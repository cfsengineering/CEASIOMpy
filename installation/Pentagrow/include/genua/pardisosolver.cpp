
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
 
#include "pardisosolver.h"
#include "timing.h"
#include "configparser.h"
#include "xcept.h"
#include "sysinfo.h"
#include "dbprint.h"

#include <mkl_pardiso.h>
#include <mkl_service.h>
#include <mkl_spblas.h>

PardisoBase::PardisoBase()
{
  init();
}

PardisoBase::PardisoBase(MatrixType t)
{
  init();
  setDefaults(t);
}

void PardisoBase::init()
{
  // by default, print messages in debug mode
#ifndef NDEBUG
  m_msglevel = 1;
#else
  m_msglevel = 0;
#endif

  m_nrhs = 1;
  memset(m_pt, 0, sizeof(m_pt));
  memset(m_iparm, 0, sizeof(m_iparm));
}

PardisoBase::~PardisoBase()
{
  release();
}

bool PardisoBase::isSymmetric(MatrixType t)
{
  switch (t) {
  case ComplexHermitianIndefinite:
  case RealSymmetricIndefinite:
  case RealPositiveDefinite:
    return true;
  case UnknownMatrixType:
  case RealStructurallySymmetric:
  case ComplexStructurallySymmetric:
    return false;
  case ComplexPositiveDefinite:
  case ComplexSymmetric:
    return true;
  case RealUnsymmetric:
  case ComplexUnsymmetric:
    return false;
  }
  assert(!"Should never be here.");
  return false;
}

void PardisoBase::setDefaults(MatrixType mtyp)
{
  if (mtyp == UnknownMatrixType)
    throw Error("Attempting to initialize PARDISO solver"
                " with unknown matrix type.");

  m_mtyp = mtyp;
  pardisoinit(m_pt, &m_mtyp, m_iparm);

  setOption(35, 1); // zero-based indexing

  // use two-level factorization when there are more than 8 threads
  if ( SysInfo::nthread() > 8 )
    setOption(24, 1);

  // debugging options
#ifndef NDEBUG
  setOption(27, 1); // matrix checker on
#endif
}

PardisoBase::MatrixType PardisoBase::pardisoMatrixType(uint flags)
{
  switch (flags) {

  case SpMatrixFlag::ComplexHermIndefinite:
    return PardisoBase::ComplexHermitianIndefinite;

  case SpMatrixFlag::RealSymIndefinite:
    return PardisoBase::RealSymmetricIndefinite;

  case SpMatrixFlag::RealStructuralSym:
    return PardisoBase::RealStructurallySymmetric;

  case SpMatrixFlag::RealPositiveDefinite:
    return PardisoBase::RealPositiveDefinite;

  case SpMatrixFlag::ComplexStructuralSym:
    return PardisoBase::ComplexStructurallySymmetric;

  case SpMatrixFlag::ComplexPositiveDefinite:
    return PardisoBase::ComplexPositiveDefinite;

  case SpMatrixFlag::ComplexSymmetric:
    return PardisoBase::ComplexSymmetric;

  case SpMatrixFlag::RealUnsymmetric:
    return PardisoBase::RealUnsymmetric;

  case SpMatrixFlag::ComplexUnsymmetric:
    return PardisoBase::ComplexUnsymmetric;

  default:
    return PardisoBase::UnknownMatrixType;
  }
}

void PardisoBase::configureBase(const ConfigParser &cfg)
{
  // use parallel metis? (default true)
  if ( cfg.getBool("PardisoParallelMetis", true) )
    setOption(2, 3);

  // print detailed info
  if ( cfg.getBool("PardisoVerbose", false) )
    m_msglevel = 1;
  else
    m_msglevel = 0;

  // check input matrix
  if ( cfg.getBool("PardisoCheckMatrix", false) )
    setOption(27, 1);
  else
    setOption(27, 0);

  // use two-level factorization ? (true/false)
  int twoLevel = cfg.getBool("PardisoTwoLevel", true) ? 1 : 0;
  setOption(24, twoLevel);

  // -log10 of the perturbation of pivots
  if (cfg.hasKey("PardisoLogPivPerturb") or
      cfg.hasKey("PardisoEpsLim") ) {
    int defaultValue = (m_mtyp >= RealUnsymmetric) ? 13 : 8;
    int epsexp = defaultValue;
    if (cfg.hasKey("PardisoLogPivPerturb"))
      epsexp = cfg.getInt("PardisoLogPivPerturb", defaultValue);
    else
      epsexp = cfg.getInt("PardisoEpsLim", defaultValue);
    setOption(10, epsexp);
    dbprint("[d] Pardiso pivot perturbation: ",
            std::pow(10.0, double(-epsexp)));
    setOption(10, epsexp);
  }

  // use LU-preconditioned iterative solution? (log10(tolerance))
  int option(0);
  int cgstol = cfg.getInt("PardisoIterativeSolve", 99);
  if (cgstol < 0) {
    option = -10 * cgstol + ( isSymmetric((MatrixType) m_mtyp) ? 2 : 1 );
    setOption(4, option);
  } else {
    setOption(4, 0);
  }
}

void PardisoBase::release()
{
  backend(-1, 0, (const int*) 0, (const int *) 0, (const void *) 0,
          (void *) 0, (void *) 0);
  mkl_free_buffers();
  init();
}

float PardisoBase::highwaterMemory() const
{
  float mbPeakSymb = 1e-3f * getOption(15);
  float mbSolve = 1e-3f * (getOption(16) + getOption(17));
  return std::max(mbPeakSymb, mbSolve);
}

void PardisoBase::backend(int phs, int nrows, const int *rowPtr,
                          const int *colIdx, const void *nzValues,
                          void *bptr, void *xptr)
{
  int maxfct = 1;  // number of factorizations to store
  int mnum = 1;    // index of factor to use
  int phase = phs; // factorization/solve phase

  int n = nrows;
  int status = 0;

  // default permutation
  int *pperm(0);
  if (phs > 0) {
    if (m_perm.size() != size_t(nrows)) {
      m_perm.allocate(nrows);
      for (int i=0; i<nrows; ++i)
        m_perm[i] = i+1;
    }
    pperm = m_perm.pointer();
  }

  pardiso(m_pt, &maxfct, &mnum, &m_mtyp, &phase, &n,
          const_cast<void*>( nzValues ),
          const_cast<int *>( rowPtr ),
          const_cast<int *>( colIdx ),
          pperm, &m_nrhs, &m_iparm[0], &m_msglevel, bptr, xptr,
      &status);

  bailout(status);
}

void PardisoBase::getDiagonal(void *padia, void *pfdia)
{
  if ( getOption(56) != 1 )
    throw Error("PardisoSolver: Option 56 must be set to 1 to use pardiso_getdiag().");

  MKL_INT ifact = 1;
  MKL_INT error = 0;
  pardiso_getdiag(m_pt, pfdia, padia, &ifact, &error);

  if (error != 0)
    throw Error("PardisoSolver: pardiso_getdiag() - error = "+str(error));
}

void PardisoBase::bailout(int error) const
{
  switch (error) {
  case -11:
    throw Error("PARDISO: Cannot read/write to PARDISO OOC data file.");
  case -10:
    throw Error("PARDISO: Cannot open temporary PARDISO OOC file.");
  case -9:
    throw Error("PARDISO: Not enogh memory for PARDISO OOC solver.");
  case -8:
    throw Error("PARDISO: 32bit integer overflow.");
  case -7:
    throw Error("PARDISO: Diagonal matrix is singular.");
  case -6:
    throw Error("PARDISO: Preordering failed.");
  case -5:
    throw Error("PARDISO: Internal error.");
  case -4:
    throw Error("PARDISO: Zero pivot.");
  case -3:
    throw Error("PARDISO: Reordering failed.");
  case -2:
    throw Error("PARDISO: Out of memory.");
  case -1:
    throw Error("PARDISO: Inconsistent input.");
  case 0:
    return;
  default:
    throw Error("PARDISO: Undocumented error code: "+str(error));
  }
}




