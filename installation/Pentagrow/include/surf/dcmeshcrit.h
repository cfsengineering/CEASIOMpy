
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
 
#ifndef SURF_DCMESHCRIT_H
#define SURF_DCMESHCRIT_H

#include "forward.h"
#include <genua/point.h>

/** Base class for mesh quality criteria.

  Mesh quality criteria for use with mapped 2D Delaunay procedures all
  inherit from this class. All mesh refinement implementation should only
  use the interface provided by this base class.

  \ingroup meshgen
  \sa DcMeshCrit, DcMeshHeightCrit
  */
class DcMeshCritBase
{
public:

  enum SplitFlag {NoSplit=0,
                  SplitEdge1=1, SplitEdge2=2, SplitEdge3=3,
                  InsertCircumCenter, InsertCircumCenterE1,
                  InsertCircumCenterE2, InsertCircumCenterE3,
                  InsertTriCenter,
                  TooSmall };

  /// create empty criterion
  DcMeshCritBase() : psf(0), ppuv(0), ppst(0), ppxy(0), ppnm(0),
                     omegaSmoothing(0.5), nSmoothing(0),
                     nInnerSmoothSkip(std::numeric_limits<uint>::max()),
                     nRefinePass(std::numeric_limits<uint>::max()),
                     nMaxNodeCount(std::numeric_limits<uint>::max()) {}

  /// virtual base class destructor
  virtual ~DcMeshCritBase() {}

  /// create a clone of the same type
  virtual DcMeshCritBasePtr clone() const = 0;

  /// attach to point lists
  virtual void assign(const Surface *srf,
                      const PointList<2> *uv, const PointList<2> *st,
                      const PointList<3> *xy, const PointList<3> *nm);

  /// change number of refinement passes
  void npass(uint n) {nRefinePass = n;}

  /// number of refinement passes allowed
  uint npass() const {return nRefinePass;}

  /// change max number of allowed nodes
  void maxNodes(uint n) {nMaxNodeCount = n;}

  /// access maximum number of nodes
  uint maxNodes() const {return nMaxNodeCount;}

  /// number of vertex smoothing iterations
  uint nSmooth() const {return nSmoothing;}

  /// number of vertex smoothing iterations
  void nSmooth(uint n) {nSmoothing = n;}

  /// one smoothing pass every skip refinement iterations
  void nSkipSmooth(uint skip) {nInnerSmoothSkip = skip;}

  /// one smoothing pass every skip refinement iterations
  uint nSkipSmooth() {return nInnerSmoothSkip;}

  /// relaxation factor for vertex smoothing
  Real wSmooth() const {return omegaSmoothing;}

  /// relaxation factor for vertex smoothing
  void wSmooth(Real w) {omegaSmoothing = w;}

  /// maximum permitted triangle growth ratio
  Real maxGrowthRatio() const {return maxGrowth;}

  /// maximum permitted triangle growth ratio
  void maxGrowthRatio(Real mgr) {maxGrowth = mgr;}

  /// determine whether to split a boundary edge
  virtual bool splitEdge(const Vct3 &ps, const Vct3 &pt,
                         const Vct3 &tgs, const Vct3 &tgt, Real bf = 1.0) const = 0;

  /// determine whether to split a curve on surface between ts and tt
  virtual bool splitEdge(const AbstractUvCurve &cuv, Real ts, Real tt) const;

  /// determine whether to split boundary edge (s,t)
  virtual bool splitEdge(uint s, uint t) const = 0;

  /// determine whether to split triangle (a,b,c)
  virtual int splitFace(uint a, uint b, uint c) const = 0;

  /// convenience shortcut
  int splitFace(const uint v[]) const {
    return this->splitFace(v[0], v[1], v[2]);
  }

  /// return whether to split va if it is too large for neighbor vb
  int checkGrowthRatio(const uint va[], const uint vb[]) const;

  /// determine circumcenter radius from triangle side lengths
  static Real ccRadius(const Real len[]) {
    Real a = len[0];
    Real b = len[1];
    Real c = len[2];
    Real s = 0.5*(a + b + c);
    Real t = s*(s - a)*(s - b)*(s - c);
    return 0.25*a*b*c / std::sqrt(t);
  }

protected:

  /// access vertex
  const Vct2 & puv(uint k) const {
    assert(ppuv != 0);
    return (*ppuv)[k];
  }

  /// access vertex
  const Vct2 & pst(uint k) const {
    assert(ppst != 0);
    return (*ppst)[k];
  }

  /// access vertex
  const Vct3 & pxy(uint k) const {
    assert(ppxy != 0);
    return (*ppxy)[k];
  }

  /// access vertex
  const Vct3 & pnm(uint k) const {
    assert(ppnm != 0);
    return (*ppnm)[k];
  }

protected:

  /// pointer to surface object for the evaluation of height criterion
  const Surface *psf;

  /// pointer to mesh vertices in (u,v) plane
  const PointList<2> *ppuv;

  /// pointer to mesh vertices in (s,t) plane
  const PointList<2> *ppst;

  /// pointer to mesh vertices in (x,y,z) space
  const PointList<3> *ppxy;

  /// pointer to surface normals at vertices
  const PointList<3> *ppnm;

  /// maximum permitted growth ratio
  Real maxGrowth;

  /// relaxation factor using for vertex smoothing
  Real omegaSmoothing;

  /// number of vertex smoothing iterations desired
  uint nSmoothing;

  /// smooth once every n refinement passes
  uint nInnerSmoothSkip;

  /// maximum number of refinement passes
  uint nRefinePass;

  /// maximum number of nodes accepted
  uint nMaxNodeCount;
};

/** Plain mesh quality criterion.

  This is a standard mesh quality criterion which takes both spatial and
  (s,t)-space properties into account. It may be rather expensive to
  evaluate due to the large number of geometric computations to perform,
  especially in the case of triangles which already conform to quality
  criteria.

  \ingroup meshgen
  \sa UvMapDelaunay
  */
class DcMeshCrit : public DcMeshCritBase
{
public:

  /// create empty criterion
  DcMeshCrit();

  /// virtual base class destructor
  virtual ~DcMeshCrit() {}

  /// create a clone of the same type
  virtual DcMeshCritBasePtr clone() const {
    return boost::make_shared<DcMeshCrit>(*this);
  }

  /// change lengths in (x,y,z) space
  void xyzLength(Real lmax, Real lmin = 0.0) {
    smaxLenXY = sq(lmax);
    sminLenXY = sq(lmin);
  }

  /// access squared minimum 3D space length
  Real sqMinLengthXyz() const {return sminLenXY;}

  /// access minimum 3D space length
  Real minLengthXyz() const {return std::sqrt(sminLenXY);}

  /// access squared maximum 3D space length
  Real sqMaxLengthXyz() const {return smaxLenXY;}

  /// access maximum 3D space length
  Real maxLengthXyz() const {return std::sqrt(smaxLenXY);}

  /// change lengths in (u,v) space
  void uvLength(Real lmax, Real lmin = 0.0) {
    smaxLenUV = sq(lmax);
    sminLenUV = sq(lmin);
  }

  /// change permitted u-projection
  void maxProjectionU(Real dumax) {pmaxU = dumax;}

  /// access permitted u-projection
  Real maxProjectionU() const {return pmaxU;}

  /// change maximum permitted vertex angle
  void maxNormalAngle(Real phimax) {
    minCosPhi = std::cos(phimax);
  }

  /// access maximum angle between vertex normals
  Real minCosNormalAngle() const {return minCosPhi;}

  /// change minimum permitted angle between sides
  void apexAngle(Real betamin, Real betamax = -1) {
    maxCosBeta = std::cos(betamin);
    if (betamax < betamin)
      betamax = M_PI - 2*betamin;
    minCosBeta = std::cos(betamax);
  }

  /// access apex angle
  Real maxCosApexAngle() const {return maxCosBeta;}

  /// apply a mesh density bias function in u-direction
  void ubias(uint k, Real factor, Real width = 0.25) {
    uBiasFactor[k] = factor;
    uBiasWidth[k] = width;
  }

  /// apply a mesh density bias function in u-direction
  void vbias(uint k, Real factor, Real width = 0.25) {
    vBiasFactor[k] = factor;
    vBiasWidth[k] = width;
  }

  /// test length criterion orthogonal to edge
  void testOrthogonalLength(bool flag) {checkOrthogonal = flag;}

