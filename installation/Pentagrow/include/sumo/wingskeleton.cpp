
/* ------------------------------------------------------------------------
 * file:       wingskeleton.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Holds a collection of wing sections and an interpolation surface
 * ------------------------------------------------------------------------ */

#include "wingskeleton.h"
#include <surf/curve.h>
#include <surf/linearsurf.h>
#include <surf/skinsurf.h>
#include <surf/stitchedsurf.h>
#include <surf/symsurf.h>
#include <surf/dnwingcriterion.h>
#include <surf/initgrid.h>
#include <surf/splinecapsurf.h>
#include <genua/pattern.h>
#include <genua/transformation.h>

using namespace std;

inline static Real spandist(const Vct3 & a, const Vct3 & b)
{
  return sqrt( sq(a[1]-b[1]) + sq(a[2]-b[2]) );
}

WingSkeleton::WingSkeleton() : Component(), bAutoSym(true),
                               bDetectWinglet(true), bCubic(false)
{
  // create dummy wing for testing only
  WingSectionPtr s1(new WingSection);
  s1->chordLength(1.2);
  s1->origin(vct(0.8, 6.0, 0.0));
  s1->interpolate();
  s1->rename("RightTipSection");
  sections.push_back( s1 );

  WingSectionPtr s2(new WingSection);
  s2->chordLength(2.0);
  // s2->setOrigin(vct(3.2, 0.0, 0.0));
  s2->interpolate();
  s2->rename("CentralSection");
  sections.push_back( s2 );

  sTrn[0] = 3.2;
  
  interpolate();
  rename("Wing");

  // set reasonable mesh generation criteria
  defaultCriterion();
  
  // default : all visible
  bVisible = true;
  
  // set cap definitions
  AsyComponent::endCap(AsyComponent::CapVLo, EndCap::LongCap, 1.0);
  AsyComponent::endCap(AsyComponent::CapVHi, EndCap::LongCap, 1.0);
}

WingSkeletonPtr WingSkeleton::clone() const
{
  WingSkeleton *wp = new WingSkeleton;
  wp->sections.resize(nsections());
  for (uint i=0; i<nsections(); ++i)
    wp->sections[i] = sections[i]->clone();
  wp->autoSym( autoSym() );
  wp->detectWinglet( detectWinglet() );
  wp->cubicInterpolation( cubicInterpolation() );
  wp->visible( visible() );
  wp->rotation( rotation() );
  wp->origin( origin() );
  wp->interpolate();
  
  // copy mesh properties 
  wp->stretchedMesh(stretchedMesh());
  wp->defaultCriterion();
  if (bUseMgDefaults) {
    wp->bUseMgDefaults = true;
  } else {
    wp->bUseMgDefaults = false;
    wp->criterion( DnRefineCriterionPtr( criterion()->clone() ) );
  }
  
  return WingSkeletonPtr(wp);
}

void WingSkeleton::globalScale(Real f)
{
  for (size_t i=0; i<sections.size(); ++i)
    sections[i]->globalScale(f);
  Component::globalScale(f);
}

void WingSkeleton::addSection(WingSectionPtr wsp)
{
  sections.push_back(wsp);
}

void WingSkeleton::insertSection(uint ipos, WingSectionPtr wsp)
{
  sections.insert(sections.begin()+ipos, wsp);
}

void WingSkeleton::swapSections(uint ki, uint kj)
{
  assert(ki < nsections());
  assert(kj < nsections());
  std::swap( sections[ki], sections[kj] );
}

uint WingSkeleton::findByName(const std::string & s) const
{
  for (uint i=0; i<nsections(); ++i) {
    if (sections[i]->name() == s)
      return i;
  }
  return NotFound;
}
      
bool WingSkeleton::removeSection(uint i)
{
  if (i == NotFound or i >= sections.size())
    return false;
  
  sections.erase(sections.begin() + i);
  return true;
}

