
/* ------------------------------------------------------------------------
 * file:       jetenginespec.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Data needed to write jet engine specification to mesh file
 * ------------------------------------------------------------------------ */

#include <sstream>
#include <genua/strutils.h>
#include <genua/trimesh.h>
#include "assembly.h"
#include "jetenginespec.h"

using namespace std;

// default process efficiency values 

const Real _tf_eta_inlet(0.96);
const Real _tf_eta_nozzle(0.97);
const Real _tf_eta_spool(0.99);
const Real _tf_eta_comb(0.98);
const Real _tf_eta_inf(0.93);
const Real _tf_dp_comb(0.02);

// ----------------------- JeRegion --------------------------------------

void JeRegion::insertTag(Indices & etags) const
{
  if (not bsp)
    return;
  
  if (type == JerNose)
    insert_once(etags, uint(bsp->capTag(2)));
  else if (type == JerTail)
    insert_once(etags, uint(bsp->capTag(3)));
}

uint JeRegion::merge(const TriMesh & m, Indices & el) const
{
  if (not bsp)
    return 0;
  
  uint t(NotFound);
  if (type == JerNose)
    t = bsp->capTag(2);
  else if (type == JerTail)
    t = bsp->capTag(3);
  else
    return 0;
  
  if (t == NotFound)
    return 0;
  
  uint no = el.size();
  const int nf = m.nfaces();
  for (int i=0; i<nf; ++i) {
    if (m.face(i).tag() == int(t))
      el.push_back(i);
  }
  return el.size() -  no;
}

XmlElement JeRegion::toXml() const
{
  XmlElement xe("JeRegion");
  if (bsp)
    xe["surface"] = bsp->name();
  
  string ts;
  switch (type) {
    case JerNose:
      ts = "nose"; 
      break;
    case JerTail:
      ts = "tail";
      break;
  }
  xe["type"] = ts;
  
  return xe;
}
    
void JeRegion::fromXml(const Assembly & asy, const XmlElement & xe)
{
  if (xe.name() != "JeRegion")
    throw Error("Incompatible XML representation for JeRegion.");
  
  string s = xe.attribute("surface");
  uint bi = asy.find(s);
  if (bi == NotFound)
    throw Error("Body "+s+" not defined in this assembly.");
  bsp = asy.asBody(bi);
  assert(bsp);
  
  s = xe.attribute("type");
  if (s == "nose")
    type = JerNose;
  else if (s == "tail")
    type = JerTail;
  else
    throw Error("Unknown JerRegion type: "+s);
}

// ----------------------- TfSpec ---------------------------------------------

TfSpec::TfSpec() : tit(1400.), bpr(3.5), fpr(1.7), opr(0.)
{
  eta_inlet = _tf_eta_inlet;
  eta_nozzle = _tf_eta_nozzle;
  eta_spool = _tf_eta_spool;
  eta_comb = _tf_eta_comb;
  eta_inf = _tf_eta_inf;
  dp_comb = _tf_dp_comb;
}

uint TfSpec::nBuiltinTFModels()
{
  return 4;
}
    
