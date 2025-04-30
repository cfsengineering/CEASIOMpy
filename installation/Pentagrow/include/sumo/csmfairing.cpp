
/* ------------------------------------------------------------------------
 * file:       csmfairing.cpp
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * CEASIOM fairing definition of the SimSAC project
 * ------------------------------------------------------------------------ */

#include "componentlibrary.h"
#include "csmgenerator.h"
#include "csmfairing.h"

using namespace std;

void CsmFairing::fromXml(const XmlElement & xe)
{
  // mark as unattached
  width = 0.0;
  
  tag( xe.name() );
  string xtag = toLower( tag() );
  if (xtag == "fairing1" or xtag == "fairing2") {
    fwd_fraction = 0.01*floatFromNode(xe, "Forward_chord_fraction");
    aft_fraction = 0.01*floatFromNode(xe, "Aft_chord_fraction");
    width2height = floatFromNode(xe, "flushness", 0.0);
  }
}

bool CsmFairing::isValid(const XmlElement & xe)
{
  string xtag = toLower( xe.name() );
  if (xtag == "fairing1" or xtag == "fairing2") 
    return true;
  else
    return false;
}

void CsmFairing::attach(const CsmComponentArray & csm)
{
  if (width2height == 0.0)
    return;
  
  // determine which wing to look at 
  string xtag = tag();
  string awing = string("wing") + xtag[ xtag.size()-1 ];
  
  CsmComponentPtr cwng, cfsl;
  const int nc = csm.size();
  for (int i=0; i<nc; ++i) {
    if ( toLower(csm[i]->tag()) == awing )
      cwng = csm[i];
    else if ( toLower(csm[i]->tag()) == "fuselage" )
      cfsl = csm[i];
  }
  if (not cwng)
    throw Error("Cannot figure out where to attach fairing: "+tag());
  
  CsmWing *pwng(0);
  pwng = dynamic_cast<CsmWing*>( cwng.get() );
  if (pwng == 0)
    throw Error("Cannot figure out where to attach fairing: "+tag());
  
  CsmBody *pfsl(0);
  pfsl = dynamic_cast<CsmBody*>( cfsl.get() );
  
  Real chord;
  if (tag() == "Fairing1" and pfsl != 0) {
    
    Real fwid = pfsl->meanHorizDiameter(); 
    chord = pwng->fslChord(fwid);
    fwd_length = chord*fwd_fraction;
    ctr_length = chord;
    aft_length = chord*aft_fraction;
    
    Real shift = pwng->fslChordShift(fwid);
    org = pwng->origin() - vct(fwd_length-shift, 0.0, 0.0);
    
    // adjust width to fuselage width
    width = fwid;
    // height = width/width2height;
    height = 0.35*chord;
    
  } else {
    
    chord = pwng->rootChord();
    fwd_length = chord*fwd_fraction;
    ctr_length = chord;
    aft_length = chord*aft_fraction;
    org = pwng->origin() - vct(fwd_length, 0.0, 0.0);
    
    height = 0.25*ctr_length;
    width = height*width2height;  
  }
}

ComponentPtr CsmFairing::create() const
{
  BodySkeletonPtr bsp;
  if (width == 0)
    return bsp;
  
  for (uint i=0; i<SumoComponentLib.ncomponents(); ++i) {
    const XmlElement & xe( SumoComponentLib.componentXml(i) );
    if (xe.attribute("name") == "CeasiomFairing") {
      bsp = BodySkeletonPtr(new BodySkeleton);
      bsp->fromXml(xe);
      break;
    }
  }
  
  if (not bsp)
    throw Error("Could not find component: 'Wing-body fairing' in library.");
  else if (bsp->nframes() != 8)
    throw Error("Library fairing has unexpected shape.");
  
  // intended total length
  Real length = fwd_length + ctr_length + aft_length;
  
  // scale frames to match geometry definition
  Real hmax, wmax, len;
  bsp->dimensions(hmax, wmax, len);
  bsp->scale( height/hmax, width/wmax, length/len);
  bsp->origin(org);
  bsp->rename(tag());
  
  // place sections to match intended shape
  Real xp = 0.5*fwd_length;
  bsp->frame(1)->origin( vct(xp, 0.0, 0.0) );
  xp = fwd_length;
  bsp->frame(2)->origin( vct(xp, 0.0, 0.0) );

  xp = fwd_length + ctr_length/3;
  bsp->frame(3)->origin( vct(xp, 0.0, 0.0) );
  xp = fwd_length + 2*ctr_length/3;
  bsp->frame(4)->origin( vct(xp, 0.0, 0.0) );
  xp = fwd_length + ctr_length;
  bsp->frame(5)->origin( vct(xp, 0.0, 0.0) );

  xp = fwd_length + ctr_length + 0.5*aft_length;
  bsp->frame(6)->origin( vct(xp, 0.0, 0.0) );
  
  for (int k=0; k<8; ++k)
    bsp->frame(k)->interpolate();
  bsp->interpolate();

  return bsp;
}