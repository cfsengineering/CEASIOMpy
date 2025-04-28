
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
 
#ifndef SURF_FSIMESH_H
#define SURF_FSIMESH_H

#include <genua/mxmesh.h>
#include <genua/boxsearchtree.h>
#include <genua/connectmap.h>
#include <genua/csrmatrix.h>
#include <genua/atomicop.h>
#include <boost/shared_ptr.hpp>

class FsiElement;

/** Merged mesh for aeroelastic problems.

  FsiMesh contains meshes for both structural and aerodynamic domain
  solvers, along with data about the interface nodes.

  \todo
  - Change search for nearest fluid element to use search tree for all
    fluid elements.
  - Move distance computation (integration point in nearest element search)
    to element type or MxMesh.

    \ingroup mapping
  */
class FsiMesh
{
public:

  /// matrix mapping pressure values to nodal forces and moments
  typedef CsrMatrix<Real,6> PFMap;

  /// create empty mesh
  FsiMesh() : searchRadius(0.0), minCosPhi(-1.0), maxCosPhi(1.0) {}

  /// base class
  virtual ~FsiMesh() {}

  /// radius to search for aerodynamic mesh elements to project on
  Real catchRadius() const {return searchRadius;}

  /// radius to search for aerodynamic mesh elements to project on
  void catchRadius(Real r) {searchRadius = r;}

  /// maximum angle between normals of elements considered for projection
  Real maxNormalAngle() const {return acos(minCosPhi);}

  /// maximum angle between normals of elements considered for projection
  void maxNormalAngle(Real phi) {minCosPhi = cos(phi);}

  /// minimum angle between normals of elements considered for projection
  Real minNormalAngle() const {return acos(maxCosPhi);}

  /// minimum angle between normals of elements considered for projection
  void minNormalAngle(Real phi) {maxCosPhi = cos(phi);}

  /// access attached aerodynamic mesh
  const MxMesh & fluidMesh() const {assert(fmx); return *fmx;}

  /// access attached structural mesh
  const MxMesh & structMesh() const {assert(smx); return *smx;}

  /** Import sections of the structural mesh (Nastran). */
  void mergeStruct(const MxMeshPtr & pmx,
                   const Indices & pidwet = Indices(),
                   const Indices & pidintern = Indices());

  /** Import sections of the structural mesh (Nastran). */
  void mergeBeams(const MxMeshPtr & pmx);

  /** Import aerodynamic mesh. */
  void mergeFluid(const MxMeshPtr & pmx,
                  const Indices & ifboco = Indices());

  /// call after all meshes have been merged
  void buildInterpolator();

  /// access array of structural interface elements
  const Indices & structuralElements() const {return sifElix;}

  /// access array of structural interface nodes
  const Indices & structuralNodes() const {return sifNode;}

  /// access array of structural interface elements
  const Indices & fluidElements() const {return fifElix;}

  /// access array of structural interface nodes
  const Indices & fluidNodes() const {return fifNode;}

  /// access pressure field in fluid mesh
  bool extractPressure(Real qoo, uint ixf, Vector & pf) const;

  /// access pressure field in fluid mesh
  bool extractPressure(Real qoo, Vector & pf,
                       const std::string & fieldName = "CoefPressure") const;

  /// assemble pressure field by linear combination
  void assemblePressure(Real qoo, const Indices & ifield, const Vector & coef,
                        Vector & pf) const;

  /// agglomerate aerodynamic element loads into nearest structural node
  void agglomerate(const Vector & pf, PointList<6> & fnodal) const;

  /// agglomerate aerodynamic element loads into nearest structural node
  void agglomerate(const Matrix & mpf, PointGrid<6> & fnodal) const;

  /// integrate over structural elements
  void integrate(const Vector & pf, PointList<6> & fnodal) const;

  /// integrate over structural elements, multiple pressure fields
  void integrate(const Matrix & pf, PointGrid<6> & fnodal) const;

  /// establish a mapping matrix - not implemented yet
  // void mapping(PFMap & map) const;

  /// export nodal forces to nastran bulk data file
  uint exportForces(const PointList<3> & fnodal,
                    std::ostream &os, uint sid=1, Real ff=1.0) const;

  /// export nodal forces to nastran bulk data file
  uint exportForces(const PointList<3> & fnodal,
                    const std::string & fname, uint sid=1, Real ff=1.0) const;

  /// export nodal forces and moments to nastran bulk data file
  uint exportForces(const PointList<6> & fnodal,
                    std::ostream & os,
                    uint sid=1, Real ff=1.0, Real lf=1.0) const;

  /// export nodal forces and moments to nastran bulk data file
  uint exportForces(const PointList<6> & fnodal,
                    const std::string & fname,
                    uint sid=1, Real ff=1.0, Real lf=1.0) const;

  /// export nodal forces and moments from stored field to nastran bulk data
  uint exportForces(uint ifield, std::ostream & os,
                    uint sid=1, Real ff=1.0, Real lf=1.0) const;

