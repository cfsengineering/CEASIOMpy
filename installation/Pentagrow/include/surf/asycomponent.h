
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

#ifndef SURF_ASYCOMPONENT_H
#define SURF_ASYCOMPONENT_H

#include "forward.h"
#include "endcap.h"
#include <genua/xmlelement.h>
#include <boost/shared_ptr.hpp>

/** Base class for top-level components.

  A component (for sumo) is a single continuous surface and the associated
  end closure descriptions and mesh generation parameters.

  \todo Move to sumo
  
  \ingroup meshgen
  \sa CmpAssembly
*/
class AsyComponent
{
public:

  typedef enum {CapULo=0, CapUHi=1, CapVLo=2, CapVHi=3} CapSide;

  /// undefined surface
  AsyComponent();

  /// virtual destructor
  virtual ~AsyComponent() {}

  /// check if surface is defined
  bool defined() const {return (main.get() != 0);}

  /// check if any cap was intersected
  //bool capIntersected() const {return bCapIntersected;}

  /// access name
  const std::string & name() const {
    assert(defined());
    return main->surface()->name();}

  /// set main mesh component
  void component(const MeshComponentPtr & mcp) {main = mcp;}

  /// set main surface
  void surface(const SurfacePtr & s);
  
  /// access main surface
  const SurfacePtr & surface() const {
    assert(defined());
    return main->surface();}

  /// access main surface
  void surface(const SurfacePtr & s) const {
    assert(defined());
    main->surface(s);}

  /// access mesh criterion
  const DnRefineCriterionPtr & criterion() const {
    assert(defined());
    return main->criterion();}

  /// access mesh criterion
  void criterion(const DnRefineCriterionPtr & c) {
    assert(defined());
    main->criterion(c);}

  /// access main surface mesh tag
  uint mainTag() const {return maintag;}

  /// access main surface mesh tag
  void mainTag(uint t) {maintag = t;}

  /// access end cap surface mesh tag
  uint capTag(uint k) const {
    assert(k < 4);
    return ecaps[k].tag();
  }

  /// access end cap surface mesh tag
  void capTag(uint k, uint t) {
    assert(k < 4);
    ecaps[k].tag(t);
  }

  /// mark surface as changed
  void surfaceChanged() {
    assert(defined());
    main->surfaceChanged();
  }

  /// use algorithm to generate streched mesh
  void stretchedMesh(bool flag) {
    assert(defined());
    main->stretchedMesh(flag);}

  /// access anisotropic mesh setting
  bool stretchedMesh() const {
    assert(defined());
    return main->stretchedMesh();}

  /// set number of smoothing iterations and factor
  void smoothing(uint nsm, Real wsm) {
    assert(defined());
    main->smoothingFactor(wsm);
    main->smoothingIterations(nsm);}

  /// access kink limiter
  void kinkLimit(Real k) {main->kinkLimit(k);}

  /// access kink limiter
  Real kinkLimit() const {return main->kinkLimit();}

  /// retrieve cap mesh component
  const MeshComponentPtr & cap(CapSide s) const {
    return ecaps[(int) s].component();
  }

  /// register cap
  void endCap(const EndCap & c);

  /// access end cap
  const EndCap & endCap(uint k) const {
    assert(k < 4);
    return ecaps[k];
  }

  /// access end cap
  EndCap & endCap(uint k) {
    assert(k < 4);
    return ecaps[k];
  }

  /// generate a long cap at s (axial parametrization)
  void endCap(CapSide s, EndCap::Shape shape, Real h);

  /// change translation transformation
  void translation(const Vct3 & t) {sTrn = t;}

  /// access translation transformation
  const Vct3 & translation() const {return sTrn;}

  /// change rotation transformation
  void rotation(const Vct3 & r) {sRot = r;}

  /// access rotation transformation
  const Vct3 & rotation() const {return sRot;}

  /// add to mesh generator
  void append(MeshGenerator & mg);

  /// adapt caps to main surfaces after refinement
  void adaptCaps();

  /// overload: create a sensible default mesh criterion
  virtual void defaultCriterion();

  /// generate initialization grid, provided by surface by default
  virtual void buildInitGrid(PointGrid<2> & pgi);

  /// write as XML
  virtual XmlElement toXml() const;

  /// retrieve from XML
  virtual void fromXml(const XmlElement & xe);

protected:

  /// apply transformation to surfaces
  void transform();

  /// generate cap surfaces (involves premeshing)
  void generateCaps();

protected:

  /// main surface
  MeshComponentPtr main;

  /// end caps (possibly 4)
  EndCap ecaps[4];

  /// transformation
  Vct3 sTrn, sRot, sScl;

  /// tags received after mesh generation
  uint maintag;
};



#endif
