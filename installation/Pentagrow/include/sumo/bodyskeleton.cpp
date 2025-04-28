
/* ------------------------------------------------------------------------
 * file:       bodyskeleton.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * manages body surface data
 * ------------------------------------------------------------------------ */

#include "bodyskeleton.h"

#include <surf/skinsurf.h>
#include <surf/initgrid.h>
#include <surf/splinecapsurf.h>
#include <surf/transurf.h>
#include <surf/stitchedsurf.h>
#include <genua/timing.h>
#include <genua/pattern.h>
#include <genua/algo.h>
#include <genua/dbprint.h>
#include <genua/ioglue.h>

using std::string;

class ygirth {
    public:
  ygirth(const Surface & s, Real vp, Real yc) : srf(s), v(vp), yctr(yc) {}
  Real operator() (Real u) const {
    Vct3 p = srf.eval(u, v);
    return fabs(p[1] - yctr);
  }
    private:
  const Surface & srf;
  Real v, yctr;
};

BodySkeleton::BodySkeleton() : Component()
{
  // default for new surface is Akima's tangent construction 
  bKeepStraight = true;
  
  // do not generate an inlet lip
  bInletLip = false;
  lipAxialOffset = 0.4;
  lipRadialOffset = 0.2;
  lipShapeCoef = 1.0;

  // default : all visible
  bVisible = true;
  
  // create dummy surface for interface testing
  const uint nf(8);
  Real len(10.0), w(1.5), h(1.5), fh, fw, x;
  Vector vp = cosine_pattern(nf, 2*PI, 0.0, 0.65);
  for (uint i=0; i<nf; ++i) {
    // Real t = Real(i)/(nf-1);
    Real t = vp[i];
    BodyFrame *bfp = new BodyFrame;
    fh = h*(0.05 + sqrt(1 - sq(2*t-1)));
    // fw = w*(0.05 + (1 -  4*sq(t-0.5)));
    fw = w*(0.05 + sqrt(1 - sq(2*t-1)));
    bfp->setFrameHeight(fh);
    bfp->setFrameWidth(fw);
    x = t*len;
    bfp->origin( vct(x, 0, 0) );
    bfp->interpolate();
    bfp->rename("FrameX"+str(int(100*x)));
    frames.push_back(BodyFramePtr(bfp));
  }
  interpolate();
  rename("Fuselage");

  // set reasonable mesh generation criteria
  defaultCriterion();
  
  // set cap definitions
  AsyComponent::endCap(AsyComponent::CapVLo, EndCap::LongCap, 0.0);
  AsyComponent::endCap(AsyComponent::CapVHi, EndCap::LongCap, 0.0);
}

BodySkeletonPtr BodySkeleton::clone() const
{
  BodySkeleton *bp = new BodySkeleton;
  bp->frames.resize(nframes());
  for (uint i=0; i<nframes(); ++i) 
    bp->frames[i] = frames[i]->clone();
  
  bp->bInletLip = bInletLip;
  bp->lipAxialOffset = lipAxialOffset;
  bp->lipRadialOffset = lipRadialOffset;
  bp->lipShapeCoef = lipShapeCoef;

  bp->visible( visible() );
  bp->rotation( rotation() );
  bp->origin( origin() );
  bp->interpolate();
  
  // copy cap properties
  for (int k=0; k<4; ++k)
    bp->endCap(k).reset();

  const AsyComponent::CapSide fci = AsyComponent::CapVLo;
  const AsyComponent::CapSide rci = AsyComponent::CapVHi;
  bp->endCap(fci, endCap(fci).capShape(), endCap(fci).height());
  bp->endCap(rci, endCap(rci).capShape(), endCap(rci).height());

  // transfer mesh generation properties
  if (bUseMgDefaults) {
    bp->defaultCriterion();
  } else {
    bp->bUseMgDefaults = false;
    bp->criterion( DnRefineCriterionPtr(criterion()->clone()) );
  }
  
  return BodySkeletonPtr(bp);
}

void BodySkeleton::renameFrames()
{
  for (uint i=0; i<nframes(); ++i)
    frames[i]->rename("Frame"+str(i+1));
}

uint BodySkeleton::find(const BodyFramePtr & f) const
{
  if (not f)
    return NotFound;
  
  const BodyFrame *ptr = f.get();
  const uint nf(frames.size());
  for (uint i=0; i<nf; ++i) {
    if (frames[i].get() == ptr)
      return i;
  }
  
  return NotFound;
}

