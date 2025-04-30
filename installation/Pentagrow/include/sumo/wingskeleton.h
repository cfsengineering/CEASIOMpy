
/* ------------------------------------------------------------------------
 * file:       wingskeleton.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Holds a collection of wing sections and an interpolation surface
 * ------------------------------------------------------------------------ */

#ifndef SUMO_WINGSKELETON_H
#define SUMO_WINGSKELETON_H

#include "forward.h"
#include "component.h"
#include "wingsection.h"
#include <surf/surface.h>
#include <surf/dnwingcriterion.h>

/** A collection of WingSection instances.

  WingSkeleton represents a wing surfaces constructed from a set of WingSection
  objects. In the most general case, the surface itself is a composite surface
  (implemented by StitchedSurface in libsurf) which can feature segments which
  are at least G0-continuous. Sections at which G1 continuity is broken, e.g.
  the Yehudi break of a transport aircraft wing, should be indicated by marking
  the corresponding WingSection as a break section. This allows the mesh
  generator to recognize the discontnuity in normal directions.

  \sa WingSection, BodySkeleton
  */
class WingSkeleton : public Component
{
  public:

    /// initialize
    WingSkeleton();

    /// create a cloned copy
    WingSkeletonPtr clone() const;

    /// create a copy mirrored about the xz-plane
    WingSkeletonPtr xzMirrorCopy() const;
    
    /// remove all sections 
    void clear() { sections.clear(); }
    
    /// number of frames stored
    uint nsections() const {return sections.size();}

    /// apply global scaling factor
    void globalScale(Real f);

    /// reference length (chord)
    Real refLength() const {return maxChord;}
    
    /// for control system : compute hinge position and chord from parameters   
    Real hingePos(Real v, Real chordpos, Vct3 & hp) const;
    
    /// add a new wing section
    void addSection(WingSectionPtr wsp);

    /// insert section at specified position
    void insertSection(uint ipos, WingSectionPtr wsp);

    /// swap sections ki and kj
    void swapSections(uint ki, uint kj);

    /// find index for section named s
    uint findByName(const std::string & s) const;
      
    /// delete a section with index i
    bool removeSection(uint i);
      
    /// access section object
    WingSectionPtr section(uint i) {
      assert(i < sections.size());
      return sections[i];
    }

    /// access frame object
    const WingSectionPtr & section(uint i) const {
      assert(i < sections.size());
      return sections[i];
    }

    /// access reference dimensions 
    Real geoMeanChord() const {return refChord;}
    
    /// access reference dimensions 
    Real aeroMeanChord() const {return refMac;}
    
    /// access reference dimensions 
    Real referenceArea() const {return refArea;}
    
    /// access reference dimensions 
    Real referenceSpan() const {return refSpan;}
    
    /// access reference dimensions 
    Real minRadius() const {return minLERadius;}
    
    /// access construction flags 
    bool autoSym() const {return bAutoSym;}
    
    /// access construction flags 
    bool detectWinglet() const {return bDetectWinglet;}
    
    /// access construction flags 
    bool cubicInterpolation() const {return bCubic;}
    
    /// set construction flags 
    void autoSym(bool f);
    
    /// set construction flags 
    void detectWinglet(bool f) {bDetectWinglet = f;}
    
    /// set construction flags 
    void cubicInterpolation(bool f) {bCubic = f;}
    
    /// mirror and copy section about y=0
    bool mirrorSections();

    /// create xml representation for skeleton
    XmlElement toXml() const;

    /// reconstruct from xml representation
    void fromXml(const XmlElement & xe);
    
    /// sort wing sections using heuristics
    void heuristicSort();

    /// construct surface from current sections
    void interpolate();
    
    /// draw surface using OpenGL
    void glDraw() const;

    /// compute default mesh generation criteria
    void defaultCriterion();
    
    /// compute points on grid 
    void exportGrid(uint numax, uint n2s, Real lmax, Real phimax, 
                    PointGrid<3> & pgrid) const;
    
    /// access interpolation points only 
    void ipolPoints(PointListArray & pts) const;

    /// generate improved initial mesh
    void buildInitGrid(PointGrid<2> & pgi);
    
    /// write cap representation to IGES file
    void capsToIges(IgesFile & file) const;
    
    /// parameter space grid for visualization
    void vizGrid(PointGrid<2> & qts) const; 
    
    /// locate v for a given distance from x-axis through inboard section
    Real vSpanPos(Real u, Real yrel, Real vtol=1e-5) const;

    /// fit all sections to reference geometry or mesh
    void fitSection(uint jsection, const FrameProjector &fpj,
                    Real rChord, Real rThick);

    /// fit all sections to reference geometry or mesh
    void fitSections(const FrameProjector &fpj, Real rChord, Real rThick);

  private:

    /// implicit copying is forbidden
    WingSkeleton(const WingSkeleton &) : Component() {}
    
    /// detect the index of the wingtip section, is there is a winglet
    uint lastWingletSection() const;
    
    /// locate leading edge at v 
    Real locateLeadingEdge(Real v, Real utol=1e-5) const;
    
    /// compute statistics 
    void updateStats();
    
    /// retrieve current mesh criterion
    DnWingCriterionPtr wingCriterion();
    
    /// evaluate quality of chordwise discretization pattern
    void upQuality(Real v, const Vector & up, Real & phi, Real & len);
    
    /// choose suitable pattern at station v
    uint findChordPattern(Real v, uint nufix, Vector & up);
    
    /// spanwise parameter spacing which contains sections
    uint vspacing(int n, Vector & vp) const;

    /// iteratively find reasonable u-parameter values for visualization
    void adaptVizSlice(size_t na, Real v, Vector &ua) const;

  private:

    /// sections
    WingSectionArray sections;

    /// curve pointers used for interpolation
    CurvePtrArray cpa;
    
    /// section positions 
    Vector vspos;
    
    /// regions introduced by tip refinement
    Indices trreg;
    
    /// informative values used for drawing and default MG parameters
    Real maxChord, refChord, minLERadius, refArea, refSpan, refMac;
    
    /// visibility flag, automatic symmetry, cubic interpolation
    bool bAutoSym, bDetectWinglet, bCubic;
};

#endif

