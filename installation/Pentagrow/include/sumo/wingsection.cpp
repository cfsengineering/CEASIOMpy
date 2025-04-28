
/* ------------------------------------------------------------------------
 * file:       wingsection.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Wrapper object for airfoil object
 * ------------------------------------------------------------------------ */

#include "wingsection.h"
#include "frameprojector.h"
#include <surf/naca6.h>
#include <surf/airfoil.h>
#include <surf/airfoilcollection.h>
#include <surf/airfoilfitter.h>
#include <surf/iges116.h>
#include <genua/xcept.h>
#include <genua/pattern.h>

using namespace std;

WingSection::WingSection() : m_chord(1.0), m_twist(0.0), m_dihedral(0.0), m_yaw(0.0),
  m_nap(-1), m_bBreak(false), m_bReversed(false)
{
  m_dxNose = m_dyNose = m_dxTail = m_dyTail = 0.0;
  fromNaca4( 2315 );
  rename("UnknownSection");
  m_idAirfoil = "NACA 2315";
}

WingSectionPtr WingSection::clone() const
{
  WingSection *pws = new WingSection;
  pws->m_mctr = m_mctr;
  pws->m_crd = m_crd;
  pws->m_nap = m_nap;
  pws->m_idAirfoil = m_idAirfoil;
  pws->m_chord = m_chord;
  pws->m_twist = m_twist;
  pws->m_dihedral = m_dihedral;
  pws->m_dxNose = m_dxNose;
  pws->m_dyNose = m_dyNose;
  pws->m_dxTail = m_dxTail;
  pws->m_dyTail = m_dyTail;
  pws->m_yaw = m_yaw;
  pws->m_bBreak = m_bBreak;
  pws->m_bReversed = m_bReversed;
  pws->m_nap = m_nap;
  pws->interpolate();
  pws->rename(name());
  return WingSectionPtr(pws);
}

void WingSection::transform(Airfoil *paf)
{
  paf->closeTrailingEdge();
  paf->extend(m_dxNose, m_dyNose, m_dxTail, m_dyTail);

  // simplify geometry - necessary to allow
  // IGES export to braindead importers which will not
  // read splines/surface with more than 99 control points
  if (paf->sectionCoordinates().size() > 98) {
    Vector pat;
    // paf->xpattern(96, 1.20, 1.10, pat);
    paf->adaptiveParam(96, pat);
    paf->reparametrize(pat);
  }

  // apply transformations
  m_crv = CurvePtr( paf );
  m_crv->rotate(m_dihedral, 0.0, 0.0);
  m_crv->rotate(0.0, m_twist, 0.0);
  m_crv->rotate(0.0, 0.0, m_yaw);
  m_crv->scale(m_chord);
  m_crv->translate(m_mctr);
  m_crv->apply();

  // optionally, reverse parametrization
  if (m_bReversed)
    m_crv->reverse();
}

void WingSection::globalScale(Real f)
{
  m_mctr *= f;
  m_chord *= f;
  if (m_crv) {
    m_crv->scale(f);
    m_crv->apply();
  }
}

void WingSection::interpolate()
{
  string afname;
  if (m_crv)
    afname = m_crv->name();
  else
    afname = "UnknownAirfoil";

  // initialize Airfoil object
  Airfoil *paf(0);
  paf = new Airfoil(afname, m_crd, m_nap);
  transform(paf);
}

Plane WingSection::sectionPlane() const
{
  // compute plane normal
  Vct3 pn(0.0, 1.0, 0.0);
  Trafo3d trafo;
  trafo.rotate(m_dihedral, m_twist, m_yaw);
  trafo.transformDirection(pn);
  return Plane(pn, dot(pn, m_mctr));
}

void WingSection::fromFile(const std::string & fname)
{
  // keep name if possible
  string afname;
  if (m_crv)
    afname = m_crv->name();
  else
    afname = "UnknownAirfoil";

  Airfoil *paf = new Airfoil(afname);
  paf->read(fname);
  m_crd = paf->sectionCoordinates();

  // construct airfoil name (filename without extension)
  char psep('/');
  char esep('.');
  string::size_type pos1 = fname.find_last_of(psep);
  string::size_type pos2 = fname.find_last_of(esep);
  m_idAirfoil = fname.substr( pos1+1, pos2-pos1-1 );
  
  transform(paf);
}

