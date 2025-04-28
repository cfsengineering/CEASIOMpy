
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

#include "delaunaycore.h"
#include "dcgeometry.h"
#include <genua/algo.h>
#include <genua/connectmap.h>
#include <genua/basicedge.h>
#include <genua/dbprint.h>
#include <genua/bitfiddle.h>
#include <genua/scopedsetting.h>

#include <deque>

// #include <iostream>
using namespace std;

DelaunayCore::DelaunayCore(DcGeometry & geom, size_t reserveEdges)
  : geo(geom), edgePool(sizeof(DcEdge)), edges(reserveEdges),
    bProtectConstraints(true), bCacheFaces(false), bInsertExtend(false)
{
}

CPHINT_HOTSPOT_BEGIN

uint DelaunayCore::addFace(uint a, uint b, uint c)
{
  int ori = geo.orientation(a, b, c);

  // strange if(); to give the static branch scheduler better
  if (ori == DcGeometry::CounterClockwise)
    ;  // most likely branch must be first - if() assumed to be taken
  else if (ori == DcGeometry::Clockwise)
    std::swap(b, c);
  else if ( hint_unlikely(ori == DcGeometry::Colinear) )
    return NotFound;

  assert( geo.orientation(a,b,c) == DcGeometry::CounterClockwise );

  uint fi;
  DcFace f(a, b, c);
  if (invalidFaces.empty()) {
    faces.push_back(f);
    fi = faces.size()-1;
  } else {
    fi = invalidFaces.back();
    invalidFaces.pop_back();
    faces[fi] = f;
  }

  if (bCacheFaces)
    faceCache.push_back(fi);
  geo.insertFace(fi, face(fi).vertices());
  assert(fi != NotFound);
  return fi;
}

CPHINT_HOTSPOT_END

void DelaunayCore::addFaces(const Indices &tri)
{
  const uint fi = faces.size();
  const int nf = tri.size()/3;
  for (int i=0; i<nf; ++i) {
    faces.push_back( DcFace(&tri[3*i]) );
    geo.insertFace(fi+i, face(fi+i).vertices());
  }
}

uint DelaunayCore::eraseFacesTouching(const Indices &idx)
{
  uint nerase = 0;
  const int nf = nAllFaces();
  for (int i=0; i<nf; ++i) {
    if (not face(i).valid())
      continue;
    const uint *vi = face(i).vertices();
    bool doErase = false;
    for (int k=0; k<3; ++k)
      doErase |= std::binary_search(idx.begin(), idx.end(), vi[k]);
    if (doErase) {
      eraseFace(i);
      detachFace(i);
      ++nerase;
    }
  }
  return nerase;
}



void DelaunayCore::detachFace(uint k)
{
  if ( hint_unlikely(k >= faces.size()) )
    return;

  DcFace & f(faces[k]);
  if (f.valid()) {
    for (int i=0; i<3; ++i) {
      DcEdge *pe = findEdge( f.esource(i), f.etarget(i) );
      if (pe != 0)
        pe->replaceFace(k, NotFound);
    }
  }
}

void DelaunayCore::fixate()
{
  const int nf = faces.size();

  if (not edges.empty())
    dbprint("[W] DelaunayCore::fixate() called with non-empty edge table; "
            "will loose edge flags.");

  // edges = DcEdgeTable( 1 << (1 + floorlog2(3*nf)) );
  edges.clear();
  edges.rehash((nf*3) / (2*edges.max_load_factor()) + 1);
  for (int i=0; i<nf; ++i) {
    if (not faces[i].valid())
      continue;
    for (int k=0; k<3; ++k) {
      const uint src = faces[i].esource(k);
      const uint trg = faces[i].etarget(k);
      DcEdge *pe = findEdge(src, trg);
      if (pe == 0) {
        pe = constructEdge(src, trg);
        edges.insert( pe );
      }
      assert(pe != 0);
      pe->appendFace(i);
    }
  }
}

void DelaunayCore::eraseDetachedEdges()
{
  if (edges.empty())
    return;

  DcEdgeItr itr = edges.begin();
  do {
    DcEdge *pe = *itr;
    assert(pe != nullptr);
    if (pe->nfaces() != 0)
      ++itr;
    else
      itr = edges.erase(itr);
  } while (itr != edges.end());
}

void DelaunayCore::vertexMap(uint nv, ConnectMap &v2f) const
{
  const int nf = faces.size();
  v2f.beginCount(nv);
  for (int i=0; i<nf; ++i) {
    const DcFace & f( faces[i] );
    if (not f.valid())
      continue;
    const uint *v = f.vertices();
    for (int k=0; k<3; ++k)
      v2f.incCount(v[k]);
  }
  v2f.endCount();

  for (int i=0; i<nf; ++i) {
    const DcFace & f( faces[i] );
    if (not f.valid())
      continue;
    const uint *v = f.vertices();
    for (int k=0; k<3; ++k)
      v2f.append(v[k], i);
  }
  v2f.compress();
}

bool DelaunayCore::diamond(DcEdge *pe, uint v[]) const
{
  v[0] = pe->source();
  v[1] = pe->target();

  uint fl = pe->left();
  uint fr = pe->right();
  assert(fl != fr);

  if (fl != NotFound) {
    v[2] = faces[fl].opposedVertex(pe->source(), pe->target());
    assert(v[2] != NotFound);
  } else {
    v[2] = NotFound;
  }

  if (fr != NotFound) {
    v[3] = faces[fr].opposedVertex(pe->source(), pe->target());
    assert(v[3] != NotFound);
  } else {
    v[3] = NotFound;
  }

  return (v[2] != NotFound) and (v[3] != NotFound);
}