TfSpec TfSpec::createBuiltinTFModel(uint i)
{
  TfSpec s;
  switch (i) {
    
    case 0:
      s.rename("High-BPR Airliner TF");
      s.bypassRatio( 6.5 );
      s.turbineTemperature( 1750. );
      s.totalPressureRatio( 35. );
      s.fanPressureRatio( 1.9 );
      s.etaPolytropic( 0.93 );
      s.etaInlet( 0.99 );
      s.etaNozzle( 0.97 );
      break;
     
    case 1:
      s.rename("Executive jet TF");
      s.bypassRatio( 3.5 );
      s.turbineTemperature( 1400. );
      s.totalPressureRatio( 14. );
      s.fanPressureRatio( 1.75 );
      s.etaPolytropic( 0.87 );
      s.etaInlet( 0.97 );
      s.etaNozzle( 0.95 );
      s.combPressureLoss( 0.04 );
      break;
      
    case 2:
      s.rename("Low-BPR military TF");
      s.bypassRatio( 0.4 );
      s.turbineTemperature( 1650. );
      s.totalPressureRatio( 27. );
      s.fanPressureRatio( 4.0 );
      s.etaPolytropic( 0.93 );
      s.etaInlet( 0.92 );
      s.etaNozzle( 0.93 );
      break;
      
    case 3:
      s.rename("Very high BPR geared TF");
      s.bypassRatio( 15. );
      s.turbineTemperature( 1800. );
      s.totalPressureRatio( 50. );
      s.fanPressureRatio( 1.48 );
      s.etaPolytropic( 0.95 );
      s.etaInlet( 0.99 );
      s.etaNozzle( 0.97 );
      s.etaSpool( 0.97 );
      break;
      
    default:
      s.rename("Default TF");
      s.bypassRatio( 3.5 );
      s.turbineTemperature( 1400. );
      s.totalPressureRatio( 14. );
      s.fanPressureRatio( 1.7 );
      break;
      
  }
  return s;
}

XmlElement TfSpec::toXml() const
{
  XmlElement xe("Turbofan");
  
  // design parameters 
  xe["bypass_ratio"] = str(bpr);
  xe["fan_pr"] = str(fpr);
  xe["total_pr"] = str(opr);
  xe["turbine_temp"] = str(tit);
  
  if (not id.empty())
    xe["name"] = id;
    
  // efficiency values 
  if (eta_inlet != _tf_eta_inlet)
    xe["eta_inlet"] = str(eta_inlet);
  if (eta_nozzle != _tf_eta_nozzle)
    xe["eta_nozzle"] = str(eta_nozzle);
  if (eta_comb != _tf_eta_comb)
    xe["eta_comb"] = str(eta_comb);
  if (eta_inf != _tf_eta_inf)
    xe["eta_inf"] = str(eta_inf);
  if (dp_comb != _tf_dp_comb)
    xe["dp_comb"] = str(dp_comb);
  
  return xe;  
}
    
void TfSpec::fromXml(const XmlElement & xe)
{
  if (xe.name() != "Turbofan")
    throw Error("Incompatible XML representation for 'TfSpec'.");
    
  if (xe.hasAttribute("name"))
    id = xe.attribute("name");
  else
    id.clear();
  
  // design parameters 
  bpr = Float(xe.attribute("bypass_ratio"));
  fpr = Float(xe.attribute("fan_pr"));
  opr = Float(xe.attribute("total_pr"));
  tit = Float(xe.attribute("turbine_temp"));
  
  // process losses etc.
  eta_inlet = xe.attr2float("eta_inlet", _tf_eta_inlet);
  eta_nozzle = xe.attr2float("eta_nozzle", _tf_eta_nozzle);
  eta_spool = xe.attr2float("eta_spool", _tf_eta_spool);
  eta_inf = xe.attr2float("eta_inf", _tf_eta_inf);
  eta_comb = xe.attr2float("eta_comb", _tf_eta_comb);
  dp_comb = xe.attr2float("dp_comb", _tf_dp_comb);
}

// ----------------------- JetEngineSpec --------------------------------------

void JetEngineSpec::setTranspiration(Real vin, Real vout)
{
  mflow = 0.0;
  tpin = vin;
  tpout = vout;
}
    
void JetEngineSpec::adaptToMesh(const TriMesh & m)
{
  elin.clear();
  elout.clear();
  for (uint i=0; i<rgIntake.size(); ++i)
    rgIntake[i].merge(m, elin);
  for (uint i=0; i<rgNozzle.size(); ++i)
    rgNozzle[i].merge(m, elout);
}

void JetEngineSpec::collectEngineTags(Indices & etags) const
{
  for (uint i=0; i<rgIntake.size(); ++i)
    rgIntake[i].insertTag(etags);
  for (uint i=0; i<rgNozzle.size(); ++i)
    rgNozzle[i].insertTag(etags);
}

