
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
 
#ifndef SURF_SMWINGMESH_H
#define SURF_SMWINGMESH_H

#include "forward.h"
#include "smribmesh.h"

class NstMesh;
class SmWingMesh;

extern int nearest_index(const Vector & a, Real b);

/** Description of control surface structure. 
  
  This struct contains the parameters to define a single control surface
  with multiple hinges and a single actuation attachment, which is currently
  always located at the inboard hinge.

  Scalar mass and stiffness properties can be defined in order to model the
  properties of the internal actuation mechanism.

  \ingroup structures
  \sa SmWingMesh
*/
struct SmControlSurf
{
public:

  /// construct default control surface
  SmControlSurf(Real v1, Real v2, Real hxc, uint shell, uint rib) :
    vlo(v1), vhi(v2), xc(hxc), pidshell(shell), pidrib(rib),
    pidwingrib(0), nhinge(4), cmass(0.0), cspring(0.0) {}

  /// lower and upper limits in terms of spanwise coordinate
  Real vlo, vhi;

  /// chordwise location of the hinge line (x/c)
  Real xc;

  /// shell property (PID) for upper/lower surface
  uint pidshell;

  /// shell property (PID) for inside ribs
  uint pidrib;

  /// shell property (PID) for local wing rib (default 0=none)
  uint pidwingrib;

  /// number of hinges in spanwise direction
  uint nhinge;

  /// scalar mass and attachment spring
  Real cmass, cspring;

  /// control surface name
  std::string id;

private:

  uint itop, ibot, iv1, iv2;
  Vct3 psact, pwact, hax;
  PointList<3> phinge;

  friend class SmWingMesh;
};

/** Template for wing mesh generation.

  SmWingMesh encapsulates a template for the generation of a structured
  Nastran mesh for wing surfaces. The mesh has a fixed topology, namely
  a leading edge region with constant properties along the span; a single
  wingbox with front and rear spar with configurable properties which can
  vary arbitrarily along the span; a trailing edge region with constant
  properties, and any number of control surfaces described by SmControlSurf.

  \ingroup structures
  \sa SmBodyMesh, SmRibMesh
*/
class SmWingMesh
{
public:

  /// initialize with surface
  SmWingMesh(SurfacePtr s) : m_psf(s), m_xbox1(0.25), m_xbox2(0.65) {}

  /** Define wing-box limits.
    \param xc1 Chordwise coordinate (x/c) of front box spar
    \param xc2 Coordinate (x/c) of rear box spar */
  void wingBox(Real xc1, Real xc2) {m_xbox1=xc1; m_xbox2=xc2;}

  /// generate control surface (basic form)
  uint setTrailingEdgeFlap(Real v1, Real v2, Real hxc,
                           uint pidshell, uint pidrib);

  /// generate control surface (general form)
  uint setTrailingEdgeFlap(const SmControlSurf & cs);

  /** Spar web properties.
    \param matcoord MCID for spar web properties
    \param pweb PID of the box spar webs
    \param ple PID of leading and trailing edge regions */
  void setWebPid(uint pweb, uint ple, uint matcoord=0) {
    m_mcid = matcoord;
    m_pid_web = pweb;
    m_pid_lete = ple;
  }

  /** Define an additional wing-box skin property region.
    \param vlim Chordwise coordinate limit for this PID
    \param pid Shell element property ID */
  void addBoxPid(Real vlim, uint pid) {
    m_pid_vlimits.push_back(vlim);
    m_pid_wingbox.push_back(pid);
  }

  /** Generate mesh grid.
    \param nv Number of grid points in spanwise direction (v)
    \param nle Number of grid points along the leading edge segment
    \param nwb Number of grid points used for the wing box cover skins
    \param nte Number of grid points for the trailing edge segment
    \param nweb Number of points across the spar web (uneven) */
  void grid(uint nv, uint nle, uint nwb, uint nte, uint nweb=5);

  /// grid row index nearest to span coordinate v
  uint rowIndex(Real v) const {
    return nearest_index(m_vp, v);
  }

  /// access main shell grid vertex
  const Vct3 & vertex(uint i, uint j) const {return m_pgrid(i,j);}

  /// row index positions of the wing box cap limits
  void wingBoxRows(uint idx[]) const {
    idx[0] = m_giwb2_up;
    idx[1] = m_giwb1_up;
    idx[2] = m_giwb1_lo;
    idx[3] = m_giwb2_lo;
  }

  /// add quad elements to Nastran mesh
  void addQuads(NstMesh & nst);

  /** Generate a chordwise rib.
    \param vi Spanwise grid row index where to insert rib
    \param mid MCID of the shell elements
    \param pid Shell property ID to use */
  uint createRib(uint vi, uint pid=0, uint mid=0);

  /// access rib
  SmRibMesh & rib(uint irib) {
    assert(irib < m_ribs.size());
    return m_ribs[irib];
  }

  /** Locate possible connection points.
    Call this for vi where ribs were generated in order to retrieve
    points suitable for all-directional point load introduction.
    \param vi Spanwise grid row index
    \param pcon Location of 4 points where spars intersect row vi */
  void findConnectors(uint vi, PointList<3> & pcon) const;

  /// generate control surface xml description for dwfs
  void appendControls(XmlElement & xe) const;

private:

  /// locate leading edges
  void initLE();

  /// locate relative position on upper side
  Real findUpper(uint iv, Real xc, Real utol=1e-4) const;
  
  /// locate relative position on lower side
  Real findLower(uint iv, Real xc, Real utol=1e-4) const;

  /// test is wing is symmetric
  bool isMirrored() const;

  /// generate control surface quads
  void addControlQuads(NstMesh & nst, Real gap);

  /// generate joints between flaps and main wing
  void connectFlaps(NstMesh & nst) const;

private:

  /// surface object
  SurfacePtr m_psf;

  /// v-positions
  Vector m_vp;

  /// u-positions
  VectorArray m_up;

  /// u-value at leading-edge
  Vector m_ule, m_umean;

  /// point grids for wingbox webs
  PointGrid<3> m_pgrid, m_mweb, m_rweb;

  /// wing box limits in terms of chord
  Real m_xbox1, m_xbox2;

  /// grid dimensions
  uint m_giwb2_up, m_giwb1_up, m_giwb1_lo, m_giwb2_lo;

  /// property IDs
  uint m_mcid, m_pid_lete, m_pid_web;

  /// wingbox cap PIDs
  Vector m_pid_wingbox, m_pid_vlimits;

  /// control surface cutout definitions
  std::vector<SmControlSurf> m_flaps;

  /// ribs (possibly with cutouts)
  std::vector<SmRibMesh> m_ribs;
};

#endif
