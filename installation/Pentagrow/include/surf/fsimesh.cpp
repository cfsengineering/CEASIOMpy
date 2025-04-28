
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
 

#include "fsimesh.h"
#include "fsielement.h"
#include <genua/xcept.h>
#include <genua/svd.h>
#include <genua/eig.h>
#include <genua/strutils.h>
#include <genua/timing.h>
#include <genua/ioglue.h>
#include <genua/dbprint.h>
#include <set>

using std::string;

void FsiMesh::mergeStruct(const MxMeshPtr & pmx,
                          const Indices & pidwet,
                          const Indices & pidintern)
{
  smx = pmx;

  bool bInclude = (pidwet.size() > 0);
  bool bExclude = (pidintern.size() > 0);

  if (bInclude or bExclude) {

    uint pidfi = smx->findField("PID");
    if (pidfi == NotFound)
      throw Error("PID field not found in structural mesh.");
    const MxMeshField & fpid( smx->field(pidfi) );
    if (fpid.nodal() or fpid.realField())
      throw Error("Field labeled PID does not contain element PIDs");

    DVector<int> pid;
    fpid.fetch(pid);
    // const int *pid = fpid.intPointer();

    sifElix.clear();
    for (uint k=0; k<smx->nsections(); ++k) {
      const MxMeshSection & sec( smx->section(k) );
      if (not sec.surfaceElements())
        continue;
      const int offs = sec.indexOffset();
      const int ne = sec.nelements();
      for (int i=0; i<ne; ++i) {
        const uint eix = offs + i;
        const int p = pid[eix];
        bool incel = binary_search(pidwet.begin(), pidwet.end(), p);
        bool excel = binary_search(pidintern.begin(), pidintern.end(), p);
        if ( bExclude and (not excel) )
          sifElix.push_back(eix);
        else if (bInclude and incel)
          sifElix.push_back(eix);
      }
    }

  } else {

    const int nse = smx->nelements();
    sifElix.resize(nse);
    for (int i=0; i<nse; ++i)
      sifElix[i] = i;

  }

  sort_unique(sifElix);

  // debug
  cout << "Marked " << sifElix.size() << " of "
       << smx->nelements() << " struct. elements" << endl;
  cout << "Exclude: " << bExclude << " Include: " << bInclude << endl;

  collectNodes(*smx, sifElix, sifNode);
  extractGids(*smx);

  // mark selected elements
  MxMeshBoco bc;
  bc.rename("Interface elements");
  bc.appendElements(sifElix.begin(), sifElix.end());
  smx->appendBoco(bc);
}

void FsiMesh::mergeBeams(const MxMeshPtr & pmx)
{
  smx = pmx;

  for (uint k=0; k<smx->nsections(); ++k) {
    const MxMeshSection & sec( smx->section(k) );
    if (sec.elementType() != Mx::Line2)
      continue;
    const int ne = sec.nelements();
    const int offs = sec.indexOffset();
    for (int i=0; i<ne; ++i)
      sifElix.push_back(offs+i);
  }

  collectNodes(*smx, sifElix, sifNode);
  extractGids(*smx);

  cout << sifNode.size() << " structural nodes used for interpolation." << endl;
}

void FsiMesh::collectNodes(const MxMesh & mx, const Indices & elix,
                           Indices & nds) const
{
  const int ne = elix.size();
  std::set<uint> nset;
  for (int i=0; i<ne; ++i) {
    uint nv, isec;
    const uint *vi = mx.globalElement(elix[i], nv, isec);
    assert(nv > 0 and vi != 0);
    nset.insert(vi, vi+nv);
  }

  Indices tmp(nset.begin(), nset.end());
  nds.swap(tmp);
}

void FsiMesh::extractGids(const MxMesh & smx)
{
  Indices tmp;
  XmlElement::const_iterator itn, nlast = smx.noteEnd();
  for (itn = smx.noteBegin(); itn != nlast; ++itn) {
    if (itn->name() == "NastranGID") {
      tmp.resize( Int(itn->attribute("count")) );
      itn->fetch( tmp.size(), &tmp[0] );
    }
  }

  if (tmp.empty()) {
    gids.clear();
    allGids.clear();
  } else {
    allGids = tmp;
    const int nsn = sifNode.size();
    gids.resize(nsn);
    for (int i=0; i<nsn; ++i)
      gids[i] = tmp[sifNode[i]];
  }
}

void FsiMesh::mergeFluid(const MxMeshPtr & pmx,
                         const Indices & ifboco)
{
  fmx = pmx;

  // collect all surface elements or only those in specified bocos
  if (ifboco.empty()) {
    for (uint k=0; k<fmx->nbocos(); ++k) {
      const MxMeshBoco & bc( fmx->boco(k) );
      if (bc.bocoType() == Mx::BcWall or bc.bocoType() == Mx::BcAdiabaticWall) {
        Indices elix;
        bc.elements(elix);
        const int ne = elix.size();
        for (int i=0; i<ne; ++i) {
          uint nv, isec;
          fmx->globalElement(elix[i], nv, isec);
          if ( isec != NotFound and fmx->section(isec).surfaceElements() )
            fifElix.push_back(elix[i]);
        }
      }
    }

    // some meshes may not have bocos defined, simply use all surfaces
    if (fifElix.empty()) {
      for (uint k=0; k<fmx->nsections(); ++k) {
        const MxMeshSection & sec( fmx->section(k) );
        if (not sec.surfaceElements())
          continue;
        const int ne = sec.nelements();
        const int offs = sec.indexOffset();
        for (int i=0; i<ne; ++i)
          fifElix.push_back(offs+i);
      }
    }

  } else {
    for (uint k=0; k<ifboco.size(); ++k) {
      Indices elix;
      fmx->boco( ifboco[k] ).elements(elix);
      const int ne = elix.size();
      for (int i=0; i<ne; ++i) {
        uint nv, isec;
        fmx->globalElement(elix[i], nv, isec);
        if ( isec != NotFound and fmx->section(isec).surfaceElements() )
          fifElix.push_back(elix[i]);
      }
    }
  }
  sort_unique(fifElix);

  if (fifElix.empty())
    throw Error("Could not identify any aerodynamic wall elements.");

  collectNodes(*fmx, fifElix, fifNode);
}