  /// determine whether to split a curve on surface between ts and tt
  virtual bool splitEdge(const AbstractUvCurve &cuv, Real ts, Real tt) const;

  /// determine whether to split a boundary edge
  virtual bool splitEdge(const Vct3 &ps, const Vct3 &pt,
                         const Vct3 &tgs, const Vct3 &tgt, Real bf = 1.0) const;

  /// determine whether to split boundary edge (s,t)
  virtual bool splitEdge(uint s, uint t) const;

  /// determine whether to split triangle (a,b,c)
  virtual int splitFace(uint a, uint b, uint c) const;

  /// import from legacy (sumo 2.x) definition and map as well as possible
  void importLegacy(const XmlElement &xe);

  /// evaluate bias factor at (u,v) coordinates
  Real biasReduction(const Vct2 &q) const {
    const Real bpos[3] = {0.0, 0.5, 1.0};
    Real bf = 1.0;
    for (int k=0; k<3; ++k) {
      Real ub = perlinBias( uBiasFactor[k], uBiasWidth[k],
                            2.0*std::fabs(q[0] - bpos[k]) );
      Real vb = perlinBias( vBiasFactor[k], vBiasWidth[k],
                            2.0*std::fabs(q[1] - bpos[k]) );
      bf = std::min(bf, std::min(ub, vb));
    }
    return bf;
  }

protected:

  /// evaluate bias function
  static Real perlinBias(Real bias, Real width, Real x) {
    return bias + (1.0 - bias)*perlin_step( clamp(x/width, 0.0, 1.0) );
  }

protected:

  /// maximum permitted edge length in (x,y,z) space
  Real smaxLenXY;

  /// minimum acceptable edge length in (x,y,z) space
  Real sminLenXY;

  /// maximum permitted edge length in (u,v) space
  Real smaxLenUV;

  /// minimum acceptable edge length in (u,v) space
  Real sminLenUV;

  /// maximum permitted u-projection
  Real pmaxU;

  /// cosine of minimum angle between sides in (x,y,z) space
  Real maxCosBeta;

  /// cosine of maximum angle between sides in (x,y,z) space
  Real minCosBeta;

  /// cosine of maximum angle between vertex normals
  Real minCosPhi;

  /// mesh refinement bias parameters centered at 0.0, 0.5 and 1.0
  Real uBiasFactor[3], vBiasFactor[3];

  /// mesh refinement bias region width
  Real uBiasWidth[3], vBiasWidth[3];

  /// whether to consider length criterion normal to boundary
  bool checkOrthogonal;
};

/** Mesh quality based on deviation from surface.
 *
 * This criterion will split an edge or triangle if its midpoint deviates by
 * more than a prescribed distance from the corresponding continuous surface.
 * \sa DcMeshCritBase
 *
 * \ingroup meshgen
 */
class DcMeshHeightCrit : public DcMeshCritBase
{
public:

  /// initialize criterion
  DcMeshHeightCrit() : DcMeshCritBase(), smaxHeight(1.0) {}

  /// create a clone of the same type
  virtual DcMeshCritBasePtr clone() const {
    return boost::make_shared<DcMeshHeightCrit>(*this);
  }

  /// set maximum allowed distance from surface
  void tolerance(Real h) {smaxHeight = sq(h);}

  /// access maximum allowed distance from surface
  Real tolerance() const {return std::sqrt(smaxHeight);}

  /// determine whether to split a curve on surface between ts and tt
  virtual bool splitEdge(const AbstractUvCurve &cuv, Real ts, Real tt) const;

  /// determine whether to split a boundary edge
  virtual bool splitEdge(const Vct3 &ps, const Vct3 &pt,
                         const Vct3 &tgs, const Vct3 &tgt, Real bf = 1.0) const;

  /// determine whether to split boundary edge (s,t)
  virtual bool splitEdge(uint s, uint t) const;

  /// determine whether to split triangle (a,b,c)
  virtual int splitFace(uint a, uint b, uint c) const;

private:

  /// maximum allowed distance from surface
  Real smaxHeight;
};

/** Mesh refinement controlled by point or line sources.
 *
 * \sa DcMeshCritBase
 */