bool DelaunayCore::isConvex(const uint v[]) const
{
  int ori0 = geo.orientation( v[2], v[3], v[0] );
  if (ori0 == DcGeometry::Colinear)
    return false;

  int ori1 = geo.orientation( v[2], v[3], v[1] );
  if (ori1 == DcGeometry::Colinear)
    return false;

  return (ori0 != ori1);
}

bool DelaunayCore::flipEdge(DcEdge *pe)
{
  if (pe->degree() != 2)
    return false;
  if (not pe->canFlip())
    return false;

  uint fl = pe->left();
  uint fr = pe->right();

  uint v[4];
  diamond(pe, v);

  // cannot flip if the resulting triangles would be degenerate
  int o231 = geo.orientation(v[2], v[3], v[1]);
  int o230 = geo.orientation(v[2], v[3], v[0]);
  if ((o231 == DcGeometry::Colinear) or (o230 == DcGeometry::Colinear))
    return false;

  // cannot flip if the diamond is non-convex, because that would mean
  // the triangles after flip would both be on the same side of the new edge
  if (o231 == o230)
    return false;

  //  if ( geo.orientation(v[1], v[2], v[3]) == DcGeometry::Colinear )
  //    return false;
  //  else if ( geo.orientation(v[0], v[2], v[3]) == DcGeometry::Colinear )
  //    return false;

  //  // cannot flip if the diamond is non-convex, because that would mean
  //  // the triangles after flip would both be on the same side of the new edge
  //  if ( geo.orientation(v[2], v[3], v[0]) == geo.orientation(v[2], v[3], v[1]) )
  //    return false;

  // edges
  DcEdge *e02 = findEdge(v[0], v[2]); assert(e02 != 0);
  DcEdge *e03 = findEdge(v[0], v[3]); assert(e03 != 0);
  DcEdge *e12 = findEdge(v[1], v[2]); assert(e12 != 0);
  DcEdge *e13 = findEdge(v[1], v[3]); assert(e13 != 0);

  // remove faces
  eraseFace(fl);
  eraseFace(fr);

  // remove pe before src/trg changed
  eraseEdge(pe);

  // flip edge src/target, keep left/right
  pe->assign(v[2], v[3]);

  // create new faces
  uint f1 = addFace(v[1], v[2], v[3]); assert(f1 != NotFound);
  uint f2 = addFace(v[0], v[2], v[3]); assert(f2 != NotFound);

  pe->assignFaces(f1, f2);

  edges.insert(constructEdge(*pe));

  // connect edges to new faces
  e02->replaceFace(fr, fl, f2);
  e03->replaceFace(fr, fl, f2);
  e12->replaceFace(fr, fl, f1);
  e13->replaceFace(fr, fl, f1);

  return true;
}

bool DelaunayCore::splitEdge(DcEdge *pab, uint c, bool legalizeEdges)
{
  if (pab == 0)
    return false;
  if (pab->checkFlag(DcEdge::NeverSplit))
    return false;

  uint v[4];
  diamond(pab, v);

  // faces (maybe NotFound)
  uint fl = pab->left();
  uint fr = pab->right();

  DcEdge *e03(0), *e13(0), *e02(0), *e12(0);
  if (bProtectConstraints) {

    if (fr != NotFound) {
      e03 = findEdge(v[0], v[3]);
      assert(e03 != nullptr);
      if (e03->checkFlag(DcEdge::Constrained) and
          geo.encroachesEdge(v[0], v[3], c)) {
        dbprint(str(c)+" encroaches "+str(v[0])+" - "+str(v[3]));
        return false;
      }

      e13 = findEdge(v[1], v[3]);
      assert(e13 != nullptr);
      if (e13->checkFlag(DcEdge::Constrained) and
          geo.encroachesEdge(v[1], v[3], c)) {
        dbprint(str(c)+" encroaches "+str(v[1])+" - "+str(v[3]));
        return false;
      }
    }

    if (fl != NotFound) {
      e02 = findEdge(v[0], v[2]);
      assert(e02 != nullptr);
      if (e02->checkFlag(DcEdge::Constrained) and
          geo.encroachesEdge(v[0], v[2], c)) {
        dbprint(str(c)+" encroaches "+str(v[0])+" - "+str(v[2]));
        return false;
      }

      e12 = findEdge(v[1], v[2]);
      assert(e12 != nullptr);
      if (e12->checkFlag(DcEdge::Constrained) and
          geo.encroachesEdge(v[1], v[2], c)) {
        dbprint(str(c)+" encroaches "+str(v[1])+" - "+str(v[2]));
        return false;
      }
    }
  }

  // flags of incoming edge
  int flags = pab->getFlags();

  DcEdge *pac = constructEdge(v[0], c);
  pac->setFlag(flags);
  DcEdge *pcb = constructEdge(c, v[1]);
  pcb->setFlag(flags);

  if (fr != NotFound) {
    uint f1 = addFace(v[0], c, v[3]); assert(f1 != NotFound);
    uint f2 = addFace(c, v[1], v[3]); assert(f2 != NotFound);

    // find existing edges
    if (not bProtectConstraints) {
      e03 = findEdge(v[0], v[3]);
      e13 = findEdge(v[1], v[3]);
    }
    e03->replaceFace(fr, f1);
    e13->replaceFace(fr, f2);

    pac->appendFace(f1);
    pcb->appendFace(f2);
    DcEdge *pc3 = constructEdge(v[3], c);
    pc3->assignFaces(f1, f2);
    edges.insert(pc3);
  }

  if (fl != NotFound) {
    uint f1 = addFace(v[0], v[2], c); assert(f1 != NotFound);
    uint f2 = addFace(c, v[2], v[1]); assert(f2 != NotFound);

    if (not bProtectConstraints) {
      e02 = findEdge(v[0], v[2]);
      e12 = findEdge(v[1], v[2]);
    }
    e02->replaceFace(fl, f1);
    e12->replaceFace(fl, f2);

    pac->appendFace(f1);
    pcb->appendFace(f2);
    DcEdge *pc2 = constructEdge(v[2], c);
    pc2->assignFaces(f1, f2);
    edges.insert(pc2);
  }

  eraseEdge(pab);
  edges.insert(pac);
  edges.insert(pcb);

  // legalize edges
  if (legalizeEdges) {
    if (fr != NotFound) {
      legalizeEdge(v[0], v[3], c);
      legalizeEdge(v[1], v[3], c);
    }
    if (fl != NotFound) {
      legalizeEdge(v[0], v[2], c);
      legalizeEdge(v[1], v[2], c);
    }
  }

  if (fr != NotFound)
    eraseFace(fr);
  if (fl != NotFound)
    eraseFace(fl);

  if ((flags & DcEdge::Constrained) == DcEdge::Constrained)
    vinConEdges.push_back( c );

  return true;
}

