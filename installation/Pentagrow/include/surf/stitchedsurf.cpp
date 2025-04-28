
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
 
#include <genua/pattern.h>
#include "wingtiparc.h"
#include "initgrid.h"
#include "linearsurf.h"
#include "skinsurf.h"
#include "wingletblend.h"
#include "dnmesh.h"
#include "transurf.h"
#include "stitchedsurf.h"

using namespace std;

// -------------------------------------------------------------------------

static bool nominally_less(const XmlElement & a, const XmlElement & b)
{
  int ia, ib;
  ia = Int(a.attribute("index"));
  ib = Int(b.attribute("index"));
  return ia < ib;
}

static SurfacePtr findByName(const SurfaceArray & s, const string & id)
{
  for (uint i=0; i<s.size(); ++i) {
    if (not s[i])
      continue;
    if (s[i]->name() == id)
      return s[i];
  }

  // this might be the result of a user error in input file --- troublesome!
  throw Error("No such surface named '"+id+"' in list.");
}

// -------------------- StitchedSurf --------------------------------------

void StitchedSurf::init(const SurfaceArray & s, const Vector & vb)
{
  vbreak = vb;
  const uint ns(s.size());
  sfl.resize(ns);
  for (uint i=0; i<ns; ++i) {
    sfl[i] = SurfacePtr( s[i]->clone() );
    sfl[i]->rename(ids + "Sgm" + str(i+1));
  }
}

void StitchedSurf::init(const StitchedWingSpec & spec)
{
  spec.construct( sfl, vbreak);
}

Vct3 StitchedSurf::eval(Real u, Real v) const
{
  uint s = segment(v);
  Real t = (v-vbreak[s-1]) / (vbreak[s] - vbreak[s-1]);
  return sfl[s-1]->eval(u, t);
}
    
Vct3 StitchedSurf::derive(Real u, Real v, uint ku, uint kv) const
{
  if (ku == 0 and kv == 0)
    return eval(u, v);
  else {
    uint s = segment(v);
    Real vspan = vbreak[s] - vbreak[s-1];
    Real t = (v-vbreak[s-1]) / vspan;
    Real f = pow(1.0 / vspan, Real(kv));
    return f*sfl[s-1]->derive(u, t, ku, kv);
  }
}

void StitchedSurf::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  uint s = segment(v);
  Real vspan = vbreak[s] - vbreak[s-1];
  Real t = (v-vbreak[s-1]) / vspan;
  Real f = 1.0 / vspan;
  sfl[s-1]->plane(u, t, S, Su, Sv);
  Sv *= f;
} 
    
Vct3 StitchedSurf::normal(Real u, Real v) const
{
  Vct3 S, Su, Sv;
  plane(u, v, S, Su, Sv);
  Vct3 nrm( cross(Su, Sv) );
  normalize(nrm);
  return nrm;
}
    
void StitchedSurf::apply()
{
  Mtx44 m(RFrame::trafoMatrix());
  for (uint i=0; i<sfl.size(); ++i) {
    sfl[i]->setTrafoMatrix(m);
    sfl[i]->apply();
  }
  RFrame::clear();
}
    
// void StitchedSurf::initGrid(Real lmax, Real phimax, PointGrid<2> & pts) const
// {
//   uint nu(0), nv(0);
//   const uint ns(sfl.size());
//   vector<PointGrid<2> > grids(ns);
//   for (uint i=0; i<ns; ++i) {
//     
//     // let segment initialize on its own 
//     // and see if that yields an acceptable mesh 
//     sfl[i]->initGrid(lmax, phimax, grids[i]);
//     
//     // segment mesh must be compatible in u-direction 
//     if (nu == 0) {
//       nu = grids[i].nrows();
//     } else if (grids[i].nrows() != nu) {
//       InitGrid ig(sfl[i].get());
//       ig.initPattern(equi_pattern(nu), equi_pattern(11));
//       ig.vRefineByLength(lmax);
//       ig.uAdapt(lmax, phimax);
//       Real stretch;
//       nv = ig.ncols();
//       do {
//         nv += 8;
//         stretch = ig.vRefineByStretch(nv, 100.);
//       } while (stretch > 100.);
//       ig.smooth(1);
//       ig.collect(grids[i]);
//     }
//     nv += grids[i].ncols();
//   }
//   
//   // avoid duplicate columns
//   nv -= ns-1;
//   
//   // merge point grids
//   Real vo, vd;
//   uint start, jacc(0);
//   pts.resize(nu, nv);
//   for (uint k=0; k<ns; ++k) {
//     vo = vbreak[k];
//     vd = vbreak[k+1] - vo;
//     const PointGrid<2> & g(grids[k]);
//     const uint gnv(g.ncols());
//     start = 1;
//     if (k == 0)
//       start = 0;
//     for (uint j=start; j<gnv; ++j) {
//       for (uint i=0; i<nu; ++i) {
//         const Vct2 & p(g(i,j));
//         pts(i,jacc+j-start) = vct(p[0], vo+vd*p[1]);   
//       }
//     }
//     jacc += gnv-start;
//   }
// }    

