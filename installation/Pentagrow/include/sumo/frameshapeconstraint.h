
/* ------------------------------------------------------------------------
 * file:       frameshapeconstraint.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Fit body section to special shape function 
 * ------------------------------------------------------------------------ */

#ifndef SUMO_FRAMESHAPECONSTRAINT_H
#define SUMO_FRAMESHAPECONSTRAINT_H

#include <boost/shared_ptr.hpp>
#include <genua/xmlelement.h>

class BodyFrame;
class FrameShapeConstraint;
typedef boost::shared_ptr<FrameShapeConstraint> ShapeConstraintPtr;

/** Abstract body frame shape constraint
*/
class FrameShapeConstraint
{
  public:
    
    /// default construction
    FrameShapeConstraint(int n = 7) : nip(n) {}

    /// virtual destruction
    virtual ~FrameShapeConstraint() {}
    
    /// change number of interpolation points
    void npoints(uint np) { nip = np; }
    
    /// access number of interpolation points
    uint npoints() const {return nip;}
    
    /// construct normalized interpolation points
    virtual void constrain(BodyFrame & bf) const = 0;
    
    /// convert to xml representation
    virtual XmlElement toXml() const = 0;
    
    /// construct from xml representation 
    virtual void fromXml(const XmlElement & xe) = 0;
    
    /// construct from xml representation
    static ShapeConstraintPtr createFromXml(const XmlElement & xe);
    
  protected:
    
    /// number of interpolation points to use
    int nip;
};

/** Constrains frame shape to circular shape */
class CircularShapeConstraint : public FrameShapeConstraint
{
  public:
    
    /// construct circular section shape
    CircularShapeConstraint(Real radius=1.0, int n = 7) 
        : FrameShapeConstraint(n), rds(radius) {}
    
    /// change hyperelliptic exponent
    void radius(Real r) {rds = r;}
    
    /// access radius
    Real radius() const {return rds;}
    
    /// modify body frame
    void constrain(BodyFrame & bf) const;
    
    /// convert to xml representation
    XmlElement toXml() const;
    
    /// construct from xml representation 
    void fromXml(const XmlElement & xe);
    
  protected:
    
    /// radius
    Real rds;
};

/** Constrains frame shape to hyperelliptic cross section */
class EllipticShapeConstraint : public FrameShapeConstraint
{
  public:
    
    /// construct pure elliptical cross section
    EllipticShapeConstraint(Real nx = 2.0, int n = 11) 
      : FrameShapeConstraint(n), xpn(nx) {}
    
    /// change hyperelliptic exponent
    void exponent(Real nx) {xpn = nx;}
    
    /// access exponent
    Real exponent() const {return xpn;}
    
    /// modify body frame
    void constrain(BodyFrame & bf) const;
    
    /// convert to xml representation
    XmlElement toXml() const;
    
    /// construct from xml representation 
    void fromXml(const XmlElement & xe);
    
  protected:
    
    /// superelliptic exponent
    Real xpn;
};

/** Constrains frame shape to double elliptic cross section */
class DoubleEllipticConstraint : public FrameShapeConstraint
{
  public:
    
    /// construct pure elliptical cross section
    DoubleEllipticConstraint(Real xc = -0.1, int n = 11) 
      : FrameShapeConstraint(n), rxc(xc) {}
    
    /// change relative offset
    void offset(Real xc) {rxc = xc;}
    
    /// access offset
    Real offset() const {return rxc;}
    
    /// modify body frame
    void constrain(BodyFrame & bf) const;
    
    /// convert to xml representation
    XmlElement toXml() const;
    
    /// construct from xml representation 
    void fromXml(const XmlElement & xe);
    
  protected:
    
    /// relative center offset
    Real rxc;
};

/** Generate a Huegelshaeffer curve */
class HuegelschaefferConstraint : public FrameShapeConstraint
{
  public:
    
    /// construct pure elliptical cross section
    HuegelschaefferConstraint(Real af = -0.1, int n = 11) 
      : FrameShapeConstraint(n), a(af) {}
    
    /// distortion factor, -0.9 to 0.9
    void distortion(Real af) {a = af;}
    
    /// access position of maximum width
    Real distortion() const {return a;}
    
    /// modify body frame
    void constrain(BodyFrame & bf) const;
    
    /// convert to xml representation
    XmlElement toXml() const;
    
    /// construct from xml representation 
    void fromXml(const XmlElement & xe);
    
  protected:
    
    /// relative shift of maximum width location
    Real a;
};

/** Isikveren's shape to support ceasiom geometry

  This is brittle and unsuitable for interactive use. Can be exploited 
  when reading fuselage definition from ceasiom files.
*/
class IsikverenShapeConstraint : public FrameShapeConstraint
{
  public:
    
    /// construct pure elliptical cross section
    IsikverenShapeConstraint(int n = 15) 
      : FrameShapeConstraint(n), zp(0.0), a0(1.0), a1(0.0), b1(0.0) {}
    
    /// shape parameter set
    void setParameter(Real zpos, Real A0, Real A1, Real B1) {
      zp = zpos; a0 = A0; a1 = A1, b1 = B1;
    }
    
    /// retrieve parameter set
    void getParameter(Real & zpos, Real & A0, Real & A1, Real & B1) const {
      zpos = zp; A0 = a0; A1 = a1; B1 = b1;
    }
    
    /// modify body frame
    void constrain(BodyFrame & bf) const;
    
    /// convert to xml representation
    XmlElement toXml() const;
    
    /// construct from xml representation 
    void fromXml(const XmlElement & xe);
    
  protected:
    
    /// shape parameters
    Real zp, a0, a1, b1;
};

typedef boost::shared_ptr<CircularShapeConstraint> CircularConstraintPtr;
typedef boost::shared_ptr<EllipticShapeConstraint> EllipticConstraintPtr;
typedef boost::shared_ptr<DoubleEllipticConstraint> DoubleEllipticConstraintPtr;
typedef boost::shared_ptr<HuegelschaefferConstraint> HuegelschaefferConstraintPtr;
typedef boost::shared_ptr<IsikverenShapeConstraint> IsikverenConstraintPtr;


#endif
