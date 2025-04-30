
/* ------------------------------------------------------------------------
 * file:       csmwing.cpp
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * CEASIOM wing definition of the SimSAC project
 * ------------------------------------------------------------------------ */

#include <genua/trigo.h>
#include <genua/strutils.h>
#include <genua/xmlelement.h>
#include <genua/xcept.h>
#include "componentlibrary.h"
#include "csmgenerator.h"
#include "csmwing.h"

using namespace std;

// --------------- CsmWing -------------------------------------------------

ComponentPtr CsmWing::create() const
{
  if (type == CsmUndefined)
    throw Error("CsmWing: Cannot generate undefined wing: "+tag());
  
  // construct a name 
  string wname = tag();
  
  // generate sections 
  Vct3 pos = vct(0,0,0);
  WingSkeletonPtr wsp(new WingSkeleton);
  wsp->clear();
  assert(airfoils.size() >= npanel+1);
  for (uint i=0; i<npanel+1; ++i) {
    const Airfoil & afi( *airfoils[i] );
    WingSectionPtr secp(new WingSection);
    secp->fromCoordinates(afi.name(), afi.sectionCoordinates());
    secp->rename( wname + "Section" + str(npanel+1-i) );
    secp->twistAngle( incidence[i] );
    secp->chordLength( rootchord*relchord[i] );
    secp->dihedralAngle( sdihedral[i] );
    secp->markAsBreak( true );
    secp->origin(secpos[i]);
    secp->interpolate();
    wsp->addSection(secp);
  }
  
  if (type == CsmVTP) {
    wsp->autoSym(false);
    wsp->rotation( vct(0.5*PI, 0.0, 0.0) );
  } else if (type == CsmPylon) {
    wsp->autoSym(false);
    wsp->rotation( vct(xrot, 0.0, 0.0) );
  } else {
    wsp->autoSym(true);
  }
  
  wsp->origin(apex);
  wsp->interpolate();
  wsp->rename(wname);
  wsp->useMgDefaults(true);
  
  return wsp;
}

void CsmWing::init()
{
  // relative spanwise position of the sections 
  etapos[0] = 0.0;
  for (uint i=0; i<npanel-1; ++i)
    etapos[i+1] = kink[i];
  etapos[npanel] = 1.0;
  
  // chord of the outboard sections in terms of root chord
  relchord[0] = 1.0;
  for (uint i=0; i<npanel; ++i)
    relchord[i+1] = taper[i];
    
  // span to use
  Real ss;
  if (type == CsmVTP or type == CsmPylon)
    ss = span;
  else
    ss = 0.5*span;
    
  // logic to compute root chord from area and taper ratios  
  if (type != CsmPylon) {
    
    Real uca(0.0);
    for (uint i=0; i<npanel; ++i) {
      Real pwidth = ss*(etapos[i+1] - etapos[i]);
      Real pchord = 0.5*(relchord[i+1] + relchord[i]);
      uca += pwidth*pchord;
    }
    
    // chord given by actual area then
    if (type == CsmVTP)
      rootchord = area/uca;
    else 
      rootchord = 0.5*area/uca;
  }
  
  // section dihedral 
  sdihedral[0] = 0.0;
  for (uint i=0; i<npanel-1; ++i)
    sdihedral[i+1] = 0.5*(dihedral[i] + dihedral[i+1]);
  sdihedral[npanel] = dihedral[npanel-1];
  
  // compute section positions relative to apex
  secpos.resize(npanel+1);
  secpos[0] = vct(0,0,0);
  for (uint i=0; i<npanel; ++i) {
    secpos[i+1] = secpos[i];
    Real pwidth = ss*(etapos[i+1] - etapos[i]);
    secpos[i+1][0] += pwidth*tan(lesweep[i]);
    secpos[i+1][1] += pwidth;
    secpos[i+1][2] += pwidth*tan(dihedral[i]);
  }
}

