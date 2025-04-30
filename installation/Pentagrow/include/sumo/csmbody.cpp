
/* ------------------------------------------------------------------------
 * file:       csmwing.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * CEASIOM fuselage/fairing/nacelle definition of the SimSAC project
 * ------------------------------------------------------------------------ */
 
#include <genua/strutils.h>
#include <genua/xmlelement.h>
#include <genua/xcept.h>
#include <genua/pattern.h>
#include "bodyframe.h"
#include "bodyskeleton.h"
#include "jetenginespec.h"
#include "componentlibrary.h"
#include "csmgenerator.h"
#include "csmbody.h"

using namespace std;

// -------------------------- CsmBody -----------

Real CsmBody::meanHorizDiameter() const
{
  return 0.5*(fore_hdiam + aft_hdiam);
}

void CsmBody::fromXml(const XmlElement & xe)
{
  tag( xe.name() );
  string xtag = toLower(tag());
  if (xtag == "fuselage") {
    type = CsmFuselage;
    fetchFuselage( xe );
    tag("Fuselage");
  } else if (xtag == "nacelle1" or xtag == "nacelle2"
           or xtag == "nacelle3" or xtag == "nacelle4") {
    type = CsmNacelle;
    fetchNacelle( xe );
  } else if (xtag == "pylon1" or xtag == "pylon2"
           or xtag == "pylon3" or xtag == "pylon4") {
    type = CsmPylon;
    fetchPylon( xe );
  } else if (xtag == "tailbooms") {
    type = CsmTailboom;
    fetchBoom( xe );
    tag("Tailboom");
  }
}
 
ComponentPtr CsmBody::create() const
{
  if (type == CsmFuselage)
    return createFuselage();
  else if (type == CsmFairing)
    return createFairing();
  else if (type == CsmNacelle)
    return createNacelle();
  else if (type == CsmPylon)
    return createPylon();
  else if (type == CsmTailboom)
    return createBoom();
  
  throw Error("CEASIOM import: Could not create body: "+tag());
}

void CsmBody::fetchFuselage(const XmlElement & xe)
{
  if (not isValid(xe))
    return;
  
  // extract dimensions 
  length = floatFromNode(xe, "Total_fuselage_length");
  fore_frac = floatFromNode(xe, "fraction_fore", 0.0);
  fore_shift = floatFromNode(xe, "shift_fore", 0.0);
  nose_eps = floatFromNode(xe, "epsilon_nose");
  tail_eps = floatFromNode(xe, "epsilon_tail");
  
  fore_hdiam = floatFromNode(xe, "Forefuse_X_sect_horizontal_diameter");
  fore_vdiam = floatFromNode(xe, "Forefuse_X_sect_vertical_diameter");
  fore_xi = floatFromNode(xe, "Forefuse_Xs_distortion_coefficient", 0.5);
  fore_a0 = floatFromNode(xe, "a0_fore");
  fore_a1 = floatFromNode(xe, "a1_fore");
  fore_b1 = floatFromNode(xe, "b1_fore");
  
  aft_hdiam = floatFromNode(xe, "Aftfuse_X_sect_horizontal_diameter");
  aft_vdiam = floatFromNode(xe, "Aftfuse_X_sect_vertical_diameter");
  aft_xi = floatFromNode(xe, "Aftfuse_Xs_distortion_coefficient", 0.5);
  aft_a0 = floatFromNode(xe, "a0_aft");
  aft_a1 = floatFromNode(xe, "a1_aft");
  aft_b1 = floatFromNode(xe, "b1_aft");
  
  nose_omega = floatFromNode(xe, "omega_nose");
  nose_phi = floatFromNode(xe, "phi_nose", 0.0);
  
  tail_omega = floatFromNode(xe, "omega_tail");
  tail_phi = floatFromNode(xe, "phi_tail", 0.0);
  
  // angles to radian 
  nose_omega = rad(nose_omega);
  nose_phi = rad(nose_phi);
  tail_omega = rad(tail_omega);
  tail_phi = rad(tail_phi);
}