void WingSection::fromCollection(const AirfoilCollection & afc, uint ipos)
{
  m_idAirfoil = afc.coordName(ipos);
  const AirfoilPtr & afp( afc.foil(ipos) );
  
  m_crd = afp->sectionCoordinates();
  Airfoil *ap = new Airfoil(m_idAirfoil, m_crd);
  transform(ap);
}

void WingSection::fromCoordinates(const std::string & id, const PointList<2> & pts)
{
  m_idAirfoil = id;
  m_crd = pts;
  Airfoil *ap = new Airfoil(m_idAirfoil, m_crd);
  transform(ap);
}

void WingSection::fromNaca4(uint ncode)
{
  // keep name if possible
  string afname;
  if (m_crv)
    afname = m_crv->name();
  else
    afname = "UnknownAirfoil";

  Airfoil *paf = new Airfoil(afname, m_nap);
  paf->naca(ncode);
  m_crd = paf->sectionCoordinates();

  if (ncode < 10)
    m_idAirfoil = "NACA 000" + str(ncode);
  else if (ncode < 100)
    m_idAirfoil = "NACA 00" + str(ncode);
  else if (ncode < 1000)
    m_idAirfoil = "NACA 0" + str(ncode);
  else
    m_idAirfoil = "NACA " + str(ncode);
  
  transform(paf);
}

void WingSection::fromNaca4(Real camber, Real cpos, Real thick)
{
  // keep name if possible
  string afname;
  if (m_crv)
    afname = m_crv->name();
  else
    afname = "UnknownAirfoil";

  Airfoil *paf = new Airfoil(afname, m_nap);
  paf->naca4(camber, cpos, thick);
  m_crd = paf->sectionCoordinates();
  m_idAirfoil = Airfoil::naca4name(camber, cpos, thick);
  
  transform(paf);
}

void WingSection::fromNaca5(int meanline, Real dcl, Real thick)
{
  // keep name if possible
  string afname;
  if (m_crv)
    afname = m_crv->name();
  else
    afname = "UnknownAirfoil";

  Airfoil *paf = new Airfoil(afname, m_nap);
  paf->naca5(meanline, dcl, thick);
  m_crd = paf->sectionCoordinates();
  m_idAirfoil = Airfoil::naca5name(meanline, dcl, thick);
  
  transform(paf);
}

int WingSection::fromNaca6(uint iprofile, uint icamber, Real toc, 
                           const Vector & cli, const Vector & a)
{
  // keep name if possible
  string afname;
  if (m_crv)
    afname = m_crv->name();
  else
    afname = "UnknownAirfoil";

  Airfoil *paf = new Airfoil(afname, m_nap);
  int stat = paf->naca(iprofile, icamber, toc, cli, a);
  if (stat != NACA6_SUCCESS) {
    delete paf;
    return stat;
  }
  m_crd = paf->sectionCoordinates();
  m_idAirfoil = Airfoil::naca6name(iprofile, toc, cli.front());
  
  transform(paf);
  return NACA6_SUCCESS;
}

void WingSection::fromPlate(Real toc)
{
  // keep name if possible
  string afname;
  if (m_crv)
    afname = m_crv->name();
  else
    afname = "UnknownAirfoil";

  Airfoil *paf = new Airfoil(afname, m_nap);
  paf->flatPlate(toc);
  m_crd = paf->sectionCoordinates();
  m_idAirfoil = "flat (" + str(int(100*toc)) + "%)";
  
  transform(paf);
}

void WingSection::checkCoordinates()
{
  // check for large angles
  const int nc = m_crd.size();
  const Real mincosphi = std::cos( rad(175.) );
  for (int i=1; i<nc-1; ++i) {
    Real cphi = cosarg( m_crd[i+1]-m_crd[i], m_crd[i]-m_crd[i-1] );
    if (cphi < mincosphi) {
      stringstream ss;
      ss << "Coordinates for wing section " << name() << " are not usable.";
      ss << " Sharp corner (" << deg(acos(cphi)) << "deg) at (" << endl;
      ss << m_crd[i-1] << "), (" << m_crd[i] << "), (" << m_crd[i+1] << ").";
      throw Error(ss.str());
    }
  }
}