void CsmWing::fromXml(const XmlElement & xe)
{
  if (not isValid(xe)) {
    ar = 0.0;
    return;
  }
  
  tag(xe.name());
  string xtag = toLower( tag() );
  string rtag = xtag.substr(0, xtag.size()-1);
  if (xtag == "wing1")
    type = CsmMainWing;
  else if (xtag == "wing2" or xtag == "canard")
    type = CsmCanard;
  else if (xtag == "horizontal_tail")
    type = CsmHTP;
  else if (xtag == "vertical_tail") 
    type = CsmVTP;
  else if (rtag == "pylon")
    type = CsmPylon;
  else
    throw Error("CsmWing: Wing type not recognized: "+tag());
    
  // retrieve basic dimensions
  ar = floatFromNode(xe, "AR", 0.0);
  area = floatFromNode(xe, "area", 0.0);
  span = floatFromNode(xe, "span", 0.0);
  
  // ceasiom appears to assume that pylons start life as
  // port wings, so we need to adjust the rotation angle
  xrot = PI + rad(floatFromNode(xe, "rotation", 0.0));
  if (type == CsmPylon) 
    rootchord = floatFromNode(xe, "root_chord", 0.0);
    
  if (span == 0.0)
    span = sqrt(ar*area);
  else if (area == 0.0)
    area = sq(span)/ar;
  else if (ar == 0.0)
    ar = sq(span)/area;
  
  // check and complain 
  if (type != CsmPylon and (span*area*ar) == 0.0)
    throw Error("CsmWing: Major wing dimension undefined for "+xe.name());
  
  // retrieve panel dimensions
  fetchPanels(xe);
  
  // retrieve airfoil definitions
  fetchAirfoils(xe);
  reparametrizeAirfoils();
  
  // retrieve position 
  fetchPosition(xe);
  
  // retrieve control surface definitions
  fetchControls(xe);
  
  // perform basic geometry computations
  init();
}

bool CsmWing::isValid(const XmlElement & xe)
{
  string tag = toLower(xe.name());
  string rtag = tag.substr(0, tag.size()-1);
  if (rtag == "wing" or tag == "horizontal_tail" or 
      tag == "vertical_tail" or tag == "canard" or rtag == "pylon") {
    
    // if child element 'present' is there and contains the single
    // value '0', disable further processing
    XmlElement::const_iterator itr;
    itr = xe.findChild("present");
    if (itr != xe.end()) {
      int present = 1;
      fromString(itr->text(), present);
      if (present == 0)
        return false;
    }

    // actual wings have the area child set and nonzero
    itr = xe.findChild("area");
    if (itr != xe.end()) {
      Real area = Float(itr->text());
      if (area > 0)
        return true;
      else
        return false;
    }
    
    // pylons, however, don't have it; they contain a
    // rootchord entry instead. right.
    itr = xe.findChild("root_chord");
    if (itr != xe.end()) {
      Real rc = Float(itr->text());
      if (rc > 0)
        return true;
      else
        return false;
    }
    
  }
  return false;
}

void CsmWing::fetchAirfoils(const XmlElement & xe)
{
  // no documentation whatsoever what the section for pylons should be
  // best would be something rather rectangular with a large LE radius
  if (type == CsmPylon) {
    airfoils.resize(npanel+1);
    for (uint k=0; k<npanel+1; ++k) {
      Airfoil *paf = new Airfoil("NACA 0010");
      paf->naca(10);
      airfoils[k].reset(paf);
    }
    return;
  }
  
  // check if there is a tag named airfoil present and if that 
  // airfoil is present in the library; if so, use it
  // that seems to be the right thing to do for ceasiom 48
  string afname;
  XmlElement::const_iterator itr = xe.findChild("airfoil");
  if (itr != xe.end()) {
    afname = toLower(strip(itr->text()));
    uint icscol = SumoComponentLib.findCollection("ceasiom");
    if (icscol != NotFound) {
      const AirfoilCollection & cscol( SumoComponentLib.collection(icscol) ); 
      uint iaf = cscol.findByFileName(afname);

      // try with extended names if not found
      if (iaf == NotFound)
        iaf = cscol.findByFileName(append_suffix(afname, ".dat"));
      if (iaf == NotFound)
        iaf = cscol.findByFileName(append_suffix(afname, ".txt"));

      if (iaf != NotFound) {
        airfoils.resize(npanel+1);
        for (uint k=0; k<npanel+1; ++k)
          airfoils[k] = cscol.foil(iaf);
        return;
      } else if (afname.size() == 4) {

        // intercept 4-character airfoil name
        const char *cstr = afname.c_str();
        char *tail = 0;
        uint ncode = genua_strtol(cstr, &tail, 10);
        if (tail != cstr and ncode > 0 and ncode < 8930) {
          airfoils.resize(npanel+1);
          for (uint k=0; k<npanel+1; ++k) {
            Airfoil *pnf = new Airfoil("NacaSection");
            pnf->naca(ncode, true);
            airfoils[k] = AirfoilPtr(pnf);
          }
          return;
        }
      }
    } else {
      CsmGenerator::warning("Warning: CEASIOM airfoil collection not present.");
    }
  }
  
  // we end up here if we could not find what we were looking for
  // in the library, hence we scan the explicit airfoil definitions
  airfoils.clear();
  itr = xe.findChild("Root_Airfoil");
  if (itr == xe.end())
    throw Error("Could not find airfoil '"+afname+"' in CEASIOM collection;"
                "and XML element Root_airfoil not present in file. Please "
                "preprocess CEASIOM input file with 'Geo' first, so that "
                "necessary geometry data is written to file. See explanation "
                "in <b>D 2.3-5</b> for details.");
  airfoils.push_back( normalizeCoordinates(*itr, incidence[0] ));
  
  if (npanel == 3) {
    itr = xe.findChild("Kink1_Airfoil");
    if (itr != xe.end())
      airfoils.push_back( normalizeCoordinates(*itr, incidence[1] ));
    itr = xe.findChild("Kink2_Airfoil");
    if (itr != xe.end())
      airfoils.push_back( normalizeCoordinates(*itr, incidence[2] ));
    itr = xe.findChild("Tip_Airfoil");
    if (itr != xe.end())
      airfoils.push_back( normalizeCoordinates(*itr, incidence[3] ));
  } else if (npanel == 2) {
    itr = xe.findChild("Kink_Airfoil");
    if (itr != xe.end())
      airfoils.push_back( normalizeCoordinates(*itr, incidence[1] ));
    itr = xe.findChild("Tip_Airfoil");
    if (itr != xe.end())
      airfoils.push_back( normalizeCoordinates(*itr, incidence[2] ));
  } else if (npanel == 1) {
    itr = xe.findChild("Tip_Airfoil");
    if (itr != xe.end())
      airfoils.push_back( normalizeCoordinates(*itr, incidence[1] ));
  }
  
  if (airfoils.size() != npanel+1)
    throw Error("Not enough airfoil definitions for this number of kinks.");
}