// void StitchedSurf::initGrid(Real lmax, Real phimax, PointGrid<2> & pts) const
// {
//   Vector vp(equi_pattern(11));
//   uint nu = max(15, 2*int(2*PI/phimax));
//   nu += 1 - (nu%2);
//   
//   // try to be smart : if the name contains "Wing", we pre-seed with a 
//   // suitable distribution of points in circumferential direction
//   Vector up(nu);
//   if (ids.find("Wing") != string::npos or ids.find("wing") != string::npos) {
//     up = cosine_pattern(nu, 2*PI, PI, 0.92);
//   } else {
//     up = equi_pattern(nu);
//   }
//   
//   uint nv(0);
//   const uint ns(sfl.size());
//   vector<PointGrid<2> > grids(ns);
//   for (uint i=0; i<ns; ++i) {
//     
//     // let segment initialize on its own 
//     // and see if that yields an acceptable mesh 
//     sfl[i]->initGrid(lmax, phimax, grids[i]);
//     
//     // segment mesh must be compatible in u-direction 
//     if (grids[i].nrows() != up.size()) {
//       InitGrid ig(sfl[i].get());
//       ig.initPattern(up, vp);
//       ig.vRefineByLength(lmax);
//       ig.collect(grids[i]);
//     }
//     nv += grids[i].ncols();
//   }
//   
//   // avoid duplicate columns
//   nv -= ns-1;
//   
//   // merge point grids
//   Real vo, vd;
//   uint start, jacc(0);
//   pts.resize(nu, nv);
//   for (uint k=0; k<ns; ++k) {
//     vo = vbreak[k];
//     vd = vbreak[k+1] - vo;
//     const PointGrid<2> & g(grids[k]);
//     const uint gnv(g.ncols());
//     start = 1;
//     if (k == 0)
//       start = 0;
//     for (uint j=start; j<gnv; ++j) {
//       for (uint i=0; i<nu; ++i) {
//         const Vct2 & p(g(i,j));
//         pts(i,jacc+j-start) = vct(p[0], vo+vd*p[1]);   
//       }
//     }
//     jacc += gnv-start;
//   }
// }
    
void StitchedSurf::initMesh(const DnRefineCriterion & c, DnMesh & gnr) const
{
  Surface::initMesh(c, gnr);
  gnr.markKinks( 0.25*PI );
}
    
void StitchedSurf::initGridPattern(Vector & up, Vector & vp) const
{
  // assemble subgrids
  vp = Vector();
  Vector utmp, vtmp;
  const int ns = sfl.size(); 
  for (int i=0; i<ns; ++i) {
    sfl[i]->initGridPattern(utmp, vtmp);
    vtmp *= vbreak[i+1] - vbreak[i];
    vtmp += vbreak[i];
    vp.insert(vp.end(), vtmp.begin(), vtmp.end());
    up.insert(up.end(), utmp.begin(), utmp.end());
  }
  
  // merge almost identical parameter values 
  std::sort(up.begin(), up.end());
  std::sort(vp.begin(), vp.end());
  
  almost_equal<Real> mp(1e-3);
  up.erase( std::unique(up.begin(), up.end(), mp), up.end() );
  vp.erase( std::unique(vp.begin(), vp.end(), mp), vp.end() );
}
    
void StitchedSurf::isSymmetric(bool & usym, bool & vsym) const
{
  usym = false;
  vsym = false;
}
   
XmlElement StitchedSurf::toXml(bool) const
{
  XmlElement xe("StitchedSurf");
  xe["name"] = ids;
  xe["nsurf"] = str(sfl.size());
  
  stringstream ss;
  XmlElement xb("Breaks");
  xb["count"] = str(vbreak.size());
  ss << vbreak;
  xb.text(ss.str());
  xe.append(std::move(xb));
  
  for (uint i=0; i<sfl.size(); ++i) {
    XmlElement xs = sfl[i]->toXml();
    xs.attribute("index") = str(i);
    xe.append(std::move(xs));
  }

  return xe;  
}
    
