
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
 
#ifndef SURF_DISPINTERPOLATOR_H
#define SURF_DISPINTERPOLATOR_H

#include "forward.h"
#include <genua/logger.h>
#include <genua/forward.h>
#include <genua/dvector.h>
#include <genua/svector.h>

/** Base class for displacement interpolation.
 *
 * The interpolator objects which inherit from this class are used to
 * interpolate displacement fields from structural meshes to other,
 * usually aerodynamic meshes using different strategies.
 *
 *
 * \ingroup mapping
 * \sa RbfInterpolator, SurfInterpolator
 */
class DispInterpolator : public Logger
{
public:

  typedef CsrMatrix<float,9>   MapMatrix;

  /// empty object
  DispInterpolator() : m_scale(1.0) {}

  /// base class
  virtual ~DispInterpolator() {}

  /// set structural mesh
  void setStructural(MxMeshPtr pmstr) {m_pstr = pmstr;}

  /// set aerodynamic mesh, which will be updated with deformation fields
  void setAerodynamic(MxMeshPtr pmaer) {m_paer = pmaer;}

  /// define the subset of aerodynamic nodes which are to be deformed
  void collectWallBocos(const Indices &movingBc,
                        const Indices &slidingBc = Indices(),
                        const Indices &rubberBc = Indices());

  /// define the subset of aerodynamic nodes which are to be deformed
  void collectWallSections(const Indices &movingSec,
                           const Indices &slidingSec = Indices(),
                           const Indices &rubberSec = Indices());

  /// define the subset of modes to use in terms of frequencies
  uint useEigenmodes(uint maxModeCount = NotFound, Real minFreq = -1.0,
                     Real maxFreq = std::numeric_limits<Real>::max() );

  /// change scale factor to used for displacements
  void dispScale(Real s) {m_scale = s;}

  /// access scale factor
  Real dispScale() const {return m_scale;}

  /// query the number of nodes to process
  uint nodesToMap() const {return m_mappedNodes.size();}

  /// implemented by child classes, return number of fields processed
  virtual uint map() = 0;

  /// construct mapping matrix H (optionally implemented)
  virtual void hmap(MapMatrix &) {}

  /// apply mapping matrix obtained by different means
  virtual uint map(const MapMatrix &H, DMatrix<float> &m);

  /// determine maximum permitted scale to avoid surface triangle inversion
  void maxBenignScale(Vector &maxscale) const;

  /// rescale all mapped fields to at least avoid triangle inversion
  void autoScale();

  /// add fields to aerodynamic mesh
  void appendFields(const DMatrix<float> &m);

  /// write surface displacement files for EDGE (.bdis)
  virtual void writeBdis(const std::string &prefix) const;

  /// pack mapping matrix H into FFA format
  virtual FFANodePtr mapToFFA(const MapMatrix &H) const;

  /// retreive mapping matrix H from FFA format file
  virtual bool mapFromFFA(const FFANodePtr &root, MapMatrix &H);

protected:

  /// collect wall nodes when mapped nodes not explicitely given
  void collectWallNodes();

  /// collect all fields marked as displacements or eigenmodes
  void collectDispFields();

  /// compute bounding box of mapped node set
  void boundingBox(Vct3 &plo, Vct3 &phi) const;

  /// mark sliding nodes
  void mergeSlidingNodes(const Indices &slidingNodes);

  /// determine the sliding plane normal from element
  Vct3 slidingNormal(uint eix) const;

  /// restrict displacements of sliding nodes
  void pinSlidingNodes(DMatrix<float> & dsp) const;

  /// restrict displacements of sliding nodes
  void pinSlidingNodes(MapMatrix &H) const;

  /// determine which aerodynamic elements are involved in mapping
  void findMappedElements(Indices &elix) const;

  /// assemble node-to-node connectivity of mapped aerodynamic nodes
  void mapAerTopology(const Indices &nodeSet, ConnectMap &v2v) const;

  /// determine all mapped aerodynamic nodes which are closer than threshold
  void nearbyNodes(Real threshold, const Indices &src, Indices &nbnodes) const;

  /// identify aerodynamic surface triangles for rubber sections
  void rubberTriangles(Indices &tri) const;

  /// apply smoothing to mapping matrix
  void smoothMap(int niter, float omega, const Indices &rnodes,
                 const ConnectMap &v2v, MapMatrix &H) const;

  /// used for debugging : create index sets
  uint appendNodeSet(const Indices &rnodes);

  /// flag fixed aerodynamic nodes which touch smoothed nodes
  void smoothedRegionRim(const ConnectMap &v2v,
                         const Indices &rnodes, Indices &rim) const;

  /// walk from k and find all in subset reachable within distance
  void bfsWalk(uint k, Real sqlmax, const ConnectMap &v2v,
               const Indices &subset, Indices &vnb) const;

  /// check whether aerodynamic element k is moving entirely (all nodes mapped)
  bool isMappedElement(uint k) const;

protected:

  /// data needed to enforce sliding condition
  struct SlidingNodeSet
  {
    Indices nodes;
    Vct3 normal;
    std::string boundaryName;
  };
  typedef std::vector<SlidingNodeSet> SlidingSet;

  /// structural mesh
  MxMeshPtr m_pstr;

  /// aerodynamic mesh
  MxMeshPtr m_paer;

  /// aerodynamic nodes to map
  Indices m_mappedNodes;

  /// aerodynamic nodes for which deformations will be extrapolated
  Indices m_rubberNodes;

  /// information used to enforce sliding conditions
  SlidingSet m_snset;

  /// indices of the aerodynamic mesh bocos (element sets) marked as moving
  Indices m_movingBocos, m_movingSections;

  /// indices of the aerodynamic mesh bocos (element sets) marked as moving
  Indices m_slidingBocos, m_slidingSections;

  /// indices of mesh sections marked as fixed
  Indices m_fixedBocos, m_fixedSections;

  /// indices of mesh sections/bocos marked as rubber sections
  Indices m_rubberBocos, m_rubberSections;

  /// indices of the resulting displacement fields in aerodynamic mesh
  Indices m_aerFields;

  /// indices of fields in structural mesh to use for mapping
  Indices m_strFields;

  /// modal mass and stiffness values
  Vector m_modalMass, m_modalStiffness;

  /// modal scaling factors computed by autoScale
  Vector m_autoScales;

  /// scale displacements by this global factor
  Real m_scale;  
};

#endif // DISPINTERPOLATOR_H