XmlElement WingSkeleton::toXml() const
{
  assert(criterion() != 0);
  
  XmlElement xe("WingSkeleton");
  xe["name"] = name();
  
  // store flags
  string flags;
  if (bAutoSym)
    flags += "autosym,";
  if (bDetectWinglet)
    flags += "detectwinglet,";
  if (bCubic)
    flags += "cubic,";
  
  if (not flags.empty())
    xe["flags"] = flags;
  
  xe["origin"] = str(sTrn);
  xe["rotation"] = str(sRot);
  
  for (uint i=0; i<nsections(); ++i)
    xe.append(sections[i]->toXml());

  xe.append( AsyComponent::ecaps[CapVLo].toXml() );
  xe.append( AsyComponent::ecaps[CapVHi].toXml() );

  XmlElement xmg(mgToXml());
  xmg.rename("WingCriterion");
  xe.append(xmg);
  
  return xe;
}

void WingSkeleton::fromXml(const XmlElement & xe)
{
  if (xe.name() != "WingSkeleton")
    throw Error("Incompatible XML representation for WingSkeleton: "
                +xe.name());

  // reset surface transformation 
  sTrn = 0.0;
  sRot = 0.0;
  
  // load transformation if given 
  if (xe.hasAttribute("origin"))
    fromString(xe.attribute("origin"), sTrn);
  
  if (xe.hasAttribute("rotation"))
    fromString(xe.attribute("rotation"), sRot);
  
  // if flags are not given explicitely, set to false 
  bAutoSym = bDetectWinglet = bCubic = false;
  if (xe.hasAttribute("flags")) {
    string flags = xe.attribute("flags");
    if (flags.find("autosym") != string::npos)
      bAutoSym = true;
    if (flags.find("detectwinglet") != string::npos)
      bDetectWinglet = true;
    if (flags.find("cubic") != string::npos)
      bCubic = true;
  } 
  
  Real ncaph(1.0), scaph(1.0);
  bool oldcaps(false), newcaps(false);
  sections.clear();
  XmlElement::const_iterator ite;
  for (ite = xe.begin(); ite != xe.end(); ++ite) {
    if (ite->name() == "WingSection") {
      WingSectionPtr wsp(new WingSection);
      wsp->fromXml(*ite);
      sections.push_back(wsp);
    } else if (ite->name() == "MeshCriterion" or ite->name() == "WingCriterion") {
      bUseMgDefaults = false;
      mgFromXml( *ite );
    } else if (ite->name() == "Caps") {

      // accept old format
      oldcaps = true;
      ncaph = ite->attr2float("height_north", 1.0);
      scaph = ite->attr2float("height_south", 1.0);
    } else if (ite->name() == "Cap") {

      // new format
      newcaps = true;
      AsyComponent::endCap( EndCap(*ite) );

    }
  }
  
  interpolate();
  rename(xe.attribute("name"));
  
  if (bUseMgDefaults)
    defaultCriterion();
  
  if (oldcaps) {
    AsyComponent::endCap(AsyComponent::CapVHi, EndCap::LongCap, ncaph);
    AsyComponent::endCap(AsyComponent::CapVLo, EndCap::LongCap, scaph);
  } else if (not newcaps) {
    AsyComponent::endCap(AsyComponent::CapVLo, EndCap::LongCap, 1.0);
    if (bAutoSym)
      AsyComponent::endCap(AsyComponent::CapVHi, EndCap::LongCap, 1.0);
    else
      AsyComponent::endCap(AsyComponent::CapVHi, EndCap::LongCap, 0.0);
  }
}

void WingSkeleton::autoSym(bool f)
{
  // switching from non-symmetric to symmetric 
  // requires modifications in some cases
  if (f and (not bAutoSym)) {
    
    // erase all sections on the left side 
    {
      WingSectionArray tmp;
      std::remove_copy_if(sections.begin(), sections.end(), 
                          back_inserter(tmp), is_left_section);
      tmp.swap(sections);
    }
    // sort(sections.begin(), sections.end());
    
    // check if a section at y == 0 is present -- if not, 
    // create a clone of the inboard section and put it at y=0
    const WingSectionPtr & plast(sections.back());
    Vct3 org(plast->origin());
    Real rx(plast->dihedralAngle());
    if (org[1] != 0.0) {
      WingSectionPtr sc(plast->clone());
      sc->rename("AutoCentralSection");
      org[1] = 0.0;
      sc->origin(org);
      sc->dihedralAngle(0.0);
      sc->interpolate();
      sections.push_back(sc);
    } else if (rx != 0.0) {
      plast->dihedralAngle(0.0);
      plast->interpolate();
    }
    
    Real ch = AsyComponent::ecaps[AsyComponent::CapVLo].height();
    AsyComponent::endCap(AsyComponent::CapVHi, EndCap::LongCap, ch);
  }
  
  else if (bAutoSym and (not f)) {
    AsyComponent::endCap(AsyComponent::CapVHi, EndCap::LongCap, 0.0);
  }
  
  bAutoSym = f;
}