void FsiMesh::buildInterpolator()
{
  // build search tree to lookup fluid nodes
  buildTree(*fmx, fifNode, fnTree);
  buildTree(*smx, sifNode, snTree);

  // build connectivity map from fluid nodes to fluid interface elements
  buildMap(*fmx, fifNode, fifElix, fn2e);
}

void FsiMesh::buildTree(const MxMesh & mx, const Indices & idx,
                        BSearchTree & tree) const
{
  const int nfn = idx.size();
  PointList<3> spts( nfn );
  for (int i=0; i<nfn; ++i)
    spts[i] = mx.node( idx[i] );
  tree = BSearchTree(spts);
}

void FsiMesh::buildMap(const MxMesh & mx, const Indices & nds,
                       const Indices & elm, ConnectMap & v2emap) const
{
  const int nn = nds.size();
  const int ne = elm.size();

  v2emap.beginCount(nn);
  for (int i=0; i<ne; ++i) {
    uint nv, isec;
    const uint *vi = mx.globalElement(elm[i], nv, isec);
    assert(vi != 0);
    for (uint k=0; k<nv; ++k) {
      uint ni = sorted_index(nds, vi[k]);
      if (ni != NotFound)
        v2emap.incCount(ni);
    }
  }
  v2emap.endCount();

  for (int i=0; i<ne; ++i) {
    uint nv, isec;
    const uint *vi = mx.globalElement(elm[i], nv, isec);
    assert(vi != 0);
    for (uint k=0; k<nv; ++k) {
      uint nk = sorted_index(nds, vi[k]);
      if (nk != NotFound)
        v2emap.append(nk, i);
    }
  }
  v2emap.compress();
}

void FsiMesh::clear()
{
  fmx.reset();
  smx.reset();
  gids.clear();
  sifNode.clear();
  sifElix.clear();
  fifNode.clear();
}

bool FsiMesh::extractPressure(Real qoo, uint ixf, Vector & pf) const
{
  const MxMeshField & mf( fmx->field(ixf) );
  if ((not mf.nodal()) or (not mf.realField()))
    return false;

  // const Real *rp = mf.realPointer();
  DVector<Real> rp;
  mf.fetch(rp);
  const int nfn = fifNode.size();
  pf.allocate( nfn );
  for (int i=0; i<nfn; ++i)
    pf[i] = qoo*rp[fifNode[i]];

  return true;
}

bool FsiMesh::extractPressure(Real qoo, Vector & pf,
                              const std::string & fieldName) const
{
  uint ixf = fmx->findField(fieldName);
  if (ixf == NotFound)
    return false;

  return extractPressure(qoo, ixf, pf);
}

void FsiMesh::assemblePressure(Real qoo, const Indices & ifield,
                               const Vector & coef, Vector & pf) const
{
  const int nif = fifNode.size();
  const uint ncf = ifield.size();
  assert(coef.size() == ncf);
  pf.resize(nif);
  Vector rp(fmx->nnodes());
  for (uint j=0; j<ncf; ++j) {
    const MxMeshField & mf( fmx->field(ifield[j]) );
    mf.fetch(rp);
    for (int i=0; i<nif; ++i)
      pf[i] += coef[j]*qoo*rp[fifNode[i]];
  }
}

void FsiMesh::agglomerate(const Vector & pf, PointList<6> & fnodal) const
{
  const int nsn = sifNode.size();
  fnodal.resize(nsn);
  fnodal.zero();

  // reduce aerodynamic loads to element-center forces
  PointList<3> ctr, ecf;
  centerForces(pf, ctr, ecf);

  const int nfe = ctr.size();
#pragma omp parallel for
  for (int i=0; i<nfe; ++i) {
    uint inear = snTree.nearest( ctr[i] );
    // assert(inear != NotFound);
    Vct3 r = smx->node( sifNode[inear] ) - ctr[i];
    Vct3 em = cross(ecf[i], r);
    for (int k=0; k<3; ++k) {
#pragma omp atomic
      fnodal[inear][k+0] += ecf[i][k];
#pragma omp atomic
      fnodal[inear][k+3] += em[k];
    }
  }
}

void FsiMesh::agglomerate(const Matrix & mpf, PointGrid<6> & fnodal) const
{
  const int npf = mpf.ncols();
  const int nsn = sifNode.size();
  fnodal.resize(nsn,npf);
  fnodal.zero();

  // reduce aerodynamic loads to element-center forces
  PointList<3> ctr;
  PointGrid<3> ecf;

  centerForces(mpf, ctr, ecf);

  // don't parallelize this, threads just get in each others way
  const int nfe = ctr.size();
  for (int i=0; i<nfe; ++i) {
    uint inear = snTree.nearest( ctr[i] );
    // assert(inear != NotFound);
    Vct3 r = smx->node( sifNode[inear] ) - ctr[i];
    for (int k=0; k<npf; ++k) {
      Vct6 efm;
      join_vct(ecf(i,k), cross(ecf(i,k), r), efm);
      fnodal(inear,k) += efm;
    }
  }
}

