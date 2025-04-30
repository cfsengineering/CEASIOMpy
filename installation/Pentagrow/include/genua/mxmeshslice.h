
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
 
#ifndef GENUA_MXMESHSLICE_H
#define GENUA_MXMESHSLICE_H

#include "forward.h"
#include "mxmesh.h"

/** Container for slice through MxMesh.

  \ingroup mesh
  \sa MxMesh
*/
class MxMeshSlice
{
public:

  /// empty slice object
  MxMeshSlice(const MxMeshPtr pm = MxMeshPtr()) : pmsh(pm),
    bSliceVolume(false), bSliceSurface(true), bInPlane(true) {}

  /// access referenced mesh
  MxMeshPtr mesh() const {return pmsh;}

  /// slice volume elements?
  void volumeElements(bool flag) {bSliceVolume = flag;}

  /// slice surface elements?
  void surfaceElements(bool flag) {bSliceSurface = flag;}

  /// create a slice from three points
  void slice(const Vct3 & po, const Vct3 & pu, const Vct3 & pv);

  /// number of sliced elements
  uint nsliced() const {return ice.size();}

  /// try to connect geometrically close segment endpoint
  void joinSegments(Real threshold);

  /// mark sliced elements in mesh
  void markSlicedElements(MxMesh & mx) const;

  /// number of connected segments found
  uint nsegments() const {
    return seqstart.empty() ? 0 : seqstart.size()-1;
  }

  /// segment length
  uint size(uint ks) const {
    assert(ks < nsegments());
    return seqstart[ks+1] - seqstart[ks];
  }

  /// column names for output data
  void columns(StringArray & names) const;

  /// slice data (x,y,z,field1,field2,...) for one segment
  void sliceData(uint iseg, Matrix & m) const;

  /// write plain text output
  void writePlain(uint iseg, const std::string & fname) const;

  /// write plain text output for all segments
  void writePlain(const std::string & fname) const;

  /// write a matlab function which makes all segments available
  void writeMatlab(const std::string & funcName,
                   const std::string & fileName) const;

  /// delete last slice
  void clear();

private:

  typedef std::vector<bool> Tags;

  /// construct edges from intersected elements
  void toEdges(Indices & edg) const;

  /// filter elements
  void filter();

  /// edge-based sorting
  void sortByEdges();

  /// determine vertex to start a sequence
  uint firstVertex(const Tags & vtag) const;

  /// determine next vertex to use
  uint nextVertex(uint cur, const ConnectMap & v2v,
                  const Tags & vtag) const;

  /// compute local coordinates
  void project(uint k, Vct3 & p) const {
    Vct3 r(pmsh->node(k) - org);
    p[0] = dot(Su,r) * ilu;
    p[1] = dot(Sv,r) * ilv;
    p[2] = dot(pnrm,r);
  }

  /// determine intersection parameters
  Real isecParameter(uint v1, uint v2) const {
    Real h0 = uvh[v1][2];
    Real h1 = uvh[v2][2];
    assert(h0*h1 <= 0.0);
    Real dh = h0 - h1;
    return (fabs(dh) > 0) ? (h0 / dh) : h0;
  }

private:

  /// sliced mesh
  MxMeshPtr pmsh;

  /// parametric directions of the surface
  Vct3 org, Su, Sv, pnrm;

  /// inverse axis scales
  Real ilu, ilv;

  /// global indices of sliced elements and vertices
  Indices ice, ivtx, vseq;

  /// mark start of connected sequence segments
  Indices seqstart;

  /// plane coordinates (u,v,h) of vertices
  PointList<3> uvh;

  /// flags
  bool bSliceVolume, bSliceSurface, bInPlane;
};

#endif // MXMESHSLICE_H