void BodySkeleton::importSections(const std::string & fname)
{
  ifstream in(asPath(fname).c_str());
  frames.clear();
  
  Real x(0.0), y, z;
  PointList<3> tmp;

  string line;
  const char *pos;
  char *tail = 0;
  uint iline(0), fi(1);
  while (getline(in, line, '\n')) {

    ++iline;

    // see if we can read a new point
    bool pnew = true;
    pos = line.c_str();
    x = genua_strtod(pos, &tail);
    pnew &= (tail != pos);
    pos = tail;
    y = genua_strtod(pos, &tail);
    pnew &= (tail != pos);
    pos = tail;
    z = genua_strtod(pos, &tail);
    pnew &= (tail != pos);

    // if no new point was found, create a section
    if (pnew) {
      tmp.push_back( vct(x,y,z) );
    } else {
      if (tmp.size() > 2) {
        dbprint("Identified section with",tmp.size(),"points.");
        BodyFrame *bf = new BodyFrame;
        bf->rename( "Frame "+str(fi) );
        bf->importSection( tmp );
        frames.push_back( BodyFramePtr(bf) );
        ++fi;
      } else {
        dbprint("Section with less than 3 points ended at line", iline);
      }
      tmp.clear();
    }
  }

  // store last frame
  if (tmp.size() > 2) {
    dbprint("Identified section with",tmp.size(),"points.");
    BodyFrame *bf = new BodyFrame;
    bf->rename( "Frame "+str(fi) );
    bf->importSection( tmp );
    frames.push_back( BodyFramePtr(bf) );
    ++fi;
  } else {
    dbprint("Section with less than 3 points ended at line", iline);
  }

  if (frames.size() < 4)
    throw Error("Point grid import: Must specify at "
                "least four sections per body surface.");

  interpolate();
}

void BodySkeleton::interpolate()
{
  // determine the maximum width of the body
  maxWidth = 0.0;
  minRadius = huge;
  const uint nf(frames.size());
  for (uint i=0; i<nf; ++i) {
    maxWidth = std::max(maxWidth, frames[i]->frameWidth());
    minRadius = std::min(minRadius, frames[i]->estimateMinRadius());
  }
  
  // copy curves from frames
  CurvePtrArray cpa(nf);
  for (uint i=0; i<nf; ++i) 
    cpa[i] = CurvePtr( frames[i]->curve()->clone() );
  
  // store longitudinal frame positions
  Curve::arclenParamet(cpa, vspos);
  
  // generate inlet lip if defined
  SurfacePtr sp;
  if (bInletLip) {
    sp = generateInletLip(cpa);
  } else {
    SkinSurf *ssf = new SkinSurf("UnknownBody");
    ssf->init(cpa, true, bKeepStraight);
    sp.reset(ssf);
  }

  if ( AsyComponent::defined() )
    sp->rename( Component::name() );
  
  if ( AsyComponent::defined() ) {
    surface( sp );
  } else {
    DnRefineCriterionPtr mc(new DnRefineCriterion);
    MeshComponentPtr mcp(new MeshComponent(sp, mc));
    AsyComponent::component(mcp);
  }
  transform();
  
  // compute maximum width lines
  Vector vsample;
  const int nsamp = vspacing(8, vsample);
  PointList<3> rwaist(nsamp), lwaist(nsamp);
  SurfacePtr srf = Component::surface();
  for (int i=0; i<nsamp; ++i) {
    Real ur = findWaist(vsample[i], 0.0, 0.5);
    rwaist[i] = srf->eval(ur, vsample[i]);
    Real ul = findWaist(vsample[i], 0.5, 1.0);
    lwaist[i] = srf->eval(ul, vsample[i]);
  }

  // interpolate waist lines using cubic curves
  Vector dmy;
  mwright.interpolate(rwaist, dmy);
  mwleft.interpolate(lwaist, dmy);


//  // compute maximum width lines
//  PointList<2> twmax(nf);
//  for (uint i=0; i<nf; ++i)
//    twmax[i] = vct( frames[i]->rightMaxWidth(), vspos[bInletLip ? i+1 : i] );
//  Spline<2> qsp;
//  qsp.interpolate(twmax);
//
//  const uint nip(256);
//  PointList<3> mwp(nip);
//  SurfacePtr srf = surface();
//  for (uint i=0; i<nip; ++i) {
//    Vct2 qip = qsp.eval(Real(i)/(nip-1));
//    qip[0] = std::min(1.0, std::max(0.0, qip[0]));
//    qip[1] = std::min(1.0, std::max(0.0, qip[1]));
//    mwp[i] = srf->eval(qip[0], qip[1]);
//  }
//  mwright.interpolate(mwp);
//
//  for (uint i=0; i<nf; ++i)
//    twmax[i] = vct( frames[i]->leftMaxWidth(), vspos[bInletLip ? i+1 : i] );
//  qsp.interpolate(twmax);
//  for (uint i=0; i<nip; ++i) {
//    Vct2 qip = qsp.eval(Real(i)/(nip-1));
//    qip[0] = std::min(1.0, std::max(0.0, qip[0]));
//    qip[1] = std::min(1.0, std::max(0.0, qip[1]));
//    mwp[i] = srf->eval(qip[0], qip[1]);
//  }
//  mwleft.interpolate(mwp);
  
  // surface changed - vizualization needs update 
  bGridUp2date = false;

  // tell the mesh generator that this surface was modified
  AsyComponent::surfaceChanged();
  
  // do not mark kink edges on bodies
  AsyComponent::kinkLimit(PI);
}