void FsiMesh::integrate(const Vector & pf, PointList<6> & fnodal) const
{
  // 6-point triangle integration rule
  static const Real a = 0.445948490915965;
  static const Real b = 0.091576213509771;
  static const Real c = 0.111690794839005;
  static const Real d = 0.054975871827661;
  static const Real wt6[] = {c, c, c, d, d, d};
  static const Real ut6[] = {a, 1.-2.*a, a, b, 1.-2.*b, b};
  static const Real vt6[] = {a, a, 1.-2.*a, b, b, 1.-2.*b};

  // 4x4 tensor-product rule for quads
  static const Real uq4[] = {-0.861136311594053, -0.339981043584856,
                             0.339981043584856, 0.861136311594053};
  static const Real wq4[] = { 0.173927422568727, 0.326072577431273,
                              0.326072577431273, 0.173927422568727 };

  const int nsn = sifNode.size();
  fnodal.resize(nsn);
  fnodal.zero();

  const int nse = sifElix.size();
#pragma omp parallel for schedule(dynamic,256)
  for (int i=0; i<nse; ++i) {
    uint nv, isec;
    smx->globalElement(sifElix[i], nv, isec);
    Mx::ElementType et = smx->section(isec).elementType();
    if (et == Mx::Tri3) {
      FsiTri3 fsi(*this, sifElix[i]);
      fsi.integrate(pf, 6, ut6, vt6, wt6, fnodal);
    } else if (et == Mx::Quad4) {
      FsiQuad4 fsi(*this, sifElix[i]);
      fsi.tpIntegrate(pf, 4, uq4, wq4, fnodal);
    }
  }
}

void FsiMesh::integrate(const Matrix & pf, PointGrid<6> & fnodal) const
{
  // 6-point triangle integration rule
  static const Real a = 0.445948490915965;
  static const Real b = 0.091576213509771;
  static const Real c = 0.111690794839005;
  static const Real d = 0.054975871827661;
  static const Real wt6[] = {c, c, c, d, d, d};
  static const Real ut6[] = {a, 1.-2.*a, a, b, 1.-2.*b, b};
  static const Real vt6[] = {a, a, 1.-2.*a, b, b, 1.-2.*b};

  // 4x4 tensor-product rule for quads
  static const Real xq4[] = {-0.861136311594053, -0.339981043584856,
                             0.339981043584856, 0.861136311594053};
  static const Real xwq4[] = { 0.173927422568727, 0.326072577431273,
                               0.326072577431273, 0.173927422568727 };

  // rewrite tensor product rule to simplify element loops
  Real uq4[16], vq4[16], wq4[16];
  for (int i=0; i<4; ++i) {
    for (int j=0; j<4; ++j) {
      int k = 4*i+j;
      uq4[k] = xq4[i];
      vq4[k] = xq4[j];
      wq4[k] = xwq4[i]*xwq4[j];
    }
  }

  const int ncol = pf.ncols();
  const int nsn = sifNode.size();
  fnodal.resize(nsn,ncol);
  fnodal.zero();

  const int nse = sifElix.size();
#pragma omp parallel for schedule(dynamic,256)
  for (int i=0; i<nse; ++i) {
    uint nv, isec;
    smx->globalElement(sifElix[i], nv, isec);
    Mx::ElementType et = smx->section(isec).elementType();
    if (et == Mx::Tri3) {
      FsiTri3 fsi(*this, sifElix[i]);
      fsi.integrate(6, ut6, vt6, wt6, pf, fnodal);
    } else if (et == Mx::Quad4) {
      FsiQuad4 fsi(*this, sifElix[i]);
      fsi.integrate(16, uq4, vq4, wq4, pf, fnodal);
    }
  }
}

uint FsiMesh::exportForces(uint ifield, ostream &os,
                           uint sid, Real ff, Real lf) const
{
  assert(smx);
  assert(smx->nfields() > ifield);
  const MxMeshField & mf( smx->field(ifield) );
  assert(mf.nodal() and mf.realField());
  if (mf.ndimension() == 3) {
    PointList<3> forces( smx->nnodes() );
    mf.fetch<Real,3>(forces);
    cout << "3D field " << ifield << " nnodes: "
         << smx->nnodes() << " field: " << forces.size() << endl;
    return this->exportForces(forces, os, sid, ff);
  } else if (mf.ndimension() == 6) {
    PointList<6> fomo( smx->nnodes() );
    mf.fetch<Real,6>(fomo);
    return this->exportForces(fomo, os, sid, ff, lf);
  }

  return 0;
}

uint FsiMesh::exportForces(const PointList<3> & fnodal,
                           std::ostream & os, uint sid, Real ff) const
{
#undef NZNSTR
#define NZNSTR(x)  nstr( (fabs((x)) > 1e-9) ? (x) : 0.0 )

  uint nex(0);
  const int nsn = sifNode.size();
  if (fnodal.size() == (uint) nsn) {
    for (int i=0; i<nsn; ++i) {
      if (sq(fnodal[i]) < 1e-9)
        continue;
      os << "FORCE, " << sid << ", " << gids[i] << ", 0, " << NZNSTR(ff) << ", "
         << NZNSTR(fnodal[i][0]) << ", " << NZNSTR(fnodal[i][1]) << ", "
                                                                 << NZNSTR(fnodal[i][2]) << endl;
      ++nex;
    }
  } else if (fnodal.size() == allGids.size()) {
    const int n = fnodal.size();
    for (int i=0; i<n; ++i) {
      if (sq(fnodal[i]) < 1e-9)
        continue;
      os << "FORCE, " << sid << ", " << allGids[i] << ", 0, " << NZNSTR(ff) << ", "
         << NZNSTR(fnodal[i][0]) << ", " << NZNSTR(fnodal[i][1]) << ", "
                                                                 << NZNSTR(fnodal[i][2]) << endl;
      ++nex;
    }
  } else {
    throw Error("FsiMesh::exportForces() - "
                "Force vector length (" + str(fnodal.size()) +
                ") does not match problem size ("
                + str(nsn) + "/" + str(allGids.size()) + ").");
  }

#undef NZSTR

  return nex;
}