void WingSkeleton::heuristicSort()
{
  std::sort(sections.begin(), sections.end());
}

void WingSkeleton::interpolate()
{
  const uint ns(sections.size());
  if (ns < 2) {
    clog << "Cannot construct WingSkeleton with less than 2 sections." << endl;
    return;
  }

  // if symmetry is enabled, the section at v=1 must be moved into 
  // the symmetry plane i.e. have y = 0 and dihedral = 0
  if (bAutoSym) {
    WingSection & csec(*sections.back());
    Vct3 ctr( csec.origin() );
    ctr[1] = 0.0;
    csec.origin( ctr );
    csec.dihedralAngle( 0.0 );
    csec.interpolate();
  }
  
  cpa.clear();
  for (uint i=0; i<ns; ++i) {
    cpa.push_back(sections[i]->curve());
  }
  Curve::arclenParamet(cpa, vspos);
  
  // identify guide values
  maxChord = 0.0;
  minLERadius = huge;
  for (uint i=0; i<ns; ++i) {
    maxChord = max(maxChord, sections[i]->chordLength());
    minLERadius = min(minLERadius, sections[i]->leRadius());
  }
  
  string sname("UnknownWingSkeleton");
  if (AsyComponent::defined())
    sname = Component::name();
  
  uint nwl(0);
  if (bDetectWinglet)
    nwl = lastWingletSection();
  
  uint first(0), last(1);
  StitchedWingSpec spec(cpa);
  for (uint i=1; i<ns; ++i) {
    if (nwl != 0 and i == nwl-1) {
      if (bCubic and last-first > 2)
        spec.addSegment(first, last, StitchedWingSpec::SegCubic);
      else
        spec.addSegment(first, last, StitchedWingSpec::SegLinear);
      first = i;
      last = first+1;
    } else if (nwl != 0 and i == nwl) {
      spec.addSegment(first, last, StitchedWingSpec::SegWlBlend);
      first = i;
      last = first+1;
    } else if (i+1 == ns or sections[i]->isBreak()) {
      if (bCubic and last-first > 2)
        spec.addSegment(first, last, StitchedWingSpec::SegCubic);
      else
        spec.addSegment(first, last, StitchedWingSpec::SegLinear);
      first = i;
      last = first+1;
    } else {
      ++last;
    }
  }
  
  StitchedSurf sts(sname);
  sts.init(spec);
  
  SurfacePtr psf;
  if (bAutoSym) {
    SymSurf *sys = new SymSurf(sname);
    sys->init(sts);
    psf = SurfacePtr(sys);
    
    // mirror section positions
    Vector vtmp;
    for (uint i=0; i<ns; ++i) {
      vtmp.push_back( 0.5*vspos[i] );
      vtmp.push_back(1.0 - 0.5*vspos[i]);
    }
    sort_unique(vtmp);
    vtmp.swap(vspos);
    
  } else {
    psf = SurfacePtr( sts.clone() );
  }
  
  if ( AsyComponent::defined() ) {
    surface(psf);
  } else {
    DnRefineCriterionPtr mc(new DnRefineCriterion);
    MeshComponentPtr mcp(new MeshComponent(psf, mc));
    AsyComponent::component(mcp);
    defaultCriterion();
  }
  
  // tell the mesh generator that this surface was modified
  AsyComponent::surfaceChanged();
  
  Real kinklim = max(0.25*PI, 2*criterion()->maxPhi()); 
  AsyComponent::kinkLimit(kinklim);
  
  rename(sname);
  transform();
  
  updateStats();
  bGridUp2date = false;
}

