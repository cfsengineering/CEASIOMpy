
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
 
#include "curve.h"
#include "dnmesh.h"
#include "dnwingcriterion.h"

using namespace std;

void DnWingCriterion::initBreaks()
{
  vbreak.resize(2);
  scale.resize(2);
  vbreak[0] = 0.0;
  vbreak[1] = 1.0;
  scale[0] = 1.0;
  scale[1] = 1.0;
}

void DnWingCriterion::addBreak(Real v, Real f)
{
  Vector::iterator pos;
  pos = std::lower_bound(vbreak.begin(), vbreak.end(), v);
  uint ipos = std::distance(vbreak.begin(), pos);
  vbreak.insert(pos, v);
  scale.insert(scale.begin()+ipos, 1.0 / f);
}

void DnWingCriterion::addBreaks(const CurvePtrArray & cpa, bool symflag)
{
  const uint nc(cpa.size());
//  Vector vp(nc);
  Curve::arclenParamet( cpa, vbreak );
  
//   // compute curve centers
//   const uint nu(16);
//   PointList<3> ctr(nc);
//   for (uint i=0; i<nc; ++i) {
//     for (uint j=0; j<nu; ++j) {
//       Real u = Real(j+1) / (nu+1);
//       ctr[i] += cpa[i]->eval(u);
//     }
//     ctr[i] *= 1.0/nu;
//   }
//   
//   // obtain parameters from arclength parametrization of centerline
//   for (uint i=1; i<nc; ++i) {
//     Real dst = norm(ctr[i] - ctr[i-1]);
//     vp[i] = vp[i-1] + dst;
//   }  
  
  // length of line through curve centers
//   Real slen = vp.back();
//   vbreak = vp / slen;
  
  // determine scaling : compute local chord for each curve
  Vector chord(nc);
  Real cmx(0.0);
  const uint nup(8);
  for (uint i=0; i<nc; ++i) {
    Vct3 te( cpa[i]->eval(0.0) );
    Real u, c;
    chord[i] = 0.0;
    for (uint j=0; j<nup; ++j) {
      u =  0.45 + 0.1*j/(nup-1);
      c = norm(cpa[i]->eval(u) - te);
      chord[i] = max(c, chord[i]);
      cmx = max(cmx, c);
    }
  }
  
  scale.resize(nc);
  for (uint i=0; i<nc; ++i) {
    scale[i] = cmx / chord[i];
  }
  
  // figure out how to assemble vbreak and scale vector 
  // for symmetric wings (assumes mirroring at xz-plane) 
  if (symflag) {
      Vector bt(vbreak), st(scale);
      vbreak.resize(2*nc-1);
      scale.resize(2*nc-1);
      for (uint i=0; i<nc; ++i) {
        vbreak[i] = 0.5*bt[i];
        vbreak[2*nc-2-i] = 1.0 - 0.5*bt[i];
        scale[i] = scale[2*nc-2-i] = st[i];
      }
  }
}

void DnWingCriterion::addVKinks(const Surface & srf, const Vector & vk)
{
  vkinks = vk;
  if (vkinks.empty()) {
    svkinks.clear();
    return;
  }
  
  sort(vkinks.begin(), vkinks.end());
  const uint nk(vkinks.size());
  const uint nu(8);
  svkinks.resize(nk);
  const Real vtol(1e-5);
  for (uint i=0; i<nk; ++i) {
    if (vkinks[i] > vtol and vkinks[i] < 1.0-vtol) {
      for (uint j=0; j<nu; ++j) {
        Real u = Real(j+1)/(nu+1);
        svkinks[i] += srf.derive(u , vkinks[i] - vtol, 0, 1);
        svkinks[i] += srf.derive(u , vkinks[i] + vtol, 0, 1);
      }
    } else {
      for (uint j=0; j<nu; ++j) {
        Real u = Real(j+1)/(nu+1);
        svkinks[i] += srf.derive(u , vkinks[i], 0, 1);
      }
    }
    normalize(svkinks[i]);
  }
}

