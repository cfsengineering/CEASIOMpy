
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
 
#include "plane.h"
#include "connectmap.h"
#include "dbprint.h"
#include "mxmeshfield.h"
#include "mxmeshslice.h"
#include "boxsearchtree.h"
#include "basicedge.h"
#include "ioglue.h"
#include <deque>

using std::string;

void MxMeshSlice::columns(StringArray & names) const
{
  assert(pmsh);
  names.clear();

  // first three columns are coordinates
  names.push_back("x");
  names.push_back("y");
  names.push_back("z");

  // set field names as column names
  const int nf = pmsh->nfields();
  for (int i=0; i<nf; ++i) {
    const MxMeshField & f( pmsh->field(i) );
    //if (f.ndimension() != 1)
    //  continue;
    if (not f.realField())
      continue;
    if (f.ndimension() == 1) {
      names.push_back( f.name() );
    } else {
      for (uint k=0; k<f.ndimension(); ++k)
        names.push_back(f.name() + f.componentName(k));
    }
  }
}

void MxMeshSlice::sliceData(uint iseg, Matrix & m) const
{
  assert(iseg < nsegments());

  // determine fields to use
  Indices ifields, kcomp;
  const int nf = pmsh->nfields();
  for (int i=0; i<nf; ++i) {
    const MxMeshField & f( pmsh->field(i) );
    // if (f.ndimension() != 1)
    //  continue;
    if (not f.realField())
      continue;
    for (uint k=0; k<f.ndimension(); ++k) {
      ifields.push_back(i);
      kcomp.push_back(k);
    }
  }
  const int nfields = ifields.size();

  // process segment iseg
  const int begin = seqstart[iseg];
  const int end = seqstart[iseg+1] - 1;
  m.resize(end-begin, 3+nfields);
  for (int i=begin; i<end; ++i) {
    const uint irow = i-begin;
    const uint v1 = vseq[i];
    const uint v2 = vseq[i+1];
    Real t = isecParameter(v1, v2);
    const uint w1 = ivtx[v1];
    const uint w2 = ivtx[v2];
    const Vct3 & p1( pmsh->node(w1) );
    const Vct3 & p2( pmsh->node(w2) );
    Vct3 pp = (1-t)*p1 + t*p2;
    for (int k=0; k<3; ++k)
      m(irow,k) = pp[k];
    for (int j=0; j<nfields; ++j) {
      // const Real *rp = pmsh->field(ifields[j]).realPointer();
      Real rw1, rw2;
      const MxMeshField & f( pmsh->field(ifields[j]) );
      f.scalar(w1, kcomp[j], rw1);
      f.scalar(w2, kcomp[j], rw2);
      m(irow,3+j) = (1-t)*rw1 + t*rw2;
    }
  }
}

void MxMeshSlice::markSlicedElements(MxMesh & mx) const
{
  MxMeshBoco bc;
  bc.appendElements(ice.begin(), ice.end());
  mx.appendBoco(bc);
}

void MxMeshSlice::slice(const Vct3 & po, const Vct3 & pu,
                        const Vct3 & pv)
{
  assert(pmsh != 0);
  org = po;
  Su = pu-org;
  Sv = pv-org;
  pnrm = cross(Su,Sv).normalized();
  ilu = 1.0 / dot(Su,Su);
  ilv = 1.0 / dot(Sv,Sv);

  clear();

  // determine elements cut by slice plane
  pmsh->planeCut( Plane(pnrm, dot(pnrm,org)), ice );
  if (ice.empty()) {
    dbprint("No elements intersected by definition plane.");
    return;
  }
  dbprint("planeCut:",ice.size());

  // numerically sort element indices
  filter();
  sortByEdges();
}

