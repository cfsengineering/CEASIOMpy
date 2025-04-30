
/* ------------------------------------------------------------------------
 * file:       csmcontroldef.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Control surface definition from ceasiom xml files
 * ------------------------------------------------------------------------ */
 
#ifndef SUMO_CSMCONTROLDEF_H
#define SUMO_CSMCONTROLDEF_H

#include <string>
#include <genua/defines.h>

class XmlElement;
class Assembly;
class CsmWing;

/** Control surface definitions from ceasiom files.

  Reads control surface data from ceasiom xml files and 
  generates sumo control surfaces from them.

  The file accepted file format is changed in 1.9.11 to match
  the definitions in the document "New Tornado Functionality"
  (right) of Oct 13, 2009. Sumo versions before 1.9.11 accept
  the original (much more general) definition introduced by Andres
  in December 2008.

*/
class CsmControlDef
{
  public:
    
    /// undefined control definition
    CsmControlDef() : type(CsmCsUndefined) {}

    /// check if defined after reading xml
    bool isDefined() const {return type != CsmCsUndefined;}
    
    /// attach to surface named s
    void attachTo(const CsmWing & wing);
    
    /// create mirror copy 
    void mirror(bool flag) {bMirror = flag;}
    
    /// retrieve definitions from xml (Oct09 format)
    void fromXml(const XmlElement & xe);

    /// retrieve definitions from xml (Andres format)
    void fromXmlDec08(const XmlElement & xe);
    
    /// append control definitions to sumo assembly
    void append(Assembly & asy) const;
    
  private:    

    /// create flap, aligned with kinks (Oct 2009 format)
    void createFlap(const XmlElement & xe);

    /// create aileron (Oct 2009 format)
    void createAileron(const XmlElement & xe);

    /// create rudder (Oct 2009 format)
    void createRudder(const XmlElement & xe);

    /// create elevator (Oct 2009 format)
    void createElevator(const XmlElement & xe);

    /// create user-defined control surface
    void createCSurf(const XmlElement & xe);

  private:
    
    struct CsmHp {
      int idx;
      Real rspan;
      Real rchord;
      bool operator< (const CsmHp & a) const {return rspan < a.rspan;}
    };
    
    typedef enum {CsmCsUndefined, CsmCsLE, CsmCsTE, CsmCsAM} CsType;
    typedef enum {CsmCsIndep, CsmCsSym, CsmCsAntiSym} MotionType;

    /// control surface name
    std::string id;
    
    /// name of the surface to which it is attached
    std::string wingid;
    
    /// movement limits
    Real delta_min, delta_max;
    
    /// surface type
    CsType type;

    /// motion pattern
    MotionType motion;

    /// hinge point locations
    std::vector<CsmHp> hpts;
    
    /// create a mirror copy or not?
    bool bMirror;
};

#endif