bool DelaunayCore::splitFace(uint fix, uint x, bool legalizeEdges)
{
  assert(fix < faces.size());
  assert(faces[fix].valid());

  uint v[3];
  faces[fix].copyVertices(v);
  assert(std::find(v, v+3, x) == v+3);
  DcEdge *e01 = findEdge( v[0], v[1] ); assert(e01 != 0);
  DcEdge *e12 = findEdge( v[1], v[2] ); assert(e12 != 0);
  DcEdge *e20 = findEdge( v[2], v[0] ); assert(e20 != 0);

  if (bProtectConstraints) {
    if (e01->checkFlag(DcEdge::Constrained) and
        geo.encroachesEdge(v[0], v[1], x))
      return false;
    else if (e12->checkFlag(DcEdge::Constrained) and
             geo.encroachesEdge(v[1], v[2], x))
      return false;
    else if (e20->checkFlag(DcEdge::Constrained) and
             geo.encroachesEdge(v[2], v[0], x))
      return false;
  }

  uint f1 = addFace(v[0], v[1], x); assert(f1 != NotFound);
  uint f2 = addFace(v[1], v[2], x); assert(f2 != NotFound);
  uint f3 = addFace(v[2], v[0], x); assert(f3 != NotFound);

  e01->replaceFace(fix, f1);
  e12->replaceFace(fix, f2);
  e20->replaceFace(fix, f3);

  // new edges
  DcEdge *e0x = constructEdge(v[0], x);
  e0x->assignFaces(f1, f3);
  edges.insert(e0x);

  DcEdge *e1x = constructEdge(v[1], x);
  e1x->assignFaces(f1, f2);
  edges.insert(e1x);

  DcEdge *e2x = constructEdge(v[2], x);
  e2x->assignFaces(f2, f3);
  edges.insert(e2x);

  if (legalizeEdges) {
    //    legalizeEdge(v[0], v[1], x);
    //    legalizeEdge(v[1], v[2], x);
    //    legalizeEdge(v[2], v[0], x);

    legalizeEdge(e01, x);
    if (not e12->connects(v[1], v[2]))
      e12 = findEdge(v[1], v[2]);
    legalizeEdge(e12, x);
    if (not e20->connects(v[2], v[0]))
      e20 = findEdge(v[2], v[0]);
    legalizeEdge(e20, x);
  }

  eraseFace(fix);
  return true;
}

void DelaunayCore::addExternalVertex(DcEdge *pab, uint c, bool legalizeEdges)
{
  assert(pab != 0);
  assert(pab->left() == NotFound or pab->right() == NotFound);

  // flags of boundary edge pab
  int abflags = pab->getFlags();

  // new face
  const uint a = pab->source();
  const uint b = pab->target();
  const uint fnew = addFace(a, b, c);
  pab->appendFace(fnew);

  // new edges
  DcEdge *pac = constructEdge(a, c);
  pac->appendFace(fnew);
  pac->setFlag(abflags);
  edges.insert(pac);

  DcEdge *pbc = constructEdge(b, c);
  pbc->appendFace(fnew);
  pbc->setFlag(abflags);
  edges.insert(pbc);

  // Edge pab is no longer a boundary edge
  pab->unsetFlag(abflags);

  // only the old edge, pab, may perhaps be flipped, the newly added
  // edges are boundary edges
  if (legalizeEdges)
    legalizeEdge(a, b, c);
}