void MxMeshSlice::joinSegments(Real threshold)
{
  if (nsegments() < 2)
    return;

  assert(pmsh != 0);

  // determine segment endpoints
  const uint nseg = nsegments();
  PointList<3> pendp(2*nseg);
  for (uint iseg=0; iseg<nseg; ++iseg) {
    const int begin = seqstart[iseg];
    const int end = seqstart[iseg+1] - 1;

    // first point
    {
      const uint v1 = vseq[begin];
      const uint v2 = vseq[begin+1];
      Real t = isecParameter(v1, v2);
      const Vct3 & p1( pmsh->node( ivtx[v1] ) );
      const Vct3 & p2( pmsh->node( ivtx[v2] ) );
      pendp[2*iseg+0] = (1-t)*p1 + t*p2;
    }

    // last point
    {
      const uint v1 = vseq[end-1];
      const uint v2 = vseq[end];
      Real t = isecParameter(v1, v2);
      const Vct3 & p1( pmsh->node( ivtx[v1] ) );
      const Vct3 & p2( pmsh->node( ivtx[v2] ) );
      pendp[2*iseg+1] = (1-t)*p1 + t*p2;
    }
  }

  // build search tree for end points
  BSearchTree eptree(pendp);

  // new segment sequences
  Indices tseq, tstart(1,0);

  // look for connections
  Tags used(nseg, false);
  uint nused = 0;

  uint cur = NotFound;
  while (nused < nseg) {

    // find next unused segment
    for (uint i=0; i<nseg; ++i) {
      if (not used[i]) {
        cur = i;
        break;
      }
    }

    if (cur == NotFound)
      break;

    // start with the segment cur and try to find connected
    // segments from the remaining pool of unused ones
    used[cur] = true;
    ++nused;
    std::deque<int> chain( vseq.begin() + seqstart[cur],
                           vseq.begin() + seqstart[cur+1] );

    Indices inear;
    uint ihead, itail, nnear;
    ihead = 2*cur;
    itail = 2*cur+1;
    bool enchained = false;

    do {

      enchained = false;

      // find end points near head of segment
      inear.clear();
      eptree.find( pendp[ihead], threshold, inear );
      nnear = inear.size();

      for (uint j=0; j<nnear; ++j) {
        uint jseg = inear[j] / 2;
        if (used[jseg])
          continue;

        bool jtail = ((inear[j] & 1) == 1);
        if (jtail) {

          // tail of jseg is close to head of cur
          Indices::const_iterator fbeg(vseq.begin() + seqstart[jseg]);
          Indices::const_iterator fend(vseq.begin() + seqstart[jseg+1]);
          chain.insert(chain.begin(), fbeg, fend);

          // new head is head of jseg
          ihead = 2*jseg;

        } else {

          // head of jseg is close to head of cur
          Indices::const_reverse_iterator rbeg(vseq.begin() + seqstart[jseg+1]);
          Indices::const_reverse_iterator rend(vseq.begin() + seqstart[jseg]);
          chain.insert(chain.begin(), rbeg, rend);

          // new head is tail of jseg
          ihead = 2*jseg+1;
        }

        used[jseg] = true;
        ++nused;
        enchained = true;
        break;
      }

      // find end points near tail of segment
      inear.clear();
      eptree.find( pendp[itail], threshold, inear );
      nnear = inear.size();

      for (uint j=0; j<nnear; ++j) {
        uint jseg = inear[j] / 2;
        if (used[jseg])
          continue;

        bool jtail = ((inear[j] & 1) == 1);
        if (jtail) {

          // tail of jseg is close to tail of cur
          Indices::const_reverse_iterator rbeg(vseq.begin() + seqstart[jseg+1]);
          Indices::const_reverse_iterator rend(vseq.begin() + seqstart[jseg]);
          chain.insert(chain.end(), rbeg, rend);

          // new tail is head of jseg
          itail = 2*jseg;

        } else {

          // head of jseg is close to tail of cur
          Indices::const_iterator fbeg(vseq.begin() + seqstart[jseg]);
          Indices::const_iterator fend(vseq.begin() + seqstart[jseg+1]);
          chain.insert(chain.end(), fbeg, fend);

          // new tail is tail of jseg
          itail = 2*jseg+1;

        }

        used[jseg] = true;
        ++nused;
        enchained = true;
        break;
      }

    } while (enchained and (nused < nseg));

    tseq.insert(tseq.end(), chain.begin(), chain.end());
    tstart.push_back(tseq.size());
  }

  vseq.swap(tseq);
  seqstart.swap(tstart);
}