XmlElement JetEngineSpec::toMeshXml() const
{
  XmlElement xe("JetEngine");
  xe["name"] = id;
  
  if (tpout != 0.0) {
    xe["vt_in"] = str(tpin);
    xe["vt_out"] = str(tpout);
  } else {
    xe["massflow"] = str(mflow);
    xe.append(tfpar.toXml());
  }
  
  {
    stringstream ss;
    int n(elin.size());
    int top(8*(n/8));
    for (int i=0; i<top; i+=8) {
      ss << "  ";
      for (int j=0; j<8; ++j)
        ss << elin[i+j] << " ";
      ss << endl;
    }
    ss << "  ";
    for (int i=top; i<n; ++i)
      ss << elin[i] << " ";
    ss << endl;
    XmlElement xi("IntakeElements");
    xi.text(ss.str());
    xe.append(xi);
  }
  
  {
    stringstream ss;
    int n(elout.size());
    int top(8*(n/8));
    for (int i=0; i<top; i+=8) {
      ss << "  ";
      for (int j=0; j<8; ++j)
        ss << elout[i+j] << " ";
      ss << endl;
    }
    ss << "  ";
    for (int i=top; i<n; ++i)
      ss << elout[i] << " ";
    ss << endl;
    XmlElement xi("NozzleElements");
    xi.text(ss.str());
    xe.append(xi);
  }
  
  return xe;
}

XmlElement JetEngineSpec::toModelXml() const
{
  XmlElement xe("JetEngineSpec");
  xe["name"] = id;
  
  if (tpout != 0) {
    xe["vt_in"] = str(tpin);
    xe["vt_out"] = str(tpout);
  } else {
    xe["massflow"] = str(mflow);
    xe.append(tfpar.toXml());
  }
  
  XmlElement xin("IntakeRegions");
  for (uint i=0; i<rgIntake.size(); ++i)
    xin.append(rgIntake[i].toXml());
  xe.append(xin);
  
  XmlElement xout("NozzleRegions");
  for (uint i=0; i<rgNozzle.size(); ++i)
    xout.append(rgNozzle[i].toXml());
  xe.append(xout);
  
  return xe;
}

void JetEngineSpec::fromXml(const Assembly & asy, const XmlElement & xe)
{
  if (xe.name() != "JetEngineSpec")
    throw Error("Incompatible XML representation for JetEngineSpec");
    
  id = xe.attribute("name");
  tpin = xe.attr2float("vt_in", 0.0);
  tpout = xe.attr2float("vt_out", 0.0);
  mflow = xe.attr2float("massflow", 0.0);
  
  XmlElement::const_iterator itr, ite;
  itr = xe.findChild("Turbofan");
  if (itr != xe.end()) {
    tfpar.fromXml(*itr);
  }
  
  itr = xe.findChild("IntakeRegions");
  if (itr == xe.end())
    throw Error("No intake regions defined for jet engine spec.");
  
  rgIntake.clear();
  for (ite = itr->begin(); ite != itr->end(); ++ite) {
    JeRegion jer;
    jer.fromXml(asy, *ite);
    rgIntake.push_back(jer);
  }
  
  itr = xe.findChild("NozzleRegions");
  if (itr == xe.end())
    throw Error("No nozzle regions defined for jet engine spec.");
  
  rgNozzle.clear();
  for (ite = itr->begin(); ite != itr->end(); ++ite) {
    JeRegion jer;
    jer.fromXml(asy, *ite);
    rgNozzle.push_back(jer);
  }
  
}

bool JetEngineSpec::onBody(const std::string & b) const
{
  for (uint i=0; i<rgIntake.size(); ++i) {
    if (rgIntake[i].srfName() == b)
      return true;
  }
  
  for (uint i=0; i<rgNozzle.size(); ++i) {
    if (rgNozzle[i].srfName() == b)
      return true;
  }
  
  return false;
}