void CsmWing::reparametrizeAirfoils()
{
  // pattern parameter
  const Real xte = 1.06;
  const Real xle = 1.20;
  const int np = 60;
  
  Vector pat;
  const int n = airfoils.size();
  for (int i=0; i<n; ++i) {
    airfoils[i]->closeTrailingEdge();
    airfoils[i]->xpattern(np, xle, xte, pat);
    airfoils[i]->reparametrize(pat);
  }
}

void CsmWing::fetchPanels(const XmlElement & xe)
{
  Real s1(0.0), s2(0.0), s3(0.0);
  if (type == CsmPylon) {
    
    npanel = 3;
    s1 = floatFromNode(xe, "inboard_span");
    s2 = floatFromNode(xe, "midboard_span");
    s3 = floatFromNode(xe, "outboard_span");
    span = s1 + s2 + s3;
    
  } else {
  
    if (xe.findChild("spanwise_kink1") != xe.end())
      npanel = 3;
    else if (xe.findChild("spanwise_kink") != xe.end()) {
      Real kpos = floatFromNode(xe, "spanwise_kink", 0.0);
      if (kpos == 0.0 or kpos == 1.0)
        npanel = 1;
      else
        npanel = 2;
    } else
      npanel = 1;
    
  }
    
  switch (npanel) {
  
    case 1:
      taper[0] = floatFromNode(xe, "taper_tip", 1.0);
      lesweep[0] = floatFromNode(xe, "LE_sweep_inboard", 0.0);
      dihedral[0] = floatFromNode(xe, "dihedral_inboard", 0.0);
      incidence[0] = floatFromNode(xe, "root_incidence", 0.0);
      incidence[1] = floatFromNode(xe, "tip_incidence", 0.0);
      break;
      
    case 2:
      kink[0] = floatFromNode(xe, "spanwise_kink");
      taper[0] = floatFromNode(xe, "taper_kink", 1.0);
      taper[1] = floatFromNode(xe, "taper_tip", 1.0);
      lesweep[0] = floatFromNode(xe, "LE_sweep_inboard", 0.0);
      lesweep[1] = floatFromNode(xe, "LE_sweep_outboard", 0.0);
      dihedral[0] = floatFromNode(xe, "dihedral_inboard", 0.0);
      dihedral[1] = floatFromNode(xe, "dihedral_outboard", 0.0);
      incidence[0] = floatFromNode(xe, "root_incidence", 0.0);
      incidence[1] = floatFromNode(xe, "kink_incidence", 0.0);
      incidence[2] = floatFromNode(xe, "tip_incidence", 0.0);
      break;
      
    case 3:
      if (type != CsmPylon) {
        kink[0] = floatFromNode(xe, "spanwise_kink1");
        kink[1] = floatFromNode(xe, "spanwise_kink2");
      } else {
        kink[0] = s1/span;
        kink[1] = (s1+s2)/span;
      }
      taper[0] = floatFromNode(xe, "taper_kink1", 1.0);
      taper[1] = floatFromNode(xe, "taper_kink2", 1.0);
      taper[2] = floatFromNode(xe, "taper_tip", 1.0);
      lesweep[0] = floatFromNode(xe, "LE_sweep_inboard", 0.0);
      lesweep[1] = floatFromNode(xe, "LE_sweep_midboard", 0.0);
      lesweep[2] = floatFromNode(xe, "LE_sweep_outboard", 0.0);
      dihedral[0] = floatFromNode(xe, "dihedral_inboard", 0.0);
      dihedral[1] = floatFromNode(xe, "dihedral_midboard", 0.0);
      dihedral[2] = floatFromNode(xe, "dihedral_outboard", 0.0);
      incidence[0] = floatFromNode(xe, "root_incidence", 0.0);
      incidence[1] = floatFromNode(xe, "kink1_incidence", 0.0);
      incidence[2] = floatFromNode(xe, "kink2_incidence", 0.0);
      incidence[3] = floatFromNode(xe, "tip_incidence", 0.0);
      break;
  
  }
  
  // transform all angles to radian
  for (int i=0; i<3; ++i) {
    lesweep[i] = rad(lesweep[i]);
    dihedral[i] = rad(dihedral[i]);
  }
  for (int i=0; i<4; ++i) {
    incidence[i] = rad(incidence[i]);
  }
}

