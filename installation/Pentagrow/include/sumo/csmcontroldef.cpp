
/* ------------------------------------------------------------------------
 * file:       csmcontroldef.cpp
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Control surface definition from ceasiom xml files
 * ------------------------------------------------------------------------ */
 
#include <genua/xmlelement.h>
#include "ctsurface.h"
#include "ctpattern.h"
#include "csmgenerator.h"
#include "csmwing.h"
#include "csmcontroldef.h"

using namespace std;

void CsmControlDef::attachTo(const CsmWing & wing)
{
  wingid = wing.tag();

  if (type == CsmCsUndefined)
    return;

  // flap hinge positions are at the kink locations
  if (id == "Flap") {
    assert(hpts.size() >= 2);
    hpts[0].rspan = 0.0;
    hpts[1].rspan = wing.kink1Pos();
    if (hpts.size() > 2)
      hpts[2].rspan = wing.kink2Pos();
  } else if (id == "Aileron") {
    assert(hpts.size() == 2);
    Real outspan = 1.0 - wing.kink2Pos();
    Real pos = hpts[0].rspan;
    Real rspan = hpts[1].rspan;
    Real bail = rspan*outspan;
    if (pos == 1.0) {
      hpts[0].rspan = wing.kink2Pos();
      hpts[1].rspan = wing.kink2Pos() + bail;
    } else if (pos == 2.0) {
      Real off = 0.5*(1.0 - rspan)*outspan;
      hpts[0].rspan = off + wing.kink2Pos();
      hpts[1].rspan = off + wing.kink2Pos() + bail;
    } else {
      Real off;
      if (pos + rspan <= 1.0)
        off = pos*outspan;
      else
        off = (1.0 - rspan)*outspan;
      hpts[0].rspan = off + wing.kink2Pos();
      hpts[1].rspan = off + wing.kink2Pos() + bail;
    }
  }

  // filter out ill-defined surfaces
  const int nhp = hpts.size();
  if (nhp < 2)
    type = CsmCsUndefined;

  for (int i=0; i<nhp; ++i) {
    if (hpts[i].rchord >= 1.0) {
      type = CsmCsUndefined;
      string msg = "Control surface "+id+" not imported: zero chord width.";
      CsmGenerator::information(msg);
      break;
    }
    if (hpts[i].rchord < 0.0) {
      type = CsmCsUndefined;
      stringstream msg;
      msg << "Control surface '" << id << "'' not imported: ";
      msg << "ill-defined chord width: " << 1.0 - hpts[i].rchord;
      CsmGenerator::warning(msg.str());
      break;
    }
  }
}

void CsmControlDef::fromXml(const XmlElement & xe)
{
  hpts.clear();

  type = CsmCsUndefined;
  string tg = toLower( xe.name() );

  // chop off the index at the end
  string::size_type pos = tg.find_last_not_of("0123456789");
  tg = tg.substr(0, pos+1);

  // interpret symmetry flag
  int sym = intFromNode(xe, "defl_sym", 0);
  if (sym == -1)
    motion = CsmCsAntiSym;
  else if (sym == 1)
    motion = CsmCsSym;
  else
    motion = CsmCsIndep;

  // set deflection limits (not used by sumo)
  if (xe.findChild("limit_deflection") != xe.end()) {
    delta_max = floatFromNode(xe, "limit_deflection", 30.0);
    delta_min = -delta_max;
  } else {
    delta_min = -floatFromNode(xe, "limit_deflection_down", 30.0);
    delta_max = +floatFromNode(xe, "limit_deflection_up", 30.0);
  }

  // This is a very common error in xml file definition, so we
  // should probably not bail out on it.

//  if (delta_max - delta_min == 0) {
//    string msg = "Control surface " + xe.name() + " not created: ";
//    msg += "Deflection limited to zero.";
//    CsmGenerator::warning(msg);
//    return;
//  }

  if (tg == "aileron")
    createAileron(xe);
  else if (tg == "rudder")
    createRudder(xe);
  else if (tg == "elevator")
    createElevator(xe);
  else if (tg == "flap")
    createFlap(xe);
  else if (tg.find("csurf") == 0)
    createCSurf(xe);

  // sort hinge points along the span
  std::sort(hpts.begin(), hpts.end());
}

