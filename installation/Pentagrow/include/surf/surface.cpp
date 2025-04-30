
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
 
#include "srfprojector.h"
#include "initgrid.h"
#include "rotsurf.h"
#include "stitchedsurf.h"
#include "linearsurf.h"
#include "skinsurf.h"
#include "cylinder.h"
#include "wingletblend.h"
#include "symsurf.h"
#include "transurf.h"
#include "planesurface.h"
#include "polysplinesurf.h"
#include "revosurf.h"
#include "rationalsplinesurface.h"
#include "dnmesh.h"
#include "dnrefine.h"
#include "surface.h"
#include "igesfile.h"
#include "igesentity.h"
#include "iges124.h"
#include "iges128.h"
#include "iges406.h"
#include <genua/pattern.h>
#include <genua/xcept.h>
#include <genua/meshfields.h>
#include <genua/dbprint.h>
#include <genua/cgmesh.h>
#include <iostream>
#include <atomic>

using namespace std;

// static data
std::atomic<uint> g_surface_object_counter(1);

uint Surface::nextObjectId()
{
  return g_surface_object_counter++;
}

Surface::Surface(const string &s)
  : ids(s) { object_id = nextObjectId(); }

void Surface::eval(const PointList<2> & uv, PointList<3> & xyz) const
{
  const int np = uv.size();
  xyz.resize(np);
  for (int i=0; i<np; ++i)
    xyz[i] = eval(uv[i][0], uv[i][1]);
}

Vct3 Surface::normal(Real u, Real v) const    
{
  Vct3 du( derive(u,v,1,0) );
  Vct3 dv( derive(u,v,0,1) );
  Vct3 nrm( cross(du,dv) );
  normalize(nrm);
  return nrm;
}

Real Surface::vcurvature(Real u, Real v) const
{
  u = clamp(u, 0.0, 1.0);
  v = clamp(v, 0.0, 1.0);
  
  Vct3 dc = derive(u, v, 0, 1);
  Vct3 ddc = derive(u, v, 0, 2);
  
  return localCurvature(dc, ddc);
}

Real Surface::ucurvature(Real u, Real v) const
{
  u = clamp(u, 0.0, 1.0);
  v = clamp(v, 0.0, 1.0);
  
  Vct3 dc = derive(u, v, 1, 0);
  Vct3 ddc = derive(u, v, 2, 0);
  
  return localCurvature(dc, ddc);
}

Real Surface::gaussianCurvature(Real u, Real v) const
{
  Vct3 Su = derive(u, v, 1, 0);
  Vct3 Sv = derive(u, v, 0, 1);
  Vct3 Suu = derive(u, v, 2, 0);
  Vct3 Suv = derive(u, v, 1, 1);
  Vct3 Svv = derive(u, v, 0, 2);
  Vct3 nrm = cross(Su, Sv);
  normalize(nrm);
  
  // coefficients of the first fundamental
  Real E = dot(Su, Su);
  Real F = dot(Su, Sv);
  Real G = dot(Sv, Sv);
  
  // coefficients of the second fundamental
  Real L = dot(Suu, nrm);
  Real M = dot(Suv, nrm);
  Real N = dot(Svv, nrm);
  
  return (L*N - M*M) / (E*G - F*F);
}

void Surface::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  S = eval(u, v);
  Su = derive(u, v, 1, 0);
  Sv = derive(u, v, 0, 1);
}

bool Surface::project(const Vct3 & pt, Vct2 & q, Real tol, Real dpmin) const
{
  SrfProjector pj(*this, tol, dpmin);
  return pj.project(pt, q);
}

bool Surface::intersect(const AbstractCurve &c, Vct2 &q, Real &t, Real tol, Real dpmin) const
{
  SrfProjector pj(*this, tol, dpmin);
  return pj.intersect(c, q, t);
}