uint FsiMesh::exportForces(const PointList<3> & fnodal,
                           const std::string & fname, uint sid, Real ff) const
{
  ofstream os(asPath(fname).c_str(), std::ios::binary);
  return exportForces(fnodal, os, sid, ff);
}

uint FsiMesh::exportForces(const PointList<6> & fnodal,
                           const std::string & fname, uint sid,
                           Real ff, Real lf) const
{
  ofstream os(asPath(fname).c_str(), std::ios::binary);
  return exportForces(fnodal, os, sid, ff, lf);
}

uint FsiMesh::exportForces(const PointList<6> & fnodal,
                           ostream &os, uint sid,
                           Real ff, Real lf) const
{
#undef NZNSTR
#define NZNSTR(x)  nstr( (fabs((x)) > 1e-9) ? (x) : 0.0 )

  uint nex = 0;
  const int nsn = sifNode.size();
  if (fnodal.size() == (uint) nsn) {
    for (int i=0; i<nsn; ++i) {
      Real fmag = sq(fnodal[i][0]) + sq(fnodal[i][1]) + sq(fnodal[i][2]);
      Real mmag = sq(fnodal[i][3]) + sq(fnodal[i][4]) + sq(fnodal[i][5]);
      if (fmag > 1e-6) {
        os << "FORCE, " << sid << ", " << gids[i] << ", 0, " << nstr(ff) << ", "
           << NZNSTR(fnodal[i][0]) << ", " << NZNSTR(fnodal[i][1]) << ", "
                                                                   << NZNSTR(fnodal[i][2]) << endl;
        ++nex;
      }
      if (mmag > 1e-6) {
        os << "MOMENT, " << sid << ", " << gids[i] << ", 0, " << nstr(ff*lf) << ", "
           << NZNSTR(fnodal[i][3]) << ", " << NZNSTR(fnodal[i][4]) << ", "
                                                                   << NZNSTR(fnodal[i][5]) << endl;
        ++nex;
      }
    }
  } else if (fnodal.size() == allGids.size()) {
    const int n = fnodal.size();
    for (int i=0; i<n; ++i) {
      Real fmag = sq(fnodal[i][0]) + sq(fnodal[i][1]) + sq(fnodal[i][2]);
      Real mmag = sq(fnodal[i][3]) + sq(fnodal[i][4]) + sq(fnodal[i][5]);
      if (fmag > 1e-6) {
        os << "FORCE, " << sid << ", " << allGids[i] << ", 0, " << nstr(ff) << ", "
           << NZNSTR(fnodal[i][0]) << ", " << NZNSTR(fnodal[i][1]) << ", "
                                                                   << NZNSTR(fnodal[i][2]) << endl;
        ++nex;
      }
      if (mmag > 1e-6) {
        os << "MOMENT, " << sid << ", " << allGids[i] << ", 0, " << nstr(ff*lf) << ", "
           << NZNSTR(fnodal[i][3]) << ", " << NZNSTR(fnodal[i][4]) << ", "
                                                                   << NZNSTR(fnodal[i][5]) << endl;
        ++nex;
      }
    }
  } else {
    throw Error("FsiMesh::exportForces() - "
                "Force vector length (" + str(fnodal.size()) +
                ") does not match problem size ("
                + str(nsn) + "/" + str(allGids.size()) + ").");
  }

#undef NZSTR

  return nex;
}

uint FsiMesh::exportDarea(uint sid, const PointList<6> & fnodal,
                          ostream &os, Real ff, Real lf) const
{
  // load to consider zero (NASTRAN complains about too small loads)
  const Real limit = 1e-14;

  const int nsn = sifNode.size();
  assert(fnodal.size() == uint(nsn));
  assert(gids.size() == uint(nsn));

  uint n(0);
  for (int i=0; i<nsn; ++i) {
    for (int k=0; k<6; ++k) {
      Real f = fnodal[i][k];
      if (fabs(f) < limit)
        continue;
      f *= ( (k < 3) ? ff : (ff*lf) );
      if (n%2 == 0)
        os << "DAREA, " << sid << ", ";
      os << gids[i] << ", " << k+1 << ", " << nstr(f);
      ++n;
      if (n%2 == 0)
        os << endl;
      else
        os << ", ";
    }
  }

  return n;
}

Vct6 FsiMesh::sum(const Vct3 & ptref, const PointList<6> & fm) const
{
  Vct6 gfm;

#pragma omp parallel
  {
    Vct3 nf, nm, sf, sm; // thread-private copy
    const int nsn = sifNode.size();
    // assert(fm.size() == (uint) nsn);
#pragma omp for
    for (int i=0; i<nsn; ++i) {
      const Vct3 & node( smx->node( sifNode[i] ) );
      split_vct(fm[i], nf, nm);
      sf += nf;
      sm += nm + cross( node-ptref, nf );
    }
#pragma omp critical
    for (int k=0; k<3; ++k) {
      gfm[k+0] += sf[k];
      gfm[k+3] += sm[k];
    }
  }

  return gfm;
}