void CsmControlDef::createFlap(const XmlElement & xe)
{
  id = "Flap";
  bMirror = true;

  type = CsmCsTE;
  motion = CsmCsSym;

  // first hinge point is farthest inboard
  uint nhp = 2 + (xe.findChild("kink2_chord") != xe.end() ? 1 : 0);
  hpts.resize(nhp);
  hpts[0].rspan = 0.0;
  hpts[0].rchord = 1.0 - floatFromNode(xe, "root_chord");
  hpts[1].rspan = 0.5;
  hpts[1].rchord = 1.0 - floatFromNode(xe, "kink1_chord");
  if (nhp == 3) {
    hpts[2].rspan = 1.0;
    hpts[2].rchord = 1.0 - floatFromNode(xe, "kink2_chord");
  }
}

void CsmControlDef::createAileron(const XmlElement & xe)
{
  id = "Aileron";
  bMirror = true;

  type = CsmCsTE;

  // assume that the aileron extends outboard from the
  // specified location on the right wing, where +spanwise
  // is from the centerline to the right
  Real width = floatFromNode(xe, "chord");
  Real hspan = floatFromNode(xe, "span");
  Real pos = floatFromNode(xe, "position");

  // aileron location depends on kink positions, which
  // are only available in attachTo(); hence, this just
  // stores the shape parameters
  hpts.resize(2);
  hpts[0].rspan = pos;
  hpts[0].rchord = 1.0 - width;
  hpts[1].rspan = hspan;
  hpts[1].rchord = 1.0 - width;
}

void CsmControlDef::createRudder(const XmlElement & xe)
{
  id = "Rudder";
  bMirror = false;

  type = CsmCsTE;

  Real width = floatFromNode(xe, "chord");
  Real hspan = floatFromNode(xe, "span");

  // spanwise positions will be set by attachTo
  hpts.resize(2);
  hpts[0].rspan = 1.0 - hspan;
  hpts[0].rchord = 1.0 - width;
  hpts[1].rspan = 1.0;
  hpts[1].rchord = 1.0 - width;
}

void CsmControlDef::createElevator(const XmlElement & xe)
{
  id = "Elevator";
  bMirror = true;

  // symmetric unless specified
  if (xe.findChild("defl_sym") == xe.end())
    motion = CsmCsSym;

  type = CsmCsTE;

  // assume that the aileron extends outboard from the
  // specified location on the right wing, where +spanwise
  // is from the centerline to the right
  Real width = floatFromNode(xe, "chord");
  Real hspan = floatFromNode(xe, "span");

  hpts.resize(2);
  hpts[0].rspan = 0.0;
  hpts[0].rchord = 1.0 - width;
  hpts[1].rspan = hspan;
  hpts[1].rchord = 1.0 - width;
}

void CsmControlDef::createCSurf(const XmlElement & xe)
{
  // chop off 'CSurf' from the front
  id = xe.name().substr(5);

  // default : switch on mirroring, will be disregarded
  // in case the wing surface attached is not symmetric
  bMirror = true;

  Real rci = floatFromNode(xe, "chord");
  Real rco = floatFromNode(xe, "chord_out", rci);
  Real rsi = floatFromNode(xe, "root_span");
  Real rso = rsi + floatFromNode(xe, "span");

  hpts.resize(2);
  hpts[0].rspan = rso;
  hpts[0].rchord = 1.0 - rco;
  hpts[1].rspan = rsi;
  hpts[1].rchord = 1.0 - rci;
}

