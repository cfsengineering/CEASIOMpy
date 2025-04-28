
/* ------------------------------------------------------------------------
 * file:       bodyframe.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Fuselage section object
 * ------------------------------------------------------------------------ */

#include <sstream>
#include <genua/line.h>
#include <genua/trafo.h>
#include <genua/dbprint.h>
#include "aabb.h"
#include "bodyframe.h"

using namespace std;

BodyFrame::BodyFrame() : bSymmetric(true)
{
  crv = CurvePtr(new Curve("NoName"));
  
  // generate default points
  const uint np(7);
  rpts.resize(np);
  for (uint i=0; i<np; ++i) {
    Real phi = PI*Real(i)/(np-1);
    rpts[i][0] = sin(phi);
    rpts[i][1] = -cos(phi);
  }
  mwidth = mheight = 1.0;
  twmax = 0.25;
  interpolate();
}

BodyFramePtr BodyFrame::clone() const
{
  BodyFrame *pbf = new BodyFrame;
  pbf->mctr = mctr;
  pbf->mheight = mheight;
  pbf->mwidth = mwidth;
  pbf->rpts = rpts;
  pbf->bSymmetric = bSymmetric;
  pbf->interpolate();
  pbf->rename(name());
  return BodyFramePtr(pbf);
}

void BodyFrame::globalScale(Real f)
{
  mctr *= f;
  mheight *= f;
  mwidth *= f;
  if (crv) {
    crv->scale(f);
    crv->apply();
  }
}

Plane BodyFrame::framePlane() const
{
  // always yz for now
  Vct3 pn = vct(1.0,0.0,0.0);
  return Plane( pn, dot(pn, mctr) );
}

void BodyFrame::importSection(PointList<3> & pts)
{
  if (pts.empty())
    throw Error("Trying to import empty point set to frame.");

  // determine whether the point set is a full section or not
  bool fullsec = norm(pts.front() - pts.back()) < gmepsilon;

  // determine center of the enclosing box
  AABBox<3,Real> box;
  box.enclose(pts.size(), pts.pointer());
  Vct3 blo(box.low()), bhi(box.high());
  Vct3 ctr(0.5*(blo+bhi));

  // complain if this looks like it's no body section
  Real dx = bhi[0] - blo[0];
  Real dy = bhi[1] - blo[1];
  Real dz = bhi[2] - blo[2];
  if (dx > dy or dx > dz) {
    stringstream ss;
    ss << "Point grid section is not a body section:" << endl;
    ss << " dx " << dx << " dy " << dy << " dz " << dz << endl;
    throw Error(ss.str());
  }

  // frame dimensions
  uint np = 0;
  if (fullsec) {
    mctr = ctr;
    mheight = bhi[2] - blo[2];
    mwidth = bhi[1] - blo[1];
    np = (pts.size()+1) / 2;
  } else {
    mctr = ctr;
    mctr[1] = pts[0][1];
    mheight = bhi[2] - blo[2];
    mwidth = 2*(bhi[1] - blo[1]);
    np = pts.size();
  }
  assert(std::isfinite(mheight));
  assert(std::isfinite(mwidth));

  // 2D projection on mean-x plane
  rpts.clear();
  rpts.reserve(np);
  Vct2 rp;
  for (uint i=0; i<np; ++i) {
    const Vct3 & p(pts[i]);
    rp[0] = 2*(p[1] - mctr[1]) / mwidth;
    rp[1] = 2*(p[2] - mctr[2]) / mheight;
    if (rpts.empty() or sq(rp-rpts.back()) > gmepsilon)
      rpts.push_back(rp);
  }

  // ensure that the first/last points are aligned
  Vct2 & ro(rpts.front());
  Vct2 & rn(rpts.back());
  if (fullsec) {
    rn[0] = ro[0] = 0.5*(rn[0] + ro[0]);
  }
  
  // reverse order if necessary 
  if (ro[1] > rn[1])
    std::reverse(rpts.begin(), rpts.end());

  normalize();
  interpolate();
}

