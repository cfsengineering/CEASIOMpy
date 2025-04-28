
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

#ifndef SURF_NSTELEMENTS_H
#define SURF_NSTELEMENTS_H

#include <genua/smatrix.h>
#include <genua/element.h>

typedef enum { NstCMASS=101,
               NstCONM,
               NstCELAS,
               NstCBEAM,
               NstCTRIA3,
               NstCTRIAR,
               NstCTRIA6,
               NstCQUAD4,
               NstCQUADR,
               NstCQUAD8,
               NstCHEXA,
               NstCTETRA,
               NstRBAR,
               NstRBE2,
               NstMPC,
               NstUndefined } NstTypeId;

typedef enum { NstGrounded=0,
               NstTransX=1,
               NstTransY=2,
               NstTransZ=3,
               NstRotX=4,
               NstRotY=5,
               NstRotZ=6,
               NstNoDof } NstDof;

class NstMesh;

#define PID_DONT_USE    NotFound 

/** Base class for NASTRAN finite elements.
 *
 * \ingroup structures
 * \sa NstMesh
 */
class NstElementBase
{
public:

  /// default construction
  NstElementBase(const NstMesh *m) : msh(m), propid(1), matcid(0) {}

  /// initialize undefined element
  NstElementBase() : msh(0), propid(1), matcid(0) {}

  /// intended as base class
  virtual ~NstElementBase() {}

  /// access property id
  uint pid() const {return propid;}

  /// set property id
  void pid(uint p) {propid = p;}

  /// access material coordinate system
  uint mcid() const {return matcid;}

  /// set property id
  void mcid(uint m) {matcid = m;}

  /// attach to mesh
  void mesh(const NstMesh *m) {msh = m;}

  /// access parent mesh
  const NstMesh & mesh() const {return *msh;}

  /// convert index to GID
  void index2gid(const Element & e, uint vg[]) const;

  /// change id offsets for writing
  static void indexOffsets(int gidoffset, int eidoffset);

protected:

  /// vertex index offset for output only
  static int s_vixoffset;

  /// element index offset for output only
  static int s_eixoffset;

private:

  /// pointer to parent mesh
  const NstMesh *msh;

  /// property id and material coordinate system
  uint propid, matcid;
};

/** Scalar mass element : CMASS2
 * \ingroup structures
 * \sa NstMesh
 */
class NstScalarMass : public Line2Element, public NstElementBase
{
public:

  /// construct with reference to node
  NstScalarMass(const NstMesh *m, uint a, uint b) : Line2Element(a,b),
    NstElementBase(m), mss(0.0)
  {
    vdof[0] = vdof[1] = 1;
  }

  /// set dofs
  void dof(NstDof da, NstDof db) {
    vdof[0] = uint(da);
    vdof[1] = uint(db);
  }

  /// access mass value
  Real mass() const {return mss;}

  /// access mass value
  void mass(Real m) {mss = m;}

  /// return id code
  uint idtype() const {return uint(NstCMASS);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;

private:

  /// dofs to attach to
  uint vdof[2];

  /// mass value
  Real mss;
};

/** Concentrated mass element : CONM2
 * \ingroup structures
 * \sa NstMesh
 */
class NstConMass : public PointElement, public NstElementBase
{
public:

  /// construct with reference to node
  NstConMass(const NstMesh *m, uint a) :
    PointElement(a), NstElementBase(m), mss(0.0) {}

  /// access mass value
  Real mass() const {return mss;}

  /// access mass value
  void mass(Real m) {mss = m;}

  /// set rotational inertia
  void setJ(const Mtx33 & J) {mj = J;}

  /// access offset coordinates
  const Vct3 & offset() const {return poff;}

  /// set coordinate offset
  void offset(const Vct3 & p) {poff = p;}

  /// return id code
  uint idtype() const {return uint(NstCONM);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;

private:

  /// scalar mass
  Real mss;

  /// inertia matrix
  Mtx33 mj;

  /// offset
  Vct3 poff;
};

/** Scalar spring element : CELAS2
 * \ingroup structures
 * \sa NstMesh
 */
class NstSpring : public Line2Element, public NstElementBase
{
public:

