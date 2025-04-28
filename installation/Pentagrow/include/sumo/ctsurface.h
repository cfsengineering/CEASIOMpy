
/* ------------------------------------------------------------------------
 * file:       ctsurface.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Control surface geometry data
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CTSURFACE_H
#define SUMO_CTSURFACE_H

#include <string>
#include <genua/point.h>
#include <genua/xmlelement.h>
#include <genua/plane.h>
#include "wingskeleton.h"

class Assembly;

/** Geometry data for control surface.
  */
class CtSurface
{
  public:
    
    typedef enum {CsTef, CsLef, CsAm} CsType;
    
    /// construct unattached surface (dangerous)
    CtSurface() : firstTag(0) {}
    
    /// constructs default surface
    CtSurface(const WingSkeletonPtr & w);
    
    /// change wing surface 
    void attachTo(const WingSkeletonPtr & w) {
      wsp = w;
      updateGeometry();
    }
    
    /// name of the wing to which this flap is connected 
    const std::string & wing() const {
      assert(wsp);
      return wsp->name();
    }
    
    /// generate a mirror copy (flipped y-coordinates)
    CtSurface mirrorCopy() const;
    
    /// add a hinge point 
    uint addHingepoint(Real spos, Real cpos);
    
    /// modify a hinge point 
    uint changeHingepoint(uint i, Real spos, Real cpos);
    
    /// access data for a hinge point 
    Real spanwisePosition(uint i) const {
       assert(i < spanpos.size());
       return spanpos[i];
    }
    
    /// access data for a hinge point 
    Real chordwisePosition(uint i) const {
       assert(i < chordpos.size());
       return chordpos[i];
    }
    
    /// change the surface type 
    void type(CsType t) {cstype = t;}
    
    /// access the surface type 
    CsType type() const {return cstype;}
    
    /// return number of segments
    uint nsegments() const {
      if (spanpos.empty())
        return 0;
      else
        return spanpos.size()-1;
    }
    
    /// number of hinges 
    uint nhinges() const {return spanpos.size();}
    
    /// access name
    const std::string & name() const {return id;}
    
    /// named of base wing 
    const std::string & srfName() const {return wsp->name();}
    
    /// change name
    void rename(const std::string & s) {id = s;}
    
    /// generate list of segment names
    void segments(StringArray & sgnames) const;
    
    /// update geometry after parameter change 
    void updateGeometry();
    
    /// draw using OpenGL
    void draw() const;
    
    /// read XML representation
    void fromXml(const XmlElement & xe, const Assembly & asy);
    
    /// export to xml representation
    XmlElement toXml() const;
    
    /// geometry xml representation for mesh 
    XmlElement meshXml() const;
    
    /// tag mesh elements in range with tags starting at t
    int tagElements(TriMesh & msh, int t);
    
    /// return tag range used
    void tags(int & tag0, int & tagn) {
      tag0 = firstTag;
      tagn = firstTag + (hp.size()-1);
    }
    
    /// remove all hinges 
    void clearHinges() {
      spanpos.resize(0);
      chordpos.resize(0);
    }
    
  private:
    
    /// top-level name of (multi-segment) surface
    std::string id;
    
    /// attachment surface 
    WingSkeletonPtr wsp;
    
    /// leading/trailing edge flag 
    CsType cstype;
    
    /// chordwise and spanwise position of hinges 
    Vector spanpos, chordpos;
    
    /// hinge points and end points (derived)
    PointList<3> hp, ep;
    
    /// tagged triangles start with this
    int firstTag;
};

class CtSurfaceBox
{
  public:
    
    /// construct from forward and aft points
    CtSurfaceBox(uint iseg, const PointList<3> & pfwd, 
                 const PointList<3> & paft);
    
    /// check if a vertex is inside
    bool isInside(const Vct3 & p) const {
      bool inside(true);
      for (int k=0; k<6; ++k) {
        inside &= (dot(pn[k],p)-pd[k] > 0.0);
      }
      return inside;
    }
    
  private:
    
    /// six plane normal vectors
    Vct3 pn[6];

    /// plane distances so that dot(pn,p) == pd
    Real pd[6];
};

#endif