void BodyFrame::makeDoubleEllipse(Real rzc, int np)
{
  assert(rzc > 0.0);
  assert(rzc < 1.0);
  
  // determine center of double elliptic curve
  // height in relative coordinates
  Real cz = 2*rzc - 1;
  
  Real phi, dphi = PI/(np-1);
  rpts.resize(np);
  for (int i=0; i<np; ++i) {
    phi = i*dphi;
    rpts[i][0] = sin(phi);
    if (phi < 0.5*PI)
      rpts[i][1] = cz - 2*rzc*cos(phi);    
    else
      rpts[i][1] = cz - 2*(1.0 - rzc)*cos(phi); 
  }

  bSymmetric = true;
  interpolate();
}

void BodyFrame::makeIsikveren(Real zp, Real a0, Real a1, Real b1, int np)
{
  rpts.resize(np);
  Real ymax(0.0), zmax(0.0), zmin(huge);
  Real t, phi, sp, cp, r;
  for (int i=0; i<np; ++i) {
    t = Real(i) / (np-1);
    phi = PI * ( t - 0.5 );
    sincosine(phi, sp, cp);
    r = a0 + a1*cos(2.*phi) + b1*sp;
    rpts[i][0] = r*cp;
    rpts[i][1] = zp + r*sp;
    ymax = max(ymax, rpts[i][0]);
    zmax = max(zmax, rpts[i][1]);
    zmin = min(zmin, rpts[i][1]);
  }

  bSymmetric = true;
  normalize();
  interpolate();
}

void BodyFrame::normalize()
{
  // We cannot allow relative coordinates larger than 1, because
  // that would defeat the whole concept of keeping height and width
  // as separate parameters. Therefore, this function updates height
  // and width and changes relative points in order not to change
  // the actual curve shape.

  Real ymin(huge), ymax(-huge), zmin(huge), zmax(-huge);
  const int np(rpts.size());
  assert(np > 3);
  for (int i=0; i<np; ++i) {
    const Vct2 & rp(rpts[i]);
    ymin = min(ymin, rp[0]);
    ymax = max(ymax, rp[0]);
    zmin = min(zmin, rp[1]);
    zmax = max(zmax, rp[1]);
  }
  
  // define scaling factors for width and height 
  // considering that the symmetric section should 
  // have an ymin of exactly zero
  Real yf = 1.0 / ymax;
  Real zf = 2.0 / (zmax - zmin);
  
  // movement of the origin to compensate asymmetrical 
  // change to the height/z-coordinates 
  Real zoff = 0.25*(zmax + zmin);
  mctr[2] += zoff*mheight;
  
  // scale relative coordinates 
  for (int i=0; i<np; ++i) {
    Vct2 & rp(rpts[i]);
    rp[0] *= yf;
    rp[1]  = (rp[1] - 2*zoff)*zf;
  }
  
  mheight /= zf;
  mwidth /= yf;
}

Real BodyFrame::estimateMinRadius() const
{
  // TODO : replace with golden_ratio_minimum over segments
  const int ns(16);
  Real up[ns], cvp[ns], ulo(0.0), uhi(1.0), cvmax;  
  for (uint iter=0; iter<8; ++iter) {
    for (int k=0; k<ns; ++k) {
      up[k] = ulo + k*(uhi - ulo)/(ns-1);
      cvp[k] = crv->curvature(up[k]);
    }
    int j1, j2;
    cvmax = 0.0;
    for (int k=0; k<ns; ++k) {
      if (cvp[k] > cvmax) {
        cvmax = cvp[k];
        j1 = max(0, k-2);
        j2 = min(ns-1, k+2);
        ulo = up[j1];
        uhi = up[j2];
      }
    }
  }
  return 1.0 / cvmax;
}

