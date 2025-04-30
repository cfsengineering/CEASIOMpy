
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
 
#include <genua/dbprint.h>
#include "meshcomponent.h"
#include "ttintersector.h"
#include "tticonnection.h"

using namespace std;

static inline Real foot_point(const Vct3 & p1, const Vct3 & p2,
                              const Vct3 & a)
{
  const Real accept_dsq = 1e-6;
  Vct3 r(a - p1);
  Vct3 d(p2 - p1);
  Real t = dot(r,d) / sq(d);
  Real dsq = sq( (1.0-t)*p1 + t*p2 - a );
  return (dsq < accept_dsq) ? t : 1e18;
}

static inline Real foot_par(const Vct3 & p1, const Vct3 & p2,
                            const Vct3 & a)
{
  Vct3 r(a - p1);
  Vct3 d(p2 - p1);
  return dot(r,d) / sq(d);
}

//static inline bool could_match(Real t[])
//{
//  if (t[0] > t[1])
//    std::swap(t[0], t[1]);
//  return ((t[1] >= 0.0) and (t[0] <= 1.0));
//}

//static inline int set_if_inside(Real t, const Vct3 & p1,
//                                const Vct3 & p2, Vct3 & ip)
//{
//  if (t >= 0.0 and t <= 1.0) {
//    ip = (1.0-t)*p1 + t*p2;
//    return 1;
//  }
//  return 0;
//}

static inline bool pinside(Real t)
{
  return ((t >= 0.0) and (t <= 1.0));
}

static inline bool poutside(Real t)
{
  return (not pinside(t));
}

const Vct3 & TTiConnection::ConVertex::pos() const
{
  assert(cmp != 0);
  return cmp->vertex(vix);
}

bool TTiConnection::appendSegments(TTIntersector & tti)
{
  // identify edges which lie on the specified line
  bvx.clear();
  Indices aedges, bedges;
  bool ok = true;
  ok &= collectCandidates(acomp, ap1, ap2, aedges);
  ok &= collectCandidates(bcomp, bp1, bp2, bedges);
  if (not ok)
    return false;

  // sort border vertices wrt edge arclength parameter
  std::sort(bvx.begin(), bvx.end());

//  // debug
//  for (uint i=0; i<bvx.size(); ++i) {
//    cout << i << " : "  << bvx[i].tc << (bvx[i].cmp == acomp ? " a " : " b ")
//         << bvx[i].pos() << endl;
//  }


  // compute opposed triangle for each border vertex
  const int nbv = bvx.size();
  Indices optri(nbv);

  // parallel
  for (int i=0; i<nbv; ++i) {
    if ( bvx[i].cmp == acomp ) {
      uint iedge = nearestEdge(bcomp, bedges, bvx[i].pos());
      optri[i] = triangleFromEdge( tti, bcomp, iedge );
    } else {
      uint iedge = nearestEdge(acomp, aedges, bvx[i].pos());
      optri[i] = triangleFromEdge( tti, acomp, iedge );
    }
  }

  // build segments from vertices,
  uint isrc(0), itrg(0);
  while (itrg < bvx.size()) {

    // skip identical points
    do {
      ++itrg;
      if (itrg >= bvx.size())
        break;
    } while (bvx[itrg].tc == bvx[isrc].tc);
    if (itrg >= bvx.size())
      break;

    // debug
    cout << "Connecting " << isrc << " to " << itrg << endl;
    cout << "src at " << bvx[isrc].pos()
         << " trg " << bvx[itrg].pos() << endl;

    uint ttri = optri[itrg];
    if (ttri == optri[isrc])
      ttri = triangleFromVertex(tti, bvx[itrg].cmp, bvx[itrg].vix);
    if (optri[isrc] != NotFound and ttri != NotFound) {

      // confirmed : vertex actually is in ttri
      //             itri1 != itri2

      tti.enforce(optri[isrc], ttri,
                  bvx[isrc].pos(), bvx[itrg].pos());
    } else {
      return false;
    }

    isrc = itrg;
    if (isrc == bvx.size() - 1)
      break;
  }


//  dbprint(aedges.size(), " candidate edges on a,");
//  dbprint(bedges.size(), " candidate edges on b.");

//  Vct3 st[4];
//  uint nseg = 0;
//  const int na = aedges.size();
//  const int nb = bedges.size();
//  for (int i=0; i<na; ++i) {
//    for (int j=0; j<nb; ++j) {
//      if ( connectedPair(aedges[i], bedges[j], st) ) {
//        uint atri = triangleFromEdge(tti, acomp, aedges[i]);
//        uint btri = triangleFromEdge(tti, bcomp, bedges[j]);
//        if (atri == NotFound or btri == NotFound)
//          return false;
//        else
//          tti.enforce(atri, btri, st[0], st[1]);
//        ++nseg;
//      }
//    }
//  }

//  dbprint(nseg, " connection constraint segments inserted.");

  return true;
}