bool WingSkeleton::mirrorSections() 
{
  if (nsections() == 0)
    return false;

  // check if we can mirror at all
  Vector ypos(nsections());
  for (uint i=0; i<nsections(); ++i) {
    const Vct3 & ctr(sections[i]->origin());
    ypos[i] = ctr[1];
  }

  // not possible if not defined along y
  if ((nsections() > 1) and (abs(ypos.back() - ypos.front()) < 1e-3))
    return false;

  if ( nsections() > 1 and ypos.front() != 0 and ypos.back() != 0
       and sign(ypos.front()) != sign(ypos.back()) )
    return false;

  Vct3 nctr;
  uint ns(sections.size());
  for (uint i=0; i<ns; ++i) {
    nctr = sections[i]->origin();
    if (nctr[1] == 0.0)
      continue;
    else {
      const char Left[] = "Left";
      const char Right[] = "Right";
      string sname = sections[i]->name();
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
      WingSectionPtr sp(sections[i]->clone());
      nctr[1] = -nctr[1];
      sp->origin(nctr);
      sp->dihedralAngle(-sp->dihedralAngle());
      sp->interpolate();
      sp->rename(sname);
      sections.push_back(sp);
    }
  }
  interpolate();

  return true;
}

void WingSkeleton::glDraw() const
{
  if (not bVisible)
    return;
  
  if (nsections() < 2) 
    return;

  updateVizGrid();
  glDrawGrid();
  
  // draw translated frames
  Vector up( cosine_pattern(120, 4*PI, 0.0, 0.9) );
  const uint nf(sections.size());
  for (uint i=0; i<nf; ++i) {
    CurvePtr cp( sections[i]->curve() );
    glDrawCurve(*cp, up);
  }
}

uint WingSkeleton::vspacing(int n, Vector & vp) const
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

void WingSkeleton::adaptVizSlice(size_t na, Real v, Vector &ua) const
{
  // initialize ua by allocating na/2 points to equidistant spacing
  size_t nap = std::max(size_t(20), na/2);
  ua = equi_pattern(nap, 0.0, 1.0);

  // start by inserting nodes in segments where local kink angle is > 45deg
  Real climit = cos(rad(45.));

  // number of smoothing iterations to run inside each refinement sweep
  const size_t nsm = 2;

  const Surface &srf( *(this->surface()) );

  Vct3 pa, pb, tga, tgb, dummy;
  while (nap < na) {

    // insert points where angle between tangents is too large
    srf.plane(ua[0], v, pa, tga, dummy);
    for (size_t i=1; i<nap; ++i) {
      Real umid = 0.5*(ua[i-1] + ua[i]);
      srf.plane(ua[i], v, pb, tgb, dummy);
      if ( cosarg(tga, tgb) < climit )
        ua.push_back( umid );
      tga = tgb;
      pa = pb;

      // limit insertions to prescribed maximum
      if (ua.size() == na)
        break;
    }

    // if no points were inserted, reduce the criterion and repeat'
    // limit = 45, 32.8, 23.5, 16.7, ...
    if (ua.size() == nap) {
      climit = std::sqrt(climit);
      continue;
    }

    // inserted points are already sorted, just merge ranges
    std::inplace_merge(ua.begin(), ua.begin()+nap, ua.end());

    // if any points were inserted, smooth parameter distribution a little
    // in order to avoid too large differences between segment sizes
    nap = ua.size();
    for (size_t j=0; j<nsm; ++j) {
      for (size_t i=1; i<nap-1; ++i)
        ua[i] = 0.5*ua[i] + 0.25*(ua[i-1] + ua[i+1]);
      for (size_t i=(nap-2); i>=1; --i)
        ua[i] = 0.5*ua[i] + 0.25*(ua[i-1] + ua[i+1]);
    }
  }
}