uint BodySkeleton::vspacing(int n, Vector & vp) const
{
  const int nseg = vspos.size() - 1;
  const int np = n*nseg + vspos.size();
  vp.allocate(np);

  int k(0);
  vp[k++] = 0.0;
  for (int j=0; j<nseg; ++j) {
    Real a = vspos[j];
    Real b = vspos[j+1];
    for (int i=0; i<n; ++i) {
      Real t = Real(i+1) / (n+1);
      vp[k++] = (1.0-t)*a + t*b;
    }
    vp[k++] = b;
  }

  return np;
}

SurfacePtr BodySkeleton::generateInletLip(CurvePtrArray & cpa)
{
  // assemble main surface
  SkinSurf *skin = new SkinSurf("UnknownBody");
  skin->init(cpa, true, bKeepStraight);
  SurfacePtr pskin(skin);

  // compute curve center and circunference
  const int nev = 128;
  PointList<3> pts(nev);
  for (int i=0; i<nev; ++i)
    pts[i] = cpa[0]->eval( Real(i) / (nev-1) );

  Real len, ccf = 0.0;
  Vct3 ctr;
  for (int i=1; i<nev; ++i) {
    len = norm(pts[i] - pts[i-1]);
    ccf += len;
    ctr += len * (pts[i] + pts[i-1]);
  }
  ctr /= 2*ccf;

  // approximate axial direction
  const Vct3 & a1( pts[nev/6] );
  const Vct3 & a2( pts[nev/2] );
  const Vct3 & a3( pts[5*nev/6] );

  // vector pointing forward - positive axial
  // offset means shifting towards -ax
  Vct3 ax = cross(a1-a2, a3-a2).normalized();

  // generate points for inner curve
  // generate a circular curve with an appropriate offset
  // as the radial offset increases, the internal curve
  // will be gradually morphed into a circle
  const Vector & cup( frame(0)->parametrization() );
  const int nup = cup.size(); // cup.size()/2 + cup.size()%2;
  Real rmean = ccf / (2*PI);
  pts.resize(nup);
  for (int i=0; i<nup; ++i) {

    // evaluate external curve and shift inward
    Vct3 px = cpa[0]->eval( cup[i] );
    Vct3 dr = ctr - px;
    //Real rlocal = normalize(dr);
    //Real rshift = sqrt(rlocal*rmean);
    normalize(dr);
    px += lipRadialOffset*rmean * dr;

    // apply circular projection factor
    Vct3 py = ctr - rmean*(1.0 - lipRadialOffset)*dr;
    Real t = lipRadialOffset;
    px = (1.0-t)*px + t*py;

    // apply axial offset
    pts[i] = px - lipAxialOffset*rmean*ax;
  }

  SymFrame *symf = new SymFrame("InletLipFrame");
  symf->init(pts);
  CurvePtr pcin(symf);

  // scale ax to match magnitude of pskin surface slope at u=0
  Real SvScale = 0.0;
  const int nsamp = 8;
  for (int i=0; i<nsamp; ++i)
    SvScale += norm( pskin->derive(0.0, Real(i)/(nsamp-1), 0, 1) );
  SvScale *= 1.0/nsamp;
  ax *= SvScale;

  // generate transition from inner curve to
  // skinned surface for the shell
  TranSurf *tsf = new TranSurf("InletLip");
  tsf->init(ax, pcin, pskin, cpa[0], lipShapeCoef);
  SurfacePtr ptsf(tsf);

  // stitch together the two surfaces so that the
  // arclength parametrization of the combined surface
  // is approximately continuous
  const int nu = 4;
  const int nv = 16;
  PointList<3> line(nv);
  Real tslen(0.0), sslen(0.0);
  for (int i=0; i<nu; ++i) {
    Real u = (0.5 + i) / nu;
    for (int j=0; j<nv; ++j) {
      Real v = Real(j) / (nv-1);
      line[j] = ptsf->eval(u,v);
    }
    for (int j=1; j<nv; ++j)
      tslen += norm(line[j] - line[j-1]);

    for (int j=0; j<nv; ++j) {
      Real v = Real(j) / (nv-1);
      line[j] = pskin->eval(u,v);
    }
    for (int j=1; j<nv; ++j)
      sslen += norm(line[j] - line[j-1]);
  }

  // adapt breakpoints to reflect arclengths
  Real brk = tslen / (tslen + sslen);
  Vector vbreak(3);
  vbreak[0] = 0.0;
  vbreak[1] = brk;
  vbreak[2] = 1.0;

  // change vspos to reflect implicit inner frame
  const int nf = nframes();
  Vector tmp(nf+1);
  tmp[0] = 0.0;
  for (int i=0; i<nf; ++i)
    tmp[i+1] = brk + (1.0 - brk)*vspos[i];
  vspos.swap(tmp);

  SurfaceArray sfl(2);
  sfl[0] = ptsf;
  sfl[1] = pskin;

  StitchedSurf *sts = new StitchedSurf("NoName");
  sts->init(sfl, vbreak);

  // set corresponding front cap height to zero
  // since this is the fan face, which should be flat
  Component::southCapHeight(0.0);

  // adapt the radius property used for the default
  // mesh generation criterion
  const int ncu = 4;
  const int ncv = 8;
  Real cvmax = 0.0;
  for (int j=0; j<ncv; ++j) {
    Real v = 0.2 + 0.8*j/(ncv-1);
    for (int i=0; i<ncu; ++i) {
      Real u = (i + 0.5) / ncu;
      cvmax = std::max(cvmax, fabs(tsf->vcurvature(u,v)));
    }
  }
  minRadius = std::min(minRadius, 1.0/cvmax);
  // cout << "Adpated minRadius to " << minRadius << endl;

  return SurfacePtr(sts);
}

