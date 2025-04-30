
/* ------------------------------------------------------------------------
 * project:    Surf
 * file:       symsurf.cpp
 * begin:      May 2007
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Automatically mirrored surface
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#include "linearsurf.h"
#include "skinsurf.h"
#include "stitchedsurf.h"
#include "wingletblend.h"
#include "dnmesh.h"
#include "dnrefine.h"
#include "igesfile.h"
#include "iges124.h"
#include "symsurf.h"

using namespace std;

SymSurf::SymSurf(const std::string & name) : Surface(name)
{
  // default mirror plane
  mipo = 0.0;
  mipn[0] = 0.0;
  mipn[1] = 1.0;
  mipn[2] = 0.0;
}

void SymSurf::init(const Surface & srf)
{
  psf = SurfacePtr(srf.clone());
}

Vct3 SymSurf::eval(Real u, Real v) const
{
  if (v <= 0.5) {
    return psf->eval(u, 2*v);
  } else {
    Vct3 mp;
    mirror(psf->eval(u, 2 - 2*v), mp);
    return mp;
  }
}

Vct3 SymSurf::derive(Real u, Real v, uint du, uint dv) const
{
  if (du == 0 and dv == 0)
    return eval(u,v);
    
  if (v <= 0.5) {
    Real f = pow(2.0, Real(dv));
    return f*psf->derive(u, 2*v, du, dv);
  } else {
    Real f = pow(-2.0, Real(dv));
    Vct3 gu = f*psf->derive(u, 2 - 2*v, du, dv);
    return gu - (2.0*dot(gu,mipn))*mipn;
  }
}

void SymSurf::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  if (v <= 0.5) {
    psf->plane(u, 2*v, S, Su, Sv);
    Sv *= 2.0;
  } else {
    Vct3 tmp;
    psf->plane(u, 2-2*v, tmp, Su, Sv);
    mirror(tmp, S);
    Sv *= -2.0;
    Su -= 2.0*dot(Su,mipn)*mipn;
    Sv -= 2.0*dot(Sv,mipn)*mipn;
  }
} 
    
Vct3 SymSurf::normal(Real u, Real v) const
{
  Vct3 S, Su, Sv;
  plane(u, v, S, Su, Sv);
  Vct3 nrm( cross(Su, Sv) );
  normalize(nrm);
  return nrm;
}

void SymSurf::apply()
{
  psf->setTrafoMatrix(RFrame::trafoMatrix());
  psf->apply();
  
  // transform mirror plane as well 
  Vct3 opn(mipo + mipn);
  mipo = RFrame::forward(mipo);
  mipn = RFrame::forward(opn) - mipo;
  normalize(mipn);
  
  RFrame::clear();
}

void SymSurf::initGridPattern(Vector & up, Vector & vp) const
{
  Vector vps;
  psf->initGridPattern(up, vps);
  int nv = vps.size();
  vp.resize(2*nv - 1);
  for (int i=0; i<nv; ++i) {
    vp[i] = 0.5*vps[i];
    vp[2*nv-2-i] = 1.0 - vp[i]; 
  }
}

void SymSurf::initGrid(Real lmax, Real lmin, Real phimax, 
                       PointGrid<2> & pts) const
{
  PointGrid<2> right;
  psf->initGrid(lmax, lmin, phimax, right);
  
  uint nv = right.ncols();
  uint nu = right.nrows();
  pts.resize(nu, 2*nv-1);
  for (uint j=0; j<nv; ++j) {
    for (uint i=0; i<nu; ++i) {
      const Vct2 & p(right(i,j));
      pts(i,j)[0] = p[0];
      pts(i,j)[1] = 0.5*p[1];
      pts(i,2*nv-2-j)[0] = p[0];
      pts(i,2*nv-2-j)[1] = 1.0 - 0.5*p[1];
    }
  }
}


void SymSurf::initMesh(const DnRefineCriterion & c, DnMesh & gnr) const
{
  Real lmax = 2.*c.maxLength();
  Real lmin = 2.*c.minLength();
  Real phimax = PI/3.;
  
  PointGrid<2> qts;
  initGrid(lmax, lmin, phimax, qts);
  gnr.init(qts);
  gnr.elimNeedles(1.5*c.maxStretch(), 0.5*c.maxPhi());
  gnr.markKinks( 0.25*PI );
}

XmlElement SymSurf::toXml(bool) const
{
  XmlElement xe("SymSurf");
  xe["name"] = ids;
  xe["miporigin"] = str(mipo);
  xe["mipnormal"] = str(mipn);
  if (psf)
    xe.append(psf->toXml());
  return xe;
}
    
void SymSurf::fromXml(const XmlElement & xe)
{
  if (xe.name() != "SymSurf")
    throw Error("SymSurf: Incompatible XML representation: "+xe.name());
  
  if (xe.hasAttribute("name"))
    rename(xe.attribute("name"));
  fromString(xe.attribute("miporigin"), mipo);
  fromString(xe.attribute("mipnormal"), mipn);
  
  if (xe.begin() != xe.end())
    psf = Surface::createFromXml( *(xe.begin()) );
}

int SymSurf::toIges(IgesFile & file, int tfi) const
{
  int s1 = psf->toIges(file, tfi);

  // if the child surface supports export to IGES, add the surface again 
  // with a reflection transformation matrix added 
  if (s1 != 0) {
    
    Mtx33 r;
    Vct3 t;
    Real c = dot(mipn,mipo);
    Real iasq = 1.0/dot(mipn,mipn);
    for (int j=0; j<3; ++j) {
      r(j,j) = 1.0;
      for (int i=0; i<3; ++i) 
        r(i,j) -= 2.0 * (mipn[i]*mipn[j])*iasq;
      t[j] = 2*c*iasq*mipn[j];
    }
    
    // this reflection must be subject to the same 
    // global transformation tfi
    IgesTrafoMatrix tfm;
    tfm.setup( r.pointer(), t.pointer() );
    tfm.trafoMatrix( tfi );
    tfm.label("REFL_TRF");
    int tfr = tfm.append(file);
    
    // add reflected surface
    psf->toIges(file, tfr);

    return tfr;
  } else {
    return 0;
  }
}