void CsmWing::fetchPosition(const XmlElement & xe)
{
  apex[0] = floatFromNode(xe, "longitudinal_location", 0.0);
  apex[1] = floatFromNode(xe, "lateral_location", 0.0);
  apex[2] = floatFromNode(xe, "vertical_location", 0.0);
  rpos[0] = floatFromNode(xe, "apex_locale", 0.0);
  if (type == CsmVTP or type == CsmHTP or type == CsmCanard)
    rpos[2] = floatFromNode(xe, "vertical_locale", 0.0);
  else
    rpos[2] = floatFromNode(xe, "placement", 0.0);

  // there are different definitions as well
  apex[0] = floatFromNode(xe, "x", apex[0]);
  apex[1] = floatFromNode(xe, "y", apex[1]);
  apex[2] = floatFromNode(xe, "z", apex[2]);
}

void CsmWing::fetchControls(const XmlElement & xe)
{
  ctrl.clear();
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    CsmControlDef cdef;
    cdef.fromXml(*itr);
    if (cdef.isDefined()) {
      cdef.attachTo( *this );
      ctrl.push_back(cdef);
    }
  }
}

void CsmWing::postAttach(Assembly & asy)
{
  const int nc = ctrl.size();
  for (int i=0; i<nc; ++i) {
    ctrl[i].append(asy);
  }
}

Real CsmWing::fslChord(Real fwidth) const
{
  Real yt, fy = 0.5*fwidth;
  uint k(0);
  for (k = 0; k<npanel; ++k) {
    Real yleft = 0.5*span*etapos[k];
    Real yright = 0.5*span*etapos[k+1];
    yt = (fy - yleft) / (yright - yleft);
    if ( yleft <= fy and yright >= fy )
      break;
  }
  
  if (k == npanel)
    return rootchord;
  
  Real tpl = (k == 0) ? 1.0 : taper[k-1];
  Real tpr = taper[k];
  return rootchord*( (1.0-yt)*tpl + yt*tpr );
}

Real CsmWing::fslChordShift(Real fwidth) const
{
  return 0.5*fwidth*tan(lesweep[0]);
}

AirfoilPtr CsmWing::normalizeCoordinates(const XmlElement & xe, Real phi) const
{
  Real x, y, sphi, cphi;
  PointList<2> pts;
  stringstream ss(xe.text());
  
  Real xmin(huge), xmax(-huge), yle(0.0);
  while (ss >> x >> y) {
    
    if (x < xmin) {
      xmin = x;
      yle = y;
    }
    xmax = max(xmax, x);
    pts.push_back( vct(x,y) );
  }

  // check input
  if (pts.size() < 3) {
    string msg = "<b>Invalid CEASIOM input file.</b> ";
    msg += "Preprocessed airfoil XML elements (e.g. ";
    msg += xe.name() + ") must contain (x,y) ";
    msg += "coordinates, not airfoil names. ";
    throw Error(msg);
  }
  
  // incidence backrotation
  Mtx22 r;
  sincosine(phi, sphi, cphi);
  r(0,0) = cphi;
  r(0,1) = -sphi;
  r(1,0) = sphi;
  r(1,1) = cphi;
  
  // normalize to unit chord
  Real ichord = 1.0/(xmax - xmin);
  const int np = pts.size();
  for (int i=0; i<np; ++i) {
    Vct2 & p( pts[i] );
    p[0] -= xmin;
    p[1] -= yle;
    p *= ichord;
  
    // rotate back the incidence
    p = r*p;
  }
  
  return AirfoilPtr( new Airfoil(xe.name(), pts) );
}