Real BodySkeleton::findWaist(Real v, Real ulo, Real uhi) const
{
  SurfacePtr psf = Component::surface();
  Vct3 pmean = 0.5*(psf->eval(ulo,v) + psf->eval(uhi,v));
  ygirth f(*psf, v, pmean[1]);

  // since the body contour may not be convex, we subdivide
  // into a few subsegments and find the maximum in each
  Real uw, ubest(ulo), yg, ymax(0.0);
  const int nseg = 4;
  Real sulo, suhi, du = (uhi - ulo) / nseg;
  for (int i=0; i<nseg; ++i) {
    sulo = ulo + i*du;
    suhi = sulo + du;
    uw = golden_ratio_maximum(f, sulo, suhi, Real(0.0001));
    yg = f(uw);
    if (yg > ymax) {
      ymax = yg;
      ubest = uw;
    }
  }

  return ubest;
}

Vct3 BodySkeleton::evaluate(PointList<3> & pbot, PointList<3> & ptop,
                            PointList<3> & pleft, PointList<3> & pright) const
{   
  // construct evaluation positions
  Vector vip;
  vspacing(8, vip);
  const int np = vip.size();

  SurfacePtr srf = Component::surface();
  Vct3 dmy;
  pbot.resize(2*np);
  ptop.resize(2*np);
  pleft.resize(2*np);
  pright.resize(2*np);
  for (int i=0; i<np; ++i) {
    Real v = vip[i];
    srf->plane(0.5, v, ptop[2*i], dmy, ptop[2*i+1]);
    srf->plane(0.0, v, pbot[2*i], dmy, pbot[2*i+1]);
    mwleft.tgline(v, pleft[2*i], pleft[2*i+1]);
    mwright.tgline(v, pright[2*i], pright[2*i+1]);
  }
  
  return origin();
}

Vct3 BodySkeleton::localDimensions(Real v, Real & lh, Real & lw) const
{
  SurfacePtr srf = Component::surface();
  Vct3 pbot( srf->eval(0.0, v) );
  Vct3 ptop( srf->eval(0.5, v) );
  Vct3 pleft( mwleft.eval(v) );
  Vct3 pright( mwright.eval(v) );
  Vct3 ctr = 0.5*(pbot + ptop);

  lw = fabs(pleft[1] - pright[1]);
  lh = fabs(ptop[2] - pbot[2]);

  // compute origin of new curve
  Vector::const_iterator pos, first;
  first = vspos.begin();
  if (bInletLip)
    first++;

  pos = lower_bound(first, vspos.end(), v);
  int ihi = std::distance(first, pos);
  ihi = std::max(1, std::min(ihi, int(vspos.size()-1)));
  int ilo = ihi-1;
  Real t = (v - vspos[ilo]) / (vspos[ihi] - vspos[ilo]);
  ctr = (1.-t)*frames[ilo]->origin() + t*frames[ihi]->origin();

  return ctr;
}

