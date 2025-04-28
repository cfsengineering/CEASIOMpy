
/* ------------------------------------------------------------------------
 * file:       csmwing.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * CEASIOM fuselage/fairing/nacelle definition of the SimSAC project
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CSMBODY_H
#define SUMO_CSMBODY_H

#include "bodyskeleton.h"
#include "csmcomponent.h"

class XmlElement;

/** CEASIOM body

  This object interprets the XML definition used in the CEASIOM project 
  and generates a sumo body from that.

*/
class CsmBody : public CsmComponent
{
  public:

    typedef enum {CsmFuselage, CsmFairing, CsmNacelle,
                  CsmPylon, CsmTailboom, CsmUndefined} BodyType;

    /// empty body definition 
    CsmBody() : type(CsmUndefined) {}
    
    /// read from xml description 
    void fromXml(const XmlElement & xe);
    
    /// generate a body pointer 
    ComponentPtr create() const;
    
    /// mean horizontal diameter
    Real meanHorizDiameter() const;
    
    /// attach engine spec to assembly
    void postAttach(Assembly & asy);
    
    /// undefined body 
    static bool isValid(const XmlElement & xe);
    
  private:
    
    /// fetch fuselage definition from XML
    void fetchFuselage(const XmlElement & xe);
    
    /// generate a fuselage body 
    BodySkeletonPtr createFuselage() const;
    
    /// fetch fairing definition from XML
    void fetchFairing(const XmlElement & xe);
    
    /// generate a fairing body 
    BodySkeletonPtr createFairing() const;
    
    /// fetch boom definition from XML
    void fetchBoom(const XmlElement & xe);

    /// generate a fairing body
    BodySkeletonPtr createBoom() const;

    /// fetch engine definition from XML
    void fetchNacelle(const XmlElement & xe);
    
    /// generate a nacelle body 
    BodySkeletonPtr createNacelle() const;
    
    /// fetch pylon definition from XML
    void fetchPylon(const XmlElement & xe);
    
    /// generate a fairing body 
    BodySkeletonPtr createPylon() const;
    
  private:
    
    /// body type
    BodyType type;
    
    /// basic length dimensions 
    Real length, fore_frac, nose_eps, tail_eps; 
    
    /// basic width dimensions
    Real fore_hdiam, fore_vdiam, fore_shift, aft_hdiam, aft_vdiam; 
    
    /// section shape parameters 
    Real fore_xi, fore_a0, fore_a1, fore_b1, aft_xi, aft_a0, aft_a1, aft_b1;
    
    /// nose and tail cone parameter 
    Real nose_omega, nose_phi, tail_omega, tail_phi;
    
    /// fairing length dimensions
    Real fairing_lfore, fairing_lcentral, fairing_laft;
    
    /// fairing width and height
    Real fairing_width, fairing_height, fairing_xpos, fairing_zpos;

    /// engine positions
    Vct3 engine_pos;
    
    /// engine nacelle parameters
    Real nacelle_diam, nacelle_fine;

    /// pylon parameters 
    Real pylon_length, pylon_height;

    /// tailboom position
    Vct3 boom_pos;

    /// tailboom parameters
    Real boom_length, boom_diameter;

    /// boom symmetry flag
    bool boom_symmetry;
};

typedef boost::shared_ptr<CsmBody> CsmBodyPtr;
typedef std::vector<CsmBodyPtr> CsmBodyArray; 

#endif
