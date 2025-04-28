
/* ------------------------------------------------------------------------
 * file:       bodyframe.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Fuselage section object
 * ------------------------------------------------------------------------ */

#ifndef SUMO_BODYFRAME_H
#define SUMO_BODYFRAME_H

#include "forward.h"
#include "frameshapeconstraint.h"
#include <surf/symframe.h>
#include <genua/xmlelement.h>
#include <genua/plane.h>

/** Section for body-type surfaces.

  BodyFrame encapsulates section curves from which body surfaces
  are interpolated. For more intuitive editing, frames are represented
  by a set of 2D coordinates relative to the frame center and two
  scalar values for maximum width and height. 

  \sa BodySkeleton
  */
class BodyFrame 
{
  public:

    /// default initialization
    BodyFrame();

    /// generate a clone of the current frame
    BodyFramePtr clone() const;

    /// access frame name
    const std::string & name() const {return crv->name();}

    /// change frame name
    void rename(const std::string & s) {crv->rename(s);}
    
    /// apply global scaling factor
    void globalScale(Real f);

    /// access frame origin
    const Vct3 & origin() const {return mctr;}
    
    /// move frame origin to pos
    void origin(const Vct3 & pos) {mctr = pos;}

    /// return the plane of the frame
    Plane framePlane() const;

    /// symmetry flag
    bool symmetric() const {return bSymmetric;}

    /// import coordinates from file 
    void importSection(PointList<3> & pts);
    
    /// make frame a double ellipse; rzc is the relative height of the center
    void makeDoubleEllipse(Real rzc, int np = 7);
    
    /// make frame a Isikveren section 
    void makeIsikveren(Real zp, Real a0, Real a1, Real b1, int np=16);
    
    /// estimate minimum in-plane radius
    Real estimateMinRadius() const;
    
    /// access relative interpolation points (2D)
    const PointList<2> & riPoints() const {return rpts;}

    /// set interpolation points (2D)
    PointList<2> & riPoints() {return rpts;}

    /// evaluate curve and transform to relative coordinates
    void revaluate(PointList<3> & pts) const;

    /// access frame width
    Real frameWidth() const {return mwidth;}

    /// modify frame width
    void setFrameWidth(Real w)  {mwidth = w;}

    /// access frame height
    Real frameHeight() const {return mheight;}

    /// modify frame height
    void setFrameHeight(Real h) {mheight = h;}

    /// access parametric position of maximum width (right)
    Real rightMaxWidth() const {return twmax;}
    
    /// access parametric position of maximum width (left)
    Real leftMaxWidth() const {return 1.0-twmax;}

    /// compute bottom point
    Vct3 pbottom() const {
      return crv->eval(0.0);
    }

    /// compute top point
    Vct3 ptop() const {
      return crv->eval(0.5);
    }

    /// compute side point
    Vct3 pside() const {
      return crv->eval(twmax);
    }

    /// convert 3D point into frame coordinates (y,z only)
    Vct2 space2frame(const Vct3 & p) const {
      Real x = 2*(p[1] - mctr[1])/mwidth;
      Real y = 2*(p[2] - mctr[2])/mheight;
      return vct(x,y);
    }

    /// convert 2D frame point to 3D space
    Vct3 frame2space(const Vct2 & p) const {
      Real y = mctr[1] + 0.5*mwidth*p[0];
      Real z = mctr[2] + 0.5*mheight*p[1];
      return vct(mctr[0], y, z);
    }

    /// normalize relative coordinates to [0,1]x[-1,1]
    void normalize();
    
    /// recreate spline curve
    void interpolate();

    /// evaluate interpolation points after change of control points 
    void evalIpp();
    
    /// access parameters of interpolation points
    const Vector & parametrization() const {return ipt;}
    
    /// access curve pointer for surface interpolation
    const CurvePtr & curve() const {return crv;}

    /// linear search for interpolation point nearest to pos
    uint nearestRPoint(const Vct2 & pos) const;

    /// remove interpolation point closest to relative position pos
    void removePoint(const Vct2 & pos);

    /// insert interpolation point at relative position pos
    void insertPoint(const Vct2 & pos);

    /// scale relative coordinates so that they fit into [0,1]x[-1,1]
    void rebox();
    
    /// access pointer to shape constraint 
    ShapeConstraintPtr shapeConstraint() const {return fsconp;}
    
    /// replace shape constraint
    void shapeConstraint(const ShapeConstraintPtr & s);
    
    /// remove any shape constraint
    void eraseConstraint() {fsconp.reset();}
    
    /// create xml representation for skeleton
    XmlElement toXml() const;

    /// reconstruct from xml representation
    void fromXml(const XmlElement & xe);

    /// compute bounding box for rendering
    void extendBoundingBox(float plo[3], float phi[3]) const;

  private:

    /// do not allow implicit copying
    BodyFrame(const BodyFrame &) {}

    /// find curve parameter for maximum width, iteratively
    Real findMaxWidth(Real ttol = 1e-3) const;
    
  private:

    /// origin of frame
    Vct3 mctr;
    
    /// size parameters and parametric position of maximum width
    Real mheight, mwidth, twmax;

    /// *relative* coordinates of interpolation points
    PointList<2> rpts;

    /// approximate parametric positions of interpolation points
    Vector ipt;

    /// spline interpolation of frame
    CurvePtr crv;
    
    /// nonzero if shape is fixed to analytical curve
    ShapeConstraintPtr fsconp;

    /// symmetric frame ?
    bool bSymmetric;
  };

inline bool operator< (const BodyFramePtr & a, const BodyFramePtr & b)
{
  Real xa = a->origin()[0];
  Real xb = b->origin()[0];
  return xa < xb;
}

#endif