void BodySkeleton::dimensions(Real & hmax, Real & wmax, Real & len) const
{
  if (nframes() < 2) {
    hmax = 0.0;
    wmax = 0.0;
    len = 0.0;
  }

  Real xmin(huge), xmax(-huge);
  hmax = 0.0;
  wmax = 0.0;
  for (uint i=0; i<nframes(); ++i) {
    const BodyFrame & bf(*frames[i]);
    const Vct3 & ctr(bf.origin());
    hmax = std::max(hmax, bf.frameHeight());
    wmax = std::max(wmax, bf.frameWidth());
    xmax = std::max(xmax, ctr[0]);
    xmin = std::min(xmin, ctr[0]);
  }
  len = xmax - xmin;
}
    
void BodySkeleton::globalScale(Real f)
{
  maxWidth *= f;
  minRadius *= f;
  for (size_t i=0; i<frames.size(); ++i)
    frames[i]->globalScale(f);
  Component::globalScale(f);
}

void BodySkeleton::scale(Real fh, Real fw, Real fl)
{
  Vct3 p0 = frames.front()->origin();
  for (uint i=0; i<nframes(); ++i) {
    BodyFrame & bf(*frames[i]);
    if (fl != 1.0) {
      Vct3 ctr(bf.origin());
      ctr = p0 + fl*(ctr - p0);
      bf.origin(ctr);
    }
    bf.setFrameWidth(bf.frameWidth()*fw);
    bf.setFrameHeight(bf.frameHeight()*fh);
    bf.interpolate();
  }
  interpolate();
}

void BodySkeleton::removeFrame(Real x)
{
  // find frame closest to x
  Real dst, mindst(huge);
  BodyFrameArray::iterator itr, idel(frames.end());
  for (itr = frames.begin(); itr != frames.end(); ++itr) {
    dst = fabs(x - (*itr)->origin()[0]);
    if (dst < mindst) {
      idel = itr;
      mindst = dst;
    }
  }

  // kill frame
  if (idel != frames.end())
    frames.erase(idel);

  // rebuild modified surface
  interpolate();
}
    
BodyFramePtr BodySkeleton::insertFrame(Real x)
{
  // fetch current x-positions of existing frames
  SurfacePtr srf = Component::surface();
  const uint nf(nframes());
  Real xmin(huge), xmax(-huge);
  Vector xpos(nf);
  for (uint i=0; i<nf; ++i) {
    const Vct3 & ctr(frames[i]->origin());
    xpos[i] = ctr[0];
    xmin = std::min(xmin, xpos[i]);
    xmax = std::max(xmax, xpos[i]);
  }
  Real blen = fabs(xmax-xmin);
  
  // find parameter v which belongs to this x
  Vct3 lctr;
  Real vn, lh, lw;
  if (x <= xpos.front()) {
    vn = 0.0;
    lctr = frames.front()->origin();
    lh = frames.front()->frameHeight();
    lw = frames.front()->frameWidth();
  } else if (x >= xpos.back()) {
    vn = 1.0;
    lctr = frames.back()->origin();
    lh = frames.back()->frameHeight();
    lw = frames.back()->frameWidth();
  } else {
    vn = (x - xpos.front()) / (xpos.back() - xpos.front());
    lctr = localDimensions(vn, lh, lw);
  }
  lctr[0] = x;

  // construct interpolation frame
  BodyFramePtr bfp(new BodyFrame);
  bfp->origin(lctr);
  bfp->setFrameWidth(lw);
  bfp->setFrameHeight(lh);

  uint ipos;
  Vector::iterator xipos;
  xipos = std::lower_bound(xpos.begin(), xpos.end(), x);
  ipos = std::distance(xpos.begin(), xipos);
  
  // adapt interpolation points to neighbors if frame
  // is inserted in between two existing frames
  if (ipos == 0) {
    bfp->riPoints() = frames.front()->riPoints();
  } else if (ipos >= nf-1) {
    bfp->riPoints() = frames.back()->riPoints();
  } else {
    const Vector & plft(frames[ipos-1]->parametrization());
    const Vector & prgt(frames[ipos+1]->parametrization());
    uint np = (plft.size() + prgt.size())/2;
    Vector pmix(np);
    pmix = 0.5*( resize_pattern(plft, np) + resize_pattern(prgt, np) );
    PointList<2> & rip(bfp->riPoints());
    rip.resize(np);
    for (uint i=0; i<np; ++i) {
      Vct3 sp = srf->eval(pmix[i], vn) - origin();
      rip[i] = bfp->space2frame( sp );
    }
  }
  
  // set default name 
  bfp->rename( "Frame" + str(int(1000*(x/blen))) );
  
  bfp->interpolate();
  frames.push_back(bfp);
  std::sort(frames.begin(), frames.end());
  interpolate();

  return bfp;
}

