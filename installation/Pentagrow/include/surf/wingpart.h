
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
 
#ifndef SURF_WINGPART_H
#define SURF_WINGPART_H

#include "forward.h"
#include "topopart.h"
#include <genua/svector.h>

/** Segmented lifting surface with wake.
 *
 *  Each wing segment surface is paramterized such that the u-parameter
 *  runs from the trailing edge along the upper side around the leading
 *  edge and back on the lower side. In order to achieve the canonical
 *  normal pointing outward, the v-direction runs from the right wing tip
 *  towards the left. The v=0 boundary of the second segment is connected to
 *  the v=1 boundary of the first segment, so that the first segment
 *  necessarily is located at the right tip.
 *
 *  Wakes are parameterized compatibly, so that the v-parameter of the wake
 *  runs along the spanwise direction from right tip towards the left and the
 *  u-direction starts at the trailing edge and increases downstream.
 *
 *  \ingroup meshgen
 *  \sa Surface, Topology
 */
class WingPart : public TopoPart
{
public:

  /// create empty default part
  WingPart(const std::string &s);

  /// can be base class
  virtual ~WingPart();

  /// configuration parameters
  void configure(const ConfigParser &cfg);

  /// change mesh bias properties to apply to mesh quality criteria internally
  void meshBias(Real leRefine, Real teRefine, Real tipRefine);

  /// set mesh quality criterion for wing and wake segments
  void meshQuality(DcMeshCritBasePtr wingCrit,
                   DcMeshCritBasePtr wakeCrit = DcMeshCritBasePtr());

  /// append segment to wing w/o wakes
  uint appendSegment(SurfacePtr wingSegment);

  /// append a new segment to the end
  uint appendSegment(SurfacePtr wingSegment, SurfacePtr wakeSegment);

  /// generate new segments mirrored about the plane mipo, mipn
  void mirrorSegments(const Vct3 &mipo = Vct3(0,0,0),
                      const Vct3 &mipn = Vct3(0,1,0));

  /// insert this part into the topology object
  virtual void inject(Topology &topo);

  /// generate flat tip caps (requires that edges are discretized), left: v=1
  std::pair<uint, uint> makeFlatCaps(Topology &topo,
                                     bool makeLeft=true, bool makeRight=true);

  /// generate elliptic tip caps (requires that edges are discretized), left: v=1
  std::pair<uint, uint> makeRoundedCaps(Topology &topo,
                                        bool makeLeft=true, bool makeRight=true);

  /// locate the end-cap boundary edge at v = 0 or v = 1
  uint findWingTipEdge(const Topology &topo, Real v) const;

  /// locate the wake edge at v = 0 or v = 1
  uint findWakeTipEdge(const Topology &topo, Real v) const;

  /// create wakes using the default cubic guide curves
  void createSimpleWakes(const Vct3 &edgeDistance = Vct3(),
                         const Vct3 &farTangent = Vct3(),
                         Real compression = 0.2);

  /// create wakes using body-attached guide curves
  void createAttachedWakes(SurfaceArray bodies,
                           const Vct3 &edgeDistance = Vct3(),
                           const Vct3 &farTangent = Vct3());

  /// append final face meshes to global (does no merge nodes)
  virtual void appendTo(const Topology &topo, MxMesh &mx, bool mergeBc=false);

  /// simplify import of legacy smx data
  virtual void importLegacy(const XmlElement &xe);

  /// generate cap surfaces for sumo 2.x geometry
  virtual void makeLegacyCaps(Topology &topo);

  /// export all surfaces to IGES
  void toIges(IgesFile &file, int tfi = 0) const;

private:

  /// cut up a stitched surface and add each segment
  DcMeshCritPtr appendStitched(const XmlElement &xe);

  /// generate default wake parameters if needed
  void fillDefaultDimensions(Vct3 &ed, Vct3 &ft) const;

  /// test whether a wake at v on segment iseg can be attached to body
  CurvePtr tryAttachWake(SurfacePtr body, int iseg, Real v,
                         const Vct3 &edgeDistance,
                         const Vct3 &farTangent) const;

private:

  /// segment surfaces of the wing
  SurfaceArray m_segments;

  /// one wake surface for each segment
  SurfaceArray m_wakes;

  /// indices of body faces and wake faces once added to topology
  Indices m_ifaces, m_iwakes;

  /// indices of bocos generated when adding to MxMesh object
  Indices m_ifbocos, m_iwbocos;

  /// meshing criterion used for all wing and wake segments
  DcMeshCritBasePtr m_wingCrit, m_wakeCrit;

  /// internally generated surfaces which close blunt trailing edges
  //SurfaceArray m_trailingEdgeCaps;

  /// length of the wake relative to bounding box dimensions
  Real m_relWakeLength;

  /// mesh bias options
  Real m_leBias, m_teBias, m_tipBias;

  /// maximum permitted edge length in terms of u-coordinate projection
  Real m_maxProjectedU;

  /// used for import of legacy surfaces
  Real m_capheight[4];

  /// indices of autogenerated tip caps, if any, generated by
  uint m_rightCap, m_leftCap;

  /// whether the first segment connects to the last (ring-wing)
  bool m_toroidal = false;

  /// trailing edge thickness switch (default false)
  bool m_bluntEdge = false;

  /// remember whether this was constructed from a mirrored surface
  bool m_fromSymSurf;
};

#endif // SURF_CHAINED_PART_H
