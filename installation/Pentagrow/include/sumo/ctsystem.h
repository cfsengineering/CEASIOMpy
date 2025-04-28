
/* ------------------------------------------------------------------------
 * file:       ctsystem.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Stores control system data
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CTSYSTEM_H
#define SUMO_CTSYSTEM_H

#include <genua/xmlelement.h>
#include "ctsurface.h"
#include "ctpattern.h"

class CtSystem
{
  public:
    
    /// empty construction
    CtSystem() : bVisible(false) {}
    
    /// number of defined surfaces
    uint nsurf() const {return surfaces.size();}
    
    /// number of defined patterns
    uint npattern() const {return patterns.size();}
    
    /// access definition of surface i
    const CtSurface & surface(uint i) const {
      assert(i < surfaces.size());
      return surfaces[i];
    }
    
    /// access definition of surface i
    CtSurface & surface(uint i) {
      assert(i < surfaces.size());
      return surfaces[i];
    }
    
    /// access definition of pattern i
    const CtPattern & pattern(uint i) const {
      assert(i < patterns.size());
      return patterns[i];
    }
    
    /// access definition of pattern i
    CtPattern & pattern(uint i) {
      assert(i < patterns.size());
      return patterns[i];
    }
    
    /// append surface
    uint append(const CtSurface & s) {
      surfaces.push_back(s);
      return surfaces.size()-1;
    }
    
    /// append pattern
    uint append(const CtPattern & s) {
      patterns.push_back(s);
      return patterns.size()-1;
    }
    
    /// remove all data
    void clear();
    
    /// fetch all segment names
    void segments(StringArray & sgs) const;
    
    /// delete surface
    void removeSurface(uint idx);
    
    /// delete pattern
    void removePattern(uint idx);
    
    /// rename control surface
    void renameSurface(uint idx, const std::string & s);
    
    /// update geometry for surfaces 
    void updateGeometry();
    
    /// draw using OpenGL 
    void draw() const;
    
    /// change visibility in 3D view
    void toggleVisible(bool flag) {bVisible = flag;}
    
    /// read from xml
    void fromXml(const XmlElement & xe, const Assembly & asy);
     
    /// write to xml
    XmlElement toXml() const;
  
    /// write to xml (mesh format)
    XmlElement meshXml() const;
    
  private:
    
    /// remove all patterns which do not reference a surface
    void dropEmptyPatterns();
    
  private:
    
    /// geometric definition of surfaces
    std::vector<CtSurface> surfaces;
    
    /// compinations of surface deflections
    std::vector<CtPattern> patterns;
    
    /// visibility flag
    bool bVisible;
};

#endif