void FsiMesh::centerForces(const Vector & pf,
                           PointList<3> & ctr, PointList<3> & ecf) const
{
  const int nfe = fifElix.size();
  ctr.resize(nfe);
  ecf.resize(nfe);

#pragma omp parallel for
  for (int i=0; i<nfe; ++i) {
    uint nv, isec;
    const uint *vi = fmx->globalElement(fifElix[i], nv, isec);
    //assert(vi != 0);
    Mx::ElementType et = fmx->section(isec).elementType();
    if (et == Mx::Tri3) {
      const Vct3 & p1( fmx->node(vi[0]) );
      const Vct3 & p2( fmx->node(vi[1]) );
      const Vct3 & p3( fmx->node(vi[2]) );
      Vct3 fna = cross(p2-p1, p3-p1);

      // map node indices to pf indices
      uint w[3];
      w[0] = sorted_index(fifNode, vi[0]); // assert(w[0] != NotFound);
      w[1] = sorted_index(fifNode, vi[1]); // assert(w[1] != NotFound);
      w[2] = sorted_index(fifNode, vi[2]); // assert(w[2] != NotFound);

      Real pc = pf[w[0]] + pf[w[1]] + pf[w[2]];
      ctr[i] = (p1 + p2 + p3) / 3.0;
      ecf[i] = fna * (-pc / 6.);
    }
  }
}

void FsiMesh::centerForces(const Matrix & pf,
                           PointList<3> & ctr, PointGrid<3> & ecf) const
{
  const int npf = pf.ncols();
  const int nfe = fifElix.size();
  ctr.resize(nfe);
  ecf.resize(nfe,npf);

#pragma omp parallel for
  for (int i=0; i<nfe; ++i) {
    uint nv, isec;
    const uint *vi = fmx->globalElement(fifElix[i], nv, isec);
    // //assert(vi != 0);
    Mx::ElementType et = fmx->section(isec).elementType();
    if (et == Mx::Tri3) {
      const Vct3 & p1( fmx->node(vi[0]) );
      const Vct3 & p2( fmx->node(vi[1]) );
      const Vct3 & p3( fmx->node(vi[2]) );
      Vct3 fna = cross(p2-p1, p3-p1);
      ctr[i] = (p1 + p2 + p3) / 3.0;

      // map node indices to pf indices
      uint w[3];
      w[0] = sorted_index(fifNode, vi[0]); // assert(w[0] != NotFound);
      w[1] = sorted_index(fifNode, vi[1]); // assert(w[1] != NotFound);
      w[2] = sorted_index(fifNode, vi[2]); // assert(w[2] != NotFound);

      for (int k=0; k<npf; ++k) {
        Real pc = pf(w[0],k) + pf(w[1],k) + pf(w[2],k);
        ecf(i,k) = fna * (-pc / 6.);
      }
    }
  }

}

Vct3 FsiMesh::moment(const Vct3 & c, const PointList<3> & ctr,
                     const PointList<3> & cf) const
{
  Vct3 sum;
  const int n = ctr.size();
  for (int i=0; i<n; ++i)
    sum += cross(c - ctr[i], cf[i]);
  return sum;
}

uint FsiMesh::appendSifField(const PointList<3> & fn,
                             const std::string & suffix)
{
  if (fn.size() == sifNode.size()) {
    PointList<3> ndf( smx->nnodes() );
    const int nsn = sifNode.size();
    for (int i=0; i<nsn; ++i)
      ndf[sifNode[i]] = fn[i];
    uint fix = smx->appendField("Pressure Forces"+suffix, ndf);
    smx->field(fix).valueClass(MxMeshField::ValueClass::Force);
    return fix;
  } else if (fn.size() == smx->nnodes()) {
    uint fix = smx->appendField("Pressure Forces"+suffix, fn);
    smx->field(fix).valueClass(MxMeshField::ValueClass::Force);
    return fix;
  } else {
    // can't map.
    return NotFound;
  }
}

void FsiMesh::appendSifField(const PointList<6> & fn,
                             const std::string & suffix)
{
  PointList<3> ndf( smx->nnodes() ), ndm( smx->nnodes() );
  if (fn.size() == sifNode.size()) {
    const int nsn = sifNode.size();
    for (int i=0; i<nsn; ++i)
      split_vct( fn[i], ndf[sifNode[i]], ndm[sifNode[i]] );
  } else if (fn.size() == smx->nnodes()) {
    const int nn = smx->nnodes();
    for (int i=0; i<nn; ++i)
      split_vct( fn[i], ndf[i], ndm[i] );
  } else {
    // don't know how to map
    return;
  }

  uint fix;
  fix = smx->appendField("Pressure Forces "+suffix, ndf);
  smx->field(fix).valueClass(MxMeshField::ValueClass::Force);
  fix = smx->appendField("Pressure Moments "+suffix, ndm);
  smx->field(fix).valueClass(MxMeshField::ValueClass::Moment);
}

void FsiMesh::evalPressure(const Vector & pf, uint eix,
                           const Vct2 & uv, Vct3 & psn) const
{
  uint nv, isec;
  const uint *vi = fmx->globalElement(eix, nv, isec);
  assert(isec != NotFound);
  Mx::ElementType et = fmx->section(isec).elementType();

  // lookup element indices
  uint vf[16];
  assert(nv <= 16);
  for (uint i=0; i<nv; ++i) {
    vf[i] = sorted_index(fifNode, vi[i]);
    assert( vf[i] != NotFound );
  }

  Real puv(0);
  if (et == Mx::Tri3) {
    puv = (1.0-uv[0]-uv[1])*pf[vf[0]]
        + uv[0]*pf[vf[1]] + uv[1]*pf[vf[2]];
    const Vct3 & p1( fmx->node(vi[0]) );
    const Vct3 & p2( fmx->node(vi[1]) );
    const Vct3 & p3( fmx->node(vi[2]) );
    psn = cross(p2-p1, p3-p1);
  } else {
    throw Error("FsiMesh: Don't know how to evaluate on this element: "
                + fmx->section(isec).elementTypeName());
  }

  psn *= -puv / norm(psn);
}

