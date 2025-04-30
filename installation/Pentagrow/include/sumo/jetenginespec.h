
/* ------------------------------------------------------------------------
 * file:       jetenginespec.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Data needed to write jet engine specification to mesh file
 * ------------------------------------------------------------------------ */

#ifndef SUMO_JETENGINESPEC_H
#define SUMO_JETENGINESPEC_H

#include <genua/xmlelement.h>
#include "bodyskeleton.h"

class Assembly;
class TriMesh;

class JeRegion
{
  public:
    
    /// type of region body nose/tail/constraint
    typedef enum {JerNose, JerTail} JerType; 
    
    /// undefined region
    JeRegion() {} 
    
    /// construct region 
    JeRegion(const BodySkeletonPtr & bp, JerType t) : bsp(bp), type(t) {}
  
    /// body name 
    const std::string & srfName() const {return bsp->name();}
    
    /// change associated body 
    void body(const BodySkeletonPtr & b) {bsp = b;}
    
    /// boundary region
    JerType region() const {return type;}
    
    /// compute triangular elements in this region, merge with el
    uint merge(const TriMesh & m, Indices & el) const;
    
    /// insert tag used by this region
    void insertTag(Indices & etags) const;
    
    /// generate description for smx file
    XmlElement toXml() const;
    
    /// load from xml file 
    void fromXml(const Assembly & asy, const XmlElement & xe);
    
  private:
    
    /// body surface on which this region is 
    BodySkeletonPtr bsp;
    
    /// type of region 
    JerType type;
};

typedef std::vector<JeRegion> JeRegionArray;

class TfSpec
{
  public:
    
    /// create undefined turbofan
    TfSpec();
    
    /// number of built-in engine models 
    static uint nBuiltinTFModels();
    
    /// generate built-in engine model number i
    static TfSpec createBuiltinTFModel(uint i);
    
    /// access name 
    const std::string & name() const {return id;}
    
    /// change name 
    void rename(const std::string & s) { id = s; }
    
    /// access bypass ratio  
    void bypassRatio(Real m) {bpr= m;}
        
    /// access bypass ratio  
    Real bypassRatio() const  {return bpr;}
    
    /// access total pressure ratio  
    void totalPressureRatio(Real m) {opr = m;}
        
    /// access total pressure ratio  
    Real totalPressureRatio() const  {return opr;}
    
    /// access fan pressure ratio  
    void fanPressureRatio(Real m) {fpr = m;}
        
    /// access fan pressure ratio  
    Real fanPressureRatio() const  {return fpr;}
    
    /// access turbine inlet temperature
    void turbineTemperature(Real m) {tit = m;}
        
    /// access turbine inlet temperature
    Real turbineTemperature() const  {return tit;}
    
    /// access etaPolytropic  
    void etaPolytropic(Real m) {eta_inf = m;}
        
    /// access etaPolytropic  
    Real etaPolytropic() const  {return eta_inf;}
    
    /// access etaInlet  
    void etaInlet(Real m) {eta_inlet = m;}
        
    /// access etaInlet  
    Real etaInlet() const  {return eta_inlet;}
    
    /// access etaNozzle  
    void etaNozzle(Real m) {eta_nozzle = m;}
        
    /// access etaNozzle  
    Real etaNozzle() const  {return eta_nozzle;}
    
    /// access etaSpool  
    void etaSpool(Real m) {eta_spool = m;}
        
    /// access etaSpool  
    Real etaSpool() const  {return eta_spool;}
    
    /// access etaCombustion  
    void etaCombustion(Real m) {eta_comb = m;}
        
    /// access etaCombustion  
    Real etaCombustion() const  {return eta_comb;}
    
    /// access combustion chamber pressure loss 
    void combPressureLoss(Real m) {dp_comb = m;}
        
    /// access combustion chamber pressure loss 
    Real combPressureLoss() const  {return dp_comb;}
    
    /// generate xml representation 
    XmlElement toXml() const;
    
    /// initialize from xml representation 
    void fromXml(const XmlElement & xe);
    
  private:
    
    /// identifier for this model 
    std::string id;
    
    /// turbofan parameters
    Real tit, bpr, fpr, opr;
    
    /// process efficiencies 
    Real eta_inf, eta_inlet, eta_nozzle, eta_spool, eta_comb, dp_comb;
};

