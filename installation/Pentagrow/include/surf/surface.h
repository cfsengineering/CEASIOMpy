
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
 
#ifndef SURF_SURFACE_H
#define SURF_SURFACE_H

#include "forward.h"
#include <string>
#include <iosfwd>
#include <genua/svector.h>
#include <genua/trafo.h>
#include <genua/xmlelement.h>
#include <boost/enable_shared_from_this.hpp>

class MeshFields;

/** Surface interface.

  Abstract base class which defines the minimum interface of a surface
  implementation. Whenever possible, a reasonable default implementation for
  all non-pure virtual interfaces is provided. Nevertheless, it will usually
  be beneficial to override even these functions for best results.

  \ingroup geometry
  */
class Surface : public RFrame, public boost::enable_shared_from_this<Surface>
{
public:

  /** Surface size statistics. */
  struct DimStat {

    /// initialize struct
    DimStat() : area(0), nControlU(10), nControlV(10), nu(8), nv(8) {
      bblo = std::numeric_limits<Real>::max();
      bbhi = -bblo;
    }

    /// diagonal of the bounding box
    Real diagonal() const {return norm(bbhi - bblo);}

    /// total number of control points
    uint nControl() const {return nControlU*nControlV;}

    /// low and high corner of estimated bounding box
    Vct3 bblo, bbhi;

    /// rough estimate of surface area
    Real area;

    /// number of control points, set to 10 if nothing else is known
    uint nControlU, nControlV;

    /// resolution to use for estimation
    int nu, nv;
  };

  /// default initialization
  Surface(const std::string & s = "NoNameSurface");

  /// virtual destructor
  virtual ~Surface() {}

  /// access integer object id
  uint objid() const {return object_id;}

  /// change name
  void rename(const std::string & s) {ids = s;}

  /// return name
  const std::string & name() const {return ids;}

  /// evaluation interface
  virtual Vct3 eval(Real u, Real v) const = 0;

  /// utility interface
  virtual void eval(const PointList<2> & uv, PointList<3> & xyz) const;

  /// derive at (u,v)
  virtual Vct3 derive(Real u, Real v, uint du, uint dv) const = 0;

  /// compute point and tangent derivatives at (u,v), for efficiency
  virtual void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const;

  /// compute normal vector
  virtual Vct3 normal(Real u, Real v) const;

  /// compute curvature along v at u
  virtual Real vcurvature(Real u, Real v) const;

  /// compute curvature along u at v
  virtual Real ucurvature(Real u, Real v) const;

  /// compute Gaussian curvature
  virtual Real gaussianCurvature(Real u, Real v) const;

  /// find projection of pt on surface (needs a guess in q)
  virtual bool project(const Vct3 & pt, Vct2 & q,
                       Real tol=1e-6, Real dpmin=1e-6) const;

  /// find approximate intersection with curve c
  virtual bool intersect(const AbstractCurve &c, Vct2 &q, Real &t,
                         Real tol=1e-6, Real dpmin=1e-6) const;

  /// coordinate transformation
  virtual void apply() = 0;

  /// compute dimensional statistics
  virtual void dimStats(DimStat & stat) const;

  /// compute typical dimension
  Real typLength(int nu=8, int nv=8) const;

  /// create an unconstrained point grid as initialization for mesh generator
  virtual void initGrid(Real lmax, Real lmin, Real phimax, PointGrid<2> & pts) const;

  /// initialize mesh generator - default version uses initGrid
  virtual void initMesh(const DnRefineCriterion & c, DnMesh & gnr) const;

  /// create a triangular mesh for visualization
  virtual void tessellate(CgMesh & cgm, uint maxtri = 60000) const;

  /// XML output
  virtual XmlElement toXml(bool share=false) const = 0;

  /// XML input
  virtual void fromXml(const XmlElement & xe) = 0;

  /// append to IGES file and return the directory entry index, if implemented
  virtual int toIges(IgesFile & file, int tfi = 0) const;

  /// retrieve surface from IGES file, return false if not successfull
  virtual bool fromIges(const IgesFile & file,
                        const IgesDirEntry & entry);

  /// generate a clone
  virtual Surface *clone() const = 0;

  /// return shared-pointer from *this
  SurfacePtr self() {return shared_from_this();}

  /// static factory function
  static SurfacePtr createFromXml(const XmlElement & xe);

  /// static factory : create surface from IGES entity
  static SurfacePtr createFromIges(const IgesFile & file,
                                   const IgesDirEntry & entry);

  // protected:

  /// return an initial discretization pattern to start with [equidistant]
  virtual void initGridPattern(Vector & up, Vector & vp) const;

  /// return if surface is symmetric in u- or v-direction [false]
  virtual void isSymmetric(bool & usym, bool & vsym) const;

  /// debug : create simple visualization
  virtual void gridViz(MeshFields & mvz) const;

protected:

  /// determine local curvature given first and second derivative
  Real localCurvature(const Vct3 & dc, const Vct3 & ddc) const {
    Real  x1(dc[0]),  y1(dc[1]),  z1(dc[2]);
    Real x2(ddc[0]), y2(ddc[1]), z2(ddc[2]);
    Real t1 = sq(z2*y1 - y2*z1);
    Real t2 = sq(x2*z1 - z2*x1);
    Real t3 = sq(y2*x1 - x2*y1);
    Real t4 = cb( sqrt(sq(x1) + sq(y1) + sq(z1)) );
    return sqrt(t1 + t2 + t3) / t4;
  }

  /// apply a transformation retrieved from IGES file
  void applyIgesTrafo(const IgesFile & file, const IgesDirEntry & dir);

  /// retrieve name from IGES file
  void setIgesName(const IgesFile &file, const IgesEntity &e);

  /// generate new object id
  static uint nextObjectId();

protected:

  /// string identifier
  std::string ids;

  /// integer id used to find object in serialization
  uint object_id;
};

inline Surface *new_clone(const Surface & s)
{
  return s.clone();
}

inline bool operator< (const SurfacePtr &a, const SurfacePtr &b)
{
  return (a->objid() < b->objid());
}

inline bool operator< (const SurfacePtr &a, uint obid)
{
  return (a->objid() < obid);
}

inline bool operator< (uint obid, const SurfacePtr &b)
{
  return (obid < b->objid());
}

#endif