bool TTiConnection::connectedPair(uint ae, uint be, Vct3 st[]) const
{
  const Vct3 & asrc( acomp->vertex( acomp->edge(ae).source() ) );
  const Vct3 & atrg( acomp->vertex( acomp->edge(ae).target() ) );
  const Vct3 & bsrc( bcomp->vertex( bcomp->edge(be).source() ) );
  const Vct3 & btrg( bcomp->vertex( bcomp->edge(be).target() ) );

  // compute foot point parameters on line a and b
  Real ta[2], tb[2];
  ta[0] = foot_point(asrc, atrg, bsrc);
  ta[1] = foot_point(asrc, atrg, btrg);
  tb[0] = foot_point(bsrc, btrg, asrc);
  tb[1] = foot_point(bsrc, btrg, atrg);

//  // quick check whether segments are entirely disjoint, i.e.
//  // do not overlap at all
//  bool possible = true;
//  possible &= could_match(ta);
//  possible &= could_match(tb);
//  if (not possible)
//    return false;

  // how to determine if foot points are too far away for merging?

  if ( pinside(ta[0]) and poutside(ta[1]) ) {
    st[0] = bsrc;
  } else if ( pinside(ta[1]) and poutside(ta[0]) ) {
    st[0] = btrg;
  } else if ( pinside(ta[1]) and pinside(ta[0]) ) {
    st[0] = bsrc;
    st[1] = btrg;
    return true;
  }

//  else {

//    dbprint("***No match:");
//    dbprint("ta", ta[0], ta[1]);
//    dbprint("tb", tb[0], tb[1]);
//    dbprint("asrc", asrc, "atrg", atrg);
//    dbprint("bsrc", bsrc, "btrg", btrg);


//    return false;
//  }

  if ( pinside(tb[0]) and poutside(tb[1]) ) {
    st[1] = asrc;
  } else if ( pinside(tb[1]) and poutside(tb[0]) ) {
    st[1] = atrg;
  } else if ( pinside(tb[1]) and pinside(tb[0]) ) {
    st[0] = asrc;
    st[1] = atrg;
    return true;
  } else {

        dbprint("***No match:");
        dbprint("ta", ta[0], ta[1]);
        dbprint("tb", tb[0], tb[1]);
        dbprint("asrc", asrc, "atrg", atrg);
        dbprint("bsrc", bsrc, "btrg", btrg);

    return false;
  }

  // compute those projection points (st) of the end points of one segment onto
  // the opposing segment which lie inside the opposing segment;
  // c is the number of such projection points
  // uint c = 0;
  //  c += set_if_inside(ta[0], asrc, atrg, st[c]);
  //  c += set_if_inside(ta[1], asrc, atrg, st[c]);
  //  c += set_if_inside(tb[0], bsrc, btrg, st[c]);
  //  c += set_if_inside(tb[1], bsrc, btrg, st[c]);

  //  if (ta[0] >= 0 and ta[0] <= 1)
  //    st[c++] = bsrc;
  //  if (ta[1] >= 0 and ta[1] <= 1)
  //    st[c++] = btrg;
  //  if (tb[0] >= 0 and tb[0] <= 1)
  //    st[c++] = asrc;
  //  if (tb[1] >= 0 and tb[1] <= 1)
  //    st[c++] = atrg;



//  if (c < 2)
//    return false;

//  // catch case of single shared point
//  if (c == 2 and sq(st[0]-st[1]) < gmepsilon)
//    return false;

//  // sort out which points to use if c > 2 (degeneration)
//  if (c == 3) {
//    Real d01 = sq( st[0] - st[1] );
//    Real d02 = sq( st[0] - st[2] );
//    if (d01 < d02)
//      std::swap(st[1], st[2]);
//  }

  // assumption:
  // c == 4 : always set in pairs, so st[0], st[1] valid

  // on return, st[0] and st[1] define an intersection segment of the two
  // triangles on each side of the connection

//  int cs = -1;

//  if ((ta[0] <= 0) and pinside(ta[1]) and pinside(tb[0]) and (tb[1] >= 1)) {
//    cs = 0;
//    st[0] = btrg;
//    st[1] = asrc;
//  } else if (pinside(ta[0]) and pinside(ta[1]) and (tb[0] <= 0) and (tb[1] >= 1)) {
//    cs = 1;
//    st[0] = bsrc;
//    st[1] = btrg;
//  } else if (pinside(ta[0]) and (ta[1] >= 1) and (tb[0] <= 0) and pinside(tb[1])) {
//    cs = 2;
//    st[0] = bsrc;
//    st[1] = atrg;
//  } else if ((ta[0] <= 0) and (ta[1] >= 1) and pinside(tb[0]) and pinside(tb[1])) {
//    cs = 3;
//    st[0] = asrc;
//    st[1] = atrg;
//  } else {

//    dbprint("***No match:");
//    dbprint("ta", ta[0], ta[1]);
//    dbprint("tb", tb[0], tb[1]);
//    dbprint("asrc", asrc, "atrg", atrg);
//    dbprint("bsrc", bsrc, "btrg", btrg);

//    return false;
//  }

  // debug
  dbprint("Enforcing", st[0], "to", st[1]);
  dbprint("ta", ta[0], ta[1]);
  dbprint("tb", tb[0], tb[1]);
  dbprint("asrc", asrc, "atrg", atrg);
  dbprint("bsrc", bsrc, "btrg", btrg);

  return true;
}