int DelaunayCore::insertVertex(uint c, bool legalizeEdges)
{
  uint fix;
  int loc = geo.locateTriangle(*this, c, fix);

  switch (loc) {
  case DcGeometry::Inside:
    if ( splitFace(fix, c, legalizeEdges) ) {
      return FaceSplit;
    } else {
      status = ProtectedConstraintEncroached;
      return NotInserted;
    }

  case DcGeometry::Outside:
    dbprint("Point out of domain (says locateTriangle).");
    status = InsertPointOutOfDomain;
    return NotInserted;

  case DcGeometry::OnEdge1:
  case DcGeometry::OnEdge2:
  case DcGeometry::OnEdge3:
  {
    const int ke = loc - DcGeometry::OnEdge1;
    DcEdge *pe = findEdge( face(fix).esource(ke), face(fix).etarget(ke) );
    assert(pe != nullptr);
    if ( splitEdge(pe, c, legalizeEdges) ) {
      return EdgeSplit;
    } else {
      dbprint("Point on edge, but cannot split edge w/flags:", pe->getFlags());
      status = InsertCannotSplitEdge;
      return NotInserted;
    }
  }

  case DcGeometry::OnVertex1:
  case DcGeometry::OnVertex2:
  case DcGeometry::OnVertex3:
    return VertexPresent;

  case DcGeometry::BeyondEdge1:
  case DcGeometry::BeyondEdge2:
  case DcGeometry::BeyondEdge3:
    if (bInsertExtend) {
      const int ke = loc - DcGeometry::BeyondEdge1;
      DcEdge *pe = findEdge( face(fix).esource(ke), face(fix).etarget(ke) );
      addExternalVertex(pe, c, legalizeEdges);
      // dbprint("Extended mesh with vertex",c);
      return ExtendedOutward;
    } else {
      dbprint("Point beyond edge.");
      status = InsertPointOutOfDomain;
      return NotInserted;
    }
  }

  dbprint("Triangle location not handled.");
  status = InsertTriangledNotFound;
  return NotInserted;
}

uint DelaunayCore::insertConstraint(const Indices &cinp,
                                    int flags,
                                    bool legalizeEdges)
{
  status = StatusOk;

  // constraint protection must be switched off whenever new
  // constrained edges are injected; otherwise, that would always fail.
  ScopedSetting<bool> guardConstraints(bProtectConstraints, false);

  // Permit insertion of vertices beyond the current domain:
  // Constrained points on the edge of the domain will be outside whenever
  // the (s,t) -> (u,v) mapping is locally concave on the boundary such that
  // a new point *on* an (u,v) edge is actually beyond the (s,t) edge (outside)
  ScopedSetting<bool> guardExtend(bInsertExtend, true);

  // insert constraint vertices
  startFaceCaching();
  const int np = cinp.size();
  Indices c(np, NotFound);
  for (int i=0; i<np; ++i) {
    int iflag = insertVertex(cinp[i], legalizeEdges);
    c[i] = cinp[i];
    if ( hint_unlikely(iflag == NotInserted) ) {
      stopFaceCaching();
      return i;
    } else if (iflag == VertexPresent) {
      uint fix;
      int loc = geo.locateTriangle(*this, cinp[i], fix);
      const uint *vi = faces[fix].vertices();
      c[i] = vi[ loc - DcGeometry::OnVertex1 ];
      faceCache.push_back(fix);
    }
  }
  stopFaceCaching();
  sort_unique(faceCache);

  // at this point, the faceCache contains all newly created faces processed
  // during the vertex insertion pass

  // establish constraint edges
  const int ne = np-1;
  for (int i=0; i<ne; ++i) {
    uint src = c[i];
    uint trg = c[i+1];
    if (src == trg)
      continue;

    // the desired edge may already be present
    DcEdge *pe = findEdge(src, trg);
    if (pe != nullptr) {
      pe->setFlag( flags );
      continue;
    }

    // search for an opportunity to flip an existing
    // edge in order to generate edge (src,trg)
    pe = searchCacheForFlip(src, trg);
    if (pe and flipEdge(pe)) {
      pe = findEdge(src, trg);
      assert(pe != nullptr);
      pe->setFlag( flags );
      continue;
    }

    // at this point, it appears that we need to enforce the existence of the
    // edge (src,trg) by means of erasing some faces
    pe = imprintIntersectingEdge(src, trg);
    if (pe != nullptr) {
      pe->setFlag( flags );
      continue;
    }

    pe = imprintOverlappingEdge(src, trg);
    if (pe != nullptr) {
      pe->setFlag( flags );
      continue;
    }

    if (status == StatusOk)
      status = CannotEnforceEdge;

    dbprint("Don't know how to enforce edge.");
    assert(pe != nullptr);
    return 0;
  }

  return np;
}

DcEdge *DelaunayCore::searchCacheForFlip(uint s, uint t) const
{
  const int nfc = faceCache.size();
  for (int i=0; i<nfc; ++i) {
    const DcFace & f( faces[faceCache[i]] );
    if (not f.valid())
      continue;
    for (uint k=0; k<3; ++k) {
      const uint sf = f.esource(k);
      const uint tf = f.etarget(k);
      DcEdge *pe = findEdge(sf, tf);
      assert(pe != 0);
      uint v[4];
      diamond(pe, v);
      if (v[2] == s and v[3] == t)
        return pe;
      else if (v[2] == t and v[3] == s)
        return pe;
    }
  }

  return 0;
}