void FsiMesh::evalPressure(const Matrix & pf, uint eix,
                           const Vct2 & uv, PointList<3> & psn) const
{
  uint nv, isec;
  const uint *vi = fmx->globalElement(eix, nv, isec);
  assert(isec != NotFound);
  Mx::ElementType et = fmx->section(isec).elementType();

  if (et != Mx::Tri3)
    throw Error("FsiMesh: Don't know how to evaluate on this element: "
                + fmx->section(isec).elementTypeName());

  // lookup element indices
  uint vf[16];
  assert(nv <= 16);
  for (uint i=0; i<nv; ++i) {
    vf[i] = sorted_index(fifNode, vi[i]);
    assert( vf[i] != NotFound );
  }

  // interpolation for each column
  const int ncol = pf.ncols();
  for (int j=0; j<ncol; ++j) {
    Real puv(0);
    if (et == Mx::Tri3) {
      puv = (1.0-uv[0]-uv[1])*pf(vf[0],j)
          + uv[0]*pf(vf[1],j) + uv[1]*pf(vf[2],j);
      const Vct3 & p1( fmx->node(vi[0]) );
      const Vct3 & p2( fmx->node(vi[1]) );
      const Vct3 & p3( fmx->node(vi[2]) );
      psn[j] = cross(p2-p1, p3-p1);
      psn[j] *= -puv / norm(psn[j]);
    }
  }
}

uint FsiMesh::nearestFluidElement(const Vct3 & pt, Vct2 & uv) const
{
  Vct2 uvt;
  uint enear(NotFound), inear;
  Real sqdst, mindst = std::numeric_limits<Real>::max();
  inear = fnTree.nearest( pt );

  ConnectMap::const_iterator ite, elast;
  elast = fn2e.end(inear);
  for (ite = fn2e.begin(inear); ite != elast; ++ite) {
    uint eix = fifElix[*ite];
    sqdst = project(pt, eix, uvt);
    if (sqdst < mindst) {
      mindst = sqdst;
      uv = uvt;
      enear = eix;
    }
  }

  // nearest point on element should be closer than
  // nearest node, or at least very nearly so
  assert( sq(pt - fmx->node(fifNode[inear])) + gmepsilon >= mindst );

  return enear;
}

uint FsiMesh::nearestFluidElement(const Vct3 & pt, const Vct3 & nrm,
                                  Vct2 & uv) const
{
  Indices elm;
  nearbyFluidElements(pt, nrm, elm);
  const int ne = elm.size();
  Vct2 uvt;
  uint enear(NotFound);
  Real sqdst, mindst = std::numeric_limits<Real>::max();
  for (int i=0; i<ne; ++i) {
    uint eix = fifElix[elm[i]];
    sqdst = project(pt, eix, uvt);
    if (sqdst < mindst) {
      mindst = sqdst;
      uv = uvt;
      enear = eix;
    }
  }

  return enear;
}

void FsiMesh::nearbyFluidElements(const Vct3 & pt, const Vct3 & nrm,
                                  Indices & elm) const
{
  // collect nearby nodes
  Indices nodes;
  uint nearest = fnTree.nearest(pt);
  if (searchRadius <= 0.0) {
    nodes.push_back( nearest );
  } else {
    Real dsq = sq( fmx->node(nearest) - pt );
    if (dsq > sq(searchRadius)) {
      // nearest node is farther away than search radius; using radius search
      // to resolve ambiguities is therefore not necessary
      nodes.push_back(nearest);
    } else {
      fnTree.find(pt, searchRadius, nodes);
      if (nodes.empty())
        nodes.push_back( nearest );  // must have at least one node
    }
  }

  // candidate elements by connectivity
  Indices tmp;
  const int nn = nodes.size();
  for (int i=0; i<nn; ++i)
    tmp.insert(tmp.end(), fn2e.begin(nodes[i]), fn2e.end(nodes[i]));
  sort_unique(tmp);

  // use only elements which comply with the normal angle criterion
  elm.clear();
  const int ne = tmp.size();
  for (int i=0; i<ne; ++i) {
    uint nv, isec;
    const uint *vi = fmx->globalElement(fifElix[tmp[i]], nv, isec);
    assert(vi != 0 and isec != NotFound);
    Mx::ElementType et = fmx->section(isec).elementType();
    if (nn == 1) {  // just one nearby node, test all connected elements
      switch (et) {
      case Mx::Tri3:
      case Mx::Tri6:
      case Mx::Quad4:
      case Mx::Quad8:
      case Mx::Quad9:
        elm.push_back(tmp[i]);
        break;
      default:
        break;  // other element types are not accepted
      }
    } else {   // multiple nodes, must resolve ambiguities using normal
      Vct3 fn;
      Real cphi(-2.0);
      switch (et) {
      case Mx::Tri3:
      case Mx::Tri6:
        fn = cross(fmx->node(vi[1])-fmx->node(vi[0]),
            fmx->node(vi[2])-fmx->node(vi[0]));
        cphi = cosarg(fn, nrm);
        break;
      case Mx::Quad4:
      case Mx::Quad8:
      case Mx::Quad9:
        fn = cross(fmx->node(vi[2])-fmx->node(vi[0]),
            fmx->node(vi[3])-fmx->node(vi[1]));
        cphi = cosarg(fn, nrm);
        break;
      default:
        cphi = -2.0; // other element types are not accepted
      }
      if (cphi > minCosPhi and cphi < maxCosPhi)
        elm.push_back( tmp[i] );
    }
  }
}

