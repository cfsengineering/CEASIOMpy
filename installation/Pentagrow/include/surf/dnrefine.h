
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#ifndef SURF_DNREFINE_H
#define SURF_DNREFINE_H

#include "forward.h"
#include "dnrfregion.h"
#include "dntriangle.h"
#include <genua/bounds.h>

/** Base class for mesh refinement criteria
 *
 * \ingroup meshgen
 * \sa DnMesh
 */
class DnCriterion
{
  public:
    
    /// virtual destructor
    virtual ~DnCriterion() {}
    
    /// evaluate triangle quality
    virtual Real eval(const uint *vi) const = 0;
};

/** Simplest mesh refinement criterion.
 * \ingroup meshgen
 * \sa DnMesh
 */
class DnRefineCriterion : public DnCriterion
{
  public:
    
    /// create unbound criterion (cannot be evaluated until bound)
    DnRefineCriterion() : msh(0) {setDefault();}

    /// bind criterion object to mesh object
    explicit DnRefineCriterion(const DnMesh *pm) : msh(pm) {setDefault();}
    
    /// destructor
    virtual ~DnRefineCriterion() {}

    /// bind to mesh object
    virtual void bind(const DnMesh *pm) const;
    
    /// change refinement criteria
    void setCriteria(Real lmax, Real lmin, Real phimax, Real stretch, uint n = 1073741824u);

    /// access specified maximum edge length
    Real maxLength() const {return maxlen;}

    /// set maximum edge length
    void maxLength(Real ml) {maxlen = ml;}
    
    /// access specified minimum edge length
    Real minLength() const {return minlen;}
    
    /// set minimum edge length
    void minLength(Real ml) {minlen = ml;}

    /// access maximum normal angle 
    Real maxPhi() const {return maxphi;}
    
    /// set maximum normal angle
    void maxPhi(Real mp) {maxphi = mp; mincosphi = cos(maxphi);}
    
    /// access stretch criterion
    Real maxStretch() const {return maxstretch;}
    
    /// set stretch criterion
    void maxStretch(Real ms) {maxstretch = ms;}
    
    /// access maximum number of vertices
    uint nmax() const {return nvmax;}
    
    /// set maximum number of vertices 
    void nmax(uint n) {nvmax = n;}

    /// evaluate triangle 'quality' - larger value means earlier refinement
    virtual Real eval(const uint *vi) const;

    /// apply a global scaling factor to all length values
    virtual void globalScale(Real f);

    /// read criteria from xml representation
    virtual void fromXml(const XmlElement & xe);

    /// write criteria to xml representation
    virtual XmlElement toXml() const;
    
    /// clone object 
    virtual DnRefineCriterion *clone() const;
    
    /// create any criterion from XML
    static DnRefineCriterionPtr createFromXml(const XmlElement & xe);
    
  protected:
    
    /// apply default parameters
    void setDefault();
    
  protected:

    /// mesh object to ask for coordinates
    mutable const DnMesh *msh;
    
    /// limits on geometric properties
    Real maxlen, minlen, maxphi, maxstretch;
    
    /// derived property for angle criterion
    Real mincosphi;
    
    /// maximum number of vertices to create by refinement
    uint nvmax;
};



/** Locally adapted refinement criterion.
 * \ingroup meshgen
 * \sa DnMesh
 */
class DnRegionCriterion : public DnRefineCriterion
{
  public:

    /// create unbound criterion
    DnRegionCriterion() : DnRefineCriterion() {}
    
    /// bind criterion object to mesh object
    explicit DnRegionCriterion(const DnMesh *pm) : DnRefineCriterion(pm) {}
    
    /// copy-construct a region criterion 
    explicit DnRegionCriterion(const DnRefineCriterion & a) : DnRefineCriterion(a) {} 
    
    /// destructor
    virtual ~DnRegionCriterion() {}

    /// number of currently active refinement regions
    uint nregions() const {return regions.size();}
    
    /// add a refinement region, general case  
    uint addRegion(const DnRefineRegion & rg);
    
    /// add a rectangular region with constant refinement
    uint addRegion(const BndRect & rg, Real f);
    
    /// remove regions with index [first, last)
    void removeRegions(uint first, uint last);
    
    /// remove regions with indices idx 
    void removeRegions(const Indices & idx);
    
    /// evaluate triangle 'quality' - larger value means earlier refinement
    virtual Real eval(const uint *vi) const;

    /// read criteria from xml representation
    virtual void fromXml(const XmlElement & xe);

    /// write criteria to xml representation
    virtual XmlElement toXml() const;
    
    /// clone object 
    virtual DnRegionCriterion *clone() const;
    
  protected:

    /// refinement regions
    DnRegionArray regions;
};

typedef boost::shared_ptr<DnRegionCriterion> DnRegionCriterionPtr;

/** Specialized refinement criterion for non-smooth surfaces.

  This criterion is useful for surfaces with a discontinuity in the
  surface normal at certain values of the parameter v, such that the
  y-component of the normal differs strongly between v-eps and v+eps.

 \ingroup meshgen
 \sa DnMesh

 */