XmlElement BodySkeleton::toXml() const
{
  assert(criterion() != 0);
  
  XmlElement xe("BodySkeleton");
  xe["name"] = name();
  xe["origin"] = str(sTrn);
  xe["rotation"] = str(sRot);
  xe["akimatg"] = str(bKeepStraight);
  if (bInletLip) {
    XmlElement xil("NacelleInletLip");
    xil["axialOffset"] = str(lipAxialOffset);
    xil["radialOffset"] = str(lipRadialOffset);
    xil["shapeCoef"] = str(lipShapeCoef);
    xe.append(xil);
  }
  for (uint i=0; i<frames.size(); ++i)
    xe.append(frames[i]->toXml());


  xe.append( AsyComponent::ecaps[CapVLo].toXml() );
  xe.append( AsyComponent::ecaps[CapVHi].toXml() );

  xe.append(mgToXml());
  return xe;
}

void BodySkeleton::fromXml(const XmlElement & xe)
{
  if (xe.name() != "BodySkeleton")
    throw Error("BodySkeleton::fromXml() - Incompatible XML representation.");

  // load transformation if given 
  if (xe.hasAttribute("origin"))
    fromString(xe.attribute("origin"), sTrn);
  if (xe.hasAttribute("rotation"))
    fromString(xe.attribute("rotation"), sRot);
  
  // if interpolation method is not specified (older files)
  // use Bessel's scheme by default 
  if (xe.hasAttribute("akimatg")) {
    fromString(xe.attribute("akimatg"), bKeepStraight);
  } else {
    bKeepStraight = false;
  }

  // erase currently defined caps
  for (int k=0; k<4; ++k)
    AsyComponent::ecaps[k].reset();

  bInletLip = false;
  Real ncaph(0.0), scaph(0.0);
  bool oldcaps(false), newcaps(false);
  frames.clear();
  XmlElement::const_iterator ite, ilast;
  ilast = xe.end();
  for (ite = xe.begin(); ite != ilast; ++ite) {
    string s = ite->name();
    if (s == "BodyFrame") {
      BodyFrame *pbf = new BodyFrame;
      pbf->fromXml(*ite);
      frames.push_back(BodyFramePtr(pbf));
    } else if (s == "MeshCriterion") {
      mgFromXml(*ite);
    } else if (s == "Caps") {

      // end caps : accept old format
      oldcaps = true;
      ncaph = ite->attr2float("height_north", 0.0);
      scaph = ite->attr2float("height_south", 0.0);

    } else if (s == "Cap") {

      // new format
      newcaps = true;
      AsyComponent::endCap( EndCap(*ite) );

    } else if (s == "NacelleInletLip") {
      bInletLip = true;
      lipAxialOffset = ite->attr2float("axialOffset", 0.4);
      lipRadialOffset = ite->attr2float("radialOffset", 0.2);
      lipShapeCoef = ite->attr2float("shapeCoef", 1.0);
    }
  }

  if (xe.findChild("MeshCriterion") == xe.end()) 
    bUseMgDefaults = true;
  
  // sort with respect to x-coordinate
  std::sort(frames.begin(), frames.end());
  interpolate();
  rename(xe.attribute("name"));

  if (bUseMgDefaults)
    defaultCriterion();
  
  if (oldcaps) {
    AsyComponent::endCap(AsyComponent::CapVHi, EndCap::LongCap, ncaph);
    AsyComponent::endCap(AsyComponent::CapVLo, EndCap::LongCap, scaph);
  } else if (not newcaps) {
    AsyComponent::endCap(AsyComponent::CapVHi, EndCap::RingCap, 0.0);
    AsyComponent::endCap(AsyComponent::CapVLo, EndCap::RingCap, 0.0);
  }
}

void BodySkeleton::glDraw() const
{
  if (not bVisible)
    return;
  
  if (frames.size() < 4)
    return;
  
  updateVizGrid();
  glDrawGrid();
  
  // draw translated frames
  Vector up( equi_pattern(100) );
  const uint nf(frames.size());
  for (uint i=0; i<nf; ++i) {
    CurvePtr cp( frames[i]->curve() );
    glDrawCurve(*cp, up);
  }
}