DcEdge *DelaunayCore::imprintIntersectingEdge(uint csrc, uint ctrg)
{
  // construct edge to enforce
  DcEdge *pe(0), *pcut(0);
  pe = constructEdge(csrc, ctrg);
  edges.insert(pe);

  const uint src = pe->source();
  const uint trg = pe->target();

  // search face cache for a triangle which contains src and has an edge
  // which is intersected by (src,trg)
  uint ti(NotFound);
  while (ti == NotFound) {

    const int nfc = faceCache.size();
    for (int i=0; i<nfc; ++i) {

      const DcFace & f( faces[faceCache[i]] );
      if (not f.valid())
        continue;

      // locate vertex src in triangle f
      uint isrc = f.find(src);
      if (isrc == NotFound)
        continue;

      // determine the edge which does not contain src
      const uint *vf = f.vertices();
      const uint sf = vf[ (isrc+1)%3 ];
      const uint tf = vf[ (isrc+2)%3 ];
      assert(sf != tf);

      int isec = geo.edgesIntersect(src, trg, sf, tf);
      if (isec == DcGeometry::EdgesIntersect) {

        // normal case : unique edge sliced by constraint
        ti = faceCache[i];
        pcut = findEdge(sf, tf);
        assert(pcut != 0);
        if (pcut->checkFlag( DcEdge::NeverSplit )) {
          status = ConstraintIntersection;
          // eraseEdge(pe);
          eraseEdge(pe);
          return 0;
        }

        break;

      } else if (isec == DcGeometry::EdgesTouch ) {

        // detect case of overlap
        status = UnhandledMixedConstraint;
        // eraseEdge( pe );
        eraseEdge(pe);
        return 0;
      }
    }

    if (ti != NotFound)
      break;

    // extend set of triangles to search
    if ( not extendCache() )
      break;
  }

  if (ti == NotFound) {
    // eraseEdge(pe);
    eraseEdge(pe);
    return 0;
  }

  // if a starting triangle for Anglada's walk along (src,trg) was found,
  // start identfying further sliced triangles starting from there
  Indices ifaces, vleft, vright;
  ifaces.push_back(ti);
  while (pcut != 0) {

    const uint es = pcut->source();
    const uint et = pcut->target();
    int ori = geo.orientation(src, trg, es);
    if (ori == DcGeometry::CounterClockwise) {
      vleft.push_back(es);
      vright.push_back(et);
    } else {
      vleft.push_back(et);
      vright.push_back(es);
    }

    // determine next face across pcut
    ti = pcut->otherFace(ti);
    if (ti == NotFound)
      break;
    if (not insert_once(ifaces, ti))
      break;

    const DcFace & f( faces[ti] );
    if (not f.valid())
      break;

    // stop if this face contains the target vertex of the imprinted edge
    if (f.find(trg) != NotFound)
      break;

    // otherwise, look for another edge of ti which intersects (src,trg)
    pcut = 0;
    for (int k=0; k<3; ++k) {
      uint sf = f.esource(k);
      uint tf = f.etarget(k);

      // sort the two for comparison with (sf,tf)
      if (sf > tf)
        swap(sf,tf);

      // check if this is the same edge as the previous pcut
      if (sf == es and tf == et)
        continue;

      // check whether this edge touches (src,trg)
      // TODO : handle the case where one of the edges touching trg is
      //        colinear with (src,trg)
      if (sf == src or sf == trg)
        continue;
      if (tf == src or tf == trg)
        continue;

      int isec = geo.edgesIntersect(src, trg, sf, tf);
      if (isec == DcGeometry::EdgesIntersect) {
        pcut = findEdge(sf, tf);
        assert(pcut != 0);
        break;
      } else if (isec == DcGeometry::EdgesColinear) {
        assert(!"Existing edge colinear with constraint!");
        status = UnhandledMixedConstraint;
        eraseEdge(pe);
        return 0;
      }
    }

    // continue to walk along triangles across pcut
  }

  if (vleft.empty() and vright.empty()) {
    status = InconsistentTopology;
    eraseEdge(pe);
    return 0;
  }

  carveAndTriangulate(src, trg, ifaces, vleft, vright);

  status = StatusOk;
  return pe;
}