SurfacePtr Surface::createFromXml(const XmlElement & xe)
{
  if (xe.name() == "RotSurf") {
    RotSurf *sp = new RotSurf("Unknown");
    sp->fromXml(xe);
    return SurfacePtr(sp);
  } else if (xe.name() == "LinearSurf") {
    LinearSurf *sp = new LinearSurf("Unknown");
    sp->fromXml(xe);
    return SurfacePtr(sp);
  } else if (xe.name() == "SkinSurf") {
    SkinSurf *sp = new SkinSurf("Unknown");
    sp->fromXml(xe);
    return SurfacePtr(sp);
  } else if (xe.name() == "Cylinder") {
    Cylinder *sp = new Cylinder("Unknown");
    sp->fromXml(xe);
    return SurfacePtr(sp);
  } else if (xe.name() == "StitchedSurf") {
    StitchedSurf *sp = new StitchedSurf("Unknown");
    sp->fromXml(xe);
    return SurfacePtr(sp);
  } else if (xe.name() == "WingletBlend") {
    WingletBlend *sp = new WingletBlend("Unknown");
    sp->fromXml(xe);
    return SurfacePtr(sp);
  } else if (xe.name() == "SymSurf") {
    SymSurf *sp = new SymSurf("Unknown");
    sp->fromXml(xe);
    return SurfacePtr(sp);
  } else if (xe.name() == "TranSurf") {
    TranSurf *ts = new TranSurf("Unknown");
    ts->fromXml(xe);
    return SurfacePtr(ts);
  } else if (xe.name() == "PlaneSurface") {
    PlaneSurface *ps = new PlaneSurface("Unknown");
    ps->fromXml(xe);
    return SurfacePtr(ps);
  } else if (xe.name() == "PolySplineSurf") {
    PolySplineSurf *ps = new PolySplineSurf("Unknown");
    ps->fromXml(xe);
    return SurfacePtr(ps);
  } else if (xe.name() == "RationalSplineSurf") {
    RationalSplineSurf *ps = new RationalSplineSurf("Unknown");
    ps->fromXml(xe);
    return SurfacePtr(ps);
  } else if (xe.name() == "RevoSurf") {
    RevoSurf *ps = new RevoSurf("Unknown");
    ps->fromXml(xe);
    return SurfacePtr(ps);
  } else
    return SurfacePtr();
}

SurfacePtr Surface::createFromIges(const IgesFile &file,
                                   const IgesDirEntry &entry)
{
  SurfacePtr psf;
  if (entry.etype == 128) {

    IgesSplineSurface ispl;
    if (file.createEntity(entry, ispl)) {
      if (ispl.polynomial) {
        PolySplineSurf *pss = new PolySplineSurf;
        if (pss->fromIges(file, entry))
          psf.reset(pss);
      } else {  // rational
        RationalSplineSurf *rsp = new RationalSplineSurf;
        if (rsp->fromIges(file, entry))
          psf.reset(rsp);
      }
    }

  } else if (entry.etype == 118) {
    LinearSurf *srf = new LinearSurf();
    if (srf->fromIges(file, entry))
      psf.reset(srf);
  } else if (entry.etype == 120) {
    RevoSurf *srf = new RevoSurf();
    if (srf->fromIges(file, entry))
      psf.reset(srf);
  }
  else {
    dbprint("Surface cannot create entity type ", entry.etype);
  }

  return psf;
}

void Surface::setIgesName(const IgesFile & file,const IgesEntity & e)
{
  IgesDirEntry entry;
  IgesEntityPtr ep;
  IgesNameProperty e406;
  const int np = e.nPropRef();
  for (int i=0; i<np; ++i) {
    file.dirEntry( e.propRef(i), entry );
    if (entry.etype == 406) {
      ep = file.createEntity(entry);
      if (IgesEntity::as(ep, e406)) {
        rename( e406.str() );
        return;
      }
    }
  }

  // will end up here if no 406 property found
  std::string s = strip( e.label() );
  if (not s.empty())
    rename(s);
}