BodySkeletonPtr CsmBody::createFuselage() const
{
  if (length == 0)
    throw Error("CsmBody: Trying to create undefined fuselage.");
    
  BodySkeletonPtr bsp(new BodySkeleton);
  bsp->clear();
  
  string bname = "Fuselage";
  bsp->rename(bname);
  
  // number of sections to use 
  int nnose(16), ncyl(7), ntail(16), scount(0);
  
  // pattern for nose paraboloid
  const Real npx(1.4);
  Vector nosepat = expand_pattern(nnose, npx);
  Real lbo = nosepat[nnose-2];
  nosepat += nosepat[1]/npx;
  nosepat *= (0.5 + 0.5*lbo) / nosepat.back();
  
  // pattern for tail paraboloid
  const Real tpx(1.4);
  Vector tmp = expand_pattern(ntail, tpx);
  lbo = tmp[ntail-2];
  tmp += tmp[1]/tpx;
  tmp *= (0.5 + 0.5*lbo) / tmp.back();
  Vector tailpat(ntail);
  for (int i=0; i<ntail; ++i)
    tailpat[i] = 1.0 - tmp[ntail-1-i];
  
  // generate nose sections
  Real zshift = fore_shift * aft_vdiam;
  Real beta = 0.54 + 0.1*tan(nose_omega - nose_phi);
  for (int i=0; i<nnose; ++i) {
    
    // pick the last nose section a bit in front of the transition 
    Real t = nosepat[i]; // Real(i+1) / (nnose + 1);
    Real x = t*nose_eps*fore_vdiam;
    Real scale = pow(t, beta);
    Real z = (t - 1.)*nose_eps*fore_vdiam*tan(nose_phi) + zshift;
    Real zp = scale*(0.5 - fore_xi)*fore_vdiam;
    Real a0 = scale*fore_a0;
    Real a1 = scale*fore_a1;
    Real b1 = scale*fore_b1;
    
    BodyFramePtr bfp(new BodyFrame);
    bfp->rename( bname + "Frame" + str(scount) );
    bfp->origin( vct(x, 0.0, z) );
    bfp->setFrameWidth(2.0);
    bfp->setFrameHeight(2.0);
    bfp->makeIsikveren(zp, a0, a1, b1, 32);
    bfp->interpolate();
    ++scount;
    
    bsp->addFrame(bfp);
  }
  
  // x-offset where the next part starts
  Real xoff = nose_eps*fore_vdiam;
  Real lcentral = length - nose_eps*fore_vdiam - tail_eps*aft_vdiam;
  
  // generate sections for conical section 
  if (fore_frac > 0) {
    
    for (int i=0; i<ncyl; ++i) {
      
      Real t = (i+0.5) / ncyl;
      Real x = xoff + t*fore_frac*lcentral;
      Real z = (1.-t)*zshift;
      Real zp = (1.-t)*(0.5 - fore_xi)*fore_vdiam + t*(0.5 - aft_xi)*aft_vdiam;
      Real a0 = (1.-t)*fore_a0 + t*aft_a0;
      Real a1 = (1.-t)*fore_a1 + t*aft_a1;
      Real b1 = (1.-t)*fore_b1 + t*aft_b1;
      
      BodyFramePtr bfp(new BodyFrame);
      bfp->rename( bname + "Frame" + str(scount) );
      bfp->origin( vct(x, 0.0, z) );
      bfp->setFrameWidth(2.0);
      bfp->setFrameHeight(2.0);
      bfp->makeIsikveren(zp, a0, a1, b1);
      bfp->interpolate();
      ++scount;
      
      bsp->addFrame(bfp);
    }
    xoff += fore_frac*lcentral;
    
  }
  
  
  // generate sections for cylindrical part 
  if (fore_frac < 1.0) {
  
    for (int i=0; i<ncyl; ++i) {
      
      Real t = Real(i+0.5) / ncyl;
      Real x = xoff + t*(1.0 - fore_frac)*lcentral;
      Real z = 0.0;
      Real zp = (0.5 - aft_xi)*aft_vdiam;
      Real a0 = aft_a0;
      Real a1 = aft_a1;
      Real b1 = aft_b1;
      
      BodyFramePtr bfp(new BodyFrame);
      bfp->rename( bname + "Frame" + str(scount) );
      bfp->origin( vct(x, 0.0, z) );
      bfp->setFrameWidth(2.0);
      bfp->setFrameHeight(2.0);
      bfp->makeIsikveren(zp, a0, a1, b1);
      bfp->interpolate();
      ++scount;
      
      bsp->addFrame(bfp);
    }
    xoff += (1.0 - fore_frac)*lcentral;
    
  }
  
  // generate tail sections
  beta = 0.54 + 0.1*tan(tail_omega - tail_phi);
  for (int i=0; i<ntail; ++i) {
    
    Real t = tailpat[i]; // Real(i) / ntail;
    Real x = xoff + t*tail_eps*aft_vdiam;
    Real scale = pow(1.-t, beta);
    Real z = (x-xoff)*tan(tail_phi);
    Real zp = scale*(0.5 - aft_xi)*aft_vdiam;
    Real a0 = scale*aft_a0;
    Real a1 = scale*aft_a1;
    Real b1 = scale*aft_b1;
    
    BodyFramePtr bfp(new BodyFrame);
    bfp->rename( bname + "Frame" + str(scount) );
    bfp->origin( vct(x, 0.0, z) );
    bfp->setFrameWidth(2.0);
    bfp->setFrameHeight(2.0);
    bfp->makeIsikveren(zp, a0, a1, b1);
    bfp->interpolate();
    ++scount;
    
    bsp->addFrame(bfp);
  }
  
  bsp->interpolate();
  bsp->useMgDefaults(true);
  return bsp;
}