DcEdge *DelaunayCore::imprintOverlappingEdge(uint csrc, uint ctrg)
{
  // construct edge to enforce
  DcEdge *pe(0);
  pe = constructEdge(csrc, ctrg);
  edges.insert(pe);

  const uint src = pe->source();
  const uint trg = pe->target();

  // faces to erase, left and right vertex sets
  Indices ifaces, vleft, vright;

  // search face cache for a triangle which contains src and has an edge
  // which is intersected by (src,trg)
  uint vpivot(src);
  deque<uint> nbq;
  while (vpivot == src) {

    const int nfc = faceCache.size();
    for (int i=0; i<nfc; ++i) {

      const DcFace & f( faces[faceCache[i]] );
      if (not f.valid())
        continue;

      // locate vertex src in triangle f
      uint isrc = f.find(src);
      if (isrc == NotFound)
        continue;

      // determine the edge which does not contain src
      const uint *vf = f.vertices();
      const uint sf = vf[ (isrc+1)%3 ];
      const uint tf = vf[ (isrc+2)%3 ];
      assert(sf != tf);

      int isec = geo.edgesIntersect(src, trg, sf, tf);
      if (isec == DcGeometry::EdgesIntersect) {

        // detected edge intersecting constraint -> indicates mixed case
        // of overlap and intersection
        assert(!"Mixed constraint intersection and overlap not handled");
        status = UnhandledMixedConstraint;
        eraseEdge(pe);
        return 0;

      } else if (isec == DcGeometry::EdgesTouch ) {

        // the one edge in f which does not contain src has a vertex *on*
        // the constraint (src,trg), meaning that one edge of the triangle
        // overlaps (src,trg) - must be erased.
        insert_once(ifaces, faceCache[i]);
        int sori = geo.orientation(src, trg, sf);
        if (sori == DcGeometry::CounterClockwise)
          vleft.push_back(sf);
        else if (sori == DcGeometry::Clockwise)
          vright.push_back(sf);
        int tori = geo.orientation(src, trg, tf);
        if (tori == DcGeometry::CounterClockwise)
          vleft.push_back(tf);
        else if (tori == DcGeometry::Clockwise)
          vright.push_back(tf);

        // both neighbors of pce need to be eliminated
        DcEdge *pce = findEdge(sf, tf);
        assert(pce != 0);
        nbq.push_back(pce->left());
        nbq.push_back(pce->right());
        // cout << "Marked f" << pce->left() << " and f" << pce->right() << endl;

        // locate the edge which is overlapping (src,trg)
        uint vo = (sori == DcGeometry::Colinear) ? sf : tf;
        DcEdge *peo = findEdge(src, vo);
        assert(peo != 0);

        // if both faces
        const uint fleft = peo->left();
        const uint fright = peo->right();
        bool leftFound = (fleft == NotFound) or
                         (binary_search(ifaces.begin(), ifaces.end(), fleft));
        bool rightFound = (fright == NotFound) or
                          (binary_search(ifaces.begin(), ifaces.end(), fright));
        if (leftFound and rightFound)
          vpivot = vo;

      } else {

        // face touches src but the one edge in it which does not contain src
        // neither intersects nor touches constraint

      }
    }

    // terminate search as soon as a new pivot vertex is identified
    if (vpivot != src)
      break;

    // extend set of triangles to search
    if ( not extendCache() )
      break;
  }

  if (ifaces.empty()) {
    status = InconsistentTopology;
    eraseEdge(pe);
    return 0;
  }

  if (ifaces.back() == NotFound)
    ifaces.pop_back();

  // walk along edges overlapped by constraint
  while (not nbq.empty()) {

    uint ti = nbq.front();
    nbq.pop_front();
    if (ti == NotFound)
      continue;

    // already processed ?
    if ( binary_search(ifaces.begin(), ifaces.end(), ti) )
      continue;

    const DcFace & f( faces[ti] );
    if (not f.valid())
      continue;

    // locate pivot in current face
    uint isrc = f.find( vpivot );
    if (isrc == NotFound)
      continue;

    insert_once(ifaces, ti);

    // determine the one edge which does not contain src
    const uint *vf = f.vertices();
    const uint sf = vf[ (isrc+1)%3 ];
    const uint tf = vf[ (isrc+2)%3 ];
    assert(sf != tf);

    // cout << "Processing f" << ti << " : " << f << endl;

    int isec = geo.edgesIntersect(src, trg, sf, tf);
    assert(isec != DcGeometry::EdgesColinear);
    if (isec == DcGeometry::EdgesIntersect) {
      assert(!"Mixed constraint intersection and overlap not handled");
      eraseEdge(pe);
      status = UnhandledMixedConstraint;
      return 0;
    } else if (isec == DcGeometry::EdgesTouch ) {

      int sori = geo.orientation(src, trg, sf);
      if (sori == DcGeometry::CounterClockwise)
        vleft.push_back(sf);
      else if (sori == DcGeometry::Clockwise)
        vright.push_back(sf);
      int tori = geo.orientation(src, trg, tf);
      if (tori == DcGeometry::CounterClockwise)
        vleft.push_back(tf);
      else if (tori == DcGeometry::Clockwise)
        vright.push_back(tf);

      // both neighbors of pce need to be eliminated
      DcEdge *pce = findEdge(sf, tf);
      assert(pce != 0);
      nbq.push_back(pce->left());
      nbq.push_back(pce->right());
      // cout << "Marked f" << pce->left() << " and f" << pce->right() << endl;

      // locate the edge which is overlapping (src,trg)
      uint vo = (sori == DcGeometry::Colinear) ? sf : tf;
      DcEdge *peo = findEdge(vpivot, vo);
      assert(peo != 0);

      const uint fleft = peo->left();
      const uint fright = peo->right();
      bool leftFound = (fleft == NotFound) or
                       (binary_search(ifaces.begin(), ifaces.end(), fleft));
      bool rightFound = (fright == NotFound) or
                        (binary_search(ifaces.begin(), ifaces.end(), fright));
      if (leftFound and rightFound)
        vpivot = vo;

    } else if (isec == DcGeometry::NoEdgeIntersection) {

      // this is a face which only touches (src,trg) in vpivot
      DcEdge *pvs = findEdge(vpivot, sf);
      assert(pvs != 0);
      if (pvs->left() == ti)
        nbq.push_back( pvs->right() );
      else
        nbq.push_back( pvs->left() );

      DcEdge *pvt = findEdge(vpivot, tf);
      assert(pvt != 0);
      if (pvt->left() == ti)
        nbq.push_back( pvt->right() );
      else
        nbq.push_back( pvt->left() );

    }

    if (vpivot == trg)
      break;
  }

  carveAndTriangulate(src, trg, ifaces, vleft, vright);

  status = StatusOk;
  return pe;
}