void CsmControlDef::append(Assembly & asy) const
{
  if (hpts.size() < 2 or type == CsmCsUndefined)
    return;
  
  uint wix = asy.find(wingid);
  if (wix == NotFound) {
    return;
  }
  
  WingSkeletonPtr wsp = asy.asWing(wix);
  if (not wsp) {
    return;
  }
  
  CtSurface csurf(wsp);
  csurf.clearHinges();
  if (type == CsmCsLE)
    csurf.type( CtSurface::CsLef );
  else
    csurf.type( CtSurface::CsTef );
  
  // append surfaces (which may be defined implicitely)
  CtSystem & csys( asy.ctsystem() );
  if (bMirror and wsp->autoSym()) {
  
    csurf.rename( "Right" + id );
    const int nhp = hpts.size();
    for (int i=nhp-1; i>=0; --i) {
      Real rspan = 0.5*(1.0-hpts[i].rspan);
      Real rchord = hpts[i].rchord;
      Real v = wsp->vSpanPos(0.5+0.5*rchord, rspan);
      csurf.addHingepoint(v, rchord);
    }
    
    csys.append(csurf);
    csys.append(csurf.mirrorCopy());
    
    // add a deflection pattern
    if (motion != CsmCsIndep) {
      CtPattern cpat;
      cpat.rename(id);

      // symmetrical or antisymmetrical?
      Real fright = 1.0;
      Real fleft = (motion == CsmCsAntiSym) ? -fright : fright;

      // simple pattern
      if (hpts.size() == 2) {
        cpat.append( "Right"+id, fright );
        cpat.append( "Left"+id, fleft );
      } else {
        for (uint i=0; i<hpts.size()-1; ++i) {
          cpat.append( "Right"+id+"Segment"+str(i), fright );
          cpat.append( "Left"+id+"Segment"+str(i), fleft );
        }
      }
      csys.append(cpat);
    }

  } else {
    csurf.rename( id );
    const int nhp = hpts.size();
    for (int i=nhp-1; i>=0; --i) {
      Real rspan = 1.0-hpts[i].rspan;
      Real rchord = hpts[i].rchord;
      csurf.addHingepoint(rspan, rchord);
    }
    csys.append(csurf);
  }
}

void CsmControlDef::fromXmlDec08(const XmlElement & xe)
{
  type = CsmCsUndefined;
  string tg = toLower( xe.name() );

  // chop off the index at the end
  string::size_type pos = tg.find_last_not_of("0123456789");
  tg = tg.substr(0, pos+1);
  if (tg == "control_surface") {
    delta_min = floatFromNode(xe, "min_deflection", 0.0);
    delta_max = floatFromNode(xe, "max_deflection", 0.0);
    if ( delta_min == 0 and delta_max == 0 )
      return;

    XmlElement::const_iterator itr;
    for (itr = xe.begin(); itr != xe.end(); ++itr) {
      string stag = toLower( strip(itr->name()) );
      if (stag == "name") {
        id = strip(itr->text());
      } else if (stag == "configuration") {
        string cs = csmCanonicalStr(itr->text());
        if (cs == "leadingedge")
          type = CsmCsLE;
        else if (cs == "trailingedge")
          type = CsmCsTE;
        else
          type = CsmCsUndefined;
      } else if (stag == "motion") {
        string cs = csmCanonicalStr(itr->text());
        if (cs == "symmetrical")
          motion = CsmControlDef::CsmCsSym;
        else if (cs == "antisymmetrical")
          motion = CsmControlDef::CsmCsAntiSym;
        else
          motion = CsmControlDef::CsmCsIndep;
      } else if (stag.find("hinge_point") != string::npos) {
        CsmHp hp;
        pos = stag.find_last_not_of("0123456789");
        hp.idx = atol( stag.substr(pos+1, stag.size()).c_str() );
        hp.rspan = floatFromNode(*itr, "relative_span_position");
        hp.rchord = floatFromNode(*itr, "relative_chord_position");
        hpts.push_back( hp );
      }
    }
  }

  std::sort(hpts.begin(), hpts.end());
}