Real DnWingCriterion::eval(const uint *vi) const
{
  assert(msh != 0);
  
  // invalid triangles are not refined
  if (vi[0] == NotFound)
    return 0.0;
  
  // fetch vertices
  const Vct3 & p1(msh->position(vi[0]));
  const Vct3 & p2(msh->position(vi[1]));
  const Vct3 & p3(msh->position(vi[2]));

  // compute edge lengths 
  Real len[3], lmax, lmin;
  len[0] = norm(p2-p1);
  len[1] = norm(p3-p1);
  len[2] = norm(p3-p2);
  lmax = max( len[0], max(len[1], len[2]) );
  lmin = min( len[0], min(len[1], len[2]) );  
  // assert(lmin > 0);
  if (lmax < 2*minlen)
    return 0.0;

  // compute triangle area and stretch
  const Real sf(0.43301270189222); // sqrt(3)/4
  Vct3 ntri( cross(p2-p1, p3-p1) );
  Real area = 0.5*norm(ntri);
  assert(area > 0);
  Real stretch = sf*sq(lmax) / area;  

  // if the triangle is too small by area, stop
  if (area < sf*sq(minlen))
    return 0.0;
  
  Vct3 n1(msh->normal(vi[0]));
  Vct3 n2(msh->normal(vi[1]));
  Vct3 n3(msh->normal(vi[2]));
  const Vct2 & q1(msh->parpos(vi[0]));
  const Vct2 & q2(msh->parpos(vi[1]));
  const Vct2 & q3(msh->parpos(vi[2]));

  // reactivate gap criterion near kinks
  Real sphi2, cphi2;
  sincosine( 0.5*maxPhi(), sphi2, cphi2 );
  const Real maxgap = 0.5*maxLength() * (1. - cphi2)/sphi2;
  
  // check if the triangle is near a kink
  const Real ptol(1e-6);
  Real cgap(0.0);
  const uint nk(vkinks.size());
  for (uint i=0; i<nk; ++i) {
    Real d1 = q1[1] - vkinks[i];
    Real d2 = q2[1] - vkinks[i];
    Real d3 = q3[1] - vkinks[i];
    if ( (d1*d2) < 0.0 or (d1*d3) < 0.0 or (d2*d3) < 0.0
         or fabs(d1) < ptol or fabs(d2) < ptol 
         or fabs(d3) < ptol ) 
    {
      const Vct3 & Sv(svkinks[i]);
      n1 -= dot(n1, Sv)*Sv;
      normalize(n1);
      n2 -= dot(n2, Sv)*Sv;
      normalize(n2);
      n3 -= dot(n3, Sv)*Sv;
      normalize(n3);
      ntri -= dot(ntri, Sv)*Sv;
      normalize(ntri);
      // stretch *= 0.5;

      // activate gap criterion
      Real umid = (q1[0]+q2[0]+q3[0])/3.0;
      Real vmid = (q1[1]+q2[1]+q3[1])/3.0;
      Real gap = norm(msh->eval(umid, vmid) - (p1+p2+p3)/3.0);
      cgap = max(cgap, gap/maxgap);
    }
  } 
  
  Real cphi[6], cphimin, acrit;
  cphi[0] = cosarg(n1, ntri);
  cphi[1] = cosarg(n2, ntri);
  cphi[2] = cosarg(n3, ntri);
  cphi[3] = cosarg(n1, n2);
  cphi[4] = cosarg(n1, n3);
  cphi[5] = cosarg(n2, n3);
  cphimin = *min_element(cphi, cphi+6);
  acrit = (1.0 + mincosphi) / (1.0 + gmepsilon + cphimin);

  const uint ncrit(4);
  Real crit[ncrit];
  crit[0] = lmax/maxlen;
  crit[1] = stretch/maxstretch;
  crit[2] = cb(acrit);
  crit[3] = sq(cgap);
  
  // compute local scale
  assert(vbreak.size() > 1);
  Real vmean = (q1[1] + q2[1] + q3[1]) / 3.0;
  uint ilo(0), ihi(vbreak.size()-1);
  while (ihi-ilo > 1) {
    uint ipos = (ilo + ihi) / 2;
    if (vbreak[ipos] >= vmean)
      ihi = ipos;
    else
      ilo = ipos;
  }
  Real lst = (vmean - vbreak[ilo]) / (vbreak[ihi] - vbreak[ilo]);
  Real tsf = 1.0 / ((1.0 - lst)*scale[ilo] + lst*scale[ihi]);
  tsf = sqrt(tsf);
  crit[0] = lmax / (tsf*maxlen + (1-tsf)*minlen);
  
  Real mxrf(1.0);
  const uint nr(regions.size());
  for (uint i=0; i<nr; ++i) {
    mxrf = max(mxrf, regions[i].factor(q1));
    mxrf = max(mxrf, regions[i].factor(q2));
    mxrf = max(mxrf, regions[i].factor(q3));
  }
  
  // determine edge refinement factor 
  if (lerFactor != 1.0 or terFactor != 1.0) {
    Real xu, y0, y1;
    Real umean = (q1[0] + q2[0] + q3[0]) / 3.;
    if (umean < 0.25) {
      xu = 4.*umean;
      y0 = terFactor;
      y1 = 1.0;
    } else if (umean < 0.5) {
      xu = 4.*(umean - 0.25);
      y1 = lerFactor;
      y0 = 1.0;
    } else if (umean < 0.75) {
      xu = 4.*(umean - 0.5);
      y1 = 1.0;
      y0 = lerFactor;
    } else {
      xu = 4.*(umean - 0.75);
      y1 = terFactor;
      y0 = 1.0;
    }
    Real x2 = sq(xu);
    Real x3 = xu*x2;
    Real x4 = x2*x2;
    Real x5 = x2*x3;
    Real mxlf = y0 + (y1-y0)*( 10.*x3 - 15.*x4 + 6.*x5 );
    mxrf = max(mxrf, 1.0/mxlf);
  }
  
  if (mxrf != 1.0) {
    crit[0] *= mxrf;
    crit[3] *= mxrf;
    
    // do not require shorter length than lmin 
    crit[0] = min(crit[0], lmax/minlen);
    
    // crit[2] = pow(acrit, 3.*mxrf);
  }
  
  // return worst violation
  return *(max_element(crit, crit+ncrit));
}