XmlElement WingSection::toXml() const
{
  XmlElement xe("WingSection");
  xe["chord"] = str(m_chord);
  xe["twist"] = str(m_twist);
  xe["dihedral"] = str(m_dihedral);
  xe["yaw"] = str(m_yaw);
  xe["center"] = str(m_mctr);
  xe["name"] = name();
  xe["napprox"] = str(m_nap);
  xe["vbreak"] = m_bBreak ? "true" : "false";
  xe["reversed"] = m_bReversed ? "true" : "false";
  xe["airfoil"] = m_idAirfoil;
  if (m_dxNose != 0)
    xe["extend_xle"] = str(m_dxNose);
  if (m_dyNose != 0)
    xe["extend_yle"] = str(m_dyNose);
  if (m_dxTail != 0)
    xe["extend_xte"] = str(m_dxTail);
  if (m_dyTail != 0)
    xe["extend_yte"] = str(m_dyTail);

  stringstream ss;
  ss << m_crd;
  xe.text(ss.str());

  return xe;
}

void WingSection::fromXml(const XmlElement & xe)
{
  if (xe.name() != "WingSection")
    throw Error("Incompatible XML representation for WingSection: "
                +xe.name());

  string sname(xe.attribute("name"));
  m_chord = Float(xe.attribute("chord"));
  m_twist = xe.attr2float("twist", 0.0);
  m_dihedral = xe.attr2float("dihedral", 0.0);
  m_yaw = xe.attr2float("yaw", 0.0);
  m_nap = xe.attr2int("napprox", -1);
  m_dxNose = xe.attr2float("extend_xle", 0.0);
  m_dyNose = xe.attr2float("extend_yle", 0.0);
  m_dxTail = xe.attr2float("extend_xte", 0.0);
  m_dyTail = xe.attr2float("extend_yte", 0.0);
  
  if (xe.hasAttribute("vbreak")) {
    string s = toLower( xe.attribute("vbreak") );
    if (s == "true" or s == "yes")
      m_bBreak = true;
  } else {
    m_bBreak = false;
  }

  if (xe.hasAttribute("reversed")) {
    string s = toLower( xe.attribute("reversed") );
    if (s == "true" or s == "yes")
      m_bReversed = true;
  } else {
    m_bReversed = false;
  }
  
  {
    stringstream ss;
    ss << xe.attribute("center");
    ss >> m_mctr;
  }

  m_crd.clear();
  if (xe.hasAttribute("naca")) {
    uint nacaCode = Int(xe.attribute("naca"));
    fromNaca4( nacaCode );
    if (nacaCode < 10)
      m_idAirfoil = "NACA 000" + str(nacaCode);
    else if (nacaCode < 100)
      m_idAirfoil = "NACA 00" + str(nacaCode);
    else if (nacaCode < 1000)
      m_idAirfoil = "NACA 0" + str(nacaCode);
    else
      m_idAirfoil = "NACA " + str(nacaCode);
  } else {
    if (xe.hasAttribute("airfoil"))
      m_idAirfoil = xe.attribute("airfoil");
    stringstream ss;
    ss << xe.text();
    Real x, y;
    while (ss >> x >> y)
      m_crd.push_back( vct(x,y) );
    if (m_crd.empty()) {
      clog << ss.str();
      throw Error("Airfoil "+sname+" does not contain coordinates.");
    }
    checkCoordinates();
  }

  interpolate();
  rename(sname);
}