void Surface::dimStats(Surface::DimStat &stat) const
{
  const int nu = std::max(2, stat.nu);
  const int nv = std::max(2, stat.nv);
  PointGrid<3> ptg(nu,nv);
  for (int i=0; i<nu; ++i) {
    Real u = clamp(Real(i)/(nu-1), 0.0, 1.0);
    for (int j=0; j<nv; ++j) {
      Real v = clamp(Real(j)/(nv-1), 0.0, 1.0);
      ptg(i,j) = eval(u, v);
      for (int k=0; k<3; ++k) {
        Real pk = ptg(i,j)[k];
        stat.bbhi[k] = std::max(pk, stat.bbhi[k]);
        stat.bblo[k] = std::min(pk, stat.bblo[k]);
      }
    }
  }

  for (int i=1; i<nu; ++i) {
    for (int j=1; j<nv; ++j) {
      Real w = norm(ptg(i,j) - ptg(i-1,j)) + norm(ptg(i,j-1) - ptg(i-1,j-1));
      Real h = norm(ptg(i,j) - ptg(i,j-1)) + norm(ptg(i-1,j) - ptg(i-1,j-1));
      stat.area += 0.25*w*h;
    }
  }
}

Real Surface::typLength(int nu, int nv) const
{
  // evaluate 8x8 points on the surface
  PointGrid<3> ptg(nu,nv);
  for (int i=0; i<nu; ++i)
    for (int j=0; j<nv; ++j)
      ptg(i,j) = eval( Real(i)/(nu-1), Real(j)/(nv-1) );

  Real w, h, area(0);
  for (int i=1; i<nu; ++i)
    for (int j=1; j<nv; ++j) {
      w = norm(ptg(i,j) - ptg(i-1,j)) + norm(ptg(i,j-1) - ptg(i-1,j-1));
      h = norm(ptg(i,j) - ptg(i,j-1)) + norm(ptg(i-1,j) - ptg(i-1,j-1));
      area += 0.25*w*h;
    }

  return sqrt(area);
}

void Surface::initGrid(Real lmax, Real lmin, Real phimax, PointGrid<2> & pts) const
{
  // try to find a reasonable initial discretization
  Vector up, vp;
  initGridPattern(up, vp);
  InitGrid ig(this);

  ig.initPattern(up, vp);
  ig.refine(lmax, lmin, phimax);

  bool usym , vsym;
  isSymmetric(usym, vsym);
  if (usym)
    ig.enforceUSymmetry();
  if (vsym)
    ig.enforceVSymmetry();
  ig.collect(pts);
}

void Surface::initMesh(const DnRefineCriterion & c, DnMesh & gnr) const
{
  Real lmax = 2.*c.maxLength();
  Real lmin = 2.*c.minLength();
  Real phimax = min(rad(60.), 1.5*c.maxPhi());

  PointGrid<2> qgrid;
  initGrid(lmax, lmin, phimax, qgrid);
  // gnr.init(qts);
  // gnr.elimNeedles(1.5*c.maxStretch(), 0.5*c.maxPhi());

  gnr.init(qgrid, c.maxStretch());
}

void Surface::initGridPattern(Vector & up, Vector & vp) const
{
  up = equi_pattern(15);
  vp = equi_pattern(9);
}

