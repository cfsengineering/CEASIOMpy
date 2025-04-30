
/* ------------------------------------------------------------------------
 * file:       component.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Interface for surfaces which can be meshed
 * ------------------------------------------------------------------------ */

#ifndef SUMO_COMPONENT_H
#define SUMO_COMPONENT_H

#include <string>
#include <boost/shared_ptr.hpp>
#include <surf/dnrefine.h>
#include <surf/asycomponent.h>

class Curve;
class XmlElement;
class IgesFile;

typedef std::vector<PointList<3> > PointListArray;

/** Interface for meshable objects.
  */
class Component : public AsyComponent
{
  public:

    /// set default values
    Component();

    /// empty
    virtual ~Component() {}
    
    /// visualization : draw using OpenGL 
    virtual void glDraw() const = 0;
    
    /// store regularly evaluated grid lines in file 
    virtual void exportGrid( uint numax, uint n2s, Real lmax, Real phimax, 
                             PointGrid<3> & pgrid ) const = 0;
    
    /// fetch all interpolation points 
    virtual void ipolPoints(PointListArray & pts) const = 0;
    
    /// return a reference length scale (width or chord)
    virtual Real refLength() const = 0;
    
    /// apply global scaling factor (used to change units etc)
    virtual void globalScale(Real f);

    /// apply global translation, update bounding box and visualization
    virtual void globalTranslate(const Vct3 &trn);

    /// access surface name
    const std::string & name() const;

    /// change name
    void rename(const std::string & s);

    /// access surface translation 
    const Vct3 & origin() const {return sTrn;}
     
    /// set surface translation 
    void origin(const Vct3 & pos) {sTrn = pos;}
    
    /// access surface rotation
    const Vct3 & rotation() const {return sRot;}
     
    /// set surface rotation
    void rotation(const Vct3 & rot) {sRot = rot;}
    
    /// access cap height for cap at v=0
    Real southCapHeight() const {return AsyComponent::ecaps[2].height();}
    
    /// access cap height for cap at v=0
    void southCapHeight(Real h) {AsyComponent::ecaps[2].height(h);}
    
    /// access cap height for cap at v=1
    Real northCapHeight() const {return AsyComponent::ecaps[3].height();}
    
    /// access cap height for cap at v=1
    void northCapHeight(Real h) {AsyComponent::ecaps[3].height(h);}
    
    /// true if mesh generation defaults activated 
    virtual bool useMgDefaults() const {return bUseMgDefaults;}
    
    /// set defaults Mg settings flag
    virtual void useMgDefaults(bool f) {bUseMgDefaults = f;} 
    
    /// use coarse mesh algorithm 
    virtual bool stretchedMesh() const {return main->stretchedMesh();}
    
    /// use coarse mesh algorithm 
    virtual void stretchedMesh(bool f) {main->stretchedMesh(f);}
    
    /// visibility flag 
    bool visible() const {return bVisible;}
    
    /// set visibility 
    void visible(bool f) {bVisible = f;}
    
    /// access polygon color 
    const Vct4 & pgColor() const {return cPolygon;}
    
    /// access polygon color 
    void pgColor(const Vct4 & c) {cPolygon = c;}
    
    /// compute bounding box for rendering
    void extendBoundingBox(float plo[3], float phi[3]) const;
    
    /// export raw surface data with annotations
    XmlElement rawXml(bool share=false) const;

    /// generate xml representation of mg settings 
    XmlElement mgToXml() const;
    
    /// initialize ng settings from xml representation 
    void mgFromXml(const XmlElement & xe);
    
    /// write cap representation to IGES file
    virtual void capsToIges(IgesFile & file) const;
    
    /// compute parameter space grid to use for visualization
    virtual void vizGrid(PointGrid<2> & qts) const = 0;
    
    /// updates visualization grid in parameter space
    void updateVizGrid() const;
    
  protected:
    
    /// compute points for surface rendering 
    void evalGrid(const PointGrid<2> & qts) const;
    
    /// draw surface approximation
    void glDrawGrid() const;
    
    /// draw surface only 
    void glDrawGrid(const PointGrid<2> & qts) const;
    
    /// draw a single component curve under transformation 
    void glDrawCurve(const Curve & c, const Vector & t) const;
    
  protected:
    
    /// bounding box for visualization (computed by drawGrid)
    mutable Vct3 bbplo, bbphi;
    
    /// grids of points and normals for drawing 
    mutable PointGrid<3> vzpts, vznrm;
    
    /// colors for surface and line drawing 
    Vct4 cLine, cPolygon;
    
    /// flag set if defaults should be used for mesh generation
    bool bUseMgDefaults;
    
    /// used to switch surface display on/off 
    bool bVisible;
    
    /// true if viz grid coordinates are up2date 
    mutable bool bGridUp2date;
    
    /// for automatic color selection 
    static int lasthue;
};

typedef boost::shared_ptr<Component> ComponentPtr;

#endif