class DnYKinkCriterion : public DnRegionCriterion
{
  public:

    /// create unbound criterion
    DnYKinkCriterion() : DnRegionCriterion() {}
    
    /// bind criterion object to mesh object
    DnYKinkCriterion(const DnMesh *pm) : DnRegionCriterion(pm) {}
    
    /// register a kink location
    void addKink(Real v) {vkinks.push_back(v);}
    
    /// evaluate triangle 'quality' - larger value means earlier refinement
    Real eval(const uint *vi) const;
    
  private:
    
    /// kink locations
    Vector vkinks;
};

typedef boost::shared_ptr<DnYKinkCriterion> DnYKinkCriterionPtr;

/** Criterion which uses stretch only
 * \ingroup meshgen
 * \sa DnMesh
 */
class DnStretchCriterion : public DnCriterion
{
  public:

    /// bind criterion object to surface and vertex list
    DnStretchCriterion(const DnMesh *pm) : msh(pm) {}
    
    /// destructor
    virtual ~DnStretchCriterion() {}

    /// simply return stretch ratio
    virtual Real eval(const uint *vi) const;

  private:

    /// pointer to mesh which is asked for coordinates
    const DnMesh *msh;
}; 

/** Adaptor for triangle comparison by quality
 * \ingroup meshgen
 * \sa DnMesh
 */
class DnTriangleCompare
{
  public:

    /// construct comparison object
    DnTriangleCompare(const DnCriterion & crit, const DnTriangleArray & t) :
      c(crit), triangles(t) {}

    /// evaluate comparison criterion
    bool operator() (uint a, uint b) const {
      assert(a < triangles.size());
      assert(b < triangles.size());
      Real qa = c.eval(triangles[a].vertices());
      Real qb = c.eval(triangles[b].vertices());
      assert(std::isfinite(qa));
      assert(std::isfinite(qb));
      if (qa != qb)
        return (qa < qb);
      else
        return a < b;
    }
    
    /// evaluate sorting criterion
    Real eval(uint a) const {return c.eval(triangles[a].vertices());}
    
  private:

    /// comparison criterion
    const DnCriterion & c;
    
    /// triangle list
    const DnTriangleArray & triangles;
};

/** Priority queue for mesh refinement/improvement

  The idea is to keep a heap of triangles sorted by their geometric
  quality, so that the top element is always the 'worst'. 
  Unfortunately, this does not work very well, because the refinement
  process modifies the quality of triangles already in the heap,
  so that the heap property is destroyed.

  \ingroup meshgen
  \sa DnMesh
*/
class DnTriangleHeap
{
  public:
  
    /// initialize, put all valid triangles into heap
    DnTriangleHeap(const DnCriterion & crit, const DnTriangleArray & t); 
    
    /// initialize, put valid triangles from index set into heap
    DnTriangleHeap(const DnCriterion & crit, const DnTriangleArray & t, const Indices & idx); 
  
    /// put all critical triangles into heap again
    void refill();
    
    /// empty or not?
    bool empty() const {return iheap.empty();}
    
    /// number of elements on heap
    uint size() const {return iheap.size();}
    
    /// return top element
    uint top() const {return iheap.front();}
    
    /// pop top element 
    void pop() {
      std::pop_heap(iheap.begin(), iheap.end(), cmp);
      iheap.pop_back();
    }
    
    /// push new element on heap
    void push(uint i) {
      iheap.push_back(i);
      std::push_heap(iheap.begin(), iheap.end(), cmp);
    }
    
    /// add list of triangles to existing ones, re-establish heap
    void append(const Indices & idx);
    
    // debug: print sorting criterion for sorted heap
    void print();
    
  private:
    
    /// triangle array
    const DnTriangleArray & triangles;
    
    /// comparison object
    DnTriangleCompare cmp;
    
    /// indices into triangle array
    Indices iheap;
};

typedef std::pair<uint, Real> TqPair;
typedef std::vector<TqPair> TqArray;

/** Priority queue for adaptive mesh refinement.
 * \ingroup meshgen
 * \sa DnMesh
 */
class DnTriangleQueue
{
  public:
    
    /// construct queue
    DnTriangleQueue(const DnCriterion & crit, const DnTriangleArray & t);
      
    /// put all critical triangles into queue
    void refill();
    
    /// number of triangles left to refine
    uint size() const {return irf.size();}
    
    /// no more triangles left?
    bool empty() const {return irf.empty();}
    
    /// retrieve next critical triangle to refine
    uint next(Real & cval) {
      uint tnext(NotFound);
      cval = 0.0;
      while (cval <= 1.0 and (not irf.empty())) {        
        tnext = irf.back().first;
        irf.pop_back();
        if (tnext < triangles.size() and triangles[tnext].isValid())
          cval = crit.eval(triangles[tnext].vertices());
        else 
          cval = 0.0;
      } 
      return tnext;
    } 
    
  private:
    
    /// triangle array
    const DnTriangleArray & triangles;
    
    /// quality criterion (returns > 1 if refinement necessary)
    const DnCriterion & crit;
    
    /// indices of triangles waiting for refinement
    TqArray irf;
};

#endif
