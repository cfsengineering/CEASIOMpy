
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
 
#include "spoolessolver.h"
#include "xcept.h"
#include "connectmap.h"
#include "sysinfo.h"
#include "configparser.h"
#include "dbprint.h"
#include <cstdio>

SpoolesBase::SpoolesBase(Symmetry symflag, ElementType etype)
  : m_etype(etype), m_symflag(symflag), m_permuted(false)
{
  m_inp = InpMtx_new();
  m_bridge = BridgeMT_new();
  BridgeMT_setDefaultFields(m_bridge);
  m_mx = DenseMtx_new();
  m_mb = DenseMtx_new();
  m_nthread = SysInfo::nthread();
  m_lookahead = m_nthread / 2;
  m_exactFactor = true;
  m_pivoting = false;
  m_taupivot = 100.0;
  m_droptol = 0.0;
#ifndef NDEBUG
  m_msglevel = 2;
#else
  m_msglevel = 0;
#endif
  BridgeMT_setMessageInfo(m_bridge, m_msglevel, stderr);
}

SpoolesBase::~SpoolesBase()
{
  m_inp = InpMtx_free(m_inp);
  if (m_bridge != nullptr)
    BridgeMT_free(m_bridge);
  if (m_mx != nullptr)
    DenseMtx_free(m_mx);
  if (m_mb != nullptr)
    DenseMtx_free(m_mb);
}

void SpoolesBase::configure(const ConfigParser &cfg)
{
  m_nthread = cfg.getInt("SpoolesNThread", m_nthread);
  m_lookahead = cfg.getInt("SpoolesLookahead", m_lookahead);
  m_exactFactor = (not cfg.getBool("SpoolesIncomplete", false));
  m_droptol = cfg.getFloat("SpoolesDropTolerance", m_droptol);
  m_pivoting = cfg.getBool("SpoolesPivot", m_pivoting);
  m_taupivot = cfg.getFloat("SpoolesPivotTau", m_taupivot);
  m_msglevel = cfg.getInt("SpoolesVerbosity", m_msglevel);
  if ((m_msglevel > 0) and cfg.hasKey("SpoolesLogFile")) {
    FILE *msgFile = fopen(cfg["SpoolesLogFile"].c_str(), "w");
    BridgeMT_setMessageInfo(m_bridge, m_msglevel, msgFile);
  } else {
    BridgeMT_setMessageInfo(m_bridge, m_msglevel, stderr);
  }
}

SpoolesBase::ElementType SpoolesBase::mapElementType(uint typeflag)
{
  switch ( SpMatrixFlag::valueFlag(typeflag) ) {
  case SpMatrixFlag::IndexOnly:
    return SpoolesBase::IndexOnly;
  case SpMatrixFlag::RealValued:
    return SpoolesBase::Real;
  case SpMatrixFlag::ComplexValued:
    return SpoolesBase::Complex;
  default:
    return SpoolesBase::Real;
  }
}

SpoolesBase::Symmetry SpoolesBase::mapSymmetry(uint typeflag)
{
  switch ( SpMatrixFlag::symmetryFlag(typeflag) ) {
  case SpMatrixFlag::Unsymmetric:
    return SpoolesBase::Symmetric;
  case SpMatrixFlag::Symmetric:
    return SpoolesBase::Symmetric;
  case SpMatrixFlag::Hermitian:
    return SpoolesBase::Hermitian;
  default:
    return SpoolesBase::Unsymmetric;
  }
}

void SpoolesBase::assemble(const ConnectMap &spty, const double *val)
{
  const int nrow = spty.size();
  InpMtx_init(m_inp, INPMTX_BY_ROWS, m_etype, spty.nonzero(), 0);
  switch (m_etype) {
  case IndexOnly:
    for (int i=0; i<nrow; ++i) {
      uint *colidx = const_cast<uint *>( spty.first(i) );
      InpMtx_inputRow(m_inp, i, spty.size(i),
                      reinterpret_cast<int *>(colidx));
    }
    break;
  case Real:
    for (int i=0; i<nrow; ++i) {
      uint *colidx = const_cast<uint *>( spty.first(i) );
      const uint roff = spty.offset(i);
      InpMtx_inputRealRow(m_inp, i, spty.size(i),
                          reinterpret_cast<int *>(colidx),
                          const_cast<double*>( &val[roff]) );
    }
    break;
  case Complex:
    for (int i=0; i<nrow; ++i) {
      uint *colidx = const_cast<uint *>( spty.first(i) );
      const uint roff = spty.offset(i);
      InpMtx_inputComplexRow(m_inp, i, spty.size(i),
                             reinterpret_cast<int *>(colidx),
                             const_cast<double*>( &val[2*roff]));
    }
    break;
  default:
    throw Error("Element type not supported.");
    break;
  }
  InpMtx_changeStorageMode(m_inp, INPMTX_BY_VECTORS);

  m_permuted = false;
}