void WingSkeleton::vizGrid(PointGrid<2> & qts) const
{
//  // visualization grid parameters
//  Real lmax = 0.25 * refChord;
//  Real lmin = 0.25 * minLERadius;
//  Real phimax = rad(25.);
  
//  // construct good approximation grid
//  Vector up, vp;
//  InitGrid ig(surface().get());
//  surface()->initGridPattern(up, vp);

//  vspacing(8, vp);
//  ig.initPattern(up, vp);
//  ig.vRefineByLength(lmax);
//  ig.vRefineByAngle(phimax);
//  ig.uAdapt(lmax, lmin, phimax, 64);
//  ig.vsmooth(1);
  
//  if (bAutoSym)
//    ig.enforceVSymmetry();
//  ig.collect(qts);

  const size_t nu(128);
  Vector vp, up(nu);
  vspacing( 8, vp );
  const size_t nv = vp.size();
  qts.resize(nu, nv);
  for (size_t j=0; j<nv; ++j) {
    adaptVizSlice(nu, vp[j], up);
    for (size_t i=0; i<nu; ++i)
      qts(i,j) = Vct2(up[i], vp[j]);
  }
}

uint WingSkeleton::lastWingletSection() const
{
  if (not bDetectWinglet)
    return 0;
  
  // assume sections are sorted
  uint nwl(0);
  const uint ns(sections.size());
  if (ns < 4)
    return 0;
  
  for (uint i=0; i<ns; ++i) {
    if (fabs(sections[i]->dihedralAngle()) > 0.25*PI)
      ++nwl;
  }
  
  // we actually return the first index past the winglet, so 
  // we cannot have 1, since we want at least 2 sections for the winglet
  if (nwl == 1)
    return 0;
  
  return nwl;
}