void CsmBody::fetchFairing(const XmlElement & xe)
{
  if (not isValid(xe))
    return;
  
  // extract dimensions 
  fairing_lfore = floatFromNode(xe, "l_fore");
  fairing_laft = floatFromNode(xe, "l_aft");
  fairing_lcentral = floatFromNode(xe, "l_central");
  
  fairing_width = floatFromNode(xe, "width");
  fairing_height = floatFromNode(xe, "thickness");
  
  fairing_xpos = floatFromNode(xe, "longitudinal_location");
  fairing_zpos = floatFromNode(xe, "vertical_location");
}

BodySkeletonPtr CsmBody::createFairing() const
{
  // locate component and generate template
  BodySkeletonPtr bsp;
  for (uint i=0; i<SumoComponentLib.ncomponents(); ++i) {
    const XmlElement & xe( SumoComponentLib.componentXml(i) );
    if (xe.attribute("name") == "CenterFairing") {
      bsp = BodySkeletonPtr(new BodySkeleton);
      bsp->fromXml(xe);
      break;
    }
  }
  
  if (not bsp)
    throw Error("Could not find component: 'Wing-body fairing' in lib.");
  
  // scale and relocate
  Real width, height, length, fairing_length;
  fairing_length = fairing_lfore + fairing_lcentral + fairing_laft;
  bsp->dimensions(height, width, length);
  bsp->scale( fairing_height/height, fairing_width/width, 
              fairing_length/length );
  bsp->origin( vct(fairing_xpos, 0.0, fairing_zpos) );
  bsp->interpolate();
  bsp->useMgDefaults(true);
  
  return bsp;
}

void CsmBody::fetchBoom(const XmlElement & xe)
{
  if (not isValid(xe))
    return;

  if (intFromNode(xe, "present", 0) == 0)
    return;

  boom_length = floatFromNode(xe, "total_length");
  boom_diameter = floatFromNode(xe, "diameter");
  boom_pos[0] = floatFromNode(xe, "x");
  boom_pos[1] = floatFromNode(xe, "y");
  boom_pos[2] = floatFromNode(xe, "z");
  boom_symmetry = intFromNode(xe, "symmetry", boom_pos[1] != 0.0);
}

BodySkeletonPtr CsmBody::createBoom() const
{
  // locate component and generate template
  BodySkeletonPtr bsp;
  for (uint i=0; i<SumoComponentLib.ncomponents(); ++i) {
    const XmlElement & xe( SumoComponentLib.componentXml(i) );
    if (xe.attribute("name") == "Tailboom") {
      bsp = BodySkeletonPtr(new BodySkeleton);
      bsp->fromXml(xe);
      break;
    }
  }

  if (not bsp)
    throw Error("Could not find component: 'Tail boom' in lib.");

  Real width, height, length;
  bsp->dimensions(height, width, length);
  bsp->scale( boom_diameter/height, boom_diameter/width,
              boom_length/length );
  bsp->origin( boom_pos );
  bsp->interpolate();
  bsp->useMgDefaults(true);
  bsp->rename("Tailboom");

  return bsp;
}

void CsmBody::fetchNacelle(const XmlElement & xe)
{
  if (not isValid(xe))
    return;
  
  nacelle_diam = floatFromNode(xe, "d_max");
  nacelle_fine = floatFromNode(xe, "fineness_ratio");
  
  engine_pos[0] = floatFromNode(xe, "longitudinal_location");
  engine_pos[1] = floatFromNode(xe, "lateral_location");
  engine_pos[2] = floatFromNode(xe, "vertical_location");
}