  /// export a nodal load vector as a DAREA set for direct transient analysis
  uint exportDarea(uint sid, const PointList<6> & fnodal,
                   std::ostream & os, Real ff=1.0, Real lf=1.0) const;

  /// sum nodal forces and moments for a given reference point
  Vct6 sum(const Vct3 & ptref, const PointList<6> & fm) const;

  /// append nodal structural nodal force vector as a vector field
  uint appendSifField(const PointList<3> & fn,
                      const std::string & suffix = "");

  /// append nodal structural nodal force and moment vector as two vector fields
  void appendSifField(const PointList<6> & fn,
                      const std::string & suffix = "");

  /// residualize all stored load fields
  void residualizeLoads(const CsrMatrix<Real> & M);

  /// compute augmented states for MTA method
  void augmentedStates(const CsrMatrix<Real> & M, const CsrMatrix<Real> & K);

  /// overload clear
  virtual void clear();

  /// compute element centers and center forces (for moments)
  void centerForces(const Vector & pf,
                    PointList<3> & ctr, PointList<3> & cf) const;

  /// compute element centers and center forces (for moments)
  void centerForces(const Matrix & pf,
                    PointList<3> & ctr, PointGrid<3> & cf) const;

private:

  /// collect node indices
  void collectNodes(const MxMesh & mx, const Indices & elix,
                    Indices & nds) const;

  /// extract nastran GIDs
  void extractGids(const MxMesh & smx);

  /// build search tree for node set
  void buildTree(const MxMesh & mx, const Indices & idx,
                 BSearchTree & tree) const;

  /// build node-to-element mapping
  void buildMap(const MxMesh & mx, const Indices & nds, const Indices & elm,
                ConnectMap & v2emap) const;

  /// compute -p*normal for fluid element eix
  void evalPressure(const Vector & pf, uint eix,
                    const Vct2 & uv, Vct3 & psn) const;

  /// compute -p*normal for fluid element eix
  void evalPressure(const Matrix & pf, uint eix,
                    const Vct2 & uv, PointList<3> & psn) const;

  /// determine nearest element and element coordinates
  uint nearestFluidElement(const Vct3 & pt, Vct2 & uv) const;

  /// determine nearest element and element coordinates
  uint nearestFluidElement(const Vct3 & pt, const Vct3 & nrm, Vct2 & uv) const;

  /// collect fluid elements near an integration point
  void nearbyFluidElements(const Vct3 & pt, const Vct3 & nrm, Indices & elm) const;

  /// compute point-to-surface element distance and projection
  Real project(const Vct3 & pt, uint eix, Vct2 & uv) const;

  /// element projection for linear triangles
  Real projectTri3(const Vct3 & pt, const uint *vi, Vct2 & uv) const;

  /// update nodal force vector atomically
  template <int M>
  void atomicUpdate(uint inode, const SVector<M> & fj, PointList<M> & nf) const {
    uint jnode = sorted_index(sifNode, inode);
    if (jnode == NotFound)
      return;
    for (int k=0; k<M; ++k)
      atomic_add(nf[jnode][k], fj[k]);
  }

  /// update nodal force vector atomically
  template <int M>
  void atomicUpdate(uint inode, const SVector<M> & fj, uint jcol,
                    PointGrid<M> & nf) const {
    uint jnode = sorted_index(sifNode, inode);
    if (jnode == NotFound)
      return;
    for (int k=0; k<M; ++k)
      atomic_add(nf(jnode,jcol)[k], fj[k]);
  }

  /// compute moments about c
  Vct3 moment(const Vct3 & c,
              const PointList<3> & ctr, const PointList<3> & cf) const;

  /// compute sparsity pattern for mapping matrix
  void mappingPattern(ConnectMap & spty) const;

private:

  /// pointer to structural mesh
  MxMeshPtr smx;

  /// pointer to aerdynamic mesh
  MxMeshPtr fmx;

  /// indices of structural interface nodes
  Indices sifNode;

  /// indices of structural interface elements
  Indices sifElix;

  /// indices of fluid interface nodes
  Indices fifNode;

  /// indices of fluid interface elements
  Indices fifElix;

  /// nastran grid-point IDs for structIfNodes and all nodes
  Indices gids, allGids;

  /// search tree for fluid nodes
  BSearchTree fnTree;

  /// search tree for structural nodes
  BSearchTree snTree;

  /// connectivity from fluid nodes to elements
  ConnectMap fn2e;

  /// algorithm parameter : radius to search for nearby element nodes
  Real searchRadius;

  /// algorithm parameter : minimum and maximum cosine of angle between normals
  Real minCosPhi, maxCosPhi;

  friend class FsiElement;
  friend class FsiTri3;
  friend class FsiQuad4;
};

typedef boost::shared_ptr<FsiMesh> FsiMeshPtr;

#endif // FSIMESH_H