Real FsiMesh::project(const Vct3 & pt, uint eix, Vct2 & uv) const
{
  uint nv, isec;
  const uint *vi = fmx->globalElement(eix, nv, isec);
  assert(nv != 0);

  // TODO
  // - accurate projection on 6-node triangles
  // - projection on quads

  Mx::ElementType etype = fmx->section(isec).elementType();
  if (etype == Mx::Tri3 or etype == Mx::Tri6) {
    return projectTri3(pt, vi, uv);
  } else {
    throw Error("FsiMesh: Don't know how to project on this element: "
                + fmx->section(isec).elementTypeName());
  }
}

Real FsiMesh::projectTri3(const Vct3 & pt, const uint *vi, Vct2 & uv) const
{
  const Vct3 & p1( fmx->node(vi[0]) );
  const Vct3 & p2( fmx->node(vi[1]) );
  const Vct3 & p3( fmx->node(vi[2]) );

  // edge directions
  Vct3 a(p2 - p1), b(p3 - p1);
  Vct3 un = cross(a, b);

  Real ilen = 1.0 / norm(un);
  un *= ilen;

  // dot products
  Real dab, dbb, daa;
  dab = dot(a, b);
  dbb = dot(b, b);
  daa = dot(a, a);

  // parametric directions
  Vct3 vxi(a - b*(dab/dbb)), veta(b - a*(dab/daa));

  // length of direction vectors
  Real lxi = dot(vxi, vxi);
  Real leta = dot(veta, veta);

  // vector from p1 to cpt
  Vct3 cr( pt - p1 );

  // compute projection
  Real u = dot(cr, vxi) / lxi;
  Real v = dot(cr, veta) / leta;
  Real w = 1.0 - u - v;
  Real h = dot(cr, un);

  // projection inside triangle
  if (u >= 0.0 and v >= 0.0 and w >= 0.0) {
    uv[0] = u;
    uv[1] = v;
    return sq(h);
  }

  // projection outside
  if (u < 0.0) {
    uv[0] = 0.0;
    if (v < 0.0)
      uv[1] = 0.0;
    else if (w < 0.0)
      uv[1] = 1.0;
    else
      uv[1] = clamp(v, 0.0, 1.0);
  } else if (v < 0.0) {
    uv[1] = 0.0;
    if (u < 0.0)
      uv[0] = 0.0;
    else if (w < 0.0)
      uv[0] = 1.0;
    else
      uv[0] = clamp(u, 0.0, 1.0);
  } else if (w < 0.0) {
    Real f = 1.0 / (u+v);
    uv[0] = f*u;
    uv[1] = f*v;
  }

  Vct3 ep = (1-uv[0]-uv[1])*p1 + uv[0]*p2 + uv[1]*p3;
  return sq(ep - pt);
}

// this will be very costly to compute - interpolation with multiple
// pressure fields appears more attractive for now.

//void FsiMesh::mapping(PFMap &map) const
//{
//  // compute sparsity
//  {
//    ConnectMap spty;
//    mappingPattern(spty);
//    map.swap(spty);
//  }

//  // evaluate integration coefficients

//}

void FsiMesh::mappingPattern(ConnectMap &spty) const
{
  spty.clear();

  // 6-point triangle integration rule
  static const Real a = 0.445948490915965;
  static const Real b = 0.091576213509771;
  // static const Real c = 0.111690794839005;
  // static const Real d = 0.054975871827661;
  //  static const Real wt6[] = {c, c, c, d, d, d};
  static const Real ut6[] = {a, 1.-2.*a, a, b, 1.-2.*b, b};
  static const Real vt6[] = {a, a, 1.-2.*a, b, b, 1.-2.*b};

  // 4x4 tensor-product rule for quads
  static const Real xq4[] = {-0.861136311594053, -0.339981043584856,
                             0.339981043584856, 0.861136311594053};
  //  static const Real wq4[] = { 0.173927422568727, 0.326072577431273,
  //                              0.326072577431273, 0.173927422568727 };

  // expand tensor product rule to simplify element loops
  Real uq4[16], vq4[16];
  for (int i=0; i<4; ++i) {
    for (int j=0; j<4; ++j) {
      int k = 4*i+j;
      uq4[k] = xq4[i];
      vq4[k] = xq4[j];
    }
  }

  Vct2 fuv;
  SparsityCounter counter;

  const int nse = sifElix.size();
  for (int i=0; i<nse; ++i) {
    uint nvs, sisec, nvf, fisec;
    const uint *vs = smx->globalElement(sifElix[i], nvs, sisec);
    Mx::ElementType et = smx->section(sisec).elementType();
    if (et == Mx::Tri3) {
      FsiTri3 fsi(*this, sifElix[i]);
      for (int ki=0; ki<6; ++ki) {
        uint nfe = fsi.nearestFluidElement(ut6[ki], vt6[ki], fuv);
        if (nfe == NotFound)
          continue;
        const uint *vf = fmx->globalElement(nfe, nvf, fisec);
        for (uint kj=0; kj<nvs; ++kj)
          counter.append(vs[kj], nvf, vf);
      }
    } else if (et == Mx::Quad4) {
      FsiQuad4 fsi(*this, sifElix[i]);
      for (int ki=0; ki<16; ++ki) {
        uint nfe = fsi.nearestFluidElement(uq4[ki], vq4[ki], fuv);
        if (nfe == NotFound)
          continue;
        const uint *vf = fmx->globalElement(nfe, nvf, fisec);
        for (uint kj=0; kj<nvs; ++kj)
          counter.append(vs[kj], nvf, vf);
      }
    }
  }

  spty.assign(smx->nnodes(), counter);
}