BodySkeletonPtr CsmBody::createNacelle() const
{
  // locate nacelle component and generate template
  BodySkeletonPtr bsp;
  for (uint i=0; i<SumoComponentLib.ncomponents(); ++i) {
    const XmlElement & xe = SumoComponentLib.componentXml(i);
    if (xe.attribute("name") == "CeasiomNacelle") {
      bsp = BodySkeletonPtr(new BodySkeleton);
      bsp->fromXml(xe);
      break;
    }
  }
  
  if (not bsp)
    throw Error("Could not find component: 'Engine nacelle' in lib.");
  
  // scale and relocate
  Real width, height, length, nacelle_length;
  nacelle_length = nacelle_fine * nacelle_diam;
  bsp->dimensions(height, width, length);
  bsp->scale( nacelle_diam/height, nacelle_diam/width, 
              nacelle_length/length );
  bsp->origin( engine_pos );
  bsp->rename(tag());
  bsp->interpolate();
  bsp->useMgDefaults(true);
  
  return bsp;
}

void CsmBody::fetchPylon(const XmlElement & xe)
{
  if (not isValid(xe))
    return;
  
  pylon_length = floatFromNode(xe, "root_chord");
  Real span1 = floatFromNode(xe, "inboard_span");
  Real span2 = floatFromNode(xe, "midboard_span");
  Real span3 = floatFromNode(xe, "outboard_span");
  pylon_height = span1 + span2 + span3;
  
  Real tkink1 = floatFromNode(xe, "taper_kink1");
  Real tkink2 = floatFromNode(xe, "taper_kink2");
  Real ttip = floatFromNode(xe, "taper_tip");
  Real tmax = max(ttip, max(tkink1, tkink2));
  pylon_length *= max(1.0, tmax);
  
  engine_pos[0] = floatFromNode(xe, "longitudinal_location");
  engine_pos[1] = floatFromNode(xe, "lateral_location");
  engine_pos[2] = floatFromNode(xe, "vertical_location");
  engine_pos[2] += 0.5*pylon_height;
}

BodySkeletonPtr CsmBody::createPylon() const
{
  // locate nacelle component and generate template
  BodySkeletonPtr bsp;
  for (uint i=0; i<SumoComponentLib.ncomponents(); ++i) {
    const XmlElement & xe = SumoComponentLib.componentXml(i);
    if (xe.attribute("name") == "RightInboardPylon") {
      bsp = BodySkeletonPtr(new BodySkeleton);
      bsp->fromXml(xe);
      break;
    }
  }
  
  if (not bsp)
    throw Error("Could not find component: 'Engine pylon' in lib.");
  
  // scale and relocate
  Real width, height, length;
  bsp->dimensions(height, width, length);
  bsp->scale( pylon_height/height, pylon_height/height, 
              pylon_length/length );
  bsp->origin( engine_pos );
  bsp->rename(tag());
  bsp->interpolate();
  bsp->useMgDefaults(true);
  
  return bsp;
}

bool CsmBody::isValid(const XmlElement & xe)
{
  string tag = toLower(xe.name());
  if (tag == "fuselage") 
  {
    if (floatFromNode(xe, "Total_fuselage_length", 0.0)  == 0.0)
      return false;
    else
      return true;
  } 
  
  else if (tag == "nacelle1" or tag == "nacelle2"
           or tag == "nacelle3" or tag == "nacelle4") 
  {
    if (floatFromNode(xe, "d_max", 0.0)  == 0.0)
      return false;
    else
      return true;
  } 
    
  else if (tag == "tailbooms")
  {
    if (intFromNode(xe, "present", 0)  == 0)
      return false;
    else
      return true;
  }

  return false;
}

void CsmBody::postAttach(Assembly & asy)
{
  // find body 
  uint bix = asy.find(tag());
  if (bix == NotFound) {
    return;
  }
  BodySkeletonPtr bsp = asy.asBody(bix);
  if (not bsp) {
    return;
  }
  
  if (type == CsmNacelle) {
    JetEngineSpec spec;
    spec.rename( tag() + "Engine" );
    spec.turbofan() = TfSpec::createBuiltinTFModel(0);
    spec.intakeRegion(0) = JeRegion(bsp, JeRegion::JerNose);
    spec.nozzleRegion(0) = JeRegion(bsp, JeRegion::JerTail);
    asy.addJetEngine(spec);
  } else if ((type == CsmTailboom) and boom_symmetry) {
    CsmGenerator::information("Creating tail boom mirror copy.");
    bsp->rename("RightTailboom");
    BodySkeletonPtr lboom = bsp->xzMirrorCopy();
    lboom->interpolate();
    lboom->rename("LeftTailboom");
    asy.addBody( lboom );
  }
}
