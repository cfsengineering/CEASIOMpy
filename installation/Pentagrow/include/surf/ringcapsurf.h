
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
 
#ifndef SURF_RINGCAPSURF_H
#define SURF_RINGCAPSURF_H

#include "forward.h"
#include "transurf.h"

/** Ring-parameterized cap surface.
 *
 * This is a specialized surface based on a slope-continuous extension of
 * a tubular (u-periodic) main surface. The main intended application of this
 * class is to automatically generate small, well-formed smooth nose and
 * tail tip surfaces for elongated bodies which are G^1 continuous in the
 * u-direction.
 *
 * \todo
 * - How to avoid self-intersections for wavy boundaries?
 * - Modify center slope to permit convergent pointed tips
 *
 * \ingroup geometry
 * \sa TranSurf, LongCapSurf
 */
class RingCapSurf : public TranSurf
{
public:

  /// construct named surface
  RingCapSurf(const std::string & s = "Unknown") : TranSurf(s) {}

  /// construct flat surface from boundary points
  void init(const Surface & srf, const PointList<2> & qts, Real h=0);

  /// access boundary points in this surface's (u,v) space
  const PointList<2> & boundaryRing() const {return m_bnq;}

  /// initialize mesh generation
  void initMesh(const DnRefineCriterion & c, DnMesh & gnr) const;

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// generate a clone
  Surface *clone() const {return new RingCapSurf(*this);}

  /// generate initial mesh by paving
  void pavedMesh(PointList<2> &pts, Indices &tri) const;

private:

  /// construct flat surface from boundary points
  void initFlat(const Surface & srf, const PointList<2> & qts);

  /// construct G1 continuous dome from boundary points
  void initDome(const Surface & srf, const PointList<2> & qts, Real h);

private:

  /// mean boundary normal
  Vct3 meanNormal(const Vct3 & ctr, const PointList<3> & bp) const;

  /// smooth normal directions, single pass
  void smooth(PointList<3> & ni, int npass) const;

  /// generate a regularly spaced set of inward normals
  void flatNormals(const Vct3 & pn, const Vector & up,
                   PointList<3> & ni) const;

  // debug : write simple quad mesh to file
  void dump();

  /// smooth control point grid to avoid self-intersection
  void smoothCpGrid(int npass=1, Real omg=0.5);

  /// determine standard height factor
  Real stdFactor(const Vct3 & pn, const PointList<3> & nout) const;

private:

  /// map of the generating boundary points in parameter space
  PointList<2> m_bnq;
};

#endif // RINGCAPSURF_H