void BodyFrame::interpolate()
{
  // normalize coordinates always
  normalize();
  
  // compute absolute interpolation points
  const uint np(rpts.size());
  PointList<3> pts(np);
  for (uint i=0; i<np; ++i) {
    pts[i][0] = mctr[0];
    pts[i][1] = mctr[1] + 0.5*mwidth*rpts[i][0];
    pts[i][2] = mctr[2] + 0.5*mheight*rpts[i][1];
  }

//   // compute arclength parametrization
//   ipt.resize(np);
//   for (uint i=1; i<np; ++i) {
//     ipt[i] = ipt[i-1] + norm(pts[i] - pts[i-1]);
//   }
//   ipt /= 2*ipt.back();

  SymFrame *psf;
  if (crv)
    psf = new SymFrame(crv->name());
  else
    psf = new SymFrame("NoName");
  ipt = psf->init(pts);
  crv = CurvePtr(psf);

  // make ipt point to the parameter values
  // of the first half of points
  Vector tmp(np);
  std::copy(ipt.begin(), ipt.begin()+np, tmp.begin());
  tmp.swap(ipt);
  
  twmax = findMaxWidth();
}

void BodyFrame::evalIpp()
{
  if (ipt.empty())
    return;
  
  const int np(ipt.size());
  for (int i=0; i<np; ++i) {
    Vct3 pt = crv->eval(ipt[i]);
    rpts[i][0] = 2.*(pt[1] - mctr[1]) / mwidth;
    rpts[i][1] = 2.*(pt[2] - mctr[2]) / mheight; 
  }
  normalize();
}

void BodyFrame::revaluate(PointList<3> & pts) const
{
  // construct curve parameters at which to evaluate 
  // points and derivatives 
  const int nip(ipt.size());
  const int nt(4*nip - 3);
  Vector t(nt);
  t[0] = ipt[0];
  for (int i=1; i<nip; ++i) {
    t[2*i - 1] = 0.5*( ipt[i-1] + ipt[i]  );
    t[2*i] = ipt[i];
  } 
  
  // mirror values 
  for (int i=0; i<(2*nip-1); ++i) 
    t[nt-1-i] = 1.0 - t[i];

  pts.resize(2*nt);
  for (int i=0; i<nt; ++i) {
    crv->tgline(t[i], pts[2*i], pts[2*i+1]);
  }
}

Real BodyFrame::findMaxWidth(Real ttol) const
{
  // first, compute parametric positions of the interpolation points
  const uint np(rpts.size());
  Vector u(np);
  for (uint i=1; i<np; ++i) 
    u[i] = u[i-1] + norm(rpts[i] - rpts[i-1]);
  u /= 2*u.back();

  // find the interpolation point with maximum y
  uint iymax(0);
  Real yp, ymax(0);
  for (uint i=0; i<np; ++i) {
    yp = fabs(rpts[i][0]);
    if (yp > ymax) {
      ymax = yp;
      iymax = i;
    }
  }

  // special case: iymax is first or last point
  // this is an error for curves which can currently be defined
  // we tolerate it for now because there may be zero-width curves
  if (iymax == 0 or iymax == np-1) {
    return 0.25;
  }

  // search between iymax-1 and iymax+1 for maximum width
  Vct3 mp1, mp2;
  Real t1, t2, tlo, thi, y1, y2;
  tlo = u[iymax-1];
  thi = u[iymax+1];
  
  y1 = fabs(mwidth*rpts[iymax-1][0]);
  y2 = fabs(mwidth*rpts[iymax+1][0]);
  t1 = (2*tlo+thi)/3;
  t2 = (tlo+2*thi)/3;
  
  Real yp1, yp2;
  while ( fabs(thi - tlo) > ttol ) {
    mp1 = crv->eval(t1) - origin();
    mp2 = crv->eval(t2) - origin();
    yp1 = fabs(mp1[1]);
    yp2 = fabs(mp2[1]);
    if ( yp1 > yp2 ) {
      thi = t2;
      y2 = yp2;
    } else if ( yp1 < yp2 ) {
      tlo = t1;
      y1 = yp1;
    } else {
      tlo = t1;
      thi = t2;
      y1 = yp1;
      y2 = yp2;
    }
    t1 = (2*tlo+thi)/3;
    t2 = (tlo+2*thi)/3;
  }
  
  return 0.5*(t1+t2);
}

