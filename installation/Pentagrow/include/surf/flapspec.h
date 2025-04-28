
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
 
#ifndef SURF_FLAPSPEC_H
#define SURF_FLAPSPEC_H

#include <genua/point.h>
#include <genua/xmlelement.h>

class MxMesh;

/** Geometrical specification of control surface.

  FlapSpec contains the geometric data needed to identify a control surface with
  multiple segments. The data stored is the minimum low-level information
  required to identify mesh nodes and generate transpiration boundary conditions
  which can be used to determine small-displacement loads resulting from
  control surface deflections.

  \ingroup geometry
  \sa MxMesh
  */
class FlapSpec
{
public:

  typedef std::vector<Indices> NodeIndexSet;

  /// empty, invalid flap spec
  FlapSpec(const std::string & s = "") : sid(s), balanceExtension(0.0) {}

  /// change name
  void rename(const std::string & s) {sid = s;}

  /// access name
  const std::string & name() const {return sid;}

  /// number of segments present
  uint nsegments() const {return hp.empty() ? 0 : hp.size()-1;}

  /// extend flap by adding another segment
  void addSegment(const Vct3 & hingePoint, const Vct3 & endPoint) {
    hp.push_back( hingePoint );
    ep.push_back( endPoint );
  }

  /// access hinge point k
  const Vct3 & hingePoint(uint k) const {return hp[k];}

  /// access hinge point k
  const Vct3 & endPoint(uint k) const {return ep[k];}

  /// access extension parameter used to model aerodynamic balancing
  Real balancing() const {return balanceExtension;}

  /// access extension parameter used to model aerodynamic balancing
  void balancing(Real balex) {balanceExtension = balex;}

  /// create an element group for each flap segment
  void createBoco(MxMesh & mx, NodeIndexSet & segNodes) const;

  /// create a displacement field for positive deflection of each segment
  void createDisplacement(MxMesh & mx, const NodeIndexSet & segNodes) const;

  /// create a displacement field for positive deflection of each segment
  void createDisplacement(const MxMesh & mx, uint iseg, const Indices & segNodes,
                          PointList<3> & dsp, Real fseg = 1.0) const;

  /// export to XML format
  XmlElement toXml(bool share = false) const;

  /// retrieve from XML format
  void fromXml(const XmlElement & xe);

private:

  /// collects nodes associated with a certain BC type (e.g. wall BC)
  static void collectBcElements(const MxMesh & mx, int bc, Indices & ielm);

  /// collects nodes used by any type of surface element
  static void collectSurfaceElements(const MxMesh & mx, Indices & ielm);

  /// extract nodes from element set
  static void nodesFromElements(const MxMesh & mx, const Indices & ielm,
                                Indices & inodes);

private:

  /// flap identifier
  std::string sid;

  /// hinge points
  PointList<3> hp;

  /// end points, i.e. trailing edge for TE flaps
  PointList<3> ep;

  /// extension of the flap beyond the hinge line (balancing)
  Real balanceExtension;
};

/** Holds a set of flap geometry specifications along with deflection patterns.
  */
class FlapSpecSet
{
public:

  struct Pattern {
  public:

    /// create empty pattern
    Pattern() {}

    /// append a participating flap
    void append(const std::string & flap, Real f = 1.0, uint iseg = 0) {
      flaps.push_back(flap);
      segments.push_back(iseg);
      factors.push_back(f);
    }

    /// clear out entire pattern
    void clear() {
      flaps.clear();
      segments.clear();
      factors.clear();
    }

    /// create XML representation
    XmlElement toXml(bool share=false) const;

    /// recover from XML representation
    void fromXml(const XmlElement & xe);

    std::string name;
    StringArray flaps;
    Indices segments;
    Vector factors;
  };

  /// empty flap set
  FlapSpecSet() {}

  /// number of flap geometries defined
  uint nflaps() const {return flaps.size();}

  /// determine flap index from name
  uint findFlap(const std::string & s) const;

  /// access flap geometry
  const FlapSpec & flap(uint k) const {return flaps[k];}

  /// append a flap geometry specification
  uint append(const FlapSpec & f) {
    flaps.push_back(f);
    return flaps.size()-1;
  }

  /// access flap deflection pattern
  const Pattern & pattern(uint k) const {return patterns[k];}

  /// append a pattern specification
  uint append(const Pattern & p) {
    patterns.push_back(p);
    return patterns.size()-1;
  }

  /// create displacement fields for all patterns
  void createDisplacements(MxMesh & mx) const;

  /// create XML representation
  XmlElement toXml(bool share) const;

  /// recover from XML representation
  void fromXml(const XmlElement & xe);

private:

  /// control surface definitions
  std::vector<FlapSpec> flaps;

  /// each pattern
  std::vector<Pattern> patterns;
};

#endif // FLAPSPEC_H
