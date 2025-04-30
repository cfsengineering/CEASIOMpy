
/* ------------------------------------------------------------------------
 * file:       bodyskeleton.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * set of frames which defines a body shape
 * ------------------------------------------------------------------------ */

#ifndef SUMO_BODYSKELETON_H
#define SUMO_BODYSKELETON_H

#include "forward.h"
#include "component.h"
#include "bodyframe.h"
#include "frameprojector.h"
#include <surf/spline.h>
#include <genua/xmlelement.h>

/** Single surface representing a body-like component.

  BodySkeleton is a single cubic spline surface defined by a number of
  interpolated support frames (BodyFrame) and a longitudinal interpolation
  method (Bessel or Akima).

  \sa WingSkeleton, BodyFrame
  */
class BodySkeleton : public Component
{
  public:

    typedef FrameProjector::SegmentArray SegmentArray;

    /// create a default surface for testing
    BodySkeleton();

    /// create a deep copy 
    BodySkeletonPtr clone() const;
    
    /// create a mirror copy 
    BodySkeletonPtr xzMirrorCopy() const;
    
    /// generate points for drawing
    Vct3 evaluate(PointList<3> & pbot, PointList<3> & ptop,
                  PointList<3> & pleft, PointList<3> & pright) const;

    /// number of frames stored
    uint nframes() const {return frames.size();}

    /// reference length (width)
    Real refLength() const {return maxWidth;}
    
    /// access frame object
    BodyFramePtr frame(uint i) {
      assert(i < frames.size());
      return frames[i];
    }

    /// access frame object
    const BodyFramePtr & frame(uint i) const {
      assert(i < frames.size());
      return frames[i];
    }
    
    /// return index of frame f, or NotFound 
    uint find(const BodyFramePtr & f) const;

    /// eliminate frame next to x and re-create surface
    void removeFrame(Real x);
    
    /// insert a new frame at position x
    BodyFramePtr insertFrame(Real x);
    
    /// add an existing frame at the end 
    void addFrame(const BodyFramePtr & bfp) {frames.push_back(bfp);}
    
    /// create xml representation for skeleton
    XmlElement toXml() const;

    /// reconstruct from xml representation
    void fromXml(const XmlElement & xe);

    /// apply global scaling factor
    void globalScale(Real f);

    /// compute length, maximum height and width
    void dimensions(Real & hmax, Real & wmax, Real & len) const;
    
    /// move body by ds, scale length, height and width with factors
    void scale(Real fh = 1.0, Real fw = 1.0, Real fl = 1.0);

    /// toggle inlet lip generation on/off
    void inletLip(bool flag) {bInletLip = flag;}

    /// query flag setting
    bool inletLip() const {return bInletLip;}

    /// access inlet lip parameter
    Real axialLipOffset() const {return lipAxialOffset;}

    /// access inlet lip parameter
    Real radialLipOffset() const {return lipRadialOffset;}

    /// access inlet lip parameter
    Real shapeCoefLip() const {return lipShapeCoef;}

    /// access inlet lip parameter
    void axialLipOffset(Real x) {lipAxialOffset = x;}

    /// access inlet lip parameter
    void radialLipOffset(Real x) {lipRadialOffset = x;}

    /// access inlet lip parameter
    void shapeCoefLip(Real x) {lipShapeCoef = x;}

    /// import sections from file 
    void importSections(const std::string & fname);
    
    /// construct surface from current frames
    void interpolate();

    /// rename all frames according to their x-position
    void renameFrames();
    
    /// draw using OpenGL 
    void glDraw() const;
    
    /// find default mesh generation criteria
    void defaultCriterion();
    
    /// construct initial grid for mesh generator
    void buildInitGrid(PointGrid<2> & pgi);
    
    /// compute points on grid 
    void exportGrid(uint numax, uint n2s, Real lmax, Real phimax, 
                    PointGrid<3> & pgrid) const;
    
    /// collect interpolation points 
    void ipolPoints(PointListArray & pts) const;
    
    /// preserve collinear segments?
    bool keepStraightSegments() const {return bKeepStraight;}
    
    /// preserve collinear segments?
    void keepStraightSegments(bool flag) {bKeepStraight = flag;}
    
    /// remove all frames 
    void clear() {frames.clear();}
    
    /// write cap representation to IGES file
    void capsToIges(IgesFile & file) const;
    
    /// compute viz grid approximation 
    void vizGrid(PointGrid<2> & qts) const;

    /// project a single frame interpolation point onto CAD geometry
    void projectPoint(const FrameProjector & fpj, const SegmentArray & sgs,
                      uint iframe, uint ipt);

    /// project all interpolation points of a single frame
    void projectPoints(const FrameProjector & fpj, const SegmentArray & sgs,
                       uint iframe, Real maxdst=huge);
    
  private:

    /// forbid implicit copying (use clone)
    BodySkeleton(const BodySkeleton &) : Component() {}

    /// determine approximate mean circumference
    Real meanCircumference() const;

    /// create inlet lip surface
    SurfacePtr generateInletLip(CurvePtrArray & cpa);

    /// compute local center, width and height (for insertFrame)
    Vct3 localDimensions(Real v, Real & lh, Real & lw) const;
    
    /// generate v-parameter vector with n points between frames
    uint vspacing(int n, Vector & vp) const;

    /// locat waist point at v= const, between ulo and uhi
    Real findWaist(Real v, Real ulo, Real uhi) const;

  private:

    /// frames
    BodyFrameArray frames;

    /// breakpoints obtained during interpolation 
    Vector vspos;
    
    /// interpolated line of maximum width parameter
    Curve mwleft, mwright;

    /// parameters defining inlet lip geoemtry
    Real lipAxialOffset, lipRadialOffset, lipShapeCoef;

    /// limit dimensions 
    Real maxWidth, minRadius;
    
    /// use Akima tangent construction?
    bool bKeepStraight;

    /// generate an inlet lip?
    bool bInletLip;
};

#endif