uint BodyFrame::nearestRPoint(const Vct2 & pos) const
{
  Real dst, mindst(huge);
  uint inext(0);
  const uint nip(rpts.size());
  for (uint i=0; i<nip; ++i) {
    dst = norm(pos - rpts[i]);
    if (dst < mindst) {
      mindst = dst;
      inext = i;
    }
  }

  return inext;
}

void BodyFrame::removePoint(const Vct2 & pos)
{
  if (rpts.size() < 4)
    return;
  
  // find nearest point, but never accept first or last point.
  Real dst, mindst(huge);
  uint inext(0);
  const uint nip(rpts.size());
  for (uint i=1; i<nip-1; ++i) {
    dst = norm(pos - rpts[i]);
    if (dst < mindst) {
      mindst = dst;
      inext = i;
    }
  }

  rpts.erase(rpts.begin() + inext);
}

void BodyFrame::insertPoint(const Vct2 & pos)
{
  // find out where to insert point
  uint inext(0);
  const uint nseg(rpts.size()-1);
  Real dst, mindst(huge);
  for (uint i=0; i<nseg; ++i) {
    Line<2> line(rpts[i], rpts[i+1]);
    Real t = line.footPar(pos);
    if (t <= 0)
      dst = norm(pos - rpts[i]);
    else if (t >= 1)
      dst = norm(pos - rpts[i+1]);
    else
      dst = norm(pos - line.eval(t) );
    
    if (dst < mindst) {
      mindst = dst;
      inext = i;
    }
  }

  // insert point between i and i+1
  rpts.insert(rpts.begin()+inext+1, pos);
}

XmlElement BodyFrame::toXml() const
{
  XmlElement xe("BodyFrame");
  xe["name"] = name();
  xe["height"] = str(mheight);
  xe["width"] = str(mwidth);
  xe["center"] = str(mctr);
  xe["symmetric"] = bSymmetric ? "true" : "false";
  if (fsconp)
    xe.append(fsconp->toXml());
  
  stringstream ss;
  ss << rpts;
  xe.text(ss.str());
  
  return xe;
}

void BodyFrame::fromXml(const XmlElement & xe)
{
  fsconp.reset();
  if (xe.name() != "BodyFrame")
    throw Error("BodyFrame::fromXml() - Incompatible XML representation.");

  if (xe.hasAttribute("symmetric")) {
    if (xe.attribute("symmetric") == "false")
      bSymmetric = false;
    else
      bSymmetric = true;
  }

  rename(xe.attribute("name"));
  mheight = Float(xe.attribute("height"));
  mwidth = Float(xe.attribute("width"));

  if (mheight <= gmepsilon or mwidth <= gmepsilon)
    throw Error("Inconsistent geometry in body frame '"+name()+"'."
                " Dimensions (width/height) must be strictly positive.");

  {
    stringstream ss;
    ss << xe.attribute("center");
    ss >> mctr;
  }

  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    fsconp = FrameShapeConstraint::createFromXml(*itr);
    if (fsconp) {
      fsconp->constrain(*this);
      break;
    } 
  }
  
  if (not fsconp) {
    stringstream ss;
    ss << xe.text();
    rpts.clear();
    Vct2 rp;
    while (ss >> rp) {
      if (rpts.empty() or sq(rp - rpts.back()) > gmepsilon)
      rpts.push_back(rp);
    }

    if (rpts.size() < 4)
      throw Error("Not enough body frame points (need at least 4) in "+name());

    interpolate();
  }
}

void BodyFrame::extendBoundingBox(float plo[3], float phi[3]) const
{
  Vct3 p;
  const uint nu(64);
  for (uint i=0; i<nu; ++i) {
    p = crv->eval(Real(i)/(nu-1));
    plo[0] = min(plo[0], float(p[0]));
    plo[1] = min(plo[1], float(p[1]));
    plo[2] = min(plo[2], float(p[2]));
    phi[0] = max(phi[0], float(p[0]));
    phi[1] = max(phi[1], float(p[1]));
    phi[2] = max(phi[2], float(p[2]));
  } 
}

void BodyFrame::shapeConstraint(const ShapeConstraintPtr & s)
{
  fsconp = s;
  if (fsconp)
    fsconp->constrain(*this);
}

