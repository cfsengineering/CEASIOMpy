
/* Copyright (C) 2016 David Eller <david@larosterna.com>
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

#include "plane.h"
#include "ffanode.h"
#include "mxmesh.h"
#include "mxmeshsection.h"
#include "mxmeshboco.h"
#include "mxmeshtypes.h"
#include "cgnssection.h"
#include "cgnsfwd.h"
#include "algo.h"
#include "dbprint.h"

using namespace std;

const uint MxMeshSection::npelm[] = {0, 1, 2, 3, 3, 6, 4, 8, 9, 
                                     4, 10, 5, 14, 8, 20, 27,
                                     6, 15, 18};

void MxMeshSection::usedNodes(Indices & ipts) const
{
  ipts = inodes;
  sort_unique(ipts);
}

int MxMeshSection::triangleVertices(int vi[]) const
{  
  const int vqd8[12] = {0,4,7, 5,4,1, 7,6,3, 6,5,2};
  const int vtr6[12] = {0,3,5, 5,3,4, 4,3,1, 4,2,5};
  const int vtet[12] = {0,2,1, 0,1,3, 0,3,2, 1,2,3};
  const int vtet10[48] = { 0,4,7, 7,4,8, 8,4,1, 7,8,3,
                           0,6,7, 7,6,9, 9,6,2, 7,9,3,
                           1,8,5, 5,8,9, 5,9,2, 9,8,3 };
  const int vpyr[12] = {0,1,4, 1,2,4, 2,3,4, 0,4,3};
  const int vpen[6] = {0,1,2, 3,5,4};
  
  switch (etype) {
  case Mx::Undefined:
  case Mx::Point:
  case Mx::Line2:
  case Mx::Line3:
    return 0;
  case Mx::Tri3:
    if (vi != 0)
      for (int k=0; k<3; ++k)
        vi[k] = k;
    return 1;
  case Mx::Tri6:
    if (vi != 0)
      for (int k=0; k<12; ++k)
        vi[k] = vtr6[k];
    return 4;
  case Mx::Quad4:
    return 0;
  case Mx::Quad8:
    if (vi != 0)
      for (int k=0; k<12; ++k)
        vi[k] = vqd8[k];
    return 4;
  case Mx::Quad9:
    return 0;
  case Mx::Tet4:
    if (vi != 0)
      for (int k=0; k<12; ++k)
        vi[k] = vtet[k];
    return 4;
  case Mx::Tet10:
    if (vi != 0)
      for (int k=0; k<48; ++k)
        vi[k] = vtet10[k];
    return 16;
  case Mx::Pyra5:
  case Mx::Pyra14:
    if (vi != 0)
      for (int k=0; k<12; ++k)
        vi[k] = vpyr[k];
    return 4;
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
    return 0;
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
    if (vi != 0)
      for (int k=0; k<6; ++k)
        vi[k] = vpen[k];
    return 2;
  case Mx::NElmTypes:
    return 0;
  };
  
  return 0;
}

int MxMeshSection::quadVertices(int vi[]) const
{
  const int vqd8[4] = {4,5,6,7};
  const int vqd9[16] = {0,4,8,7, 8,4,1,5, 8,5,2,6, 8,6,3,7};
  const int vpyr[4] = {0,3,2,1};
  const int vpen[12] = {0,3,4,1, 1,4,5,2, 0,2,5,3};
  const int vhex[24] = {0,3,2,1, 0,1,5,4, 4,5,6,7, 7,6,2,3, 1,2,6,5, 0,4,7,3};

  switch (etype) {
  case Mx::Undefined:
  case Mx::Point:
  case Mx::Line2:
  case Mx::Line3:
  case Mx::Tri3:
  case Mx::Tri6:
    return 0;
  case Mx::Quad4:
    if (vi != 0)
      for (int k=0; k<4; ++k)
        vi[k] = k;
    return 1;
  case Mx::Quad8:
    if (vi != 0)
      for (int k=0; k<4; ++k)
        vi[k] = vqd8[k];
    return 1;
  case Mx::Quad9:
    if (vi != 0)
      for (int k=0; k<16; ++k)
        vi[k] = vqd9[k];
    return 4;
  case Mx::Tet4:
  case Mx::Tet10:
    return 0;
  case Mx::Pyra5:
  case Mx::Pyra14:
    if (vi != 0)
      for (int k=0; k<4; ++k)
        vi[k] = vpyr[k];
    return 1;
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
    if (vi != 0)
      for (int k=0; k<24; ++k)
        vi[k] = vhex[k];
    return 6;
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
    if (vi != 0)
      for (int k=0; k<12; ++k)
        vi[k] = vpen[k];
    return 3;
  case Mx::NElmTypes:
    return 0;
  };
  
  return 0;
}

int MxMeshSection::lineVertices(int vi[]) const
{
  const int vtr6[12] = {0,3, 3,1, 1,4, 4,2, 2,5, 5,0};
  const int vtri[6] = {0,1, 1,2, 2,0};
  const int vqd4[8] = {0,1, 1,2, 2,3, 3,0};
  const int vqd8[16] = {0,4, 4,1, 1,5, 5,2, 2,6, 6,3, 3,7, 7,0};
  const int vtet[12] = {0,1, 1,2, 2,0, 0,3, 1,3, 2,3};
  const int vpyr[16] = {0,1, 1,2, 2,3, 3,0, 0,4, 1,4, 2,4, 3,4};
  const int vpen[18] = {0,1, 1,2, 2,0, 4,5, 5,3, 3,4, 1,4, 2,5, 0,3};
  const int vhex[24] = {0,1, 1,2, 2,3, 3,0, 4,5, 5,6, 6,7,
                        7,4, 0,4, 1,5, 2,6, 3,7};
  const int vtet10[24] = {0,4, 4,1, 1,8, 8,3, 3,7, 7,0,
                          1,5, 5,2, 2,9, 9,3, 0,6, 6,2};

  switch (etype) {
  case Mx::Undefined:
  case Mx::Point:
    return 0;
  case Mx::Line2:
    if (vi != 0) {
      vi[0] = 0;
      vi[1] = 1;
    }
    return 1;
  case Mx::Line3:
    if (vi != 0) {
      vi[0] = 0;
      vi[1] = 2;
    }
    return 1;
  case Mx::Tri3:
    if (vi != 0)
      for (int k=0; k<6; ++k)
        vi[k] = vtri[k];
    return 3;
  case Mx::Tri6:
    if (vi != 0)
      for (int k=0; k<12; ++k)
        vi[k] = vtr6[k];
    return 6;
  case Mx::Quad4:
    if (vi != 0)
      for (int k=0; k<8; ++k)
        vi[k] = vqd4[k];
    return 4;
  case Mx::Quad8:
  case Mx::Quad9:
    if (vi != 0)
      for (int k=0; k<16; ++k)
        vi[k] = vqd8[k];
    return 8;
  case Mx::Tet4:
    if (vi != 0)
      for (int k=0; k<12; ++k)
        vi[k] = vtet[k];
    return 6;
  case Mx::Tet10:
    if (vi != 0)
      for (int k=0; k<24; ++k)
        vi[k] = vtet10[k];
    return 12;
  case Mx::Pyra5:
  case Mx::Pyra14:
    if (vi != 0)
      for (int k=0; k<16; ++k)
        vi[k] = vpyr[k];
    return 8;
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
    if (vi != 0)
      for (int k=0; k<24; ++k)
        vi[k] = vhex[k];
    return 12;
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
    if (vi != 0)
      for (int k=0; k<18; ++k)
        vi[k] = vpen[k];
    return 9;
  case Mx::NElmTypes:
    return 0;
  };
  
  return 0;
}

int MxMeshSection::triangleMap(Mx::ElementType etype, const int *map[])
{
  // mapping between element nodes and triangle vertices
  static const int map_tri3[] = {0,1,2};
  static const int map_tri6[] = {0,3,5, 5,3,4, 4,3,1, 4,2,5};
  static const int map_quad4[] = {0,1,2, 2,3,0};
  static const int map_quad8[] = {0,4,7, 4,5,7, 1,5,4,
                           2,6,5, 5,6,7, 3,7,6};
  static const int map_tet4[] =  { 0,1,2, 1,3,2, 0,2,3, 0,3,1 };
  static const int map_hexa8[] = { 0,1,2, 0,2,3,
                            2,6,7, 3,2,7,
                            2,5,6, 1,2,5,
                            4,7,6, 4,6,5,
                            0,4,1, 1,4,5,
                            0,3,7, 0,7,4 };

  switch (etype) {
  case Mx::Tri3:
    *map = map_tri3;
    return 1;
  case Mx::Tri6:
    *map = map_tri6;
    return 4;
  case Mx::Quad4:
    *map = map_quad4;
    return 2;
  case Mx::Quad8:
    *map = map_quad8;
    return 6;
  case Mx::Tet4:
    *map = map_tet4;
    return 4;
  case Mx::Hex8:
    *map = map_hexa8;
    return 12;
  default:
    return 0;
  }
}

bool MxMeshSection::toTriangles(Indices &tri) const
{
  // mapping between element nodes and triangle vertices
  const int map_tri3[] = {0,1,2};
  const int map_tri6[] = {0,3,5, 5,3,4, 4,3,1, 4,2,5};
  const int map_quad4[] = {0,1,2, 2,3,0};
  const int map_quad8[] = {0,4,7, 4,5,7, 1,5,4,
                           2,6,5, 5,6,7, 3,7,6};
  const int map_tet4[] =  { 0,1,2, 1,3,2, 0,2,3, 0,3,1 };
  const int map_hexa8[] = { 0,1,2, 0,2,3,
                            2,6,7, 3,2,7,
                            2,5,6, 1,2,5,
                            4,7,6, 4,6,5,
                            0,4,1, 1,4,5,
                            0,3,7, 0,7,4 };

  const int *map(0);
  int ntri(0);
  switch (elementType()) {
  case Mx::Tri3:
    map = map_tri3;
    ntri = 1;
    break;
  case Mx::Tri6:
    map = map_tri6;
    ntri = 4;
    break;
  case Mx::Quad4:
    map = map_quad4;
    ntri = 2;
    break;
  case Mx::Quad8:
    map = map_quad8;
    ntri = 6;
    break;
  case Mx::Tet4:
    map = map_tet4;
    ntri = 4;
    break;
  case Mx::Hex8:
    map = map_hexa8;
    ntri = 12;
    break;
  default:
    return false;
  }

  size_t offset(0);
  const size_t nsel = nelements();
  Indices stri(ntri*nsel*3);
  for (size_t j=0; j<nsel; ++j) {
    const uint *v = element(j);
    for (int k=0; k<ntri; ++k) {
      stri[offset+0] = v[map[3*k+0]];
      stri[offset+1] = v[map[3*k+1]];
      stri[offset+2] = v[map[3*k+2]];
      offset += 3;
    }
  }
  tri.insert(tri.end(), stri.begin(), stri.end());

  return true;
}

bool MxMeshSection::estimateNormals(PointList<3> &nrm) const
{
  assert(parent != 0);
  const PointList<3> & nds( parent->nodes() );
  const int ne = nelements();

  switch (etype) {
  case Mx::Undefined:
  case Mx::Point:
  case Mx::Line2:
  case Mx::Line3:
    return false;
  case Mx::Tri3:
  case Mx::Tri6:
    nrm.resize(ne);
#pragma omp parallel for
    for (int i=0; i<ne; ++i) {
      const uint *v = element(i);
      nrm[i] = cross( nds[v[1]]-nds[v[0]], nds[v[2]]-nds[v[0]] );
    }
    return true;
  case Mx::Quad4:
  case Mx::Quad8:
  case Mx::Quad9:
    nrm.resize(ne);
#pragma omp parallel for
    for (int i=0; i<ne; ++i) {
      const uint *v = element(i);
      nrm[i] = cross( nds[v[2]]-nds[v[0]], nds[v[3]]-nds[v[1]] );
    }
    return true;
  case Mx::Tet4:
  case Mx::Tet10:
  case Mx::Pyra5:
  case Mx::Pyra14:
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
  case Mx::NElmTypes:
    return false;
  };

  return false;
}

void MxMeshSection::ipreorder(const Indices & iperm)
{
  const int n = inodes.size();
  for (int i=0; i<n; ++i) {
    assert(inodes[i] < iperm.size());
    assert(iperm[inodes[i]] != NotFound);
    inodes[i] = iperm[inodes[i]];
  }
}

size_t MxMeshSection::dropCollapsedElements()
{
  const int nv = nElementNodes();
  if ( nv < 2 )
    return 0;

  // drops element only if it is reduced to a single node
  const size_t ne = nelements();
  size_t ndrop = 0;
  for (size_t i=0; i<(ne-ndrop); ++i) {
    assert(i >= ndrop);
    size_t j = i - ndrop;
    const uint *v = element(j);
    bool degenerate = true;
    for (int ki=1; ki<nv; ++ki)
      degenerate &= (v[ki] == v[0]);
    if (not degenerate)
      continue;
    Indices::iterator pos = inodes.begin() + nv*j;
    inodes.erase(pos, pos+nv);
    ++ndrop;
  }

  return ndrop;
}

size_t MxMeshSection::dropDegenerateElements()
{
  const int npe = nElementNodes();
  if (npe < 2)
    return 0;

  // drop element if it contains duplicate node
  const size_t nel = nelements();
  size_t shift = 0;
  Indices::iterator first = inodes.begin();
  for (size_t i=0; i<(nel-shift); ++i) {
    const size_t iel = i-shift;
    const uint *v = element(iel);
    bool duplicate = false;
    for (int j=0; j<npe-1; ++j)
      for (int k=j+1; k<npe; ++k)
        duplicate |= (v[j] == v[k]);
    if (duplicate) {
      Indices::iterator ebeg = first + iel*npe;
      Indices::iterator eend = ebeg + npe;
      inodes.erase(ebeg, eend);
      ++shift;
    }
  }

  return shift;
}

uint MxMeshSection::planeCut(const std::vector<bool> & nbelow, 
                             Indices & ise) const
{
  // walk through all elements and append to ise when
  // the plane side flag differs between nodes

  ise.clear();
  const int ne = nelements();
  const int nn = nElementNodes();
  for (int i=0; i<ne; ++i) {
    const uint *vi = element(i);
    bool cuts(false), first = nbelow[vi[0]];
    for (int k=1; k<nn; ++k)
      cuts |= (nbelow[vi[k]] != first);
    if (cuts)
      ise.push_back(i);
  }
  return ise.size();
}

void MxMeshSection::aspectRatio(Vector & aspr) const
{
  const int nel = nelements();
  aspr.allocate(nel);
  int ve[24];
  const int ned = lineVertices(ve);
#pragma omp parallel for
  for (int i=0; i<nel; ++i) {
    const uint *v = element(i);
    Real lmin(huge), lmax(0.0);
    for (int j=0; j<ned; ++j) {
      int s = v[ve[2*j+0]];
      int t = v[ve[2*j+1]];
      Real len = norm(parent->node(t) - parent->node(s));
      lmin = min(lmin, len);
      lmax = max(lmax, len);
    }
    aspr[i] = lmax/lmin;
  }
}

void MxMeshSection::elementLength(Vector & elen) const
{
  const int nel = nelements();
  elen.resize(nel);
  int ve[24];
  const int ned = lineVertices(ve);
#pragma omp parallel for
  for (int i=0; i<nel; ++i) {
    const uint *v = element(i);
    Real lmean = 0.0;
    for (int j=0; j<ned; ++j) {
      int s = v[ve[2*j+0]];
      int t = v[ve[2*j+1]];
      Real len = norm(parent->node(t) - parent->node(s));
      lmean += len;
    }
    elen[i] = lmean / ned;
  }
}

bool MxMeshSection::dropOrder()
{
  const int ne = nelements();
  int np2(0), np1(0);
  Mx::ElementType etp1 = Mx::Undefined;
  if (etype == Mx::Tri6) {
    np1 = 3;
    np2 = 6;
    etp1 = Mx::Tri3;
  } else if (etype == Mx::Tet10) {
    np1 = 4;
    np2 = 10;
    etp1 = Mx::Tet4;
  } else if (etype == Mx::Quad8) {
    np1 = 4;
    np2 = 8;
    etp1 = Mx::Quad4;
  } else if (etype == Mx::Quad9) {
    np1 = 4;
    np2 = 9;
    etp1 = Mx::Quad4;
  } else if (etype == Mx::Hex20) {
    np1 = 8;
    np2 = 20;
    etp1 = Mx::Hex8;
  } else if (etype == Mx::Hex27) {
    np1 = 8;
    np2 = 27;
    etp1 = Mx::Hex8;
  } else if (etype == Mx::Penta15) {
    np1 = 6;
    np2 = 15;
    etp1 = Mx::Penta6;
  } else if (etype == Mx::Penta18) {
    np1 = 6;
    np2 = 18;
    etp1 = Mx::Penta6;
  }

  if (np1 == 0)
    return false;

  Indices tmp(np1*ne);
  for (int i=0; i<ne; ++i)
    for (int k=0; k<np1; ++k)
      tmp[i*np1 + k] = inodes[i*np2 + k];

  inodes.swap(tmp);
  etype = etp1;

  return true;
}

bool MxMeshSection::lineElement(Mx::ElementType elemType)
{
  switch (elemType) {
  case Mx::Undefined:
  case Mx::Point:
    return false;
  case Mx::Line2:
  case Mx::Line3:
    return true;
  case Mx::Tri3:
  case Mx::Tri6:
  case Mx::Quad4:
  case Mx::Quad8:
  case Mx::Quad9:
    return false;
  case Mx::Tet4:
  case Mx::Tet10:
  case Mx::Pyra5:
  case Mx::Pyra14:
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
  default:
    return false;
  };
  return false;
}

bool MxMeshSection::surfaceElement(Mx::ElementType elemType)
{
  switch (elemType) {
  case Mx::Undefined:
  case Mx::Point:
  case Mx::Line2:
  case Mx::Line3:
    return false;
  case Mx::Tri3:
  case Mx::Tri6:
  case Mx::Quad4:
  case Mx::Quad8:
  case Mx::Quad9:
    return true;
  case Mx::Tet4:
  case Mx::Tet10:
  case Mx::Pyra5:
  case Mx::Pyra14:
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
  default:
    return false;
  };
  return false;
}

bool MxMeshSection::volumeElement(Mx::ElementType elemType)
{
  switch (elemType) {
  case Mx::Undefined:
  case Mx::Point:
  case Mx::Line2:
  case Mx::Line3:
    return false;
  case Mx::Tri3:
  case Mx::Tri6:
  case Mx::Quad4:
  case Mx::Quad8:
  case Mx::Quad9:
    return false;
  case Mx::Tet4:
  case Mx::Tet10:
  case Mx::Pyra5:
  case Mx::Pyra14:
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
    return true;
  default:
    return false;
  };
  return false;
}

void MxMeshSection::shiftVertexIndices(int offset)
{
  if (offset == 0)
    return;

  const int n = inodes.size();
  for (int i=0; i<n; ++i)
    inodes[i] += offset;
}

uint MxMeshSection::vizNormalPoints(PointList<3,float> & pts) const
{
  pts.clear();

  bool quadType = false;
  switch (etype) {
  case Mx::Undefined:
  case Mx::Point:
  case Mx::Line2:
  case Mx::Line3:
    return 0;
  case Mx::Tri3:
  case Mx::Tri6:
    quadType = false;
    break;
  case Mx::Quad4:
  case Mx::Quad8:
  case Mx::Quad9:
    quadType = true;
    break;
  case Mx::Tet4:
  case Mx::Tet10:
  case Mx::Pyra5:
  case Mx::Pyra14:
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
  default:
    return 0;
  };

  const int ne = nelements();
  pts.resize( 2*ne );

  if (not quadType) {

    // triangles - corner points
#pragma omp parallel for
    for (int i=0; i<ne; ++i) {
      const uint *vi = element(i);
      Vct3f p0( parent->node(vi[0]) );
      Vct3f p1( parent->node(vi[1]) );
      Vct3f p2( parent->node(vi[2]) );
      float len = norm(p1-p0) + norm(p2-p1) + norm(p2-p0);
      pts[2*i+0] = pts[2*i+1] = 0.3333333f * (p0 + p1 + p2);
      Vct3f fn = cross(p1-p0, p2-p0);
      float sfn = sq(fn);
      if (sfn != 0)
        pts[2*i+1] += fn * 0.25f*len / std::sqrt(sfn);
    }

  } else {

    // quads - use corner points only
#pragma omp parallel for
    for (int i=0; i<ne; ++i) {
      const uint *vi = element(i);
      Vct3f p0( parent->node(vi[0]) );
      Vct3f p1( parent->node(vi[1]) );
      Vct3f p2( parent->node(vi[2]) );
      Vct3f p3( parent->node(vi[3]) );
      float len = norm(p1-p0) + norm(p2-p1)
                + norm(p3-p2) + norm(p0-p3);
      pts[2*i+0] = pts[2*i+1] = 0.25f * (p0 + p1 + p2 + p3);
      Vct3f fn = cross(p2-p0, p3-p1);
      float sfn = sq(fn);
      if (sfn != 0)
        pts[2*i+1] += fn * 0.25f*len / std::sqrt(sfn);
    }
  }

  return pts.size() / 2;
}

Vct6 MxMeshSection::integratePressure(const MxMeshField &pfield,
                                      const Vct3 &pref) const
{
  Vct6 fm;

  // ignore lines and volumes
  if (not surfaceElements())
    return fm;

  // slash any type of elements into 3-node triangles and assume
  // linear pressures over these
  const int *tmap;
  const int tpe = triangleMap(&tmap);
  const intptr_t ne = nelements();

  if (tpe < 1)
    return fm;

  assert(parent != nullptr);

#pragma omp parallel
  {
    // thread-private copies
    Vct6 tfm, kc;
    Vct3 tn, tf, tm;
    uint vt[3];
    Real pt[3];

#pragma omp for schedule(static,256)
    for (intptr_t i=0; i<ne; ++i) {
      const uint *ve = element(i);

      // slice into triangles
      for (int j=0; j<tpe; ++j) {
        const int *m = &tmap[3*j];
        Vct3 psum;
        for (int k=0; k<3; ++k) {
          vt[k] = ve[m[k]];
          pfield.scalar(vt[k], pt[k]);
          psum += parent->node(vt[k]);
        }

        // triangle normal
        tn = cross(parent->node(vt[1]) - parent->node(vt[0]),
                   parent->node(vt[2]) - parent->node(vt[0]));

        // triangle force; |tn| = 2*A
        tf = - tn * ((pt[0] + pt[1] + pt[2]) / 6.0);

        // triangle moment assuming tf acts on center
        tm = cross((psum/3.0) - pref, tf);

        for (int k=0; k<3; ++k) {
          kahan_sum_step(tf[k], tfm[k], kc[k]);
          kahan_sum_step(tm[k], tfm[3+k], kc[3+k]);
        }
      }
    }

#pragma omp critical
    fm += tfm;
  }

  return fm;
}

bool MxMeshSection::maps(const MxMeshBoco &bc) const
{
  if (bc.isRange()) {
    uint beg = bc.rangeBegin();
    uint end = bc.rangeEnd();
    return (beg == indexOffset()) and (end-beg == nelements());
  } else {
    Indices bce;
    bc.elements(bce);
    sort_unique(bce);
    const int nbe = bce.size();
    if ( uint(nbe) != nelements())
      return false;
    if (nbe == 0)
      return true;
    if (bce[0] != indexOffset())
      return false;
    for (int i=1; i<nbe; ++i)
      if (bce[i] != bce[i-1]+1)
        return false;
    return true;
  }

  // not reached
  return false;
}

bool MxMeshSection::contains(const MxMeshBoco &bc) const
{
  if (bc.isRange()) {
    size_t beg = bc.rangeBegin();
    size_t end = bc.rangeEnd();
    size_t ibegin = indexOffset();
    size_t iend = ibegin + nelements();

    // debug
    cout << "BC " << beg << "-" << end << " in "
         << ibegin << "-" << iend << ": "
         << ((beg >= ibegin) and (end <= iend)) << endl;

    return (beg >= ibegin) and (end <= iend);
  } else {
    Indices bce;
    bc.elements(bce);
    sort_unique(bce);
    const int nbe = bce.size();
    if ( uint(nbe) > nelements())
      return false;
    if (nbe == 0)
      return true;
    uint sbegin = indexOffset();
    uint send = sbegin + nelements();
    if (bce[0] < sbegin)
      return false;
    for (int i=1; i<nbe; ++i)
      if (bce[i] < sbegin or bce[i] >= send)
        return false;
    return true;
  }

  // not reached
  return false;
}

//#ifdef HAVE_CGNS

void MxMeshSection::readCgns(CgnsSection & cs)
{
  etype = Mx::Undefined;
  cgns::ElementType_t ctype = cs.elementType();
  etype = cgns2MxElementType(ctype);
  if (etype == Mx::Undefined)
    return;

  CgnsIntMatrix ielm;
  cs.readElements(ielm);
  assert(ielm.nrows() == nElementNodes(etype));
  const size_t ne = ielm.ncols();
  const size_t n = ne * nElementNodes(etype);
  inodes.resize(n);
  for (size_t i=0; i<n; ++i)
    inodes[i] = ielm[i] - 1;

  rename( cs.name() );
}

void MxMeshSection::writeCgns(CgnsSection & cs, int isec) const
{
  cgns::ElementType_t ctype = MxElementType2Cgns(etype);
  if (ctype == cgns::ElementTypeNull)
    return;
  
  cs.rename( "S" + str(isec+1) + secid );
  cs.elementType( ctype );
  CgnsIntMatrix em(nElementNodes(etype), nelements());
  const size_t n = inodes.size();
  for (size_t i=0; i<n; ++i)
    em[i] = inodes[i] + 1;
  cs.writeElements( em );
}

//#endif

void MxMeshSection::writeAbaqus(const Indices &gid, const Indices &eid,
                                std::ostream &os) const
{
  if ( inodes.empty() )
    return;

  // look in the annotation for an element type specification
  string abqEType;
  const XmlElement *xet;
  xet = xnote.findNode("Abaqus/Element");
  if (xet != 0)
    abqEType = xet->attribute("type");

  if (abqEType.empty()) {
    if (etype == Mx::Line2)
      abqEType = "T3D2";
    else if (etype == Mx::Line3)
      abqEType = "T3D3";
    else if (etype == Mx::Tri3)
      abqEType = "S3";
    else if (etype == Mx::Tri6)
      abqEType = "STRI6";
    else if (etype == Mx::Quad4)
      abqEType = "S4";
    else if (etype == Mx::Quad8)
      abqEType = "S8";
    else if (etype == Mx::Quad9)
      abqEType = "S9";
  }

  if (abqEType.empty())
    return;

  os << "*Element, type=" << abqEType << endl;

  const int ne = nelements();
  const int nv = nElementNodes();

  for (int i=0;  i<ne; ++i) {
    os << eid[indexOffset() + i];
    for (int j=0; j<nv; ++j) {
      os << ", " << gid[inodes[i*nv+j]];
    }
    os << endl;
  }
}

XmlElement MxMeshSection::toVTK() const
{
  const uint vtkCellMap[] = {0, 1, 3, 21, 5, 22, 9, 23, 0, 10, 24,
                             14, 0, 12, 25, 0, 13, 0, 0};
  
  assert(parent != 0);
  
  XmlElement xp("Piece");
  xp["Name"] = secid;
  
  // element representation
  const int nvtmax = sizeof(vtkCellMap) / sizeof(uint);
  const int eix = (int) etype;
  if (eix >= nvtmax or vtkCellMap[eix] == 0) {
    xp["NumberOfPoints"] = "0";
    xp["NumberOfCells"] = "0";
    return xp;
  }
  
  // collect point indices used in this section
  Indices ipoints;
  usedNodes(ipoints);
  
  const int np = ipoints.size();
  const int ne = nelements();

  xp["NumberOfPoints"] = str(np);
  xp["NumberOfCells"] = str(ne);
  
  // append points element
  {
    XmlElement xpt("Points");
    XmlElement xpd("DataArray");
    xpd["NumberOfComponents"] = "3";
    xpd["type"] = "Float64";
    xpd["format"] = "ascii";
    
    // extract point data from parent mesh
    PointList<3> lp(np);
    for (int i=0; i<np; ++i)
      lp[i] = parent->node(ipoints[i]);
    xpd.array2text(3*np, lp.pointer());
    
    xpt.append(xpd);
    xp.append(xpt);
  }
  
  // append cells element
  {
    XmlElement xc("Cells");
    
    // determine relative indices
    const int nv = inodes.size();
    Indices rix(nv);
    for (int i=0; i<nv; ++i) {
      rix[i] = distance(ipoints.begin(),
                        lower_bound(ipoints.begin(), ipoints.end(), inodes[i]));
    }
    
    XmlElement xci("DataArray");
    xci["type"] = "UInt32";
    xci["Name"] = "connectivity";
    xci.array2text(rix.size(), &rix[0]);
    xc.append(xci);
    
    // generate offset and type array
    Indices off(ne), typ(ne);
    fill(typ.begin(), typ.end(), vtkCellMap[eix]);
    for (int i=0; i<ne; ++i)
      off[i] = nElementNodes(etype)*(i+1);
    
    XmlElement xco("DataArray");
    xco["type"] = "UInt32";
    xco["Name"] = "offsets";
    xco.array2text(off.size(), &off[0]);
    xc.append(xco);
    
    XmlElement xct("DataArray");
    xct["type"] = "UInt8";
    xct["Name"] = "types";
    xct.array2text(typ.size(), &typ[0]);
    xc.append(xct);
    
    xp.append(xc);
  }
  
  // extract data belonging to this piece
  const int nf = parent->nfields();
  if (nf > 0) {
    XmlElement xpd("PointData");
    for (int i=0; i<nf; ++i)
      xpd.append( parent->field(i).toVTK(ipoints) );
    xp.append(xpd);
  }
  
  return xp;
}

void MxMeshSection::writeSU2(ostream &os) const
{
  const int eix = (int) etype;
  const int code = Mx::elementType2Vtk(eix);
  if (code == 0)
    throw Error("SU2 output not supported for element type: "+str(etype));

  const int ne = nelements();
  const int nv = nElementNodes();
  for (int i=0; i<ne; ++i) {
    os << code;
    const uint *vi = element(i);
    for (int j=0; j<nv; ++j)
      os << ' ' << vi[j];
    os << endl;
  }
}

struct ensight_part_hdr
{
  ensight_part_hdr() {
    memset(spart, ' ', sizeof(spart));
    memset(sdescription, ' ', sizeof(sdescription));
    memset(scoordinates, ' ', sizeof(scoordinates));
  }

  ensight_part_hdr(const std::string &name) {
    memset(spart, ' ', sizeof(spart));
    memset(sdescription, ' ', sizeof(sdescription));
    memset(scoordinates, ' ', sizeof(scoordinates));
    strcpy(spart, "part");
    strcpy(scoordinates, "coordinates");
    size_t nchar = std::min(size_t(80), name.size());
    std::copy(name.begin(), name.begin()+nchar, sdescription);
  }

  char spart[80];
  int32_t ipartno;
  char sdescription[80];
  char scoordinates[80];
  int32_t inodecount;
};

void MxMeshSection::writeEnsight(int partno, ostream &os) const
{
  assert(parent != 0);

  string eestr = Mx::ensightstr( elementType() );
  if (eestr == "undefined")
    return;

  Indices unodes;
  usedNodes(unodes);
  const size_t nn = unodes.size();

  ensight_part_hdr hdr( name() );
  hdr.ipartno = partno;
  hdr.inodecount = unodes.size();
  os.write((const char *) &hdr, sizeof(hdr));

  // write node ids
  os.write( (const char *) &unodes[0], nn*sizeof(unodes[0]) );

  // convert coordinates
  DVector<float> cc(3*nn);
  for (size_t i=0; i<nn; ++i) {
    const Vct3 & p( parent->node(unodes[i]) );
    cc[i] = p[0];
    cc[nn+i] = p[1];
    cc[2*nn+i] = p[2];
  }
  os.write( (const char *) cc.pointer(), cc.size()*sizeof(float) );

  char tmp[84];
  memset(tmp, ' ', 80);
  std::copy(eestr.begin(), eestr.end(), tmp);

  const int32_t ne = nelements();
  memcpy(&tmp[80], &ne, 4);
  os.write(tmp, sizeof(tmp));

  // element ids
  size_t nv = size_t(ne) * nElementNodes();
  DVector<int32_t> eid(ne), vix(nv);
  for (int i=0; i<ne; ++i)
    eid[i] = indexOffset() + i;
  for (size_t i=0; i<nv; ++i)
    vix[i] = sorted_index(unodes, inodes[i]) + 1;

  os.write( (const char *) eid.pointer(), ne*4 );
  os.write( (const char *) vix.pointer(), nv*4 );
}

void MxMeshSection::writeEnsight(int partno, const MxMeshField &f,
                                 ostream &os) const
{
  assert(f.realField());
  assert(f.nodal());

  char hdr[164];
  memset(hdr, ' ', sizeof(hdr));
  strcpy(&hdr[0], "part");
  int32_t pno = partno;
  memcpy(&hdr[80], &pno, 4);
  strcpy(&hdr[84], "coordinates");
  os.write(hdr, sizeof(hdr));

  Indices unodes;
  usedNodes(unodes);

  size_t nn = unodes.size();
  if (f.ndimension() == 1) {
    DVector<float> xpv(nn);
    f.fetch( unodes, xpv.pointer() );
    os.write( (const char *) xpv.pointer(), xpv.size()*sizeof(float) );
  } else if (f.ndimension() == 3) {
    PointList<3,float> xpv(nn);
    f.fetch<float,3>( unodes, xpv );

    // need to transpose
    DVector<float> trp(3*nn);
    for (size_t i=0; i<nn; ++i) {
      const Vct3f &p( xpv[i] );
      trp[0*nn+i] = p[0];
      trp[1*nn+i] = p[1];
      trp[2*nn+i] = p[2];
    }
    os.write( (const char *) trp.pointer(), trp.size()*sizeof(float) );
  }
}

uint MxMeshSection::createFromEnsight(MxMesh *pmx, int flags, istream &in)
{
  ensight_part_hdr hdr;
  in.read( (char *) &hdr, sizeof(hdr) );
  if ( strstr(hdr.spart, "part") == 0 or
       strstr(hdr.scoordinates, "coordinates") == 0 )
    throw Error("readEnsight() - no part header; corrupt geometry file?");
  if (hdr.inodecount < 0)
    throw Error("readEnsight() - Negative node count; corrupt geometry file?");

  // use part no (which is positive number below 2^16) to determine byte order
  bool needBSwap = (hdr.ipartno < 0) or (hdr.ipartno > (1 << 16) );

  int nidFlag = flags & 255;
  int eidFlag = (flags >> 8) & 255;
  bool nidStored = (nidFlag & Mx::GivenId) or (nidFlag & Mx::IgnoreId);
  bool eidStored = (eidFlag & Mx::GivenId) or (eidFlag & Mx::IgnoreId);

  DVector<int32_t> nid, eid;
  if (nidStored) {
    nid.allocate( hdr.inodecount );
    in.read( (char *) nid.pointer(), 4*nid.size() );
  }

  // fetch nodes for this part and add to parent mesh object
  size_t nn = hdr.inodecount;
  size_t noff = pmx->nnodes();
  DVector<float> cc( 3*nn );
  in.read( (char *) cc.pointer(), 4*cc.size() );
  if (needBSwap)
    swap_bytes<4>( 4*cc.size(), (char *) cc.pointer() );
  for (size_t i=0; i<nn; ++i)
    pmx->appendNode( Vct3( cc[i], cc[nn+i], cc[2*nn+i]) );

  // extract element type
  char tmp[84];
  memset(tmp, 0, 84);
  in.read(tmp, sizeof(tmp));

  Mx::ElementType t = Mx::decodeEnsightStr( strip(string(tmp, tmp+80)) );
  if (t == Mx::Undefined)
    return NotFound;

  uint32_t ne(0);
  memcpy(&ne, &tmp[80], 4);
  if (needBSwap)
    swap_bytes<4>(4, (char *) &ne);

  if (eidStored) {
    eid.allocate( ne );
    in.read( (char *) eid.pointer(), 4*eid.size() );
  }

  // fetch element vertex indices and translat to global index set
  size_t nvi = ne * MxMeshSection::nElementNodes(t);
  DVector<uint32_t> elix(nvi);
  in.read( (char *) elix.pointer(), 4*elix.size() );
  if (needBSwap)
    swap_bytes<4>( 4*elix.size(), (char *) elix.pointer() );

  Indices vix( nvi );
  for (size_t i=0; i<nvi; ++i)
    vix[i] = noff + elix[i] - 1;

  uint isec = pmx->appendSection( MxMeshSection(pmx, t) );
  MxMeshSection & sec( pmx->section(isec) );
  sec.appendElements( ne, &vix[0] );

  string desc;
  desc.assign( hdr.sdescription, hdr.sdescription + 80 );
  sec.rename( strip(desc) );

  pmx->countElements();
  return isec;
}

BinFileNodePtr MxMeshSection::gbfNode(bool share) const
{
  BinFileNodePtr np(new BinFileNode("MxMeshSection"));
  np->attribute("element_type", str(int(etype)) );
  np->attribute("name", secid);
  np->attribute("displayColor", dispColor.str());
  np->assign( inodes.size(), &inodes[0], share );

  if (not xnote.name().empty())
    np->append( xnote.toGbf(share) );

  return np;
}

void MxMeshSection::fromGbf(const BinFileNodePtr & np, bool digestNode)
{
  int ftyp = Int( np->attribute("element_type") );
  if (ftyp >= 0 and ftyp < int(Mx::NElmTypes)) {
    etype = Mx::ElementType(ftyp);
  } else {
    throw Error("Unknown element type in binary file.");
  }
  secid = np->attribute("name");
  if ( np->blockTypeWidth() != sizeof(uint) )
    throw Error("Incompatible node integer type in binary file.");
  inodes.resize(np->blockElements());
  memcpy(&inodes[0], np->blockPointer(), np->blockBytes());
  np->digest(digestNode);
}

XmlElement MxMeshSection::toXml(bool share) const
{
  XmlElement xe("MxMeshSection");
  xe["name"] = secid;
  xe["element_type"] = str(etype);
  xe["count"] = str(inodes.size());
  xe["displayColor"] = dispColor.str();
  xe.asBinary(inodes.size(), &inodes[0], share);
  if (not xnote.name().empty())
    xe.append(xnote);
  return xe;
}

void MxMeshSection::fromXml(const XmlElement & xe)
{
  etype = Mx::decodeElementType(xe.attribute("element_type"));
  if (etype == Mx::Undefined)
    throw Error("Unknown element type in xml file.");
  
  secid = xe.attribute("name");
  if (xe.hasAttribute("displayColor"))
    dispColor.str( xe.attribute("displayColor") );
  else
    displayColor( Color(0.5f,0.5f,0.5f) );

  size_t n = Int(xe.attribute("count"));
  inodes.resize(n);
  xe.fetch(n, &inodes[0]);

  XmlElement::const_iterator itr, last(xe.end());
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "MxNote")
      xnote = *itr;
  }
}

void MxMeshSection::toFFA(FFANode & node) const
{
  // Not only vertices, but also element vertex indices are stored
  // in the "wrong" order in FFA files: Indices of one element
  // are far apart in memory.

  const size_t ne = nelements();
  const int vpe = nElementNodes(etype);
  DMatrix<int> ielm(ne,vpe);
  for (size_t i=0; i<ne; ++i) {
    const uint *vi = element(i);
    for (int k=0; k<vpe; ++k)
      ielm(i,k) = vi[k] + 1;
  }
  
  if (ffastr( etype ) == "undefined") {
    dbprint("toFFA: Ignoring section of element type "+str(etype));
    return;
  }

  if (volumeElements()) {

    // split section such that each is below 2GB
    size_t nblock = (ielm.size() >> 27);

    if (nblock > 1) {

      size_t rowOffset = 0;
      for (size_t j=0; j<nblock; ++j) {
        FFANodePtr element_group(new FFANode("element_group"));
        FFANodePtr element_type(new FFANode("element_type"));
        element_type->copy(ffastr(etype));
        element_group->append(element_type);

        // sub-block
        size_t nrow = std::min( ne/nblock, ne-rowOffset );
        DMatrix<int> subelm(nrow,vpe);
        for (size_t i=0; i<nrow; ++i)
          for (int k=0; k<vpe; ++k)
            subelm(i, k) = ielm(rowOffset+i, k);
        rowOffset += nrow;

        FFANodePtr element_nodes(new FFANode("element_nodes"));
        element_nodes->copy(subelm.nrows(), subelm.ncols(), &subelm[0]);
        element_group->append(element_nodes);
        node.append(element_group);
      }

    } else {

      FFANodePtr element_group(new FFANode("element_group"));
      FFANodePtr element_type(new FFANode("element_type"));
      element_type->copy(ffastr(etype));
      element_group->append(element_type);

      FFANodePtr element_nodes(new FFANode("element_nodes"));
      element_nodes->copy(ielm.nrows(), ielm.ncols(), &ielm[0]);
      element_group->append(element_nodes);
      node.append(element_group);

    }

  } else {

    FFANodePtr boundary(new FFANode("boundary"));
    FFANodePtr boundary_name(new FFANode("boundary_name"));
    boundary_name->copy(secid);
    boundary->append(boundary_name);
    FFANodePtr belem_group(new FFANode("belem_group"));
    FFANodePtr bound_elem_type(new FFANode("bound_elem_type"));
    bound_elem_type->copy(ffastr(etype));
    belem_group->append(bound_elem_type);
    FFANodePtr bound_elem_nodes(new FFANode("bound_elem_nodes"));
    bound_elem_nodes->copy(ielm.nrows(), ielm.ncols(), &ielm[0]);
    belem_group->append(bound_elem_nodes);
    boundary->append(belem_group);
    node.append(boundary);
    
  }
}

bool MxMeshSection::fromFFA(const FFANode & node)
{
  DMatrix<int> ielm;

  // volume elements are stored in a node named 'element_group'
  if (node.name() == "element_group") {

    uint ipos = node.findChild("element_type");
    if (ipos == NotFound) {
      cerr << "Expected node 'element_type' in 'element_group'; not found." << endl;
      return false;
    }

    std::string etstr;
    FFANodePtr element_type = node.child(ipos);
    element_type->retrieve(etstr);
    etype = Mx::decodeFfaElementType(etstr);

    ipos = node.findChild("element_nodes");
    if (ipos == NotFound) {
      cout << "Expected node 'element_nodes' in 'element_group'; not found." << endl;
      return false;
    }

    FFANodePtr element_nodes = node.child(ipos);
    ielm.resize(element_nodes->nrows(), element_nodes->ncols() );
    element_nodes->retrieve( (void *) &ielm[0] );

  } else if (node.name() == "belem_group") {

    uint ipos = node.findChild("bound_elem_type");
    if (ipos == NotFound) {
      cerr << "Expected node 'bound_elem_type' in 'belem_group'; not found." << endl;
      return false;
    }

    std::string etstr;
    FFANodePtr element_type = node.child(ipos);
    element_type->retrieve(etstr);
    etype = Mx::decodeFfaElementType(etstr);

    ipos = node.findChild("bound_elem_nodes");
    if (ipos == NotFound) {
      cerr << "Expected node 'bound_elem_nodes' in 'belem_group'; not found." << endl;
      return false;
    }

    FFANodePtr element_nodes = node.child(ipos);
    ielm.resize( element_nodes->nrows(), element_nodes->ncols() );
    element_nodes->retrieve( (void *) &ielm[0] );

  }

  // copy vertex indices
  if (ielm.ncols() != nElementNodes()) {
    stringstream ss;
    ss << "MxMeshSection::fromFFA - Element vertex index count mismatch. " << endl;
    ss << "Found element type " << Mx::str(etype) << ", needs " << nElementNodes();
    ss << " vertices per element, but found " << ielm.ncols() << endl;
    throw Error(ss.str());
  }

  const int ne = ielm.nrows();
  const int nv = ielm.ncols();
  inodes.resize(ielm.size());
  for (int i=0; i<ne; ++i)
    for (int j=0; j<nv; ++j)
      inodes[i*nv+j] = ielm(i,j) - 1;

  return true;
}