class DcMeshSourceCrit : public DcMeshCritBase
{
public:

  /// construct criterion w/o refinement
  DcMeshSourceCrit() : DcMeshCritBase(), m_gisl(NotDouble) {}

  /// create a clone of the same type
  virtual DcMeshCritBasePtr clone() const {
    return boost::make_shared<DcMeshSourceCrit>(*this);
  }

  /// define maximum edge length in unrefined regions
  void globalMaxLength(Real lmax) {m_gisl = 1.0 / sq(lmax);}

  /// add a point source
  uint addPointSource(const Vct3 &p, Real radius, Real factor) {
    m_points.push_back(p);
    m_psrd.push_back( 1.0 / sq(radius) );
    m_pref.push_back( factor );
    return m_points.size() - 1;
  }

  /// add a point source
  uint addLineSource(const Vct3 &ps, const Vct3 &pt,
                     Real radius, Real factor)
  {
    m_lines.push_back(ps);
    m_lines.push_back(pt);
    m_lsrd.push_back( 1.0 / sq(radius) );
    m_lref.push_back( factor );
    return m_lines.size() / 2;
  }

  /// determine whether to split a boundary edge
  virtual bool splitEdge(const Vct3 &ps, const Vct3 &pt,
                         const Vct3 &tgs, const Vct3 &tgt,
                         Real bf = 1.0) const;

  /// determine whether to split boundary edge (s,t)
  virtual bool splitEdge(uint s, uint t) const;

  /// determine whether to split triangle (a,b,c)
  virtual int splitFace(uint a, uint b, uint c) const;

private:

  /// determine refinement factor for point source k
  Real pointSource(uint k, const Vct3 & p) const {
    Real x = sq(p - m_points[k]) * m_psrd[k];
    return 1.0 + (m_pref[k] - 1.0)*sq(1.0 / (x + 1.0));
  }

  /// determine refinement factor for line source k
  Real lineSource(uint k, const Vct3 & p) const {
    const Vct3 &lp1( m_lines[2*k+0] );
    const Vct3 &lp2( m_lines[2*k+1] );
    Real t = clamp(dot(p - lp1, lp2 - lp1) / sq(lp2 - lp1), 0.0, 1.0);
    Vct3 foot = (1.0 - t)*lp1 + t*lp2;
    Real x = sq(p - foot) * m_lsrd[k];
    return 1.0 + (m_lref[k] - 1.0)*sq(1.0 / (x + 1.0));
  }

  /// maximum refinement factor for a pair of points
  Real factor(const Vct3 &pa, const Vct3 &pb) const;

  /// determine maximum factor for three points
  void factors(const Vct3 p[], Real f[]) const;

private:

  /// center points of point sources
  PointList<3> m_points;

  /// radius of influence for point sources
  Vector m_psrd;

  /// refinement factor for point sources
  Vector m_pref;

  /// two points for each line source
  PointList<3> m_lines;

  /// squared radius of influence for line sources
  Vector m_lsrd;

  /// refinement factor for line sources
  Vector m_lref;

  /// global inverse squared length criterion
  Real m_gisl;
};

class DcMeshMultiCrit : public DcMeshCritBase
{
public:

  /// create a clone of the same type
  virtual DcMeshCritBasePtr clone() const;

  /// append a new criterion
  void append(DcMeshCritBasePtr pmc);

  /// pass reference data down
  void assign(const Surface *srf,
              const PointList<2> *uv, const PointList<2> *st,
              const PointList<3> *xy, const PointList<3> *nm);

  /// determine whether to split a boundary edge
  bool splitEdge(const Vct3 &ps, const Vct3 &pt,
                 const Vct3 &tgs, const Vct3 &tgt, Real bf = 1.0) const;

  /// determine whether to split a curve on surface between ts and tt
  bool splitEdge(const AbstractUvCurve &cuv, Real ts, Real tt) const;

  /// determine whether to split boundary edge (s,t)
  bool splitEdge(uint s, uint t) const;

  /// determine whether to split triangle (a,b,c)
  int splitFace(uint a, uint b, uint c) const;

private:

  /// set of criteria to evaluate
  std::vector<DcMeshCritBasePtr> m_crits;
};

#endif // DCMESHCRIT_H
