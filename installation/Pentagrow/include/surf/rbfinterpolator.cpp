
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
 

#include "rbfinterpolator.h"
#include <genua/algo.h>
#include <genua/lls.h>
#include <genua/boxsearchtree.h>
#include <genua/mxmesh.h>
#include <genua/ndpointtree.h>
#include <genua/simdsupport.h>

using namespace std;

void RbfInterpolator::useStrNodes(bool usePoints, bool useBeams, bool useShells)
{
  clearStrNodes();
  for (uint is=0; is<m_pstr->nsections(); ++is) {
    Mx::ElementType tp = m_pstr->section(is).elementType();
    if ( useBeams and (tp == Mx::Line2 or tp == Mx::Line3) )
      useSection(is);
    else if ( usePoints and (tp == Mx::Point))
      useSection(is);
    else if ( useShells and m_pstr->section(is).surfaceElements() )
      useSection(is);
  }
  sort_unique(m_strNodes);
}

void RbfInterpolator::useSection(uint isec)
{
  assert(m_pstr != 0);
  const Indices & tmp = m_pstr->section(isec).nodes();
  m_strNodes.insert(m_strNodes.end(), tmp.begin(), tmp.end());
}

uint RbfInterpolator::uniqueCenters()
{
  // candidate node indices
  sort_unique(m_strNodes);
  const int n = m_strNodes.size();

  // clean up the set of points to use (remove duplicates)
  m_ctr.resize(n);
  for (int i=0; i<n; ++i)
    m_ctr[i] = m_pstr->node(m_strNodes[i]);

  BSearchTree btree(m_ctr);
  Indices repl, kept;
  btree.repldup(m_mergeThreshold, repl, kept);

  const int nk = kept.size();
  m_ctr.resize(nk);
  for (int i=0; i<nk; ++i) {
    kept[i] = m_strNodes[kept[i]];
    m_ctr[i]  = m_pstr->node( kept[i] );
  }

  // replace node indices
  m_strNodes.swap(kept);
  return m_strNodes.size();
}

void RbfInterpolator::centersFromTree(size_t ntarget)
{
  // build a point tree for the structural mesh
  NDPointTree<3,double> sntree;
  size_t ntreenodes = sntree.allocate(m_pstr->nodes(), true, 8);
  sntree.sort();

  // tree nodes are stored in a linearized fully balanced binary tree
  uint istart(0), iend(1), nctr(1);
  while (nctr < ntarget and iend <= ntreenodes) {
    istart = iend;
    iend = iend*2 + 1;
    nctr = iend - istart;
  }

  if (iend > ntreenodes) {
    istart /= 2;
    iend /= 2;
  }

  // use the structural nodes closest to bounding volume centers as RBF centers
  Vct3 bvc;
  m_strNodes.resize(nctr);
  for (uint i=0; i<nctr; ++i) {
    sntree.dop(istart + i).center(bvc.pointer());
    uint inear = sntree.nearest(bvc);
    m_strNodes[i] = inear;
  }

  // uniqueCenters() will be called later
}

void RbfInterpolator::buildRbfBasis()
{
  // determine RBF center nodes
  uniqueCenters();

  // setup RBF interpolation matrix
  const int nc = m_ctr.size();
  const int ne = m_pstr->nnodes();

  DMatrix<double> mrbf(ne,nc);
#pragma omp parallel for
  for (int j=0; j<nc; ++j) {
    for (int i=0; i<ne; ++i)
      mrbf(i,j) = rbf(m_pstr->node(i), m_ctr[j]);
  }

  // assemble RHS for RBF fitting problem
  const int nev = m_strFields.size();
  m_wrbf.resize(ne, 3*nev);
  for (int j=0; j<nev; ++j) {
    const MxMeshField & f(m_pstr->field(m_strFields[j]));
    for (int i=0; i<ne; ++i) {
      Vct3f dx;
      f.value(i, dx);
      for (int k=0; k<3; ++k)
        m_wrbf(i, 3*j+k) = dx[k];
    }
  }

  int stat = lls_solve(mrbf, m_wrbf);
  assert(m_wrbf.nrows() == uint(nc));
  if (stat != 0)
    throw Error("Least-squares solution failed in xGELS"
                " with INFO = "+str(stat));
}

void RbfInterpolator::eval(uint jm, const Vct3 & p, Vct3 & dx) const
{
  dx = 0.0;
  const int nc = m_ctr.size();
  for (int i=0; i<nc; ++i) {
    double phi = rbf(p, m_ctr[i]);
    for (int k=0; k<3; ++k)
      dx[k] += phi*m_wrbf(i, 3*jm+k);
  }
}

uint RbfInterpolator::map()
{
  assert(m_pstr);
  assert(m_paer);

  // run default procedure of collecting all nodes marked with wall
  // boundary conditions
  if (m_mappedNodes.empty())
    collectWallNodes();
  if (m_strFields.empty())
    collectDispFields();

  const int na = m_mappedNodes.size();
  if (na == 0)
    return 0;

  // build large, dense matrix of RBF function values
  const int nc = m_ctr.size();
  DMatrix<double> phi(na,nc);

#pragma omp parallel for
  for (int j=0; j<nc; ++j) {
    for (int i=0; i<na; ++i)
      phi(i,j) = rbf(m_paer->node(m_mappedNodes[i]), m_ctr[j]);
  }

  // evaluation reduces to GEMM:
  // mda = phi * wrbf
  DMatrix<double> mda;
  matmul(phi, m_wrbf, mda);

  PointList<3,double> dx( m_paer->nnodes() );
  const int nm = m_strFields.size();
  const double fs = m_scale;
  for (int jm=0; jm<nm; ++jm) {
    for (int i=0; i<na; ++i) {
      for (int k=0; k<3; ++k)
        dx[m_mappedNodes[i]][k] = fs * mda(i,3*jm+k);
    }

    // append new field to aerodynamic mesh
    const MxMeshField & sf(  m_pstr->field( m_strFields[jm] ) );
    uint fix = m_paer->appendField( sf.name(), dx );
    MxMeshField::ValueClass vcl = sf.valueClass();
    cout << "Field " << sf.name() << " class: " << vcl.str() << endl;
    if (vcl != MxMeshField::ValueClass::Field)
      m_paer->field(fix).valueClass( vcl );
    else
      m_paer->field(fix).valueClass( MxMeshField::ValueClass::Displacement );

    // extract annotation from original mode dataset
    m_paer->field(fix).annotate( sf.note() );
    m_aerFields.push_back(fix);
  }

  return nm;
}