void WingSkeleton::exportGrid(uint numax, uint n2s, Real lmax, Real phimax, 
                              PointGrid<3> & pgrid) const
{
  // v-direction pattern
  const uint ns(vspos.size());
  Vector vp;
  for (uint i=1; i<ns; ++i) {
    Real base = vspos[i-1];
    Real dv = (vspos[i] - base) / n2s;
    for (uint j=0; j<n2s; ++j)
      vp.push_back(base + j*dv);
  }
  vp.push_back(1.0);
  
  // construct good approximation grid 
  InitGrid ig(surface().get());
  ig.initPattern(equi_pattern( min(30u,numax) ), vp);
  ig.uAdapt(lmax, minLERadius, phimax, numax);
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

void WingSkeleton::ipolPoints(PointListArray & pts) const
{
  // construct transformation 
  Transformer tf;
  tf.rotate(sRot[0], sRot[1], sRot[2]);
  tf.translate(sTrn);
  
  // collect points 
  const uint ns(sections.size());
  pts.resize(ns);
  for (uint i=0; i<ns; ++i) {
    Transformer tfs;
    tfs.scale( sections[i]->chordLength() );
    tfs.rotate(sections[i]->dihedralAngle(), sections[i]->twistAngle(), 0.0);
    tfs.translate( sections[i]->origin() );
    const PointList<2> & rp(sections[i]->riPoints());
    const uint np(rp.size());
    pts[i].resize(np);
    for (uint j=0; j<np; ++j) {
      Vct3 p( vct(rp[j][0], 0.0, rp[j][1]) );
      pts[i][j] = tf.forward(tfs.forward(p));
    }
  }
}
Real WingSkeleton::locateLeadingEdge(Real v, Real utol) const
{
  // locate u for the leading edge point (min x)
  SurfacePtr srf = Component::surface();
  Real u(0.5), ulo(0.4), uhi(0.6);
  Vct3 tg;
  while ( fabs(uhi-ulo) > utol ) {
    u = 0.5*(ulo + uhi);
    tg = srf->derive(u, v, 1, 0);
    if (tg[0] < 0)
      ulo = u;
    else if (tg[0] > 0)
      uhi = u;
    else
      return u;
  }
  return u;
}

Real WingSkeleton::vSpanPos(Real u, Real yrel, Real vtol) const
{
  const Surface & srf = *(Component::surface());
  Vct3 yzero = srf.eval(u, 0.0);
  Vct3 yone = srf.eval(u, 1.0);
  Real ispan = 1.0 / spandist(yzero, yone);
  Real vlo(0.0), vmid(0.5), vhi(1.0);
  while ( fabs(vhi-vlo) > vtol ) {
    vmid = 0.5*(vlo+vhi);
    Real yrm = spandist(yzero, srf.eval(u,vmid)) * ispan;
    if (yrm < yrel)
      vlo = vmid;
    else if (yrm > yrel)
      vhi = vmid;
    else
      return vmid;
  }
  return vmid;
}

Real WingSkeleton::hingePos(Real v, Real chordpos, Vct3 & hp) const
{
  SurfacePtr srf = Component::surface();
  Real vcap = min(1.0, max(0.0, v));
  Real ule = locateLeadingEdge(vcap);
  Vct3 lepos = srf->eval(ule, vcap);
  Vct3 tepos = srf->eval(0.0, vcap);  
  Real chord = norm(lepos - tepos);
  hp = (1.0 - chordpos)*lepos + chordpos*tepos;
  return chord;
}

void WingSkeleton::updateStats()
{
  const int ns(sections.size());
  refChord = 0.0;
  refSpan = 0.0;
  refArea = 0.0;
  refMac = 0.0;
  
  SurfacePtr srf = Component::surface();
  Vct3 dsv, xax;
  xax[0] = 1.0;
  for (int i=1; i<ns; ++i) {
    const WingSection & ws1( *sections[i-1] );
    const WingSection & ws2( *sections[i] );
    dsv = ws1.origin() - ws2.origin();
    Real ds = norm(dsv - dot(dsv,xax)*xax);
    Real ca = ws1.chordLength();
    Real cb = ws2.chordLength();
    Real vmid = 0.5*(vspos[i-1] + vspos[i]);
    Real ule = locateLeadingEdge(vmid);
    Real cm = norm( srf->eval(0.0,vmid) - srf->eval(ule,vmid) );
    refSpan += ds;
    refArea += (ds/6.)*(ca + 4*cm + cb);
    refMac  += (ds/6.)*(sq(ca) + 4*sq(cm) + sq(cb));
  }
  refChord = refArea / refSpan;
  refMac *= 1.0/refArea;
  
  if (bAutoSym) {
    refSpan *= 2.0;
    refArea *= 2.0;
  }
}

WingSkeletonPtr WingSkeleton::xzMirrorCopy() const
{
  WingSkeletonPtr mc = clone();
  
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
  
  // mirror sections 
  const int nf(mc->nsections());
  for (int i=0; i<nf; ++i) {
    WingSection & bf( *(mc->section(i)) );
    
    bf.dihedralAngle( -bf.dihedralAngle() );
    bf.yawAngle( -bf.yawAngle() );
    
    org = bf.origin();
    org[1] *= -1.0;
    bf.origin( org );
    bf.interpolate();
  }

  // reverse section order
  std::reverse(mc->sections.begin(), mc->sections.end());

  mc->interpolate();
  
  return mc;
}

DnWingCriterionPtr WingSkeleton::wingCriterion()
{
  DnWingCriterionPtr wcp;
  wcp = boost::dynamic_pointer_cast<DnWingCriterion>( criterion() );
  if (not wcp) {
    wcp = DnWingCriterionPtr( new DnWingCriterion );
    criterion( boost::dynamic_pointer_cast<DnRefineCriterion>(wcp) );
  }
  return wcp;
}

void WingSkeleton::defaultCriterion()
{
  bUseMgDefaults = true;
  
  // setup specialized wing criterion
  DnWingCriterionPtr wmg( new DnWingCriterion );
  wmg->addBreaks(cpa, bAutoSym);
  
  // add break section positions as kinks
  const uint ns(sections.size());
  Vector vkpos;
  for (uint i=0; i<ns; ++i) {
    if (sections[i]->isBreak()) {
      if (bAutoSym) {
        vkpos.push_back(vspos[i]);
        vkpos.push_back(1.0 - vspos[i]);
      } else {
        vkpos.push_back(vspos[i]);
      }
    } 
  }
  if (bAutoSym)
    vkpos.push_back(0.5);
  sort_unique(vkpos);
  wmg->addVKinks(*surface(), vkpos);
  
  // default settings 
  const Real maxlen = 0.15*refChord;
  const Real minlen = min(0.08*maxlen, 0.7*minLERadius);
  const Real maxphi = rad(30.0);
  const Real maxstretch = 6.0;
  wmg->setCriteria(maxlen, minlen, maxphi, maxstretch);
  wmg->addRegion( DnRefineRegion(vct(0.0,0.03), vct(1.0,0.06), 0.6) );
  wmg->addRegion( DnRefineRegion(vct(0.0,0.0), vct(1.0,0.03), 0.4) );
  wmg->addRegion( DnRefineRegion(vct(0.0,0.94), vct(1.0,0.97), 0.6) );
  wmg->addRegion( DnRefineRegion(vct(0.0,0.97), vct(1.0,1.0), 0.4) );
  wmg->edgeRefinement(1./2., 1./2.);
  
  AsyComponent::criterion(wmg);
  AsyComponent::surfaceChanged();
}

void WingSkeleton::buildInitGrid(PointGrid<2> & pgi)
{
  // determine minimum number of u-sections
  Vector upat;
  const int nsec = vspos.size();
  uint numin = 0;
  for (int j=0; j<nsec; ++j) 
    numin = max(numin, findChordPattern(vspos[j], NotFound, upat));
  
  // use this parameter to generate optimal local patterns
  PointGrid<2> tmp(numin,nsec);
  for (int j=0; j<nsec; ++j) {
    findChordPattern(vspos[j], numin, upat);
    assert(upat.size() == numin);
    
    for (uint i=0; i<numin; ++i)
      tmp(i,j) = vct(upat[i], vspos[j]);
  }
  
  InitGrid ig(surface().get());
  ig.initPattern(tmp);
  ig.vRefineByLength( criterion()->maxLength() );
  ig.vRefineByAngle( criterion()->maxPhi() );
  
  if (autoSym()) 
    ig.enforceVSymmetry();
  ig.enforceColumns(vspos);
  ig.collect(pgi);
}

uint WingSkeleton::findChordPattern(Real v, uint nufix, Vector & up)
{
  // limits not to exceed
  const Real le_exp_max = 1.6;
  const Real te_exp_max = 1.25;
  const uint nu_max = 128;
  
  // compute xte from trailing edge refinement requirement
  Real terf(0.0), xte = 1.1;
  DnWingCriterionPtr wcr;
  wcr = boost::dynamic_pointer_cast<DnWingCriterion>( criterion() );
  if (wcr) {
    terf = 1.0 / wcr->teRefinement();
  }
  
  uint nu(24);
  Real ule = locateLeadingEdge(v, 1e-6);
  
  // initial phase: can choose nu freely
  Real xle(1.1); 
  if (nufix == NotFound) {
    
    // increase xle until angular criterion is achieved, increase
    // nu only if maximum length is exceeded; stop increasing LE
    // refinement when no improvement is achieved
    Real xlen(huge), xphi(huge), pxlen(huge), pxphi(huge);
    do {
      
      pxlen = xlen;
      pxphi = xphi;
      
      if (terf > 1.0) {
        Real nseg = (nu - nu/8 + 3)/4 + 1;
        xte = min(te_exp_max, pow(terf, 1.0/nseg));
      }
      
      airfoil_pattern(nu, ule, xle, xte, up);
      upQuality(v, up, xphi, xlen);
      
      if (xlen > 1.0) {
        xle -= 0.02;
        if (nu < nu_max)
          nu += 4;
        else
          break;
      } else if (xphi > 1.0) {
        if (xle < le_exp_max)
          xle += 0.04;
        else if (nu < nu_max)
          nu += 4;
      }
      
    } while ( max(xlen,xphi) > 1.0 and xphi <= pxphi );

    if (pxphi < xphi)
      xle -= 0.04;  
    
  } else {
  
    if (terf > 1.0) {
      Real nseg = (nufix - nufix/8 + 3)/4 + 1;
      xte = min(te_exp_max, pow(terf, 1.0/nseg));
    }
    
    // in this case, nu is fixed to a certain value
    // simply find xle which minimizes xphi*xlen
    Real xlen, xphi, xp, xpbest(huge), xleopt(xle), xstep = 0.02;
    int ntest = (int) ((le_exp_max-xle) / xstep);
    for (int i=0; i<ntest; ++i) {
      airfoil_pattern(nufix, ule, xle, xte, up);
      upQuality(v, up, xphi, xlen);
      xp = max(xlen, xphi);
      if (xp < xpbest) {
        xpbest = xp;
        xleopt = xle;
      }
      xle += xstep;
    }
    
    airfoil_pattern(nufix, ule, xleopt, te_exp_max, up);
  }

  return up.size();
}

void WingSkeleton::upQuality(Real v, const Vector & up, Real & phi, Real & len)
{
  const Surface & srf( *surface() );
  const int np = up.size();
  PointList<3> pts(np), seg(np-1);
  for (int i=0; i<np; ++i) 
    pts[i] = srf.eval( up[i], v );
  
  // allowed limits
  Real maxphi = criterion()->maxPhi();
  Real maxlen = criterion()->maxLength();
  
  // evaluate segment lengths
  len = 0;
  for (int i=0; i<np-1; ++i) {
    seg[i] = pts[i+1] - pts[i];
    len = max(len, norm(seg[i]) / maxlen);
  }
  
  phi = 0;
  for (int i=1; i<np-2; ++i) {
    Real p = arg(seg[i], seg[i-1]);
    phi = max(phi, p/maxphi); 
  }
}

void WingSkeleton::capsToIges(IgesFile & file) const
{
  CurvePtr cv0, cv1;
  
  cv0 = CurvePtr( sections.front()->curve()->clone() );
  cv0->rotate(sRot[0], sRot[1], sRot[2]);
  cv0->translate(sTrn);
  cv0->apply();
  
  if (bAutoSym) {
    const WingSection & rightTip( *(sections.front()) );
    WingSection leftTip;
    leftTip.riPoints() = rightTip.riPoints();
    leftTip.chordLength( rightTip.chordLength() );
    leftTip.twistAngle( rightTip.twistAngle() );
    leftTip.dihedralAngle( -rightTip.dihedralAngle() );
    leftTip.yawAngle( -rightTip.yawAngle() );
    Vct3 org = rightTip.origin();
    leftTip.origin( vct(org[0], -org[1], org[2]) );
    leftTip.interpolate();
    cv1 = CurvePtr( leftTip.curve()->clone() );
  } else {
    cv1 = CurvePtr( sections.back()->curve()->clone() );
  }
  cv1->rotate(sRot[0], sRot[1], sRot[2]);
  cv1->translate(sTrn);
  cv1->apply();
  
  // use flat caps for now
  SplineCapSurf fcap("RightTipCap");
  fcap.init(locateLeadingEdge(0.0, 1e-6), *cv0);
  fcap.toIges(file);
  
  SplineCapSurf rcap("LeftTipCap");
  rcap.init(locateLeadingEdge(1.0, 1e-6), *cv1);
  rcap.toIges(file);
}

void WingSkeleton::fitSection(uint jsection, const FrameProjector &fpj,
                              Real rChord, Real rThick)
{
  if (jsection >= nsections())
    return;

  // determine component-level transformation
  Trafo3d trafo;
  trafo.rotate( sRot );
  trafo.translate( sTrn );

  Mtx44 skt;
  trafo.matrix(skt);

  sections[jsection]->fitSection(fpj, skt, rChord, rThick);
  interpolate();
}

void WingSkeleton::fitSections(const FrameProjector &fpj,
                               Real rChord, Real rThick)
{
  // determine component-level transformation
  Trafo3d trafo;
  trafo.rotate( sRot );
  trafo.translate( sTrn );

  Mtx44 skt;
  trafo.matrix(skt);

  const int n = sections.size();
//#pragma omp parallel for
  for (int i=0; i<n; ++i)
    sections[i]->fitSection(fpj, skt, rChord, rThick);

  interpolate();
}