void FsiMesh::residualizeLoads(const CsrMatrix<Real> &M)
{
  assert(M.nrows() == 6*smx->nnodes());

  // identify fields containing loads
  Indices loadFields, modeFields;
  smx->findFields( MxMeshField::ValueClass::Force, loadFields );
  smx->findFields( MxMeshField::ValueClass::Eigenmode, modeFields );

  const int n = smx->nnodes();
  const int nload = loadFields.size();
  const int nmode = modeFields.size();

  // extract modes, compute M*Z
  VectorArray Z(nmode), MZ(nmode);
  for (int j=0; j<nmode; ++j) {
    const MxMeshField & mf( smx->field(modeFields[j]) );
    assert(mf.nodal() and mf.realField());
    Z[j].resize(6*n);
    MZ[j].resize(6*n);
    mf.fetch(6, Z[j]);
    M.multiply(Z[j], MZ[j]);
  }

#pragma omp parallel
  {
    // thread-local load vectors
    Vector r(6*n), rt(6*n), r3(3*n);

#pragma omp for
    for (int i=0; i<nload; ++i) {

      MxMeshField & lf( smx->field(loadFields[i]) );
      // assert(lf.nodal() and lf.realField() and lf.ndimension() == 3);

      // expand load vector to 6D
      lf.fetch(6, r);

      // compute Rt = Ro - Z^T Ro M Z
      rt = r;
      for (int j=0; j<nmode; ++j)
        axpby(-dot(Z[j], r), MZ[j], 1.0, rt);

      // restrict result to 3D
      Real sqr = 0.0;
      for (int j=0; j<n; ++j) {
        for (int k=0; k<3; ++k) {
          r3[3*j+k] = rt[6*j+k];
          sqr += sq(r3[3*j+k]);
        }
      }

      // normalize force vector
      r3 *= (n / std::sqrt(sqr));

      lf.copyReal(lf.name(), 3, r3.pointer());
      // assert(lf.nelements() == smx->nnodes());
    }
  }
}

void FsiMesh::augmentedStates(const CsrMatrix<Real> &M,
                              const CsrMatrix<Real> &K)
{
  // locate deformation fields
  Indices defoFields;
  for (uint i=0; i<smx->nfields(); ++i) {
    if (smx->field(i).valueClass() == MxMeshField::ValueClass::Displacement)
      defoFields.push_back(i);
  }

  // extract data fields
  const int nx = defoFields.size();
  if (nx == 0) {
    dbprint("No displacements in structural mesh.");
    return;
  }

  VectorArray X(nx);
  for (int i=0; i<nx; ++i)
    smx->field(defoFields[i]).fetch(X[i]);

  // assemble reduced-size eigenvalue problem
  CpxMatrix MX(nx,nx), KX(nx,nx);
  for (int j=0; j<nx; ++j) {
    Vector mxj(6*smx->nnodes()), kxj(6*smx->nnodes());
    M.multiply(X[j], mxj);
    K.multiply(X[j], kxj);
    for (int i=0; i<=j; ++i) {
      MX(i,j) = dot(X[i], mxj);
      KX(i,j) = dot(X[i], kxj);
    }
  }

  // fill upper triangular part
  for (int j=0; j<nx; ++j) {
    for (int i=j+1; i<nx; ++i) {
      MX(i,j) = MX(j,i);
      KX(i,j) = KX(j,i);
    }
  }

  // solve reduced-order eigenvalue problem
  CpxVector lambda(nx);
  CpxMatrix Q(nx,nx);
  gen_eig(MX, KX, lambda, Q);

  // transform states and overwrite displacement vectors
  VectorArray Y(nx);
  for (int i=0; i<nx; ++i) {
    Y[i].resize(6*smx->nnodes());
    for (int j=0; j<nx; ++j)
      axpby( Q(j,i).real(), X[j], 1.0, Y[i] );

    MxMeshField & fld( smx->field(defoFields[i]) );
    string fname = "AugmentedState " + str(i+1);
    fld.copyReal(fname, 6, Y[i].pointer());
    // fld.valueClass( MxMeshField::Eigenmode );
  }

  // TODO:
  // reduce number of states by PCA

  // compute resulting reduced-order mass and stiffness matrices
  Matrix MY(nx,nx), KY(nx,nx);
  for (int j=0; j<nx; ++j) {
    Vector mxj(6*smx->nnodes()), kxj(6*smx->nnodes());
    M.multiply(Y[j], mxj);
    K.multiply(Y[j], kxj);
    for (int i=0; i<nx; ++i) {
      MY(i,j) = dot(Y[i], mxj);
      KY(i,j) = dot(Y[i], kxj);
    }
  }

  XmlElement xe("ReducedOrderSystem");
  xe["nstate"] = str(nx);
  {
    XmlElement xm("MassMatrix");
    xm.asBinary(nx*nx, MY.pointer(), false);
    xe.append(std::move(xm));
  }
  {
    XmlElement xm("StiffnessMatrix");
    xm.asBinary(nx*nx, KY.pointer(), false);
    xe.append(std::move(xm));
  }

  smx->annotate(xe);
}


