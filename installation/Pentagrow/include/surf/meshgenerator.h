
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
 
#ifndef SURF_MESHGENERATOR_H
#define SURF_MESHGENERATOR_H

#include "forward.h"
#include "ttintersector.h"
#include "ttitopology.h"
#include "tticonnection.h"

/** Progress indicator and control for MeshGenerator.
 *
 * \ingroup meshgen
 * \sa MeshGenerator
 */
class MgProgressCtrl
{
  public:
    
    /// default controller counts only
    MgProgressCtrl() : step(0), nstep(0), bStop(false) {}
    
    /// virtual destructor
    virtual ~MgProgressCtrl() {}
    
    /// log steps as complete
    virtual void inc(uint k=1) {
      ScopedLock lock(guard);
      step += k;
    }
    
    /// access current state of progress
    virtual uint progress() const {return step;}
    
    /// register number of steps to perform
    virtual void nsteps(uint n) {nstep = n;}
    
    /// access number of steps to perform 
    virtual uint nsteps() const {return nstep;}
    
    /// query interrupt flag 
    virtual bool interrupt() const {return bStop;}
    
    /// set interrupt flag 
    virtual void interrupt(bool flag) {
      ScopedLock lock(guard);
      bStop = flag;
    }
    
  protected:
    
    /// synchronisation 
    Mutex guard;
    
    /// current step and number of steps 
    uint step, nstep;
    
    /// interruption flag 
    bool bStop;
};
 
/** Top-level mesh generator
  *
  * \ingroup meshgen
  * \sa DnMesh, MeshComponent
  */
class MeshGenerator : public TriMesh
{
  public:
      
    /// empty generator
    MeshGenerator() : TriMesh(), ppMergeTol(0.0), ppIter(0),
      bDropOrphanRidges(true), bDropInternal(true) {}

    /// virtual destructor
    virtual ~MeshGenerator() {}
    
    /// number of components defined
    uint ncomponents() const {return components.size();}
    
    /// add a mesh component
    uint addComponent(const MeshComponentPtr & mcp) {
      components.push_back(mcp);
      return components.size() - 1;
    }
    
    /// add a mesh component
    uint addComponent(const SurfacePtr & psf, 
                      const DnRefineCriterionPtr & rc) {
      MeshComponentPtr mcp;
      mcp = MeshComponentPtr(new MeshComponent(psf, rc));
      return addComponent(mcp);
    }
    
    /// erase component
    void eraseComponent(uint k) {
      assert(k < components.size());
      components.erase( components.begin()+k );
    }
    
    /// find component by surface name
    uint findComponent(const std::string & s) const;
    
    /// access component 
    MeshComponentPtr component(uint k) const {
      assert(k < components.size());
      return components[k];
    }
    
    /// register component connection
    void addConnection(const TTiConnection & ct) {
      connections.push_back(ct);
    }

    /// set mesh postprocessing options
    void postprocess(uint iter, Real maxStretch, Real maxPhi, Real mtol=0.0);
    
    /// toggle removal of singly-connected triangles (development)
    void toggleDropOrphanRidges(bool flag) {bDropOrphanRidges = flag;}

    /// toggle removal of internal triangles (development)
    void toggleDropInternal(bool flag) {bDropInternal = flag;}
    
    /// thread-safe component merge
    void mergeComponent(const TriMesh & mc);
    
    /// set progress indicator object
    void progressController(const MgProgressPtr & p) {prog = p;}
    
    /// access tag of surface named s
    uint findTag(const std::string & s) const;
    
    /// log progress and check for interrupt
    bool incProgress(uint k=1);

    /// interrupt process as soon as possible
    void interrupt();
    
    // high-level interface for CmpAssembly

    /// process complete assembly 
    void process(const CmpAssembly & asy, bool rflocal=true, ThreadPool *pool=0);
    
    /// premesh components from assembly (first mesh generation step)
    void preprocess(const CmpAssembly & asy, ThreadPool *pool = 0);
    
    /// process intersections
    void intersect(ThreadPool *pool = 0);
    
    /// perform local refinement after intersection processing
    void refineLocally(ThreadPool *pool = 0);
    
    /// refine globally after second intersection pass
    void refineGlobally(ThreadPool *pool = 0);
    
    /// low-level interface : determine component processing order
    void order();

    /// low-level interface : generate initial meshes for all surfaces
    void premesh();

    /// cleanup and drop internal triangles 
    void finalize();

    /// load raw surface collection as saved by sumo
    void loadCollection(const std::string & fname);
    
  protected:
    
    /// optional destretching pass
    void destretch();

    /// write current global mesh to file in debug mode
    void dbStoreMesh(const std::string & fname) const;
    
    /// determine list of external triangles to start with
    void searchExternalInit(Indices & itri) const; 
    
    /// re-assign face tags
    void retag();

    /// extract external part of all wakes and put into wkm
    void extractWakes(TriMesh & wkm);

  private:
    
    /// components
    MeshComponentArray components;
    
    /// component connections
    TTiConnectionArray connections;

    /// intersector
    TTIntersectorPtr ttip;
    
    /// intersection topology computer
    TTiTopology topo;
    
    /// guards access to merged mesh
    Mutex mgguard;
    
    /// global mesh postprocessing options
    Real ppMaxPhi, ppMaxStretch, ppMergeTol;
    
    /// number of postprocessing iterations
    uint ppIter;
    
    /// progress indicator 
    MgProgressPtr prog;
    
    /// store tag-to-surface name data
    StringArray tagmap;

    /// mesh processing order (to satisfy dependencies)
    Indices mgorder;

    /// options for final mesh processing (development)
    bool bDropOrphanRidges, bDropInternal;
};

#endif
