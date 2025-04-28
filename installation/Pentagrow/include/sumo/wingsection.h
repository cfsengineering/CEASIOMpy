
/* ------------------------------------------------------------------------
 * file:       wingsection.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Wrapper object for airfoil object
 * ------------------------------------------------------------------------ */

#ifndef SUMO_WINGSECTION_H
#define SUMO_WINGSECTION_H

#include "forward.h"
#include <surf/curve.h>
#include <genua/plane.h>
#include <genua/xmlelement.h>
#include <genua/propmacro.h>

/** One cross-section for WingSkeleton.

  WingSection is a wrapper for class Airfoil in libsurf; it adds information
  which is useful for garphical editing and provides additional interfaces
  needed for graphical representation.

  \sa WingSkeleton
  */
class WingSection
{
  public:

    /// default initialization
    WingSection();

    /// create a clone with different name
    WingSectionPtr clone() const;
    
    /// access wing section name
    const std::string & name() const {
      assert(m_crv);
      return m_crv->name();
    }

    /// change wing section name
    void rename(const std::string & s) const {
      assert(m_crv);
      return m_crv->rename(s);
    }

    /// apply global scaling factor
    void globalScale(Real f);

    /// access leading edge point
    const Vct3 & origin() const {return m_mctr;}

    /// set leading edge point
    void origin(const Vct3 & ctr) {m_mctr = ctr;}

    /// access chord length
    Real chordLength() const {return m_chord;}

    /// modify chord length
    void chordLength(Real c) {m_chord = c;}

    /// access twist angle
    Real twistAngle() const {return m_twist;}
    
    /// set twist angle (radian)
    void twistAngle(Real t) {m_twist = t;}

    /// access dihedral angle (radian)
    Real dihedralAngle() const {return m_dihedral;}

    /// modify dihedral angle
    void dihedralAngle(Real d) {m_dihedral = d;}
    
    /// modify yaw angle 
    Real yawAngle() const {return m_yaw;}
    
    /// modify yaw angle 
    void yawAngle(Real y) {m_yaw = y;}
    
    /// compute section plane in 3D space
    Plane sectionPlane() const;

    /// access number of approximation points
    int nApprox() const {return m_nap;}
    
    /// set number of approximation points (-1 for interpolation)
    void setNApprox(int n) {m_nap = n;}
    
    /// access break flag 
    bool isBreak() const {return m_bBreak;}
    
    /// set break flag 
    void markAsBreak(bool f) {m_bBreak = f;}
    
    /// access reverse flag
    bool isReversed() const {return m_bReversed;}

    /// use inverse parametrization
    void reverse(bool flag) {m_bReversed = flag;}

    /// access relative points (2D)
    const PointList<2> & riPoints() const {return m_crd;}
    
    /// access relative points (2D)
    PointList<2> & riPoints() {return m_crd;}
    
    /// build curve according to current transformations
    void interpolate();

    /// access curve pointer for interpolation
    CurvePtr curve() {return m_crv;}
    
    /// read coordinates from file
    void fromFile(const std::string & fname);
    
    /// construct from name and coordinates
    void fromCoordinates(const std::string & id, const PointList<2> & pts);
    
    /// set airfoil from builtin airfoil collection 
    void fromCollection(const AirfoilCollection & afc, uint ipos);

    /// generate section from NACA code
    void fromNaca4(uint ncode);

    /// generate section from NACA 4 spec 
    void fromNaca4(Real camber, Real cpos, Real thick);
    
    /// generate section from NACA 5 spec 
    void fromNaca5(int meanline, Real dcl, Real thick);
    
    /// generate section from NACA 6-series specification
    int fromNaca6(uint iprofile, uint icamber, Real toc,
                  const Vector & cli, const Vector & a);
    
    /// approximate rounded flat plate 
    void fromPlate(Real toc);
    
    /// airfoil identifier (for user info only)
    const std::string & airfoilName() const {return m_idAirfoil;}
    
    /// estimate leading edge radius
    Real leRadius() const;

    /// export interpolation points to IGES file
    int pointsToIges(IgesFile & file, int sectionId, int tfi = 0) const;
    
    /// create xml representation
    XmlElement toXml() const;

    /// build from xml representation
    void fromXml(const XmlElement & xe);

    /// compute bounding box for rendering
    void extendBoundingBox(float plo[3], float phi[3]) const;

    /// construct vertices of the capture rectangle used for fitting
    void captureRectangle(const Mtx44 &skeletonTrafo, Real rChord, Real rThick,
                          Vct3 &po, Vct3 &pu, Vct3 &pv, Vct3 &pn) const;

    /// fit this section to a mesh
    void fitSection(const FrameProjector &fpj, const Mtx44 &skeletonTrafo,
                    Real rChord, Real rThick);

  private:

    /// implicit copying is forbidden
    WingSection(const WingSection &) {}

    /// create interpolated curve from airfoil object
    void transform(Airfoil *paf);

    /// check airfoil coordinates for consistency
    void checkCoordinates();
    
  private:

    /// leading edge point (0,0 in airfoil coordinates)
    Vct3 m_mctr;
    
    /// section coordinates before transformation
    PointList<2> m_crd;

    /// interpolated curve
    CurvePtr m_crv;
    
    /// transformations (angles in radian)
    Real m_chord, m_twist, m_dihedral, m_yaw;
    
    /// name for the currently loaded airfoil
    std::string m_idAirfoil;
    
    /// approximation mode (-1 for interpolation, number of points for approximation)
    int m_nap;
    
    /// flag : is this section a break in the surface interpolation?  
    bool m_bBreak;

    /// reverse parametrization to run along lower side first?
    bool m_bReversed;

    /// airfoil modifications used to construct fairings

    GENUA_PROP(Real, dxNose)
    GENUA_PROP(Real, dyNose)
    GENUA_PROP(Real, dxTail)
    GENUA_PROP(Real, dyTail)
};

inline bool operator< (const WingSectionPtr & a, const WingSectionPtr & b)
{
  const Vct3 & ca(a->origin());
  const Vct3 & cb(b->origin());
  if (ca[1] == cb[1])
    return ca[2] > cb[2];
  else
    return ca[1] > cb[1];
}

inline bool is_left_section(const WingSectionPtr & s)
{
  const Vct3 & p(s->origin());
  if (p[1] < 0.0)
    return true;
  else
    return false;
}

inline bool is_right_section(const WingSectionPtr & s)
{
  const Vct3 & p(s->origin());
  if (p[1] >= 0.0)
    return true;
  else
    return false;
}

#endif

