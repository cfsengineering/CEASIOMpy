
/* ------------------------------------------------------------------------
 * file:       csmwing.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * CEASIOM wing definition of the SimSAC project
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CSMWING_H
#define SUMO_CSMWING_H

#include <boost/shared_ptr.hpp>
#include <genua/defines.h>
#include <surf/airfoil.h>
#include "wingskeleton.h"
#include "csmcontroldef.h"
#include "csmcomponent.h"

class XmlElement;
class Assembly;

/** CEASIOM wing.

  Collects dimensional definitions for the wing description used in the 
  SimSAC project.

*/
class CsmWing : public CsmComponent
{
  public:
    
    /// undefined wing    
    CsmWing() : ar(0) {}
    
    /// decode xml description 
    void fromXml(const XmlElement & xe);
    
    /// generate wing skeleton from definition 
    ComponentPtr create() const;
    
    /// attach control surfaces to assembly
    void postAttach(Assembly & asy);
    
    /// access computed root chord
    Real rootChord() const {return rootchord;}
    
    /// compute approximate chord at fuselage side
    Real fslChord(Real fwidth) const;
    
    /// compute approximate distance of fsl/wing intersection
    Real fslChordShift(Real fwidth) const;
    
    /// spanwise location of kink 1
    Real kink1Pos() const {return kink[0];}

    /// spanwise location of kink 2
    Real kink2Pos() const {return kink[1];}

    /// location of the wing apex
    const Vct3 & origin() const {return apex;}
    
    /// check xml element if it defines a wing 
    static bool isValid(const XmlElement & xe);
    
  private:
    
    /// compute derived properties 
    void init();
    
    /// fetch airfoil names according to xml spec
    void fetchAirfoils(const XmlElement & xe);
    
    /// retrieve panel properties: 2 or 3 panels as of now
    void fetchPanels(const XmlElement & xe);
    
    /// retrieve absolute position
    void fetchPosition(const XmlElement & xe);
    
    /// retrieve control surface definitions
    void fetchControls(const XmlElement & xe);
    
    /// retrieve and scale airfoil coordinates, append
    AirfoilPtr normalizeCoordinates(const XmlElement & xe, Real phi) const;
    
    /// reparametrize airfoil coordinates
    void reparametrizeAirfoils();
    
  private:
    
    typedef enum {CsmMainWing, CsmCanard, CsmHTP, CsmVTP, CsmPylon, CsmUndefined} WingType;

    /// airfoil coordinates, if found
    std::vector<AirfoilPtr> airfoils;
    
    /// wing panel properties from xml file 
    Real incidence[4], dihedral[3], taper[3], lesweep[3], kink[2];
    
    /// derived properties 
    Real etapos[4], sdihedral[4], relchord[4], rootchord, xrot;
    
    /// section leading edge positions, wing apex position 
    Vct3 apex, rpos;
    
    /// section positions 
    PointList<3> secpos;
    
    /// global wing properties
    Real ar, area, span;
    
    /// number of panels (max 5)
    uint npanel;
    
    /// type according to xml tag 
    WingType type;

    /// control surfaces
    std::vector<CsmControlDef> ctrl;
};    

typedef boost::shared_ptr<CsmWing> CsmWingPtr;
typedef std::vector<CsmWingPtr> CsmWingArray; 

#endif