void Surface::tessellate(CgMesh & cgm, uint maxtri) const
{
  // request reasonable grid discretization
  Vector up, vp;
  initGridPattern(up, vp);

  // impose a limit on refinement of 2*maxtri nodes per surface
  {
    Real freduce = sqrt(0.5*Real(maxtri) / (up.size() * vp.size()));
    if (freduce < 1) {
      Vector tmp;
      interpolate_pattern(up, freduce*up.size(), tmp);
      tmp.swap(up);
      tmp.clear();
      interpolate_pattern(vp, freduce*vp.size(), tmp);
      tmp.swap(vp);
    }
  }

  // evaluate surface grid
  const int nu = up.size();
  const int nv = vp.size();
  PointGrid<3,float> vtx(nu,nv), nrm(nu,nv);
  Vct3 S, Su, Sv;
  for (int j=0; j<nv; ++j) {
    for (int i=0; i<nu; ++i) {
      this->plane(up[i], vp[j], S, Su, Sv);
      vtx(i,j) = Vct3f( S );
      nrm(i,j) = Vct3f( cross(Su,Sv).normalized() );
    }
  }

  // generate triangles
  const int ntri = 2*(nu-1) * (nv-1);
  Indices itri(3*ntri);
  uint p1, p2, p3, p4, fi1, fi2;
  for (int i=0; i<nu-1; ++i) {
    for (int j=0; j<nv-1; ++j) {
      p1 = i + j*nu;
      p2 = i+1 + j*nu;
      p3 = i+1 + (j+1)*nu;
      p4 = i + (j+1)*nu;

      fi1 = 2*(nv-1)*i + 2*j;
      fi2 = fi1 + 1;

      itri[3*fi1 + 0] = p1;
      itri[3*fi1 + 1] = p2;
      if ( (i & 0x1) == (j & 0x1) ) {
        itri[3*fi1 + 2] = p3;
        itri[3*fi2 + 0] = p1;
      } else {
        itri[3*fi1 + 2] = p4;
        itri[3*fi2 + 0] = p2;
      }
      itri[3*fi2 + 1] = p3;
      itri[3*fi2 + 2] = p4;
    }
  }

  cgm.importMesh(nu*nv, vtx.pointer(), nrm.pointer(), ntri, &itri[0]);
}

void Surface::isSymmetric(bool & usym, bool & vsym) const
{
  usym = false;
  vsym = false;
}

int Surface::toIges(IgesFile &, int) const
{
  return 0;
}

bool Surface::fromIges(const IgesFile &, const IgesDirEntry &)
{
  return false;
}

void Surface::applyIgesTrafo(const IgesFile & file, const IgesDirEntry & dir)
{
  // chained transformation
  Mtx44 chain;
  unity(chain);

  // extract transformation matrix recursively --
  // transformation matrix entity may be transformed itself
  bool haveTrafo = false;
  int dtf = dir.trafm;
  while (dtf != 0) {

    IgesDirEntry entry;
    file.dirEntry(dtf, entry);
    IgesEntityPtr eptr = file.createEntity(entry);
    IgesTrafoMatrix itf;
    Mtx44 trafo;
    if (IgesEntity::as(eptr, itf)) {
      for (int j=0; j<3; ++j) {
        trafo(j,3) = itf.translation(j);
        for (int i=0; i<3; ++i)
          trafo(i,j) = itf.rotation(i,j);
      }
      trafo(3,3) = 1.0;

      // enchain
      chain = trafo * chain;
      haveTrafo = true;
    }

    // break infinite recursion
    if (entry.trafm == dtf)
      break;
    dtf = entry.trafm;
  }

  if (haveTrafo) {

    // debug
    cout << "IGES trafo: " << endl << chain << endl;

    setTrafoMatrix(chain);
    apply();
  }

  // look for name property
  IgesNameProperty e406;
  IgesEntityPtr eptr = file.createEntity(dir);
  const int nprop = eptr->nPropRef();
  for (int i=0; i<nprop; ++i) {
    if (file.createEntity(eptr->propRef(i), e406)) {
      rename(e406.str());
      break;
    }
  }

  if (name().empty()) {
    string s(dir.elabel, 8);
    rename(strip(s));
  }
}

void Surface::gridViz(MeshFields & mvz) const
{
  Vector up, vp;
  initGridPattern(up, vp);
  const int nu = up.size();
  const int nv = vp.size();
  PointGrid<3> pg(nu,nv);
  for (int j=0; j<nv; ++j)
    for (int i=0; i<nu; ++i)
      pg(i,j) = eval(up[i], vp[j]);
  mvz.addMesh(pg);
}