void BodySkeleton::vizGrid(PointGrid<2> & qts) const
{
  // vizualization grid parameters
  Real lmax = 0.125 * maxWidth;
  Real lmin = minRadius;
  Real phimax = rad(30.);
  
  // v-direction pattern
  Vector vp;
  vspacing(16, vp);
  
  // construct good approximation grid 
  SurfacePtr srf = Component::surface();
  InitGrid ig(srf.get());
  ig.initPattern(equi_pattern(30), vp);
  for (int k=0; k<4; ++k)
    ig.vRefineByAngle(phimax);
  ig.uAdapt(lmax, lmin, phimax, 128);
  ig.enforceUSymmetry();
  ig.vsmooth(1);
  
  // draw surface itself
  ig.collect(qts);
}

void BodySkeleton::defaultCriterion()
{
  Real maxlen = 0.08*meanCircumference();
  Real minlen = std::min(0.1*maxlen, 0.5*minRadius);
  Real maxphi = rad(30.0);
  Real maxstretch = 6.0;
  
  DnRegionCriterionPtr rcp;
  rcp = boost::dynamic_pointer_cast<DnRegionCriterion>(criterion());
  if (not rcp) {
    rcp = DnRegionCriterionPtr(new DnRegionCriterion);
    criterion(rcp);
  }
  rcp->setCriteria(maxlen, minlen, maxphi, maxstretch);
  AsyComponent::surfaceChanged();
}

void BodySkeleton::buildInitGrid(PointGrid<2> & pgi)
{
  DnRefineCriterionPtr rcp( criterion() );
  
  const int nu = 32;
  const int nv = vspos.size();
  pgi.resize(nu, nv);
  for (int j=0; j<nv; ++j) {
    for (int i=0; i<nu; ++i) {
      pgi(i,j) = vct( Real(i)/(nu-1), vspos[j] );
    }
  }
  
  InitGrid ig(surface().get());
  ig.initPattern(pgi);
  ig.refine( rcp->maxLength(), rcp->minLength(), rcp->maxPhi() );
  ig.enforceUSymmetry();
  ig.collect(pgi);
}

void BodySkeleton::exportGrid(uint numax, uint n2s, Real lmax, Real phimax, 
                              PointGrid<3> & pgrid) const
{
  // v-direction pattern
  Vector vp;
  vspacing(n2s, vp);
  
  // construct good approximation grid 
  InitGrid ig(surface().get());
  ig.initPattern(equi_pattern( std::min(30u,numax) ), vp);
  ig.uAdapt(lmax, minRadius, phimax, numax);
  ig.enforceUSymmetry();
  ig.vsmooth(1);
  
  PointGrid<2> qts;  
  ig.collect(qts);

  SurfacePtr srf = Component::surface();
  const uint nr(qts.nrows());
  const uint nc(qts.ncols());
  pgrid.resize(nr, nc);
  for (uint j=0; j<nc; ++j) {
    for (uint i=0; i<nr; ++i) {
      const Vct2 & q(qts(i,j));
      pgrid(i,j) = srf->eval(q[0], q[1]);
    }
  }
}

void BodySkeleton::ipolPoints(PointListArray & pts) const
{
  // construct transformation 
  Transformer tf;
  tf.rotate(sRot[0], sRot[1], sRot[2]);
  tf.translate(sTrn);
  
  const uint nf(frames.size());
  pts.resize(nf);
  for (uint i=0; i<nf; ++i) {
    const PointList<2> & rp(frames[i]->riPoints());
    const uint np(rp.size());
    pts[i].resize(np);
    for (uint j=0; j<np; ++j) {
      pts[i][j] = tf.forward(frames[i]->frame2space(rp[j]));
    }
  }
}

BodySkeletonPtr BodySkeleton::xzMirrorCopy() const
{
  BodySkeletonPtr mc = clone();
  
  // construct name of copy 
  string sname = name();
  const char Left[] = "Left";
  const char Right[] = "Right";
  string::size_type lpos, rpos;
  lpos = sname.find(Left);
  rpos = sname.find(Right);
  if (lpos != string::npos) {
    sname.replace(lpos, strlen(Left), Right); 
  } else if (rpos != string::npos) {
    sname.replace(rpos, strlen(Right), Left); 
  } else {
    sname += "MirrorCopy";
  }
  mc->rename(sname);
  
  // change body transformation 
  Vct3 rot = rotation();
  rot[0] *= -1.0;
  rot[2] *= -1.0;
  mc->rotation(rot);
  
  Vct3 org = origin();
  org[1] *= -1.0;
  mc->origin(org);
  
  // mirror body frames 
  const int nf(mc->nframes());
  for (int i=0; i<nf; ++i) {
    BodyFrame & bf( *(mc->frame(i)) );
    org = bf.origin();
    org[1] *= -1.0;
    bf.origin( org );
    bf.interpolate();
  }
  mc->interpolate();
  
  return mc;
}