Real WingSection::leRadius() const
{
  // TODO : replace with golden_ratio_minimum over segments
  const int ns(16);
  Real up[ns], cvp[ns], ulo(0.2), uhi(0.8), cvmax;
  for (uint iter=0; iter<8; ++iter) {
    for (int k=0; k<ns; ++k) {
      up[k] = ulo + k*(uhi - ulo)/(ns-1);
      cvp[k] = m_crv->curvature(up[k]);
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

int WingSection::pointsToIges(IgesFile &file,
                              int sectionId, int tfi) const
{
  AirfoilPtr afp = boost::dynamic_pointer_cast<Airfoil>(m_crv);
  if (afp == nullptr)
    return 0;

  Mtx44 m;
  Trafo3d tfm;
  tfm.scale(m_chord, m_chord, m_chord);
  tfm.rotate(m_dihedral, m_twist, m_yaw);
  tfm.translate(m_mctr);
  tfm.matrix(m);

  int id(0);
  string label;
  const PointList2d &sc( afp->sectionCoordinates() );
  const size_t np = sc.size();
  for (size_t i=0; i<np; ++i) {
    Vct3 p( sc[i][0], 0.0, sc[i][1] );
    Trafo3d::transformPoint(m, p);
    IgesPoint ip(p);
    label = "P" + str(sectionId) + "." + str(i+1);
    ip.label(label.c_str());
    ip.trafoMatrix(tfi);
    id = ip.append(file);
  }

  return id;
}

void WingSection::extendBoundingBox(float plo[3], float phi[3]) const
{
  Vct3 p;
  const uint nu(64);
  for (uint i=0; i<nu; ++i) {
    p = m_crv->eval(Real(i)/(nu-1));
    plo[0] = min(plo[0], float(p[0]));
    plo[1] = min(plo[1], float(p[1]));
    plo[2] = min(plo[2], float(p[2]));
    phi[0] = max(phi[0], float(p[0]));
    phi[1] = max(phi[1], float(p[1]));
    phi[2] = max(phi[2], float(p[2]));
  }
}

void WingSection::captureRectangle(const Mtx44 &skeletonTrafo, Real rChord, Real rThick,
                                   Vct3 &po, Vct3 &pu, Vct3 &pv, Vct3 &pn) const
{
  // determine bounded plane to use for intersection
  pu = Vct3(1.0,  0.0, 0.0);
  pv = Vct3(0.0,  0.0, 1.0);
  pn = Vct3(0.0,  1.0, 0.0);

  Trafo3d trafo;
  trafo.rotate(m_dihedral, m_twist, m_yaw);

  // account for transformation of the entire wing
  Mtx44 stm;
  trafo.matrix(stm);
  stm = skeletonTrafo * stm;

  po = m_mctr;
  pu *= 0.5 * m_chord * rChord;
  pv *= 0.5 * m_chord * rThick;

  Trafo3d::transformPoint(skeletonTrafo, po);
  Trafo3d::transformDirection(stm, pu);
  Trafo3d::transformDirection(stm, pv);
  Trafo3d::transformDirection(stm, pn);

  po += pu / rChord;
}

void WingSection::fitSection(const FrameProjector &fpj,
                             const Mtx44 &skeletonTrafo, Real rChord, Real rThick)
{
  // debug
  cerr << "Fitting section: " << name() << endl;

  Vct3 po, pu, pv, pn;
  captureRectangle(skeletonTrafo, rChord, rThick, po, pu, pv, pn);

  FrameProjector::SegmentArray segs;
  fpj.intersect(po, pu, pv, segs);

  PointList<3> mss;
  fpj.modelSpaceSegments(segs, mss);

  if (mss.size() == 0) {
    cerr << "Wing section plane does not intersect overlay." << endl;
    return;
  }

  Vct3 rot;
  AirfoilFitter fitter;
  fitter.principalDirections( pu.normalized(), pn.normalized() );
  AirfoilPtr fitfoil = fitter.fitSegments(mss);
  m_crd = fitfoil->sectionCoordinates();
  m_chord = fitter.chord();
  fitter.rotation( rot );

  // ensure that the actural underlying spline curve does not use more than
  // 100 control points because receiveing CAD does not accept that.
  if (m_crd.size() > 98)
    m_nap = 96;

  // fitter will generate a transformation *including* the top-level trafo
  // which is supposed to be applied at the WingSkeleton level - hence,
  // that contribution must be substracted
  Trafo3d trafo;
  trafo.rotate(rot);
  trafo.translate(fitter.origin());

  Mtx44 tffit, invskel;
  Trafo3d::inverse(skeletonTrafo, invskel);
  trafo.matrix(tffit);
  tffit = invskel * tffit;

  trafo.reconstruct(tffit);
  m_mctr = trafo.translation();
  rot = trafo.rotation();
  m_dihedral = rot[0];
  m_twist = rot[1];
  m_yaw = rot[2];

  interpolate();

  // change airfoil name
  m_idAirfoil = "(from overlay)";
}
