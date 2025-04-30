
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
 
#ifndef GENUA_MXMESHDEFORM_H
#define GENUA_MXMESHDEFORM_H

#include "mxannotated.h"
#include "dmatrix.h"
#include "splinebasis.h"
#include "point.h"

class MxMesh;

/** Represent time-domain subspace mesh deformation.

  MxMeshDeform contains a time history of deformations expressed as a linear
  combination of a set of basis functions.

  \ingroup mesh
  \sa MxMesh
  */
class MxMeshDeform : public MxAnnotated
{
  public:
    
    /// construct undefined deformation shape
    MxMeshDeform(const MxMesh *pm = 0)
      : MxAnnotated(), parent(pm), moffset(0) {}
    
    /// retrieve shape name
    const std::string & name() const {return id;}
    
    /// change name
    void rename(const std::string & s) {id = s;}
    
    /// number of time history values present
    uint ntime() const {return bptime.size();}
    
    /// access time breakpoint i
    Real time(uint i) const {return bptime[i];}
    
    /// duration of this motion
    Real duration() const {
      assert(not bptime.empty());
      return bptime.back() - bptime.front();
    }

    /// number of displacement values per time
    uint nmodes() const {return bpcoef.nrows();}

    /// determine if the trajectory contains rigid-body modes
    bool isFlightPath() const {
      return ((moffset == 6) or (moffset == 12));
    }
    
    /// retrieve interpolated subspace deformation at t 
    bool interpolateSubspace(Real t, Vector & dss) const;
     
    /// evaluate first and second time derivatives at t
    bool interpolateSubspace(Real t, Vector & x,
                             Vector & xd, Vector & xdd) const;

    /// generate TABLED1 input card for NASTRAN
    void writeTable(uint tid, uint npoints, uint imode, std::ostream & os) const;

    /// apply elastic (modal) deformation to mesh vertices
    void deformElastic(Real scale, const Vector & dss,
                            PointList<3> & vdef) const;

    /// compute path of CoG
    void flightPath(const Vct3 & CoG, Real width,
                    Real scale, PointList<3,float> & path) const;

    /// apply rigid-body transformation to vdef
    Mtx33 rbTransform(const Vct3 & CoG, Real scale,
                      const Vector & dss, PointList<3> & vdef) const;
    
    /// check if spline is present
    bool hasSpline() const {return cpcoef.size() > 0;}
    
    /// construct a cubic spline interpolation
    void buildSpline();
    
    /// estimate maximum displacement at scale 1.0
    Real estimateMaxDisplacement() const;
    
    /// set shape directly
    void setDeformation(const Indices & im, const Vector & t, 
                        const Matrix & tdef);
    
    /// assemble shape by sampling complex flutter mode shape
    void fromFlutterMode(const Indices & im, Complex p, 
                         const CpxVector & z, uint nsample=32);
    
    /// convert to xml representation
    XmlElement toXml(bool share=false) const;
    
    /// retrieve data from xml representation
    void fromXml(const XmlElement & xe);

    /// retrieve data from plain text file
    void readPlain(const std::string & fname,
                   const Indices &useCols = Indices());
    
  private:
    
    /// determine index of first elastic state
    void elasticOffset();
    
  private:
    
    /// reference to parent mesh
    const MxMesh *parent;
    
    /// identifies the deformation shape
    std::string id;
    
    /// indices of vector fields which contain subspace 
    Indices isub;
    
    /// time points for deformation values
    Vector bptime;
    
    /// complex coefficients for subspace modes
    Matrix bpcoef, cpcoef;
    
    /// spline basis for interpolation
    SplineBasis spl;
    
    /// index offset : modal states begin here
    int moffset;    
};

#endif