typedef std::vector<TfSpec> TfSpecLib;

/** Jet engine data which is written to mesh file.
	
*/
class JetEngineSpec
{
  public:
    
    /// undefined spec
    JetEngineSpec() : tpin(0.0), tpout(0.0), mflow(0.0), 
                      epsfan(1.0), xtratio(1.0), xpratio(1.0),
                      rgIntake(1), rgNozzle(1)  {}
    
    /// access name
    const std::string & name() const {return id;}
    
    /// change name
    void rename(const std::string & s) {id = s;}
    
    /// specify transpiration velocities  
    void setTranspiration(Real vin, Real vout);
    
    /// intake transpiration velocity 
    Real intakeVelocity() const {return tpin;}
    
    /// nozzle transpiration velocity 
    Real nozzleVelocity() const {return tpout;}
    
    /// access massflow  
    void massflow(Real m) {tpin = tpout = 0.0; mflow = m;}
        
    /// access massflow  
    Real massflow() const  {return mflow;}
    
    /// BC values for Edge
    void captureAreaRatio(Real eps) {epsfan = eps;}
    
    /// BC values for Edge
    Real captureAreaRatio() {return epsfan;}
    
    /// BC values for Edge 
    void nzPressureRatio(Real pr) {xpratio = pr;}
    
    /// BC values for Edge
    Real nzPressureRatio() {return xpratio;}
    
    /// BC values for Edge 
    void nzTempRatio(Real tr) {xtratio = tr;}
    
    /// BC values for Edge
    Real nzTempRatio() {return xtratio;}
    
    /// access turbofan spec 
    const TfSpec & turbofan() const {return tfpar;}
    
    /// access turbofan spec 
    TfSpec & turbofan() {return tfpar;}
    
    /// check if volume flow is nonzero 
    bool isDefined() const {return (tpout != 0) or (mflow != 0);}
    
    /// collect all tags assigned to engine BCs
    void collectEngineTags(Indices & etags) const;
    
    /// determine mesh elements corresponding to region definitions 
    void adaptToMesh(const TriMesh & m);
    
    /// number of intake regions defined 
    uint nintake() const {return rgIntake.size();}
    
    /// access default (first) intake region 
    JeRegion & intakeRegion(uint i=0) {
      assert(i < rgIntake.size());
      return rgIntake[i];
    } 
    
    /// access default (first) intake region 
    const JeRegion & intakeRegion(uint i=0) const {
      assert(i < rgIntake.size());
      return rgIntake[i];
    } 
    
    /// access default (first) nozzle region 
    JeRegion & nozzleRegion(uint i=0) {
      assert(i < rgNozzle.size());
      return rgNozzle[i];
    } 
    
    /// access default (first) nozzle region 
    const JeRegion & nozzleRegion(uint i=0) const {
      assert(i < rgNozzle.size());
      return rgNozzle[i];
    } 
    
    /// add intake region 
    uint addIntakeRegion(const JeRegion & jer) {
      rgIntake.push_back(jer);
      return rgIntake.size()-1;
    }
    
    ///  remove  region 
    void removeIntakeRegion(uint i) {
      if (i <= rgIntake.size()) {
        rgIntake.erase(rgIntake.begin()+i);
      }
    }
    
    /// access element indices for intake 
    const Indices & intakeElements() const {return elin;}
    
    /// access element indices for intake 
    const Indices & nozzleElements() const {return elout;}
    
    /// check if this spec contains a region on b
    bool onBody(const std::string & b) const;
    
    /// generate xml representation for mesh file
    XmlElement toMeshXml() const;
    
    /// generate xml representation for smx file 
    XmlElement toModelXml() const;
    
    /// load spec from smx file representation
    void fromXml(const Assembly & asy, const XmlElement & xe);
    
  private:
    
    /// identifier
    std::string id;

    /// intake and outflow volume flow 
    Real tpin, tpout, mflow;
    
    /// boundary condition values for Edge
    Real epsfan, xtratio, xpratio;
    
    /// turbofan specification 
    TfSpec tfpar;
    
    /// element indices for intake and outflow areas 
    Indices elin, elout;

    /// region definitions for intake and nozzle
    JeRegionArray rgIntake, rgNozzle;
};

typedef std::vector<JetEngineSpec> JetEngineSpecArray; 

#endif