void SpoolesBase::assemble(const CsrMatrix<double> &a)
{
  m_etype = SpoolesBase::Real;
  assemble( a.sparsity(), a.pointer() );
}

void SpoolesBase::assemble(const CsrMatrix<float> &a)
{
  m_etype = SpoolesBase::Real;
  DVector<double> tmp;
  tmp.allocate( a.nonzero() );
  const float *p = a.pointer();
  std::copy( p, p + a.nonzero(), tmp.pointer() );
  assemble( a.sparsity(), tmp.pointer() );
}

void SpoolesBase::assemble(const CsrMatrix<std::complex<double> > &a)
{
  m_etype = SpoolesBase::Complex;
  const double *p = reinterpret_cast<const double*>( a.pointer() );
  assemble(a.sparsity(), p);
}

void SpoolesBase::assemble(const CsrMatrix<std::complex<float> > &a)
{
  m_etype = SpoolesBase::Complex;
  DVector<std::complex<double> > tmp;
  tmp.allocate( a.nonzero() );
  const std::complex<float> *p = a.pointer();
  std::copy( p, p + a.nonzero(), tmp.pointer() );
  assemble( a.sparsity(), reinterpret_cast<const double*>( tmp.pointer()) );
}

void SpoolesBase::symbolicFactorization(int nrows)
{
  int stat;
  BridgeMT_clearData(m_bridge);
  BridgeMT_setMatrixParams(m_bridge, nrows, m_etype, m_symflag);

  int sparse_front = (m_exactFactor ?
                        FRONTMTX_DENSE_FRONTS : FRONTMTX_SPARSE_FRONTS);
  int pivot_flag = (m_pivoting ? SPOOLES_PIVOTING : SPOOLES_NO_PIVOTING);

  BridgeMT_setFactorParams(m_bridge, sparse_front, pivot_flag,
                           m_taupivot, m_droptol, m_lookahead, 0);

  stat = BridgeMT_setup(m_bridge, m_inp);
  if (stat != 1)
    throw Error("SPOOLES symbolic factorization failed.");

  stat = BridgeMT_factorSetup(m_bridge, m_nthread, 3, 0.0);
  if (stat != 1)
    throw Error("SPOOLES factorization setup failed.");
}

void SpoolesBase::numericalFactorization()
{
  int do_permute = (m_permuted ? 0 : 1);
  int error;

  int stat = BridgeMT_factor(m_bridge, m_inp, do_permute, &error);
  if (stat != 1)
    throw Error("SPOOLES factorization failed.");
  m_permuted = true;

  stat = BridgeMT_solveSetup(m_bridge);
  if (stat != 1)
    throw Error("SPOOLES solve setup failed.");
}

DenseMtx *SpoolesBase::bridgeSolve(int nrows, int ncols)
{
  DenseMtx_init(m_mx, m_etype, 0, 0, nrows, ncols, 1, nrows);
  DenseMtx_zero(m_mx);

  int stat;
  stat = BridgeMT_solve(m_bridge, 1, m_mx, m_mb);
  if (stat != 1)
    throw Error("SPOOLES solve step failed.");

  return m_mx;
}

void SpoolesBase::transfer(int nrows, int ncols, const double *p,
                           DenseMtx *pm) const
{
  DenseMtx_init(pm, m_etype, 0, 0, nrows, ncols, 1, nrows);
  size_t nval = nrows*ncols * (m_etype == SpoolesBase::Complex ? 2 : 1);
  std::copy(p, p+nval, DenseMtx_entries(pm));
}

void SpoolesBase::transfer(int nrows, int ncols, const float *p,
                           DenseMtx *pm) const
{
  DenseMtx_init(pm, m_etype, 0, 0, nrows, ncols, 1, nrows);
  size_t nval = nrows*ncols * (m_etype == SpoolesBase::Complex ? 2 : 1);
  std::copy(p, p+nval, DenseMtx_entries(pm));
}

void SpoolesBase::transfer(DenseMtx *pm, int nrows, int ncols,
                           double *p) const
{
  size_t nval = nrows*ncols * (m_etype == SpoolesBase::Complex ? 2 : 1);
  const double *src = DenseMtx_entries(pm);
  std::copy(src, src+nval, p);
}

void SpoolesBase::transfer(DenseMtx *pm, int nrows, int ncols,
                           float *p) const
{
  size_t nval = nrows*ncols * (m_etype == SpoolesBase::Complex ? 2 : 1);
  const double *src = DenseMtx_entries(pm);
  std::copy(src, src+nval, p);
}








