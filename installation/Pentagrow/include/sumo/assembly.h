
/* ------------------------------------------------------------------------
 * file:       assembly.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Collection of all surfaces belonging to a model
 * ------------------------------------------------------------------------ */

#ifndef SUMO_ASSEMBLY_H
#define SUMO_ASSEMBLY_H

#include "forward.h"

#include <boost/shared_ptr.hpp>
#include <genua/xmlelement.h>
#include <genua/trimesh.h>
#include <surf/assembly.h>
#include <surf/tetmesh.h>
#include "bodyskeleton.h"
#include "wingskeleton.h"
#include "ctsystem.h"
#include "jetenginespec.h"

/** Collection of components.

  */
class Assembly : public CmpAssembly
{
  public:

    /// initialization
    Assembly();

    /// access sumo component 
    ComponentPtr sumoComponent(uint i) const;
    
    /// cast component i to wing (returns zero on failure)
    WingSkeletonPtr asWing(uint i) const;
    
    /// cast component i to body (returns zero on failure)
    BodySkeletonPtr asBody(uint i) const;
    
    /// access surface, regardless of type
    SurfacePtr surface(uint i) const;
    
    /// compatibility interface: add body 
    uint addBody(const BodySkeletonPtr & sp);
    
    /// compatibility interface: add wing 
    uint addWing(const WingSkeletonPtr & sp);
    
    /// compatibility interface: access body
    BodySkeletonPtr body(uint i) const;
    
    /// compatibility interface: access wing
    WingSkeletonPtr wing(uint i) const;
    
    /// compatibility interface: count wings
    uint nwings() const;
    
     /// compatibility interface: count bodies
    uint nbodies() const;
    
    /// compatibility interface: check surface type
    bool isWing(uint i) const;
    
    /// erase component
    void erase(uint k);
    
    /// apply global scaling factor
    void globalScale(Real f);

    /// apply a global translation
    void globalTranslation(const Vct3 &trn);

    /// access control system representation
    const CtSystem & ctsystem() const {return csys;}
    
    /// access control system representation
    CtSystem & ctsystem() {return csys;}
    
    /// number of jet engine specifications 
    uint njet() const {return jes.size();}
    
    /// access engine spec i
    JetEngineSpec & jetEngine(uint i) {
      assert(i < jes.size());
      return jes[i];
    }
    
    /// access engine spec i
    const JetEngineSpec & jetEngine(uint i) const {
      assert(i < jes.size());
      return jes[i];
    }
    
    /// add jet engine 
    uint addJetEngine(const JetEngineSpec & je) {
      jes.push_back(je);
      return jes.size()-1;
    }
    
    /// remove jet engine spec 
    void removeJetEngine(uint i) {
      assert(i < jes.size());
      jes.erase(jes.begin() + i);
    }
    
    /// update engine specs after mesh generation 
    void updateJetEngines();
    
    /// generate surface mesh and postprocess result
    void processSurfaceMesh(const MgProgressPtr & mg);
    
    /// access volume mesh
    const TetMesh & volumeMesh() const {return tvm;}
    
    /// access volume mesh
    TetMesh & volumeMesh() {return tvm;}
    
    /// initialize boundary description in TetMesh
    void initMeshBoundaries(Real rfar, int nfar);

    /// test whether volume mesh is present
    bool hasVolumeMesh() const;
    
    /// transfer volume mesh
    void mxMesh(MxMeshPtr pmx) {mxm = pmx;}

    /// access general volume mesh
    const MxMesh & mxMesh() const {assert(mxm); return *mxm;}

    /// access mesh destretching options 
    int ppIterations() const {return ppIter;}
    
    /// access mesh destretching options 
    void ppIterations(int n) {ppIter = n;}
    
    /// access mesh destretching options 
    Real ppStretch() const {return ppMaxStretch;}
    
    /// access mesh destretching options 
    void ppStretch(Real s) {ppMaxStretch = s;}
    
    /// access mesh destretching options 
    Real ppGlobalMaxPhi() const {return ppMaxPhi;}
    
    /// access mesh destretching options 
    void ppGlobalMaxPhi(Real p) {ppMaxPhi = p;}

    /// access mesh vertex merge option
    Real ppMergeTolerance() const {return ppMergeTol;}

    /// access mesh vertex merge option
    void ppMergeTolerance(Real p) {ppMergeTol = p;}
    
    /// tetgen : farfield radius
    Real tgFarfieldRadius() const {return tgRadius;}
    
    /// change farfield radius parameter
    void tgFarfieldRadius(Real r) {tgRadius = r;}
    
    /// tetgen : tetrahedron quality
    Real tgTetQuality() const {return tgQuality;}
    
    /// change farfield radius parameter
    void tgTetQuality(Real q) {tgQuality = q;}
    
    /// estimate volume mesh parameters if not present
    void estimateTgParameters();
    
    /// delete all surfaces
    void clear();
    
    /// create xml representation
    XmlElement toXml() const;

    /// import from xml data
    void fromXml(const XmlElement & xe);

    /// import from xml data, add to current assembly
    void appendFromXml(const XmlElement & xe);
    
    /// load from file and replace current set
    void loadAndReplace(const std::string & fname);

    /// load from file and append to current set
    void loadAndAppend(const std::string & fname,
                       const Vct3 &trn = Vct3());
    
    /// save surface mesh for dwfs (xml)
    XmlElement toDwfsMesh();
    
    /// store as IGES file 
    void exportIges(const std::string & fname) const;
    
    /// construct xml surface descriptions
    XmlElement collectionXml() const;
    
  private:

    /// control system representation
    CtSystem csys;

    /// jet engine specifications 
    JetEngineSpecArray jes;
    
    /// tetrahedral mesh stored here TODO : remove
    TetMesh tvm;

    /// general volume mesh
    MxMeshPtr mxm;
    
    /// volume mesh generation parameters
    Real tgRadius, tgQuality;
};

#endif