void MxMeshSlice::toEdges(Indices &edg) const
{
  assert(pmsh);

  const int nse = ice.size();
  std::vector<BasicEdge> bedges;
  bedges.reserve( 12*nse );

  // - convert all intersected elements to triangles
  // - extract all triangle edges which intersect plane
  for (int i=0; i<nse; ++i) {
    const int *trimap;
    uint nv, isec;
    const uint *vi = pmsh->globalElement( ice[i], nv, isec );
    const int ntri = pmsh->section(isec).triangleMap(&trimap);

    uint mtv[64];
    assert(3*ntri < 64);
    for (int k=0; k<3*ntri; ++k)
      mtv[k] = sorted_index(ivtx, vi[trimap[k]]);
    for (int k=0; k<ntri; ++k) {
      for (int j=0; j<3; ++j) {
        uint js = mtv[3*k+j];
        uint jt = mtv[3*k+(j+1)%3];
        if (js != NotFound and jt != NotFound)
          if (uvh[js][2]*uvh[jt][2] <= 0.0)
            bedges.push_back( BasicEdge(js,jt) );
      }
    }
  }

  std::sort(bedges.begin(), bedges.end());
  std::vector<BasicEdge>::iterator last;
  last = std::unique(bedges.begin(), bedges.end());
  const int ne = std::distance(bedges.begin(), last);

  edg.resize(2*ne);
  for (int i=0; i<ne; ++i) {
    edg[2*i+0] = bedges[i].source();
    edg[2*i+1] = bedges[i].target();
  }
}

void MxMeshSlice::filter()
{
  if (bSliceVolume and bSliceSurface and (not bInPlane)) {
    sort_unique(ice);
    return;
  }

  Vct3 p;
  Indices tmp;
  const int nse = ice.size();
  tmp.reserve(nse);
  for (int i=0; i<nse; ++i) {
    uint isec, nev;
    const uint *vi = pmsh->globalElement( ice[i], nev, isec );
    assert(isec != NotFound);
    const MxMeshSection & sec(pmsh->section(isec));
    if (sec.volumeElements() and (not bSliceVolume))
      continue;
    if (sec.surfaceElements() and (not bSliceSurface))
      continue;

    // if the projection of any vertex of the element
    // is inside the plane, use the element
    if (bInPlane) {
      bool isin = false;
      for (uint k=0; k<nev; ++k) {
        project(vi[k], p);
        isin |= (p[0] >= 0.0) and (p[0] <= 1.0)
                and (p[1] >= 0.0) and (p[1] <= 1.0);
      }
      if (isin)
        tmp.push_back(ice[i]);
    } else {
      tmp.push_back(ice[i]);
    }
  }
  tmp.swap(ice);

  dbprint(ice.size(), "sliced elements found.");
}

void MxMeshSlice::sortByEdges()
{
  // collect all vertices connected to sliced elements
  ivtx.clear();
  const int nse = ice.size();
  if (nse == 0)
    return;

  uint isec, nev;
  const uint *vi;
  for (int i=0; i<nse; ++i) {
    vi = pmsh->globalElement(ice[i], nev, isec);
    ivtx.insert(ivtx.end(), vi, vi+nev);
  }
  sort_unique(ivtx);

  // compute local (plane) coordinates
  const int nv = ivtx.size();
  uvh.resize(nv);
  for (int i=0; i<nv; ++i)
    project(ivtx[i], uvh[i]);

  // assemble edges
  Indices edg;
  toEdges(edg);

  // construct vertex-to-vertex connectivity
  const int ne = edg.size() / 2;
  ConnectMap v2v;
  v2v.beginCount(nv);
  for (int i=0; i<ne; ++i) {
    uint src = edg[2*i+0];
    uint trg = edg[2*i+1];
    v2v.incCount(src);
    v2v.incCount(trg);
  }
  v2v.endCount();

  for (int i=0; i<ne; ++i) {
    uint src = edg[2*i+0];
    uint trg = edg[2*i+1];
    v2v.append(src, trg);
    v2v.append(trg, src);
  }
  v2v.compress();

  seqstart.resize(1);
  seqstart[0] = 0;
  vseq.clear();
  vseq.reserve(nv);
  Tags vtag(nv, false);

  // start with the point at max u
  uint cur = uvh.cmax<0>();
  while (cur != NotFound) {
    vseq.push_back(cur);
    vtag[cur] = true;
    cur = nextVertex(cur, v2v, vtag);
    if (cur == NotFound) {
      cur = firstVertex(vtag);
      seqstart.push_back( vseq.size() );
    }
  }

  // eliminate all single-edge segments
  Indices tmp, tstart;
  const int nseq = seqstart.size()-1;
  for (int i=0; i<nseq; ++i) {
    uint begin = seqstart[i];
    uint end = seqstart[i+1];
    if (end-begin > 1) {
      tstart.push_back(tmp.size());
      tmp.insert(tmp.end(), vseq.begin()+begin,
                            vseq.begin()+end);
      dbprint("Segment",tstart.size()-1,"length",end-begin);
    }
  }
  tstart.push_back(tmp.size());
  tmp.swap(vseq);
  tstart.swap(seqstart);
}