bool TTiConnection::collectCandidates(const MeshComponent *comp,
                                      const Vct2 & p1, const Vct2 & p2,
                                      Indices & edg)
{
  // vertex string
  Indices vstr;

  // look for indices of vertex p1 and p2 which must exist
  const int nv = comp->nvertices();
  Real mindst1 = std::numeric_limits<Real>::max();
  Real mindst2 = std::numeric_limits<Real>::max();
  Real dst;
  uint ip1(NotFound), ip2(NotFound);
  for (int i=0; i<nv; ++i) {
    dst = sq(p1 - comp->parameter(i));
    if (dst < mindst1) {
      mindst1 = dst;
      ip1 = i;
    }
    dst = sq(p2 - comp->parameter(i));
    if (dst < mindst2) {
      mindst2 = dst;
      ip2 = i;
    }
  }

  // parameter space direction
  Vct2 direct = (p2 - p1).normalized();

  // acceptance limit
  const Real cphi_accept = 0.8;

  // guard against infinite recursion
  uint nemax = comp->nedges();

  vstr.push_back(ip1);

  // walk along mesh edges in the direction p2-p1 and
  // collect triangles encountered
  uint iprev = ip1, inext = NotFound;
  do {
    TriMesh::nb_edge_iterator ite, elast;
    elast = comp->v2eEnd(iprev);
    Real mxcphi = -std::numeric_limits<Real>::max();
    uint ebest = NotFound;
    const Vct2 & qlast( comp->parameter(iprev) );
    for (ite = comp->v2eBegin(iprev); ite != elast; ++ite) {
      uint opp = ite->opposed(iprev);
      Real cphi = cosarg(direct, comp->parameter(opp) - qlast);
      if (cphi > mxcphi) {
        inext = opp;
        ebest = ite.index();
        mxcphi = cphi;
      }
    }

    if (mxcphi < cphi_accept) {
      cout << "Best cphi found is " << mxcphi << endl;
      return false;
    }

    vstr.push_back(inext);
    edg.push_back( ebest );
    iprev = inext;

    if (edg.size() > nemax) {
      dbprint("TTiConnection::collectCandidates - Infinite recursion.");
      return false;
    }

  } while (inext != ip2);

  assert(vstr.back() == ip2);

  // store border vertices
  const int nbv = vstr.size();
  PointList<2> border(nbv);
  Vector arclen(nbv);
  for (int i=0; i<nbv; ++i)
    border[i] = comp->parameter( vstr[i] );
  for (int i=1; i<nbv; ++i)
    arclen[i] = arclen[i-1] + norm(border[i] - border[i-1]);

  Real alf = 1.0 / arclen.back();

  // create border vertex objects
  for (int i=0; i<nbv; ++i)
    bvx.push_back( ConVertex(comp, alf*arclen[i], vstr[i]) );

  return true;
}

uint TTiConnection::triangleFromEdge(const TTIntersector & tti,
                                     const MeshComponent *comp,
                                     uint eix) const
{
  // locate face
  if ( comp->edegree(eix) != 1 ) {
    cout << "Edge " << eix << " has degree " << comp->edegree(eix) << endl;
    return NotFound;
  }

  uint fix = comp->e2fBegin(eix).index();
  uint idx = tti.bsearchFace( comp->face(fix) );

  return idx;
}

uint TTiConnection::nearestEdge(const MeshComponent *cmp,
                                const Indices & edges,
                                const Vct3 & p) const
{
  Real dmin = std::numeric_limits<Real>::max();
  uint ibest(NotFound);
  const int ne = edges.size();
  for (int i=0; i<ne; ++i) {
    const Vct3 & src( cmp->vertex(cmp->edge(edges[i]).source()) );
    const Vct3 & trg( cmp->vertex(cmp->edge(edges[i]).target()) );
    Real t = foot_par(src, trg, p);
    Vct3 pe = (1.0 - t)*src + t*trg;
    Real dsq = sq(pe - p);
    if (dsq < dmin) {
      ibest = i;
      dmin = dsq;
    }
  }

  return edges[ibest];
}

uint TTiConnection::triangleFromVertex(const TTIntersector & tti,
                                       const MeshComponent *comp,
                                       uint vix) const
{
  assert(comp != 0);
  TriMesh::nb_edge_iterator ite, elast = comp->v2eEnd(vix);
  for (ite = comp->v2eBegin(vix); ite != elast; ++ite) {
    if ( comp->edegree(ite.index()) == 1 )
      return triangleFromEdge( tti, comp, ite.index() );
  }

  return NotFound;
}