  /// construct with reference to node
  NstSpring(const NstMesh *m, uint a, uint b) : Line2Element(a,b),
    NstElementBase(m), mk(0.0)
  {
    vdof[0] = vdof[1] = 1;
  }

  /// set dofs
  void dof(NstDof da, NstDof db) {
    vdof[0] = uint(da);
    vdof[1] = uint(db);
  }

  /// access stiffness value
  Real stiffness() const {return mk;}

  /// access mass value
  void stiffness(Real k) {mk = k;}

  /// return id code
  uint idtype() const {return uint(NstCELAS);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;

private:

  /// dofs to attach to
  uint vdof[2];

  /// stiffness value
  Real mk;
};

/** Rigid bar element: RBAR
 * \ingroup structures
 * \sa NstMesh
 */
class NstRigidBar : public Line2Element, public NstElementBase
{
public:

  /// construct with geometry
  NstRigidBar(const NstMesh *m, uint a, uint b) :
    Line2Element(a,b), NstElementBase(m), cna(0), cnb(0), cma(0), cmb(0) {}

  /// set component DOF codes
  void components(uint na, uint nb, uint ma, uint mb) {
    cna = na; cnb = nb; cma = ma; cmb = mb;
  }

  /// return id code
  uint idtype() const {return uint(NstRBAR);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;

private:

  /// component numbers
  uint cna, cnb, cma, cmb;
};

/** MPC pseudo-element for two points.
 * \ingroup structures
 * \sa NstMesh
 */
class NstSimpleMpc : public Line2Element, public NstElementBase
{
public:

  /// construct with geometry
  NstSimpleMpc(const NstMesh *m, uint a, uint b) :
    Line2Element(a,b), NstElementBase(m), sid(1)
  {
    std::fill(adof, adof+6, NotFound);
    std::fill(bdof, bdof+6, NotFound);
  }

  /// assign to set-id s
  void setid(uint s) {sid = s;}

  /// define single equation
  void constrain(NstDof ad, Real ac, NstDof bd, Real bc) {
    adof[0] = uint(ad);
    bdof[0] = uint(bd);
    acf[0] = ac;
    bcf[0] = bc;
  }

  /// define up to six equations
  void constrain(uint c, NstDof ad, Real ac, NstDof bd, Real bc) {
    assert(c < 6);
    adof[c] = uint(ad);
    bdof[c] = uint(bd);
    acf[c] = ac;
    bcf[c] = bc;
  }

  /// return id code
  uint idtype() const {return uint(NstMPC);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;

private:

  /// coefficients of constraint equation
  Real acf[6], bcf[6];

  /// set id and DOFs to constrain
  uint adof[6], bdof[6], sid;
};

/** Beam element : CBEAM
 * \ingroup structures
 * \sa NstMesh
 */
class NstBeam : public Line2Element, public NstElementBase
{
public:

  /// construct with reference to node
  NstBeam(const NstMesh *m, uint a, uint b) :
    Line2Element(a,b), NstElementBase(m) {}

  /// change orientation
  void orientation(const Vct3 & o) {orn = o;}

  /// return id code
  uint idtype() const {return uint(NstCBEAM);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;

private:

  /// beam orientation vector
  Vct3 orn;
};

/** Triangular shell element : CTRIA3
 * \ingroup structures
 * \sa NstMesh
 */
class NstTria3 : public Tri3Element, public NstElementBase
{
public:

  /// construct with reference to node
  NstTria3(const NstMesh *m, uint a, uint b, uint c) :
    Tri3Element(a,b,c), NstElementBase(m) {}

  /// return id code
  uint idtype() const {return uint(NstCTRIA3);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;
};

/** Triangular shell element : CTRIAR
 * \ingroup structures
 * \sa NstMesh
 */
class NstTriaR : public Tri3Element, public NstElementBase
{
public:

  /// construct with reference to node
  NstTriaR(const NstMesh *m, uint a, uint b, uint c) :
    Tri3Element(a,b,c), NstElementBase(m) {}

  /// return id code
  uint idtype() const {return uint(NstCTRIAR);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;
};

/** Triangular shell element : CTRIA6
 * \ingroup structures
 * \sa NstMesh
 */
class NstTria6 : public Tri6Element, public NstElementBase
{
public:

  /// construct with reference to node
  NstTria6(const NstMesh *m, const uint v[]) :
    Tri6Element(v), NstElementBase(m) {}

  /// return id code
  uint idtype() const {return uint(NstCTRIA6);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;
};

/** Quadrilateral shell element : CQUAD4
 * \ingroup structures
 * \sa NstMesh
 */
class NstQuad4 : public Quad4Element, public NstElementBase
{
public:

  /// construct with reference to node
  NstQuad4(const NstMesh *m, uint a, uint b, uint c, uint d) :
    Quad4Element(a,b,c,d), NstElementBase(m) {}

  /// return id code
  uint idtype() const {return uint(NstCQUAD4);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;
};

/** Quadrilateral shell element : CQUADR
 * \ingroup structures
 * \sa NstMesh
 */
class NstQuadR : public Quad4Element, public NstElementBase
{
public:

  /// construct with reference to node
  NstQuadR(const NstMesh *m, uint a, uint b, uint c, uint d) :
    Quad4Element(a,b,c,d), NstElementBase(m) {}

  /// return id code
  uint idtype() const {return uint(NstCQUADR);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;
};

/** Quadrilateral shell element : CQUAD8
 * \ingroup structures
 * \sa NstMesh
 */
class NstQuad8 : public Quad8Element, public NstElementBase
{
public:

  /// construct with reference to nodes
  NstQuad8(const NstMesh *m, uint v[]) : Quad8Element(v), NstElementBase(m) {}

  /// return id code
  uint idtype() const {return uint(NstCQUAD8);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;
};

/** Hexahedral element solid element : CHEXA
  * \ingroup structures
  * \sa NstMesh
  */
class NstHexa : public HexElement, public NstElementBase
{
public:

  /// construct with reference to nodes
  NstHexa(const NstMesh *m, uint v[], uint nv=20) : HexElement(v, nv), NstElementBase(m) {}

  /// return id code
  uint idtype() const {return uint(NstCHEXA);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;
};

/** Tetrahedral element solid element : CTETRA
 * \ingroup structures
 * \sa NstMesh
 */
class NstTetra : public TetraElement, public NstElementBase
{
public:

  /// construct with reference to nodes
  NstTetra(const NstMesh *m, uint v[], uint nv=10) : TetraElement(v, nv), NstElementBase(m) {}

  /// return id code
  uint idtype() const {return uint(NstCTETRA);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;
};

/** Rigid-body element of type RBE2.

  RBE2 broadcasts the displacement of one independent node to an arbitrary
  number of dependent nodes.

  \ingroup structures
  \sa NstMesh
 */
class NstRigidBody2 : public Element, public NstElementBase
{
public:

  /// construct: v[0] is the number of nodes, v[1] the independent node
  NstRigidBody2(const NstMesh *m, uint c, const Indices & v) :
    Element(), NstElementBase(m), vi(v), cm(c)
  {
    Element::changeBase(&vi[0]);
  }

  /// return id code
  uint idtype() const {return uint(NstRBE2);}

  /// append to text stream
  void nstwrite(std::ostream & os) const;

  /// draw as lines
  uint add2viz(MeshFields & m) const;

  /// independent node (first in nastran card)
  uint indepNode() const {assert(vi.size() > 1); return vi[1];}

  /// number of dependent nodes
  uint ndep() const {return vi.empty() ? 0 : vi.size()-1;}

  /// dependent node k
  uint depNode(uint k) const {assert(k+1 < vi.size()); return vi[k+1];}

private:

  /// mesh vertex indices (not gids)
  Indices vi;

  /// component numbers of depedent grid points
  uint cm;
};


#endif