uint MxMeshSlice::nextVertex(uint cur, const ConnectMap & v2v,
                             const Tags & vtag) const
{
  // determine current direction
  Vct2 cdir(-1.0, 0.0);
  if (seqstart.back()+1 < vseq.size()) {
    assert(vseq.size() > 1);
    uint prev = vseq[vseq.size()-2];
    assert(prev != cur);
    cdir[0] = uvh[cur][0] - uvh[prev][0];
    cdir[1] = uvh[cur][1] - uvh[prev][1];
  }

  // first option : find a vertex connected to cur which is on
  // the other side of the slice plane and not yet tagged. if
  // there are multiple candidates for that, pick the one which
  // has the largest in-plane distance
  Real dmax(-huge);
  const Vct3 & pcur( uvh[cur] );
  const int nnb = v2v.size(cur);
  uint ibest = NotFound;
  for (int i=0; i<nnb; ++i) {
    uint ican = v2v.index(cur,i);

    // skip vertex already used
    if (vtag[ican])
      continue;

    // skip vertex on the same side
    const Vct3 & pcan( uvh[ican] );
    if (pcan[2]*pcur[2] > 0.0)
      continue;

    Real dst = cdir[0]*(pcan[0]-pcur[0])
             + cdir[1]*(pcan[1]-pcur[1]);
    if (dst > dmax) {
      ibest = ican;
      dmax = dst;
    }
  }

  return ibest;
}

uint MxMeshSlice::firstVertex(const Tags & vtag) const
{
  // pick the vertex with largest u which is not tagged yet
  const int nv = ivtx.size();
  uint ibest(NotFound);
  Real umax(-huge);
  for (int i=0; i<nv; ++i) {
    if (vtag[i])
      continue;
    if (uvh[i][0] > umax) {
      umax = uvh[i][0];
      ibest = i;
    }
  }
  return ibest;
}

void MxMeshSlice::writePlain(uint iseg,
                             const std::string & fname) const
{
  assert(iseg < nsegments());
  if (size(iseg) == 0)
    return;

  StringArray cols;
  columns(cols);

  ofstream os(asPath(fname).c_str());
  os << '%';
  for (uint j=0; j<cols.size(); ++j)
    os << ' ' << j+1 << ":" << cols[j];
  os << endl;

  Matrix m;
  sliceData(iseg, m);
  os << m;
}

void MxMeshSlice::writePlain(const std::string & fname) const
{
  ofstream os(asPath(fname).c_str());

  StringArray cols;
  this->columns(cols);

  os << "% 0:u 1:v ";
  for (uint j=0; j<cols.size(); ++j) {
    string cname = cols[j];
    std::replace(cname.begin(), cname.end(), ' ', '_');
    os << ' ' << j+2 << ":" << cname;
  }
  os << endl;

  Matrix m;
  for (uint iseg=0; iseg < nsegments(); ++iseg) {
    sliceData(iseg, m);
    // os << m << endl;

    // first three columns are always (x,y,z)
    const int np = m.nrows();
    for (int j=0; j<np; ++j) {
      Vct3 r = Vct3( m(j,0), m(j,1), m(j,2) ) - org;
      Real u = dot(Su,r) * ilu;
      Real v = dot(Sv,r) * ilv;
      os << u << ' ' << v << ' ';
      for (uint k=0; k<m.ncols(); ++k)
        os << m(j,k) << ' ';
      os << endl;
    }
    os << endl;
  }
}

void MxMeshSlice::writeMatlab(const std::string & funcName,
                              const std::string & fileName) const
{
  StringArray cols;
  this->columns(cols);

  ofstream os(asPath(fileName).c_str());
  os << "function [slices,colnames] = " << funcName << "()" << endl;
  os << "  colnames = { ..." << endl;
  for (uint j=0; j<cols.size(); ++j)
    os << "          '" << cols[j] << "', ..." << endl;
  os << "  };" << endl << endl;
  os << "  slices = cell(" << nsegments() << ",1);" << endl;

  Matrix m;
  for (uint i=0; i<nsegments(); ++i) {
    sliceData(i, m);
    os << "  slices{" << i+1 << "} = [ ..." << endl;
    os << m << "  ];" << endl;
  }

  os << endl << "end" << endl;
}

void MxMeshSlice::clear()
{
  ice.clear();
  ivtx.clear();
  vseq.clear();
  seqstart.clear();
  uvh.clear();
}