void StitchedSurf::fromXml(const XmlElement & xe)
{
  if (xe.name() != "StitchedSurf")
    throw Error("StitchedSurf: incompatible XML representation.");

  Vector vb;
  rename(xe.attribute("name"));
  sfl.clear();
  XmlElement::const_iterator itr;
  std::vector<XmlElement> xsurf;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {

    if (itr->name() == "Breaks") {
      int nb = Int(itr->attribute("count"));
      stringstream ss;
      ss << itr->text();
      vb.resize(nb);
      for (int i=0; i<nb; ++i)
        ss >> vb[i];
      
    } else if (itr->hasAttribute("index"))
      xsurf.push_back(*itr);
  }

  // sort xml representations by 'index' attribute
  std::sort(xsurf.begin(), xsurf.end(), nominally_less);

  // instantiate surfaces which can be
  sfl.resize(xsurf.size());
  for (uint i=0; i<xsurf.size(); ++i) {
    SurfacePtr cp = Surface::createFromXml(xsurf[i]);
    if (cp)
      sfl[i] = cp;    
  }

  // create tip arcs, if any are defined
  for (uint i=0; i<xsurf.size(); ++i) {
    if (xsurf[i].name() == "WingTipArc") {
      string sname = xsurf[i].attribute("surface");
      SurfacePtr refsrf = findByName(sfl, sname);
      Real span = Float(xsurf[i].attribute("span"));
      Real vpos = Float(xsurf[i].attribute("vpos"));
      WingTipArc *arc;
      if (xsurf[i].hasAttribute("name"))
        arc = new WingTipArc(xsurf[i].attribute("name"));
      else
        arc = new WingTipArc(sname+"Arc"+str(vpos));
      arc->init(*refsrf, vpos, span);
      sfl[i] = SurfacePtr(arc);
    }

    // now, every entry in sfl must be properly defined
    assert(sfl[i]);
  }
  
  if (vb.size() != sfl.size()+1) {
    stringstream ss;
    ss << "Inconsistent surface data in xml file. " << endl;
    ss << "Expected " << sfl.size()+1 << " breaks, found " << vb.size() 
       << endl; 
    throw Error(ss.str());
  }
  
  // setup inter-surface evaluation stuff
  init(sfl, vb);
}

int StitchedSurf::toIges(IgesFile & file, int tfi) const
{
  int ilast(0);
  const int n = sfl.size();
  for (int i=0; i<n; ++i)
    ilast = sfl[i]->toIges(file, tfi);
  return ilast;
}

void StitchedSurf::dimStats(Surface::DimStat &stat) const
{
  uint nuctrl(0);
  uint nvctrl(0);
  for (const SurfacePtr &psf : sfl) {
    psf->dimStats(stat);
    nuctrl = std::max(nuctrl, stat.nControlU);
    nvctrl += stat.nControlV;
  }
  stat.nControlU = nuctrl;
  stat.nControlV = nvctrl;
}

// ---------------------- StitchedWingSpec ---------------------------------

uint StitchedWingSpec::addSegment(uint first, uint last, SegType s) 
{
  assert((sEnd.empty() and first == 0) or first == sEnd.back());
  assert(s != SegWlBlend or last-first == 1);
  assert(first < cpa.size());
  assert(last < cpa.size());
  assert(last > first);
  
  // need at least four curves for cubic segments  
  if (s == SegCubic and last-first < 3)
    s = SegLinear;
  
  sBegin.push_back(first);
  sEnd.push_back(last);
  sType.push_back(s);
  
  return sType.size() - 1;
}
    
void StitchedWingSpec::construct(SurfaceArray & slist, Vector & vbreak) const
{
  slist.clear();
  Vector svp;
  Curve::arclenParamet(cpa, svp);
  if (sType.empty()) {
    LinearSurf *lsf = new LinearSurf("RuledWingSgm1");
    lsf->init(cpa);
    slist.push_back( SurfacePtr(lsf) );
    vbreak.resize(2);
    vbreak[0] = 0.0;
    vbreak[1] = 1.0;
  } else {
    const uint nseg(sType.size());
    slist.resize(nseg);
    vbreak.resize(nseg+1);
    for (uint i=0; i<nseg; ++i) {
      
      // extract a slice of curves 
      const uint iStart(sBegin[i]);
      const uint iEnd(sEnd[i]);
      CurvePtrArray c(iEnd-iStart+1);
      for (uint j=iStart; j<=iEnd; ++j)
        c[j-iStart] = cpa[j];
      
      // mark the last section of each segment
      vbreak[i+1] = svp[iEnd];
      
      if (sType[i] == SegLinear) {
        string s = "RuledWingSgm" + str(i+1); 
        LinearSurf *lsf = new LinearSurf(s);
        lsf->init(c);
        slist[i] = SurfacePtr(lsf);
      } else if (sType[i] == SegCubic) {
        string s = "SkinnedWingSgm" + str(i+1);
        SkinSurf *ssf = new SkinSurf(s);
        ssf->init(c, true, true);
        slist[i] = SurfacePtr(ssf);
      } else if (sType[i] == SegWlBlend) {
        
        // delay until the other surfaces are build 

      }
      
    }
    
    // construct winglet blends 
    for (uint i=0; i<nseg; ++i) {
      const uint iStart(sBegin[i]);
      if (sType[i] == SegWlBlend) {
        assert(i != 0 and i < nseg-1);
        string s = "WingletBlendSgm" + str(i+1);
        TranSurf *ts = new TranSurf(s);
        ts->init(slist[i-1], cpa[iStart], slist[i+1], cpa[iStart+1]);
        slist[i] = SurfacePtr(ts);
      }
    }
    
  }
}