void DelaunayCore::carveAndTriangulate(uint src, uint trg,
                                       const Indices &ifaces,
                                       Indices &vleft, Indices &vright)
{
  // clean up left/right vertex sets which contain polygons to retriangulate
  vleft.erase( std::unique(vleft.begin(), vleft.end()), vleft.end() );
  vright.erase( std::unique(vright.begin(), vright.end()), vright.end() );

  // erase all intersected faces
  for (uint i=0; i<ifaces.size(); ++i) {
    // cout << "Erasing f" << ifaces[i] << " : " << faces[ifaces[i]] << endl;
    detachFace(ifaces[i]);
    eraseFace(ifaces[i]);
  }

  // retriangulate hole(s)
  if (not vleft.empty())
    triangulatePolygon(src, trg, vleft.begin(), vleft.end());
  if (not vright.empty())
    triangulatePolygon(src, trg, vright.begin(), vright.end());
}

bool DelaunayCore::extendCache()
{
  const int nfc = faceCache.size();
  if ( uint(nfc) >= nValidFaces())
    return false;

  // collect edges of all faces currently in cache in order to minimize
  // the number of calls to findEdge()
  std::vector<BasicEdge> fcedges(3*nfc);
  for (int i=0; i<nfc; ++i) {
    if ( faces[faceCache[i]].valid() ) {
      const uint *vf = faces[faceCache[i]].vertices();
      for (int k=0; k<3; ++k)
        fcedges[3*i+k] = BasicEdge( vf[k], vf[(k+1)%3] );
    }
  }

  sort_unique(fcedges);
  for (uint i=0; i<fcedges.size(); ++i) {
    DcEdge *pce = findEdge( fcedges[i].source(), fcedges[i].target() );
    if (pce != 0) {
      faceCache.push_back( pce->left() );
      faceCache.push_back( pce->right() );
    }
  }

  sort_unique(faceCache);
  if (faceCache.back() == NotFound)
    faceCache.pop_back();
  cout << "Extended face search set to " << faceCache.size() << endl;

  return (faceCache.size() > uint(nfc));
}

void DelaunayCore::legalizeEdge(uint src, uint trg, uint v)
{
  if (v == NotFound or src == NotFound or trg == NotFound)
    return;

  legalizeEdge(findEdge(src, trg), v);
}

void DelaunayCore::legalizeEdge(DcEdge *pe, uint v)
{
  if (pe == 0)
    return;

  if (pe->checkFlag(DcEdge::Constrained))
    return;
  if (pe->checkFlag(DcEdge::Feature))
    return;

  uint ft = NotFound;
  if (pe->left() != NotFound) {
    if (faces[pe->left()].find(v) == NotFound)
      ft = pe->left();
    else
      ft = pe->right();
  }

  // there is no opposed face which needs testing, perhaps because pe
  // is on a boundary and the only neighbor face contains v
  if (ft == NotFound)
    return;

  assert(faces[ft].valid());
  assert(faces[ft].find(v) == NotFound);
  if (not geo.encroaches(*this, faces[ft].vertices(), v))
    return;

  uint opv = faces[ft].opposedVertex(pe->source(), pe->target());
  assert(opv != NotFound);

  uint src = pe->source();
  uint trg = pe->target();
  if ( flipEdge(pe) ) {
    legalizeEdge( src, opv, v );
    legalizeEdge( trg, opv, v );
  }
}

void DelaunayCore::legalizeStack(FlipStack & stack)
{
  // broken idea : edges may be flipped while on the stack

  uint iter = 0;
  while (not stack.empty()) {

    EncPair p = stack.back();
    stack.pop_back();
    DcEdge *pe = p.first;
    uint v = p.second;

    assert(pe != 0);
    assert(v != NotFound);
    if (pe->checkFlag(DcEdge::Constrained))
      continue;
    if (pe->checkFlag(DcEdge::Feature))
      continue;

    uint ft = NotFound;
    if (pe->left() != NotFound) {
      if (faces[pe->left()].find(v) == NotFound)
        ft = pe->left();
      else
        ft = pe->right();
    }
    assert(ft != NotFound);

    if (not geo.encroaches(*this, faces[ft].vertices(), v))
      continue;

    EncPair pa, pb;
    pa = std::make_pair((DcEdge *) 0,NotFound);
    pb = std::make_pair((DcEdge *) 0,NotFound);
    if (ft != NotFound) {
      uint opv = faces[ft].opposedVertex(pe->source(), pe->target());
      assert(opv != NotFound);
      DcEdge *ps = findEdge(pe->source(), opv);
      assert(ps != 0);
      pa = std::make_pair(ps, pe->target());
      DcEdge *pt = findEdge(pe->target(), opv);
      assert(pt != 0);
      pb = std::make_pair(pt, pe->source());
    }

    if (flipEdge(pe)) {
      if (pa.first != 0)
        stack.push_back(pa);
      if (pb.first != 0)
        stack.push_back(pb);
    }

    ++iter;
  }
}

