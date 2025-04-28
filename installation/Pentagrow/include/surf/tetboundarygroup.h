
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
 
#ifndef SURF_TETBOUNDARYGROUP_H
#define SURF_TETBOUNDARYGROUP_H

#include <vector>
#include <string>
#include <genua/ffanode.h>
#include <genua/dmatrix.h>
#include <genua/svector.h>

//#ifdef HAVE_CGNS
#include <genua/cgnsfwd.h>
class CgnsZone;
//#endif

class TriMesh;
class TetFace;
typedef std::vector<TetFace> TetFaceArray;

/** Boundary condition in a tetrahedral mesh.
 *
 * \deprecated
 */
class TetBoundaryGroup
{
public:

  enum BCondition {BcWall, BcFarfield, BcNacelleInlet, BcNacelleOutlet,
                   BcMassFlowInlet, BcMassFlowOutlet,
                   BcEulerTransp, BcUser};

  typedef DMatrix<int> IndexMatrix;
  typedef DVector<int> IndexVector;

  /// empty boundary group
  TetBoundaryGroup() : bc(BcWall), pratio(1.0), tratio(1.0), epsfan(0.5) {}
  
  /// extract group from TriMesh
  TetBoundaryGroup(const TriMesh & m, int tag);

  /// determine face list from tags
  void capture(const TetFaceArray & tfa);

  /// imprint boundary tag on faces
  void enforce(TetFaceArray & tfa) const;

  /// face index list
  void facelist(const IndexVector & v, int offset);

  /// access tag
  void tag(int t) {itag = t;}

  /// access tag
  int tag() const {return itag;}

  /// group name
  const std::string & name() const {return bname;}

  /// rename group
  void rename(const std::string & s) {bname = s;}

  /// number of triangles in this boundary group
  uint size() const {return ifaces.size();}

  /// access triangle indices
  uint face(uint k) const { assert(k < ifaces.size()); return ifaces[k]; }

  /// access BC tag
  BCondition boundaryCondition() const {return bc;}

  /// change boundary condition tag
  void boundaryCondition(BCondition b) {bc = b;}

  /// set BC and BC data for nacelle inlet
  void nacelleInlet(Real eps);

  /// set BC and BC data for nacelle outlet
  void nacelleOutlet(Real pr, Real tr);

  /// set BC data for massflow inlet (edge)
  void mdotInflow(Real tmf, Real tt, const Vct3 & direction);

  /// set BC data for massflow outflow (edge)
  void mdotOutflow(Real tmf);

  /// append data to FFA mesh data structure
  void ffamsh(const TetFaceArray & faces, FFANode & node) const;

  /// append data to FFA boundary data structure
  void ffaboc(FFANode & node) const;

  //#ifdef HAVE_CGNS

  /// assimilate CGNS boundary condition
  void cgnsBoundaryCondition(cgns::BCType_t b);

  /// write as cgns boundary condition set
  void writeCgnsBoco(CgnsZone & z, int offset);

  //#endif // HAVE_CGNS

private:

  /// collect vertex indices
  void collectVertices(const TetFaceArray & faces,
                       IndexMatrix & vertices,
                       bool sensible_ordering) const;

private:

  /// list of triangles belonging to this group
  IndexVector ifaces;

  /// boundary name/identifier
  std::string bname;

  /// integer tag associated with this group
  int itag;

  /// type of boundary condition to enforce
  BCondition bc;

  /// flow direction for mass flow BCs
  Vct3 fdir;

  /// boundary condition data for Edge nacelle BCs
  Real pratio, tratio, epsfan, mdot, ttotal;
};

typedef std::vector<TetBoundaryGroup> BGroupArray;

#endif