DnWingCriterion *DnWingCriterion::clone() const
{
  DnWingCriterion *wcr = new DnWingCriterion(*this); 
  return wcr;
}

void DnWingCriterion::fromXml(const XmlElement & xe)
{
  DnRegionCriterion::fromXml(xe);
  
  lerFactor = xe.attr2float("lerfactor", 1.0);
  terFactor = xe.attr2float("terfactor", 1.0);
  
  scale.resize(0);
  vbreak.resize(0);
  vkinks.resize(0);
  svkinks.clear();
  XmlElement::const_iterator itr;
  uint n, nr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    string tag = itr->name();
    if (tag == "Scale") {
      n = itr->attr2int("count", 0);
      if (n > 0) {
        scale.resize(n);
        nr = itr->text2array(n, &scale[0]);
        assert(nr == n);
      }
    } else if (tag == "Breaks") {
      n = itr->attr2int("count", 0);
      if (n > 0) {
        vbreak.resize(n);
        nr = itr->text2array(n, &vbreak[0]);
        assert(nr == n);
      }
    } else if (tag == "Kinks") {
      n = itr->attr2int("count", 0);
      if (n > 0) {
        vkinks.resize(n);
        nr = itr->text2array(n, &vkinks[0]);
        assert(nr == n);
      }
    } else if (tag == "KinkTangents") {
      n = itr->attr2int("count", 0);
      if (n > 0) {
        svkinks.resize(n);
        nr = itr->text2array(3*n, svkinks[0].pointer());
        assert(nr == 3*n);
      }
    }
  }
  
  // ignore inconsistent input 
  if (vbreak.size() != scale.size() or vbreak.size() < 2) {
    initBreaks();
  }
  if (vkinks.size() != svkinks.size()) {
    vkinks.resize(0);
    svkinks.clear();
  }
}

XmlElement DnWingCriterion::toXml() const
{
  XmlElement xe( DnRegionCriterion::toXml() );
  xe["lerfactor"] = str(lerFactor);
  xe["terfactor"] = str(terFactor);
   
  if (not scale.empty()) {
    XmlElement xs("Scale");
    xs["count"] = str(scale.size());
    xs.array2text(scale.size(), &scale[0]);
    xe.append(std::move(xs));
  }

  if (not vbreak.empty()) {
    XmlElement xs("Breaks");
    xs["count"] = str(vbreak.size());
    xs.array2text(vbreak.size(), &vbreak[0]);
    xe.append(std::move(xs));
  }
  
  if (not vkinks.empty()) {
    XmlElement xs("Kinks");
    xs["count"] = str(vkinks.size());
    xs.array2text(vkinks.size(), &vkinks[0]);
    xe.append(std::move(xs));
  }
  
  if (not svkinks.empty()) {
    XmlElement xs("KinkTangents");
    xs["count"] = str(svkinks.size());
    xs.array2text(3*svkinks.size(), svkinks[0].pointer());
    xe.append(std::move(xs));
  }
  
  return xe;
}