Real BodySkeleton::meanCircumference() const
{
  if (not vzpts.empty()) {
    
    Real len = norm( frames.back()->origin() - frames.front()->origin() );
    Real asum(0);
    const int nu = vzpts.nrows();
    const int nv = vzpts.ncols();
    for (int j=1; j<nv; ++j) {
      for (int i=1; i<nu; ++i) {
        const Vct3 & pa( vzpts(i-1,j-1) );
        const Vct3 & pb( vzpts(i-1,j) );
        const Vct3 & pc( vzpts(i,j) );
        const Vct3 & pd( vzpts(i,j-1) );
        asum += 0.5*norm(cross(pb-pa, pd-pa));
        asum += 0.5*norm(cross(pd-pc, pb-pc));
      }
    }
    return asum/len;
    
  } else {
    Real sum(0);
    const int nf = frames.size();
    for (int i=0; i<nf; ++i) {
      sum += frames[i]->frameWidth() + frames[i]->frameHeight();
    }
    return sum * 0.5*PI/nf;
  }
}

void BodySkeleton::capsToIges(IgesFile & file) const
{
  // extract limit curves
  CurvePtr cv0( frames.front()->curve()->clone() );
  cv0->rotate(sRot[0], sRot[1], sRot[2]);
  cv0->translate(sTrn);
  cv0->apply();
  
  CurvePtr cv1( frames.back()->curve()->clone() );
  cv1->rotate(sRot[0], sRot[1], sRot[2]);
  cv1->translate(sTrn);
  cv1->apply();
  
  // use flat caps for now
  SplineCapSurf fcap("FrontCap");
  fcap.init(0.5, *cv0);
  fcap.toIges(file);
  
  SplineCapSurf rcap("RearCap");
  rcap.init(0.5, *cv1);
  rcap.toIges(file);
}

void BodySkeleton::projectPoint(const FrameProjector & fpj,
                                const SegmentArray & sgs,
                                uint iframe, uint ipt)
{
  assert(iframe < nframes());
  BodyFrame & bf( *frame(iframe) );
  PointList<2> & rpt( bf.riPoints() );

  Vct2 ro = rpt[ipt];
  Vct3 pf = origin() + bf.frame2space( ro );
  Vct3 pj = fpj.lproject(sgs, pf);
  Vct2 rp = bf.space2frame(pj - origin());

  // re-establish symmetry
  if ( (bf.symmetric() and ipt == 0) or (ipt == rpt.size()-1))
    rp[0] = 0.0;

  // debug
  cout << "Incoming : " << ro << " at " << pf << endl;
  cout << "Projected: " << rp << " at " << pj << endl;

  // do not allow sign changes
  if ( (rp[0]*ro[0] < 0) or (rp[1]*ro[1] < 0) )
    return;

  rpt[ipt] = rp;
}

void BodySkeleton::projectPoints(const FrameProjector & fpj,
                                 const SegmentArray & sgs,
                                 uint iframe, Real /* maxdst */ )
{
  assert(iframe < nframes());
  BodyFrame & bf( *frame(iframe) );
  PointList<2> & rpt( bf.riPoints() );
  const int npt = rpt.size();

  // v-position of this frame
  const Vector & up( bf.parametrization() );
  const Real vfr = vspos[iframe];
  // const Real sqmax = sq(maxdst);

#pragma omp parallel for schedule(static)
  for (int ipt = 0; ipt < npt; ++ipt) {
    Vct2 ro = rpt[ipt];
    Vct3 pf = origin() + bf.frame2space( ro );
    Vct3 pn = main->surface()->normal(up[ipt], vfr);
    Vct3 pj = fpj.lproject(sgs, pf, pn);
    Vct2 rp = bf.space2frame(pj - origin());

    // enforce symmetry
    if (bf.symmetric()) {
      if (ipt == 0 or ipt == npt-1)
        rp[0] = 0.0;
    }

    //if ( sq(pj-pf) < sqmax and (rp[0]*ro[0] > 0) and (rp[1]*ro[1] > 0) )
      rpt[ipt] = rp;
  }
}

