
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
 
#ifndef SURF_NSTMESH_H
#define SURF_NSTMESH_H

#include <genua/hybridmesh.h>
#include <genua/boxsearchtree.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include "nstelements.h"
#include "nststressfield.h"

class MxMesh;

/** Nastran mesh

  This class handles nastran-specific finite elements. Most of the general
  geometry management is in its base class HybridMesh.
  
  \ingroup structures
  \sa NstReader, NstRecord, NstStressField
  */
class NstMesh : public HybridMesh
{
public:

  /// empty nastran mesh
  NstMesh() : HybridMesh() {}

  /// add a vertex with GID
  uint addVertex(const Vct3 & p, uint gid);

  /// locate a vertex index (not GID)
  uint nearest(const Vct3 & p) const {
    // assert(btree.size() == vtx.size());
    return btree.nearest(p);
  }

  /// create beam element
  uint addBeam(uint a, uint b, uint pid=1);

  /// make all DOFs in a depend on b
  uint rconnect(uint a, uint b);

  /// create a set of beam elements along newly inserted points, return first node
  uint addBeams(const PointList<3> & pts, uint pid=1);

  /// create triangular shell element
  uint addTriR(uint a, uint b, uint c, uint pid=1, uint mcid=0);

  /// create a quadrilateral shell element
  uint addQuadR(uint a, uint b, uint c, uint d, uint pid=1, uint mcid=0);

  /// add all triangles in triangular mesh
  void addTriangles(const TriMesh & t, NstTypeId tid=NstCTRIAR,
                    uint pid=1, uint mcid=0);

  /// add all quads from point grid
  void addQuads(const PointGrid<3> & pg, NstTypeId tid=NstCQUADR,
                uint pid=1, uint mcid=0);

  /// generate MPCs for a sliding hinge connection
  void addHinge(const Vct3 & ax, uint dep, uint idep);

  /// generate MPCs for a connection with free rotation
  void addJoint(uint dep, uint idep);

  /// generate a bolt connection
  void addBoltSpider(const PointList<3> & pa, const PointList<3> & pb);

  /// generate a bolt connection, return index of center point
  uint addBoltSpider(const PointList<3> & pa);

  /// generate a sliding bearing, return vertex to SPC.
  uint addSlidingBearing(const PointList<3> & pts, const Vct3 & pdir);

  /// access element k as given type, return cast success status
  template <class FElementType>
  bool as(uint k, FElementType **p) {
    assert(k < elements.size());
    *p = dynamic_cast<FElementType*>( elements[k].get() );
    return *p != 0;
  }

  /// access element k as given type, return cast success status
  template <class FElementType>
  bool as(uint k, const FElementType **p) const {
    assert(k < elements.size());
    *p = dynamic_cast<const FElementType*>( elements[k].get() );
    return *p != 0;
  }

  /// number of modeshapes present
  uint nmodes() const {return mz.size();}

  /// make space for modeshapes
  void resizeModes(uint n);

  /// swap in modeshape, do not touch generalized mass/stiffness
  void swapMode(uint i, Matrix & z);

  /// swap in modeshape
  void swapMode(uint i, Matrix & z, Real k, Real m=1.0);

  /// append vectors of modal data separately
  void generalized(const Vector &kg, const Vector &mg) {
    mgen = mg;
    kgen = kg;
  }

  /// append data for one mode
  void appendGeneralized(Real kg, Real mg) {
    mgen.push_back(mg);
    kgen.push_back(kg);
  }

  /// swap in displacements
  void appendDisp(Matrix & z);

  /// append flutter mode
  void appendFlutterMode(Complex p, const CpxVector &z) {
    flutterEigs.push_back(p);
    flutterEvals.push_back(z);
  }

  /// append a stress field
  size_t appendStress(const NstStressField &f) {
    sigma.push_back(f);
    return sigma.size() - 1;
  }

  /// merge compatible stress fields
  void mergeStressFields();

  /// access generalized stiffness values
  const Vector & gstiff() const {return kgen;}

  /// access generalized mass values
  const Vector & gmass() const {return mgen;}

  /// access modeshape
  const Matrix & modeShape(uint i) const {
    assert(i < mz.size());
    return mz[i];
  }

  /// access modeshape
  const MatrixArray & modeShapes() const {
    return mz;
  }

  /// compute connectivity and vertex search tree
  void fixate();

  /// merge nodes which are closer than threshold
  void cleanup(Real threshold);

  /// read nastran mesh (bulk) or modal result file (f06)
  void nstread(const std::string & fname);

  /// write output to text stream
  void nstwrite(std::ostream & os, int gidoffset=0, int eidoffset=0) const;

  // deprecated visualization
  void add2viz(MeshFields & mvz) const;

  /// convert to MxMesh
  void toMx(MxMesh & mx) const;

  /// access grid point ids (visualization/debugging)
  const Indices & gridids() const {return gids;}

  /// translate GID to vertex index
  uint gid2index(uint g, bool bailout=true) const {
    Indices::const_iterator pos;
    pos = std::lower_bound(gids.begin(), gids.end(), g);
    if (pos != gids.end() and *pos == g)
      return std::distance(gids.begin(), pos);
    else if (bailout) // send failure to find GID upstream
      throw Error("Nastran reader could not find GRID "+str(g));
    else
      return NotFound;
  }

  /// translate index to GID
  uint index2gid(uint i) const {
    assert(i < gids.size());
    return gids[i];
  }

private:

  /// grid id numbers of attached vertices
  Indices gids;

  /// generalized masses and stiffness values
  Vector mgen, kgen;

  /// eigenmode shapes: nm matrices sized nv-by-6
  MatrixArray mz, dsp;

  /// stress results
  std::vector<NstStressField> sigma;

  /// flutter eignemodes: npkz complex vectors nm long
  CpxVectorArray flutterEvals;

  /// flutter eigenvalues npkz complex scalars
  CpxVector flutterEigs;

  /// vertex search tree
  BSearchTree btree;
};

#endif