void DelaunayCore::triangulatePolygon(uint bs, uint bt,
                                      Indices::const_iterator vbeg,
                                      Indices::const_iterator vend)
{
  // calling function must check for this
  assert(std::distance(vbeg, vend) > 0);

  Indices::const_iterator itr(vbeg), mid(vbeg);
  uint vf[3];

  vf[0] = bs;
  vf[1] = bt;
  vf[2] = *mid;
  int ori = geo.orientation(vf[0], vf[1], vf[2]);
  if (ori == DcGeometry::Clockwise)
    std::swap(vf[1], vf[2]);

  ++itr;
  while (itr != vend) {
    if (geo.encroaches(*this, vf, *itr)) {
      mid = itr;
      vf[0] = bs;
      vf[1] = bt;
      vf[2] = *mid;
      ori = geo.orientation(vf[0], vf[1], vf[2]);
      if (ori == DcGeometry::Clockwise)
        std::swap(vf[1], vf[2]);
    }
    ++itr;
  }

  const uint vi = *mid;
  const uint fi = addFace(bs, bt, vi);
  assert(fi != NotFound);
  DcEdge *pe = findEdge(bs, bt);
  assert(pe != 0);
  pe->appendFace(fi);
  DcEdge *psn = findEdge(bs, *mid);
  if (psn == 0) {
    psn = constructEdge(bs, vi);
    edges.insert(psn);
  }
  psn->appendFace(fi);

  DcEdge *ptn = findEdge(bt, vi);
  if (ptn == 0) {
    ptn = constructEdge(bt, vi);
    edges.insert(ptn);
  }
  ptn->appendFace(fi);

  // assumes that (vbeg,vend) are sorted along (src,trg) :

  if ( std::distance(vbeg,mid) > 0 ) {
    triangulatePolygon(bs, *mid, vbeg, mid);
  }

  if ( std::distance(mid+1,vend) > 0 ) {
    triangulatePolygon(*mid, bt, mid+1, vend);
  }
}

CPHINT_HOTSPOT_BEGIN

void DelaunayCore::eraseFace(uint k)
{
  if (k < faces.size()) {
    DcFace &f( faces[k] );
    geo.eraseFace(k, f.vertices());
    f.invalidate();
    invalidFaces.push_back(k);
  }
}

CPHINT_HOTSPOT_END

uint DelaunayCore::eatHole(uint f)
{
  uint neaten = 0;
  Indices stack;
  stack.push_back(f);
  while (not stack.empty()) {
    f = stack.back();
    stack.pop_back();
    const DcFace & fc( faces[f] );
    if (not fc.valid())
      continue;
    for (int k=0; k<3; ++k) {
      DcEdge *pe = findEdge(fc.esource(k), fc.etarget(k));
      assert(pe != 0);
      if (pe->checkFlag(DcEdge::Constrained))
        continue;

      uint g = pe->otherFace(f);
      if (g != NotFound and faces[g].valid())
        stack.push_back(g);
    }
    detachFace(f);
    eraseFace(f);
    ++neaten;
  }

  return neaten;
}

void DelaunayCore::triangles(Indices &tri) const
{
  const int nf = faces.size();
  const int nt = nf - invalidFaces.size();
  tri.resize(3*nt);
  uint k = 0;
  for (int i=0; i<nf; ++i) {
    const DcFace & f( faces[i] );
    if (f.valid()) {
      const uint *v = f.vertices();
      for (int j=0; j<3; ++j)
        tri[k+j] = v[j];
      k += 3;
    }
  }
  assert(k == tri.size());
}

void DelaunayCore::constrainedEdges(Indices &lns) const
{
  DcEdgeItr itr, last = edges.end();
  for (itr = edges.begin(); itr != last; ++itr) {
    const DcEdge *pe = *itr;
    if (not pe->valid())
      continue;
    if (pe->getFlags() & DcEdge::Constrained) {
      lns.push_back( pe->source() );
      lns.push_back( pe->target() );
    }
  }
}

void DelaunayCore::setEdgeFlags(int pattern, int flags)
{
  DcEdgeItr itr, last = edges.end();
  for (itr = edges.begin(); itr != last; ++itr) {
    DcEdge *pe = *itr;
    int ef = pe->getFlags();
    if ((ef & pattern) == 0)
      continue;
    pe->setFlag(flags);
  }
}

void DelaunayCore::unsetEdgeFlags(int pattern, int flags)
{
  DcEdgeItr itr, last = edges.end();
  for (itr = edges.begin(); itr != last; ++itr) {
    DcEdge *pe = *itr;
    int ef = pe->getFlags();
    if ((ef & pattern) == 0)
      continue;
    pe->unsetFlag(flags);
  }
}

void DelaunayCore::constrainedVertices(std::vector<bool> &cvx,
                                       int edgeflag) const
{
  DcEdgeItr itr, last = edges.end();
  for (itr = edges.begin(); itr != last; ++itr) {
    const DcEdge *pe = *itr;
    if (not pe->valid())
      continue;
    uint src = pe->source();
    uint trg = pe->target();
    bool isce = allbits_set(pe->getFlags(), edgeflag);
    bool isbe = (pe->degree() != 2);
    cvx[src] = cvx[src] | isce | isbe;
    cvx[trg] = cvx[trg] | isce | isbe;
  }
}

void DelaunayCore::boundaryVertices(std::vector<bool> &bvx) const
{
  DcEdgeItr itr, last = edges.end();
  for (itr = edges.begin(); itr != last; ++itr) {
    const DcEdge *pe = *itr;
    if (not pe->valid())
      continue;
    uint src = pe->source();
    uint trg = pe->target();
    bool isbe = (pe->degree() != 2);
    bvx[src] = bvx[src] | isbe;
    bvx[trg] = bvx[trg] | isbe;
  }
}

void DelaunayCore::clear()
{
  edges.clear();
  faces.clear();
  invalidFaces.clear();
  faceCache.clear();
  vinConEdges.clear();
  status = StatusOk;
  edgePool.purge_memory();
}
