
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

#include "pentagrow.h"
#include <genua/ioglue.h>
#include <genua/pattern.h>
#include <genua/boxsearchtree.h>
#include <genua/smallqr.h>
#include <genua/transformation.h>
#include <genua/parallel_loop.h>
#include <genua/timing.h>
#include <genua/configparser.h>
#include <predicates/predicates.h>
#include <vector>

using std::string;

PentaGrow::PentaGrow(const TriMesh &m) : mwall(m)
{
  // default values
  cosFeatureAngle = cos(rad(44.0));
  cosconcave = cos(rad(3.0));
  cosSharpAngle = cos(rad(120.0));

  vtype.clear();
  etype.clear();
}

void PentaGrow::configure(const ConfigParser &cfg)
{
  firstCellHeight = cfg.getFloat("InitialHeight", 0.00001);
  maxAbsHeight = cfg.getFloat("MaxLayerThickness", 1.);
  maxRelHeight = cfg.getFloat("MaxRelativeHeight", 5.);
  numPrismLayers = cfg.getFloat("NLayers", 21);
  maxExpansionFactor = cfg.getFloat("MaxGrowthRatio", 1.5);
  attemptGridUntangling = cfg.getBool("UntangleGrid", true);
  defaultInvGrowthExp = cfg.getFloat("WallNormalTransition", 0.05);

  // when angle between two triangles is larger than this,
  // the ridge is treated as an intentional slope discontinuity
  // otherwise, its regarded as discretization artifact
  cosFeatureAngle = cos(rad(cfg.getFloat("FeatureAngle", 44.0)));
  cosSharpAngle = cos(rad(cfg.getFloat("SharpEdgeAngle", 120.0)));

  // log function values while optimization running?
  chattyOptimization = cfg.getBool("VerboseOptimization", false);

  // set to zero to disable envelope optimization entirely
  maxOptimizationTime = cfg.getFloat("MaxOptimizationTime", 30.0);

  // warn if NLopt wasn't configured on this system
#ifndef HAVE_NLOPT
  if (maxOptimizationTime > 0)
    clog << "[w] Envelope optimization requested but "
            "NLopt not available: ignored"
         << endl;
#endif
}

void PentaGrow::edgeMap(ConnectMap &map) const
{
  map.clear();

  const size_t nv = mwall.nvertices();
  map.beginCount(nv);
  for (size_t i = 0; i < nv; ++i)
    map.incCount(i, mwall.vdegree(i));
  map.endCount();

  TriMesh::nb_edge_iterator ite, elast;
  for (size_t i = 0; i < nv; ++i)
  {
    elast = mwall.v2eEnd(i);
    for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      map.append(i, ite->opposed(i));
  }
  map.compress();
}

void PentaGrow::classify(bool symmetry, Real y0)
{
  // make space
  const int nv = mwall.nvertices();
  const int ne = mwall.nedges();
  vtype.clear();
  // initialize all vtype with 0 = Undefined; necessary because of the
  // or'ing of convex/concave flags below
  vtype.resize(nv);

  // classify edges and mark vertices which are part of ridge edges
  etype.clear();
  etype.allocate(ne);

  // count number of convex/concave edges attached to each face
  const int nf = mwall.nfaces();
  Indices fncv(nf, 0), fncx(nf, 0);

  const Real ecphi = cos(1.25 * acos(cosFeatureAngle));
  for (int i = 0; i < ne; ++i)
  {
    // Search for the points on the cut edge and treat them differently
    const uint *nbf = mwall.firstFaceIndex(i);
    Vct3 nf1, nf2;
    Vct3 center1, center2;
    bool border_edge(symmetry and mwall.edegree(i) == 1 and mwall.vertex(mwall.edge(i).source())[1] < y0 + 0.0001 and mwall.vertex(mwall.edge(i).target())[1] < y0 + 0.0001);

    if (border_edge)
    {
      // We don't have two faces, so we use the mirror of the face, computing the normal
      const TriFace &f1(mwall.face(nbf[0]));
      center1 = f1.center();
      center2 = Vct3(center1[0], -center1[1], center1[2]);
      nf1 = f1.normal();
      nf2 = Vct3(nf1[0], -nf1[1], nf1[2]);
    }
    else
    {
      assert(mwall.edegree(i) == 2);
      const TriFace &f1(mwall.face(nbf[0]));
      const TriFace &f2(mwall.face(nbf[1]));
      nf1 = f1.normal();
      nf2 = f2.normal();
      center1 = f1.center();
      center2 = f2.center();
    }
    // skip this edge if normals are reasonably parallel
    Real cphi = cosarg(nf1, nf2);
    if (cphi > ecphi)
    {
      etype[i] = Flat;
      continue;
    }
    // ok, edge is a ridge; decide whether it's convex or not
    int flag = Ridge;
    const uint s = mwall.edge(i).source();
    const uint t = mwall.edge(i).target();
    Vct3 emid = 0.5 * (mwall.vertex(s) + mwall.vertex(t));
    Vct3 fmid = 0.5 * (center1 + center2);
    Vct3 nsum = nf1.normalized() + nf2.normalized();
    Real ccv = dot(nsum, fmid - emid);
    flag |= (ccv > 0) ? Concave : Convex;

    if (cphi < cosSharpAngle)
      flag |= Sharp;
    etype[i] = flag;

    if (flag & Concave)
    {
      ++fncv[nbf[0]];
      if (!border_edge)
        ++fncv[nbf[1]];
    }
    else if (flag & Convex)
    {
      ++fncx[nbf[0]];
      if (!border_edge)
        ++fncx[nbf[1]];
    }

    // bitwise 'or' vertex flags because a vertex can be on multiple
    // ridges, so that (vtype[i] & Concave) and (vtype[i] & Convex) could happen
    vtype[s] |= flag;
    vtype[t] |= flag;
  }

  // look for triangles which share three edges classed as the same
  // type of ridge which indicates that the feature angle was chosen too low
  for (int i = 0; i < nf; ++i)
  {
    if (fncv[i] > 2 or fncx[i] > 2)
    {
      std::stringstream ss;
      ss << "Wall triangle at " << mwall.face(i).center() << " bounded by ";
      ss << "three edges classified as ridges." << endl;
      ss << "Increase FeatureAngle configuration parameter." << endl;
      throw Error(ss.str());
    }
  }

  TriMesh::nb_edge_iterator ite, ebegin, elast;
  TriMesh::nb_face_iterator itf, fbegin, flast;
  for (int i = 0; i < nv; ++i)
  {
    // default - assume flat surface
    // if (vtype[i] == Undefined)
    //  vtype[i] = Flat;

    uint counterI(0), counterJ(0);
    uint tag(0), nccv(0), ncvx(0);
    uint vdeg = mwall.vdegree(i);
    if (symmetry and mwall.vertex(i)[1] < y0 + 0.0001)
      vdeg = 2 * vdeg - 2;
    //  Compensate for the double edge we are going to add (-2 for the two edges in the plane that we will not double)
    ebegin = mwall.v2eBegin(i);
    elast = mwall.v2eEnd(i);
    for (ite = ebegin; ite != elast; ++ite)
    {
      assert(ite->opposed(i) != NotFound);
      if (cosarg(wfn[i], wfn[ite->opposed(i)]) > cosFeatureAngle)
        ++counterI;
      tag = etype[ite.index()];
      nccv += (tag & Concave) != 0;
      ncvx += (tag & Convex) != 0;
      if (symmetry and mwall.vertex(i)[1] < y0 + 0.0001 and mwall.vertex(ite->opposed(i))[1] > y0 + 0.001)
      { // double the effect to counterbalance the fact that the edge is on the border and only have of the needed edges
        // we assume that wfn is in the y=y0 plane
        if (cosarg(wfn[i], wfn[ite->opposed(i)]) > cosFeatureAngle)
          ++counterI;
        nccv += (tag & Concave) != 0;
        ncvx += (tag & Convex) != 0;
      }
    }
    fbegin = mwall.v2fBegin(i);
    flast = mwall.v2fEnd(i);
    for (itf = fbegin; itf != flast; ++itf)
    {
      if (cosarg(wfn[i], itf->normal()) > cosFeatureAngle)
      {
        ++counterJ;
        if (symmetry and mwall.vertex(i)[1] < y0 + 0.0001)
          ++counterJ;
        // same we double the effect to compensate the missing half
        //(angle is the same by mirror)
      }
    }

    if (counterI == vdeg and counterJ == vdeg)
    {
      // All face and vertex normals parallel: Flat surface
      vtype[i] = Flat;
    }
    else if (ncvx > 2 and nccv == 0)
    {
      // more than 2 convex neighbouring edges
      // ConvexCorner type vertex
      vtype[i] = ConvexCorner;
    }
    else if (ncvx == 0 and nccv > 2)
    {
      // more than 2 concave neighbouring edges
      // ConcaveCorner type vertex
      vtype[i] = ConcaveCorner;
    }
    else if (ncvx == 2 and nccv == 0)
    {
      // Only two convex neighbouring edges
      // ConvexEdge type vertex
      vtype[i] = ConvexEdge;
    }
    else if (ncvx == 0 and nccv == 2)
    {
      // Only two concave neighbouring edges
      // Trench type vertex
      vtype[i] = Trench;
    }
    else if (ncvx == 1 and nccv == 1)
    {
      // 1 convex and 1 concave neighbouring edges
      // Wedgetype vertex
      vtype[i] = Wedge;
    }
    else if (ncvx > 0 and nccv > 0)
    {
      // Both convex and concave neighbouring edges
      // SaddleCorner type vertex
      vtype[i] = SaddleCorner;
    }

    if (counterI + counterJ == 0)
    {
      // No parallel vertex & face normals:
      // Wingtip(convex) or concave cone/wedge critical type vertex
      vtype[i] |= Conical;
    }

    // Clean undefined vertecies
    if (vtype[i] == Undefined && counterJ == vdeg)
    {
      // All face normals parallel:
      // Approximated flat surface, possibly connected to more critical vertices
      vtype[i] = Flat;
    }
    else if (vtype[i] == Undefined && counterJ != vdeg)
    {
      log("[W] Could not classify vertex at coordinates:", mwall.vertex(i));
      vtype[i] = Flat;
    }

  } // initial tag

  // Find & tag leading edge + fuselage intersecting vertices
  for (int i = 0; i < nv; ++i)
  {
    if (vtype[i] == Trench)
    {
      uint counterI = 0;
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      {
        if ((vtype[ite->opposed(i)] == Trench or
             vtype[ite->opposed(i)] == LeadingEdgeIntersection) and
            cosarg(wfn[i], wfn[ite->opposed(i)]) < cosconcave)
          ++counterI;
      }
      if (counterI != 0)
        vtype[i] = LeadingEdgeIntersection;
    }
  }

  // Find & Tag/UnTag  Conical / ConeTip / ConeDipp
  for (int i = 0; i < nv; ++i)
  {
    if (isClass(i, ConvexEdge) or hasClass(i, Ridge | Conical | Convex))
    {
      uint counterI = 0;
      uint counterJ = 0;
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      {
        if (vtype[ite->opposed(i)] != Flat)
          ++counterI;
        if (cosarg(wfn[i], wfn[ite->opposed(i)]) < 0.25 * cosFeatureAngle)
          ++counterJ;
        if (symmetry and mwall.vertex(i)[1] < y0 + 0.0001 and mwall.vertex(ite->opposed(i))[1] > y0 + 0.0001)
        {
          if (vtype[ite->opposed(i)] != Flat)
            ++counterI;
          if (cosarg(wfn[i], wfn[ite->opposed(i)]) < 0.25 * cosFeatureAngle)
            ++counterJ;
        }
      }
      if (counterI == 1 and counterJ != 0)
        vtype[i] = ConeTip;
    }
  }

  // Check/Clean Corners & Ridges with only flat neighbours
  // TODO: why are these corners tagged at all??
  for (int i = 0; i < nv; ++i)
  {
    if (hasClass(i, Corner) or hasClass(i, Ridge))
    {
      uint counterI = 0;
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      {
        if (vtype[ite->opposed(i)] != Flat)
          ++counterI;
      }
      if (counterI == 0)
        vtype[i] = Flat;
    } // no need to change for symmetry as we count if there is at least one
  }

  // Find and tag vertices with multiple neighbours of same type e.g.
  // coarse grid at trailing edge or wedge,trench etc.
  for (int i = 0; i < nv; ++i)
  {
    if (hasClass(i, Ridge | Conical | Concave))
    {
      uint nBC(0), nSC(0);
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      {
        if (vtype[ite->opposed(i)] == BluntCorner)
          ++nBC;
        if (vtype[ite->opposed(i)] == SaddleCorner)
          ++nSC;
        if (symmetry and mwall.vertex(i)[1] < y0 + 0.0001 and mwall.vertex(ite->opposed(i))[1] > y0 + 0.0001)
        {
          if (vtype[ite->opposed(i)] == BluntCorner)
            ++nBC;
          if (vtype[ite->opposed(i)] == SaddleCorner)
            ++nSC;
        }
      }
      if (nBC + nSC > 1)
        vtype[i] = Trench;
    }
    else if (hasClass(i, Ridge | Conical | Convex))
    {
      uint nCC(0), nCT(0);
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      {
        if (vtype[ite->opposed(i)] == ConvexCorner)
          ++nCC;
        if (vtype[ite->opposed(i)] == ConeTip)
          ++nCT;
        if (symmetry and mwall.vertex(i)[1] < y0 + 0.0001 and mwall.vertex(ite->opposed(i))[1] > y0 + 0.0001)
        {
          if (vtype[ite->opposed(i)] == ConvexCorner)
            ++nCC;
          if (vtype[ite->opposed(i)] == ConeTip)
            ++nCT;
        }
      }
      if (nCC + nCT > 1)
        vtype[i] = ConvexEdge;
    }
  }
}

void PentaGrow::adjustRidgeNormals(bool symmetry, Real y0)
{
  const int nv = mwall.nvertices();
  const uint ConcaveTag = Ridge | Concave;
  const uint SharpConvexTag = Ridge | Convex | Sharp;
  for (int i = 0; i < nv; ++i)
  {
    bool border_vertex(symmetry and mwall.vertex(i)[1] < y0 + 0.0001);

    if (isClass(i, Flat) or hasClass(i, ConeTip) or hasClass(i, RidgeConeTip))
      continue;

    uint ncv(0), ncx(0), nc(0);
    uint iex[2] = {NotFound, NotFound};
    uint iev[2] = {NotFound, NotFound};
    TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
    for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
    {
      bool edge_doubled(symmetry and border_vertex and mwall.vertex(ite->opposed(i))[1] > y0 + 0.0001);
      uint et = etype[ite.index()];

      if ((et & SharpConvexTag) == SharpConvexTag)
      {
        if (ncx < 2)
          iex[ncx] = ite.index();
        ++ncx;
        if (edge_doubled)
        {
          if (ncx < 2)
            iex[ncx] = ite.index();
          ++ncx;
        }
      }
      else if ((et & ConcaveTag) == ConcaveTag)
      {
        if (ncv < 2)
          iev[ncv] = ite.index();
        ++ncv;
        if (edge_doubled)
        {
          if (ncv < 2)
            iev[ncv] = ite.index();
          ++ncv;
        }
      }
      if (hasClass(ite->opposed(i), Corner))
        ++nc;
      if (edge_doubled)
        ++nc;
    }

    // if ( (ncx == 2 and ncv == 0) /* or (ncx == 0 and ncv == 2) */ ) {
    if ((ncx == 2 and ncv == 0))
    {

      // if vertex is either concave *or* convex, but not both,
      // it is a pure ridge vertex -> project tangential components away
      Vct3 etg[2];
      const uint *nbe = (ncx == 2) ? iex : iev;
      for (int k = 0; k < 2; ++k)
      {
        assert(nbe[k] != NotFound);
        uint s = mwall.edge(nbe[k]).source();
        uint t = mwall.edge(nbe[k]).target();
        etg[k] = (mwall.vertex(t) - mwall.vertex(s)).normalized();
      }

      Vct3 tg;
      if (dot(etg[0], etg[1]) < 0)
        tg = etg[0] - etg[1];
      else
        tg = etg[0] + etg[1];

      wfn[i] -= (dot(tg, wfn[i]) / sq(tg)) * tg;
      normalize(wfn[i]);
    }
    else if (isClass(i, SaddleCorner))
    {
      // else if ( ncv > 0 and ncx > 0 /* and nc == 0 */ ) {

      // both convex and concave : corner/saddle point vertex
      // this is the weighting factor applied to the normal along the
      // convex incident edges
      const Real cvxWeight = 2.0;

      Vct3 rpn; // replacement normal direction
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      {
        const int et = etype[ite.index()];
        if ((et & Ridge) or isClass(ite->opposed(i), SaddleCorner))
        {
          Vct3 edir = mwall.vertex(ite->opposed(i)) - mwall.vertex(i);
          Real weight = (et & Convex) ? cvxWeight : -1.0; // sign(dot(edir,wfn[i]));
          rpn += weight * edir.normalized();
          if (symmetry and border_vertex and mwall.vertex(mwall.edge(ite.index()).target())[1] > y0 + 0.0001)
          {
            edir[1] = -edir[1];
            rpn += weight * edir.normalized();
          }
        }
      }

      if (symmetry and border_vertex)
      {
        rpn[1] = 0;
        // replace corner/saddle point normal
        wfn[i] = rpn.normalized();
      }
      else
      {
        // replace corner/saddle point normal
        wfn[i] = rpn.normalized();
      }
    }
  }
}

void PentaGrow::generateShell(int hiter, int niter,
                              int ncrititer, int laplaceiter,
                              bool symmetry, Real y0)
{
  // user-level error checking must occur at higher level
  // assert(h2e >= 0.01 and h2e <= 10.0);
  // Real elf = clamp(h2e, 0.01, 10.0);

  // compute normal vectors
  mwall.estimateNormals(symmetry, y0);
  cosconcave = 0.99875; // concave detection

  // shortcuts
  Real hi = firstCellHeight;
  Real tmax = maxAbsHeight;
  Real elfmax = maxRelHeight;
  uint nl = numPrismLayers;
  Real rmax = maxExpansionFactor;
  Real y0eps = y0 + 0.0001;

  // Categorize vertices
  const int nv = mwall.nvertices();
  wfn = mwall.normals();
  classify(symmetry, y0);

  adjustRidgeNormals(symmetry, y0);
  // prism height as a function of edge length
  // determine local layer thickness
  Vector lyt(nv), elf(nv);
  for (int i = 0; i < nv; ++i)
  {
    // Define mean relative height based on neighbours
    TriMesh::nb_edge_iterator ite, elast;
    elast = mwall.v2eEnd(i);
    Real lbt = 0.;
    for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
    {
      if (symmetry and mwall.vertex(i)[1] < y0eps and mwall.vertex(ite->opposed(i))[1] > y0eps)
      { // if i is a vertex on the boundary and the edge is one not on the border, then by symmetry its effect should be doubles as usually there is the same edge in the other direction
        lbt += norm(mwall.vertex(ite->opposed(i)) - mwall.vertex(i));
      }
      lbt += norm(mwall.vertex(ite->opposed(i)) - mwall.vertex(i));
    }
    if (symmetry and mwall.vertex(i)[1] < y0eps)
    {
      lbt /= (2 * mwall.vdegree(i) - 2); // should be teh degree because we add every edge except the two on the border double
    }
    else
    {
      lbt /= mwall.vdegree(i);
    }
    Real hn = 1.0 * lbt;
    Real r0 = clamp(std::pow(hn / hi, 1.0 / (nl - 1.0)), 1.0000001, rmax);
    Real htot = hi * (1.0 - std::pow(r0, Real(nl))) / (1.0 - r0);
    elf[i] = clamp(htot / lbt, 0.1, elfmax);
    lyt[i] = std::min(lbt * elf[i], tmax);
  }

  // adjust wingtip and TE type vertices
  for (int i = 0; i < nv; ++i)
  {
    if (hasClass(i, Trench))
      lyt[i] *= std::sqrt(2.0); // sqrt(2.*pow(lyt[i],2.));
    else if (hasClass(i, Sharp | Ridge))
      lyt[i] *= 0.75;
  }

  // smooth local layer thickness
  hiter = std::max(hiter, int(std::ceil((max(elf) + 9) * 3)));
  Vector tmpy(lyt);
  Real counterR;
  for (int it = 0; it < hiter; ++it)
  {
    // parallel
    for (int i = 0; i < nv; ++i)
    {
      bool border_vertex(symmetry and mwall.vertex(i)[1] < y0eps);
      tmpy[i] = lyt[i];
      counterR = 1;
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      // Taking consideration to wingtip and TE type vertices
      if (vtype[i] == Flat)
      {
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          if (hasClass(ite->opposed(i), ConeTip) or
              hasClass(ite->opposed(i), RidgeConeTip))
          {
            if (border_vertex and mwall.vertex(ite->opposed(i))[1] > y0eps)
            { // if i is a vertex on the boundary and the edge is one not on the border, then by symmetry its effect should be doubles as usually there is the same edge in the other direction
              tmpy[i] += Real(mwall.vdegree(i)) * lyt[ite->opposed(i)];
              counterR += Real(mwall.vdegree(i));
            }
            tmpy[i] += Real(mwall.vdegree(i)) * lyt[ite->opposed(i)];
            counterR += Real(mwall.vdegree(i));
          }
          else
          {
            if (border_vertex and mwall.vertex(ite->opposed(i))[1] > y0eps)
            { // if i is a vertex on the boundary and the edge is one not on the border, then by symmetry its effect should be doubles as usually there is the same edge in the other direction
              tmpy[i] += (1.2 - cosarg(wfn[i], wfn[ite->opposed(i)])) *
                         lyt[ite->opposed(i)];
              counterR += (1.2 - cosarg(wfn[i], wfn[ite->opposed(i)]));
            }
            tmpy[i] += (1.2 - cosarg(wfn[i], wfn[ite->opposed(i)])) *
                       lyt[ite->opposed(i)];
            counterR += (1.2 - cosarg(wfn[i], wfn[ite->opposed(i)]));
          }
        }
        tmpy[i] /= counterR;
      }
      else if (hasClass(i, ConvexEdge))
      {
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          uint opv = ite->opposed(i);
          uint vto = vtype[opv];
          if ((not hasClass(opv, Trench)) and (vto != Flat))
          {
            if (border_vertex and mwall.vertex(ite->opposed(i))[1] > y0eps)
            { // if i is a vertex on the boundary and the edge is one not on the border, then by symmetry its effect should be doubles as usually there is the same edge in the other direction
              tmpy[i] += lyt[ite->opposed(i)];
              ++counterR;
            }
            tmpy[i] += lyt[ite->opposed(i)];
            ++counterR;
          }
        }
        tmpy[i] /= counterR;
      }
      else if (hasClass(i, Trench))
      {
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          uint opv = ite->opposed(i);
          uint vto = vtype[opv];
          if ((not hasClass(opv, ConvexEdge)) and vto != Flat)
          {
            if (border_vertex and mwall.vertex(ite->opposed(i))[1] > y0eps)
            { // if i is a vertex on the boundary and the edge is one not on the border, then by symmetry its effect should be doubles as usually there is the same edge in the other direction
              tmpy[i] += lyt[ite->opposed(i)];
              ++counterR;
            }
            tmpy[i] += lyt[ite->opposed(i)];
            ++counterR;
          }
        }
        tmpy[i] /= counterR;
      }
      else if (hasClass(i, Corner))
      {
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          uint vto = vtype[ite->opposed(i)];
          if (vto != Flat)
          {
            if (border_vertex and mwall.vertex(ite->opposed(i))[1] > y0eps)
            { // if i is a vertex on the boundary and the edge is one not on the border, then by symmetry its effect should be doubles as usually there is the same edge in the other direction
              tmpy[i] += lyt[ite->opposed(i)];
              ++counterR;
            }
            tmpy[i] += lyt[ite->opposed(i)];
            ++counterR;
          }
        }
        tmpy[i] /= counterR;
      }
      if ((it > hiter * 0.7) and (it < hiter * 0.9))
      {
        counterR = 1;
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          if (lyt[ite->opposed(i)] < lyt[i])
          {
            if (border_vertex and mwall.vertex(ite->opposed(i))[1] > y0eps)
            { // if i is a vertex on the boundary and the edge is one not on the border, then by symmetry its effect should be doubles as usually there is the same edge in the other direction
              tmpy[i] += lyt[ite->opposed(i)];
              ++counterR;
            }
            tmpy[i] += lyt[ite->opposed(i)];
            ++counterR;
          }
        }
        tmpy[i] /= counterR;
      }
    }
    tmpy.swap(lyt);
  }

  // smooth normals taking into account vertex types.
  // TODO: corner angle weighted smoothing
  PointList<3> wfntmp(wfn);
  PointList<3> wfnorig(wfn);

  Vector wfnweight(nv, 1.0);
  Vector tmpwfnweight(nv);
  niter = std::max(niter, int(std::ceil((max(elf) + 9) * 3)));
  for (int it = 0; it < niter; ++it)
  {
    // TODO: parallel
    for (int i = 0; i < nv; ++i)
    {
      bool border_vertex(symmetry and mwall.vertex(i)[1] < y0eps);
      uint ntip = 0;
      uint nvtivto = 0;
      uint ncorner = 0;
      wfntmp[i] = wfn[i];
      tmpwfnweight[i] = wfnweight[i];
      PointList<3> ne(mwall.vdegree(i));
      Vct3 eridge;
      uint j = 0;
      uint neridges = 0;
      int vti = vtype[i];
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      {
        int opv = ite->opposed(i);
        int vto = vtype[opv];
        if (hasClass(opv, ConeTip) or hasClass(opv, RidgeConeTip))
          ++ntip;
        if (vto == vti)
          ++nvtivto;
        if (hasClass(opv, Corner))
          ++ncorner;
        if (hasClass(i, Ridge))
          ne[j] = (mwall.vertex(opv) - mwall.vertex(i)).normalized();
        ++j;
      }
      if (hasClass(i, Ridge))
      {
        for (uint k = 0; k < j; ++k)
        {
          for (uint k2 = 0; k2 < j; ++k2)
          {
            if (cosarg(ne[k], ne[k2]) < -cosconcave)
            {
              eridge = ne[k];
              ++neridges;
            }
          }
        }
      }
      for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      {
        int opv = ite->opposed(i);
        bool doubled_edge(border_vertex and mwall.vertex(opv)[1] > y0eps);
        // we need to double the effect of some of the edges near symmetry, so we just use this factor to do it --> factor-1 is 0 when not doubled edge, and 1 otherwise
        int factor = doubled_edge ? 2 : 1;
        int vti = vtype[i];
        int vto = vtype[opv];
        Vct3 a = mwall.vertex(opv) - mwall.vertex(i);
        Vct3 b = 0.3 * norm(a) * wfn[opv] + mwall.vertex(opv) - (0.3 * norm(a) * wfn[i] + mwall.vertex(i));
        Vct3 wfn_op_mir, vtx_op_mir, wfn_orig_op_mir;
        if (doubled_edge)
        {
          Vct3 a_mir(a[0], -a[1], a[2]);
          wfn_op_mir = Vct3(wfn[opv][0], -wfn[opv][1], wfn[opv][2]);
          vtx_op_mir = Vct3(mwall.vertex(opv)[0], -mwall.vertex(opv)[1], mwall.vertex(opv)[2]);
          wfn_orig_op_mir = Vct3(wfnorig[i][0], -wfnorig[i][1], wfnorig[i][2]);
          // b_mir should be b with the y-coord of inverse sign
          Vct3 b_mir = 0.3 * norm(a_mir) * wfn_op_mir + vtx_op_mir - (0.3 * norm(a_mir) * wfn[i] + mwall.vertex(i));
          /// in fact useless I think?
        }
        bool concave = false;
        if (sq(a) > sq(b))
          concave = true;
        // Adjust FLAT type nodes
        if ((vti == Flat) and (it < niter - 3))
        {
          // Adjust Flat type nodes
          if (hasClass(opv, ConeTip) or hasClass(opv, RidgeConeTip))
          {
            wfntmp[i] += factor * Real(mwall.vdegree(i)) * wfn[i];
          }
          else if (hasClass(opv, Concave))
          { // and concave ){
            tmpwfnweight[i] = pow(2., elfmax + 1.);
            wfntmp[i] += tmpwfnweight[i] * wfn[opv] + (factor - 1.0) * tmpwfnweight[i] * wfn_op_mir;
          }
          else if (hasClass(opv, ConvexEdge))
          {
            wfntmp[i] += 2. * wfn[opv] + (factor - 1.0) * 2.0 * wfn_op_mir;
          }
          else if ((wfnweight[opv] > 1.) and (wfnweight[opv] > wfnweight[i]) and concave)
          {
            tmpwfnweight[i] = wfnweight[opv] * 0.5 + 1.;
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * wfnweight[opv] *
                         std::max(cosarg(wfnorig[i], wfnorig[opv]), 0.); // the angle is the same by symmetry
          }
          else
          {
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * std::max(cosarg(wfnorig[i], wfnorig[opv]), 0.);
          }
        }
        else if ((vti == Flat) and (it >= niter - 3))
        {
          wfntmp[i] += wfn[opv] + (factor - 1.0) * wfn_op_mir;
        } // Adjust CONVEXEDGE type nodes
        else if (hasClass(i, ConvexEdge) and (vto != Flat) and (not hasClass(opv, Trench)) and (not hasClass(opv, LeadingEdgeIntersection)))
        {
          if (hasClass(opv, ConvexEdge))
          {
            if (ncorner == 0 or cosarg(wfnorig[i], wfnorig[opv]) > cosconcave)
            {
              if ((wfnweight[opv] > 1.) and (wfnweight[opv] > wfnweight[i]))
                tmpwfnweight[i] = wfnweight[opv] * 0.5 + 1.;
              if (cosarg(wfnorig[i], wfnorig[opv]) > cosconcave)
              {
                wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * wfnweight[opv] *
                             std::max(cosarg(wfnorig[i], wfnorig[opv]), 0.);
              }
              else
              {
                wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * wfnweight[opv] *
                             std::max(cosarg(wfnorig[i], wfnorig[opv]), 0.) / Real(niter * 0.125);
              }
            }
          }
          else if (isClass(opv, SaddleCorner) or isClass(opv, BluntCorner))
          {
            if (ncorner == 1 or fabs(cosarg(eridge, a)) > cosconcave)
            {
              tmpwfnweight[i] = pow(2., elfmax + 1);
              wfntmp[i] += tmpwfnweight[i] * (wfn[opv] + (factor - 1.0) * wfn_op_mir); //* std::max(cosarg(wfnorig[i],wfnorig[opv]),0.);
            }
            else
              wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * std::max(cosarg(wfnorig[i], wfnorig[opv]), 0.);
          }
          else if (isClass(opv, ConeTip) or isClass(opv, ConvexCorner) or
                   isClass(opv, RidgeConeTip))
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * std::max(cosarg(wfnorig[i], wfnorig[opv]), 0.);
        }
        else if (hasClass(i, ConvexEdge) and hasClass(opv, Trench) and concave)
        {
          wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir);
        } // Adjust TRENCH type nodes
        else if (hasClass(i, Trench) and (vto != Flat) and (not hasClass(opv, ConvexEdge)) and (not hasClass(i, LeadingEdgeIntersection)))
        {
          if (hasClass(opv, Trench) and
              cosarg(wfnorig[i], wfnorig[opv]) > cosFeatureAngle)
          {
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * std::max(cosarg(wfnorig[i], wfnorig[opv]), 0.);
          }
          else if (hasClass(opv, SaddleCorner))
          {
            wfntmp[i] += 0.5 * (wfn[opv] + (factor - 1.0) * wfn_op_mir) + a.normalized() / Real(niter * 0.25);
          }
          else if ((isClass(opv, ConeDipp) or isClass(opv, ConcaveCorner)))
          { // and ncorner==1 ){
            tmpwfnweight[i] = pow(2., elfmax + 1);
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * tmpwfnweight[i];
          }
          else if (nvtivto == 0)
            wfntmp[i] += wfnorig[i] + (factor - 1.0) * wfn_orig_op_mir;
        } // Adjust LE
        else if (hasClass(i, LeadingEdgeIntersection))
        {
          if (hasClass(opv, SaddleCorner))
            wfntmp[i] += 0.0125 * (wfn[opv] + (factor - 1.0) * wfn_op_mir) + a.normalized() / Real(niter * 0.5);
          else if (hasClass(opv, LeadingEdgeIntersection) and
                   (cosarg(wfnorig[i], wfnorig[opv])) > cosFeatureAngle)
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * std::max(cosarg(wfnorig[i], wfnorig[opv]), 0.);
          else if (hasClass(opv, ConeDipp) or hasClass(opv, ConcaveCorner))
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * pow(2., elfmax + 1);
        } // Adjust ConvexCorners
        else if (isClass(i, ConvexCorner) or isClass(i, ConvexCorner | Sharp) or
                 isClass(i, ConeTip))
        {
          if (hasClass(opv, ConeDipp) or hasClass(opv, ConcaveCorner))
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * pow(9., elfmax + 1);
          else if (hasClass(opv, SaddleCorner))
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * pow(9., elfmax + 1) * 0.5 + 1.;
          else if (hasClass(opv, ConvexEdge) and wfnweight[opv] > 1.)
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * wfnweight[opv];
        } // Adjust SaddleCorners
        else if (hasClass(i, SaddleCorner) and hasClass(opv, Trench) and nvtivto == 0)
        {
          if (tmpwfnweight[opv] > 2.)
            wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir) * tmpwfnweight[opv];
        } // Adjust Wedges
        else if (isClass(i, Wedge))
          wfntmp[i] += (wfn[opv] + (factor - 1.0) * wfn_op_mir);
      }
      normalize(wfntmp[i]);
      // Check that new proposed normal is inside max allowed cone angle
      uint npass(0);
      if (symmetry and border_vertex)
      {
        wfntmp[i][1] = 0;
        normalize(wfntmp[i]);
      }
      TriMesh::nb_face_iterator itf, fbegin, flast;
      fbegin = mwall.v2fBegin(i);
      flast = mwall.v2fEnd(i);
      for (itf = fbegin; itf != flast; ++itf)
      {
        if (cosarg(wfntmp[i], itf->normal()) > 1 - cosFeatureAngle)
          ++npass;
        else if (cosarg(wfntmp[i], itf->normal()) > (1. - cosconcave) and
                 not hasClass(i, Flat) and not hasClass(i, Corner))
          ++npass;
      }
      uint nb_faces = border_vertex ? mwall.vdegree(i) - 1 : mwall.vdegree(i); // If not border, nb neighbours=nb face, but not for border --> one more vertex
      if (npass == nb_faces)
        wfntmp[i] = wfntmp[i] * std::max(0., cosarg(wfnorig[i], wfntmp[i])) +
                    wfn[i] * (1. - std::max(0., cosarg(wfnorig[i], wfntmp[i])));
      else
      {
        wfntmp[i] = wfn[i];
      }
    }
    wfntmp.swap(wfn);
    tmpwfnweight.swap(wfnweight);
  }

  const Real permitted_etwist = rad(60.);
  for (int j = 0; j < 2; ++j)
    untangle(lyt, 4, permitted_etwist);

  //  // XP
  //  ConnectMap map;
  //  edgeMap(map);
  //  // smooth outer layer height indiscriminately
  //  for (int it=0; it<hiter; ++it)
  //    smooth(map, lyt);
  //  auto writeNode = [&] (int inode) {
  //    return !hasClass(inode, Sharp|Ridge);
  //  };
  //  auto readNode = [&] (int inode) {
  //    return true;
  //  };
  //  // smooth normal vectors not touching ridges
  //  for (int it=0; it<niter; ++it)
  //    smooth(map, wfn, writeNode, readNode);

  // generate vertices for outer layer
  vout.resize(nv);
  for (int i = 0; i < nv; ++i)
    vout[i] = mwall.vertex(i) + lyt[i] * wfn[i] / norm(wfn[i]);

  // detect indirect collisions and reduce height accordingly
  uncollide(4, 1.6, 0.90, rad(60.), rad(170.), symmetry, y0);
  //  // XP
  //  for (int it=0; it<laplaceiter; ++it)
  //    smooth(map, vout);

  // Laplace smoothing of outer layer; normal weighted
  if (laplaceiter > 0)
  {
    PointList<3> pl1(vout);
    PointList<3> pl2(nv);
    for (int it = 0; it < laplaceiter; ++it)
    {
      for (int i = 0; i < nv; ++i)
      {
        Vct3 pa, pb, pc, nab, nbc;
        pl2[i] = pl1[i];
        pa = mwall.vertex(i);
        if ((not hasClass(i, ConeTip)) and (not hasClass(i, ConvexEdge)) and
            (not hasClass(i, SaddleCorner)) and (not hasClass(i, BluntCorner)) and
            (not hasClass(i, CriticalCorner)) and (not hasClass(i, ConvexCorner)))
        {
          pc = pb = pl1[i];
          TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
          for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
          {
            pc += pl1[ite->opposed(i)];
            if (symmetry and pa[1] < y0eps and mwall.vertex(ite->opposed(i))[1] > y0eps)
            {
              pc += pl1[ite->opposed(i)];
            }
          }
          if (symmetry and pa[1] < y0eps)
          {
            pc /= Real(2 * mwall.vdegree(i) - 1);
          }
          else
          {
            pc /= Real(mwall.vdegree(i) + 1);
          }
          nab = (pb - pa).normalized();
          nbc = (pc - pb).normalized();
          if (it >= laplaceiter and elf[i] >= 1.0)
          {
            pl2[i] = 0.25 * (pc + 3.0 * pb);
          }
          else if (cosarg(nab, nbc) > (1.0 - cosconcave))
          {
            pl2[i] = (1 - cosarg(nab, nbc)) * pb + cosarg(nab, nbc) * pc;
          }
        }
        if (symmetry and pa[1] < y0eps)
        { // forces to stay on y=y0
          pl2[i][1] = y0;
        }
        else
        {
          //  Check that resulting normal is inside max allowed cone angle
          uint npass(0);
          TriMesh::nb_face_iterator itf, fbegin, flast;
          fbegin = mwall.v2fBegin(i);
          flast = mwall.v2fEnd(i);
          Vct3 npl2i = (pl2[i] - pa).normalized();
          for (itf = fbegin; itf != flast; ++itf)
          {
            if (cosarg(npl2i, itf->normal()) > 1. - cosFeatureAngle)
              ++npass;
            else if (cosarg(npl2i, itf->normal()) > (1. - cosconcave) and
                     not isClass(i, Flat) and not hasClass(i, Corner))
              ++npass;
          }
          if (npass != mwall.vdegree(i))
            pl2[i] = pl1[i];
        }
      }
      pl1.swap(pl2);
    }
    vout.swap(pl1);
    for (int i = 0; i < nv; ++i)
    {
      lyt[i] = norm(vout(i) - mwall.vertex(i));
      wfn[i] = (vout[i] - mwall.vertex(i));
      normalize(wfn[i]);
    }
  }

  // handle indirect collisions and warped pentas caused by smoothing
  if (laplaceiter > 0)
    uncollide(ncrititer, 1.6, 0.90, rad(60.), rad(170.), symmetry, y0);

  if (symmetry)
  {
    for (uint i = 0; i < nv; i++)
    {
      if (mwall.vertex(i)[1] < 0.00001 and wfn[i][1] > 0.00001)
      {
        log("[w] : Vertex", i, "on the border with coordinates : (", mwall.vertex(i)[0], ",", mwall.vertex(i)[1], ",", mwall.vertex(i)[2], "), has a normal not on the symmetry plane :(", wfn[i][0], ",", wfn[i][1], ",", wfn[i][2], ")");
      }
    }
  }
  unwarp(16, rad(89.), symmetry, y0);
}

void PentaGrow::retractNeighbors(const Indices &afv, Vector &lyt, int ring)
{
  // collect ring-n neighborhood of the modified vertices
  Indices nbh(afv);
  sort_unique(nbh);
  for (int i = 0; i < ring; ++i)
    mergeNeighbors(nbh);

  size_t nring = nbh.size();
  const int nsmooth(5);
  Vector htmp(lyt.size());
  // smooth height distribution in the neighborhood of affected vertices
  for (int jt = 0; jt < nsmooth; ++jt)
  {
    htmp = lyt;
    for (size_t i = 0; i < nring; ++i)
    {
      int nnb(0);
      int j = nbh[i];
      Real hsum(0.0);
      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(j);
      for (ite = mwall.v2eBegin(j); ite != elast; ++ite)
      {
        uint opv = ite->opposed(j);
        if (lyt[opv] < lyt[j])
        {
          hsum += lyt[opv];
          ++nnb;
        }
      }
      if (nnb > 0)
        htmp[j] = 0.5 * (lyt[j] + hsum / nnb);
    }
    lyt.swap(htmp);
  }
}

void PentaGrow::unwarp(int niter, Real permitted_angle, bool symmetry, Real y0)
{
  const Real cpa = cos(permitted_angle);
  const int nf = mwall.nfaces();
  Indices afv;

  // Update lyt and wfn
  const int nv = mwall.nvertices();
  Vector lyt(nv);
  for (int i = 0; i < nv; ++i)
  {
    if (symmetry and mwall.vertex(i)[1] < y0 + 0.00001)
    {
      Vct3 r = vout[i] - mwall.vertex(i);
      r[1] = 0;
      vout[i] = mwall.vertex(i) + r;
      wfn[i] = r.normalized();
      lyt[i] = norm(r);
    }
    else
    {
      lyt[i] = norm(vout(i) - mwall.vertex(i));
      wfn[i] = (vout[i] - mwall.vertex(i)).normalized();
    }
  }

  // keep track of nodal retraction factor to avoid additive application
  Vector nretract(nv, 1.0);

  // lower retraction limit
  const Real rmin(1e-3);

  for (int it = 0; it < niter; ++it)
  {
    uint nwarped(0), ngiveup(0);
    for (int i = 0; i < nf; ++i)
    {

      Vct3 pw[3], ps[3], vxn[3], fns;
      const uint *v = mwall.face(i).vertices();
      for (int k = 0; k < 3; ++k)
      {
        pw[k] = mwall.vertex(v[k]);
        vxn[k] = vout[v[k]] - pw[k];             // original vector wall-shell
        ps[k] = pw[k] + nretract[v[k]] * vxn[k]; // current, retracted point
      }
      fns = cross(ps[1] - ps[0], ps[2] - ps[0]); // current shell normal

      Vct3 cosalfa;
      for (int k = 0; k < 3; ++k)
        cosalfa[k] = cosarg(vxn[k], fns);
      int jmin = std::distance(cosalfa.begin(),
                               std::min_element(cosalfa.begin(),
                                                cosalfa.end()));
      int jmax = std::distance(cosalfa.begin(),
                               std::max_element(cosalfa.begin(),
                                                cosalfa.end()));
      if (cosalfa[jmin] > cpa)
        continue;

      Real rhi(1.0), rlo(0.0), retract;
      for (int j = 0; j < 8; ++j)
      {

        retract = 0.5 * (rhi + rlo);
        for (int k = 0; k < 3; ++k)
        {
          Real r = std::min(retract, nretract[v[k]]);
          ps[k] = pw[k] + r * vxn[k];
        }

        // envelope normal after retraction
        fns = cross(ps[1] - ps[0], ps[2] - ps[0]);
        for (int k = 0; k < 3; ++k)
          cosalfa[k] = cosarg(vxn[k], fns);
        jmin = std::distance(cosalfa.begin(),
                             std::min_element(cosalfa.begin(),
                                              cosalfa.end()));
        jmax = std::distance(cosalfa.begin(),
                             std::max_element(cosalfa.begin(),
                                              cosalfa.end()));

        if (cosalfa[jmin] < cpa)
          rhi = retract;
        else
          rlo = retract;
      }

      // be conservative, will not converge otherwise
      retract = rlo;

      if (retract < rmin)
        ++ngiveup;

      ++nwarped;
      for (int k = 0; k < 3; ++k)
        nretract[v[k]] = std::max(rmin, std::min(retract, nretract[v[k]]));
      afv.insert(afv.end(), v, v + 3);
    }

    if (nwarped == 0)
    {
      log("[i] All warped pentas resolved.");
      break;
    }
    else if (ngiveup < nwarped)
    {
      log("[i]", nwarped, " warped pentas detected in iteration", it);
    }
    else
    {
      log("[i]", nwarped, " warped pentas remain unresolvable, giving up.");
      break;
    }
  }

  // update height values
  for (int i = 0; i < nv; ++i)
    lyt[i] *= nretract[i];

  // smooth neighborhood unidirectionally, i.e. reduce height only
  retractNeighbors(afv, lyt);
  for (int i = 0; i < nv; ++i)
    vout[i] = mwall.vertex(i) + lyt[i] * wfn[i] / norm(wfn[i]);
}

int PentaGrow::untangle(Vector &lyt, int niter, Real permitted_etwist)
{
  const size_t ne = mwall.nedges();
  size_t ncol(0);
  Indices afv;
  const Real cpt = cos(permitted_etwist);
  const int nsmooth(5);
  for (int it = 0; it < niter; ++it)
  {
    ncol = 0;
    afv.clear();
    for (size_t i = 0; i < ne; ++i)
    {
      const TriEdge &e(mwall.edge(i));
      const size_t s = e.source();
      const size_t t = e.target();
      const Vct3 &pws(mwall.vertex(s));
      const Vct3 &pwt(mwall.vertex(t));

      Real alpha_s = arg(pwt - pws, wfn[s]); // wall-normal angle at s
      Real alpha_t = arg(pws - pwt, wfn[t]); // wall-normal angle at t

      // arg() returns the principal value, which is positive, so that
      // gamma must be smaller than PI.
      Real gamma = PI - alpha_s - alpha_t;
      assert(gamma <= PI);

      // gamma negative if locally 'convex', divergent normals -> uncritical
      if (gamma <= 0.0 or gamma >= PI)
        continue;

      // determine maximum allowed height which avoid entanglement
      Real lisg = norm(pws - pwt) / sin(gamma);
      Real lsmax = 0.9 * lisg * sin(alpha_s);
      Real ltmax = 0.9 * lisg * sin(alpha_t);
      if (lsmax < lyt[s])
      {
        lyt[s] = lsmax;
        ++ncol;
        afv.push_back(s);
      }
      if (ltmax < lyt[t])
      {
        lyt[t] = ltmax;
        ++ncol;
        afv.push_back(t);
      }

      // check twist angle, i.e. angle of envelope edge against wall edge
      Vct3 pes = pws + lyt[s] * wfn[s];
      Vct3 pet = pwt + lyt[t] * wfn[t];
      Real ctwist = cosarg(pet - pes, pwt - pws);
      if (ctwist > cpt)
        continue;

      afv.push_back(s);
      afv.push_back(t);

      Real etwist = acos(ctwist);
      Real etwist_rfactor = std::min(1.0, 0.95 * permitted_etwist / etwist);

      Real rfactor = std::max(0.75, etwist_rfactor);
      lyt[s] *= rfactor;
      lyt[t] *= rfactor;

      ++ncol;

    } // edge loop

    if (ncol == 0)
    {
      log("[i] All entangled edges resolved.");
      break;
    }
    else
    {
      log("[i] Entangled edged detected:", ncol);
    }

    if (nsmooth == 0)
      continue;

    retractNeighbors(afv, lyt);
  }
  return ncol;
}

void PentaGrow::uncollide(int niter, Real safety, Real retraction, Real limitphi,
                          Real limitphif, bool symmetry, Real y0)
{
  Wallclock clk;
  clk.start();

  // Update lyt and wfn
  const int nv = mwall.nvertices();
  Vector lyt(nv);
  for (int i = 0; i < nv; ++i)
  {
    Vct3 r = vout[i] - mwall.vertex(i);
    if (symmetry and mwall.vertex(i)[1] < y0 + 0.00001)
    {
      r[1] = 0;
      lyt[i] = normalize(r);
      wfn[i] = r;
      vout[i] = mwall.vertex(i) + lyt[i] * wfn[i];
    }
    else
    {
      lyt[i] = normalize(r); // not sure why we need lyt, but was there
      wfn[i] = r;
    }
  }

  updateShellNormals(symmetry, y0);

  uint ncol(0);
  Indices afv;
  const Real cphi = cos(limitphi);
  const Real cphif = cos(limitphif);
  const Real rtrarg = retraction;
  for (int j = 0; j < niter; ++j)
  {
    ncol = 0;
    rebuildTree();
    // UncollideTask task(*this, lyt, safety, retraction, cphi, cphif);
    // parallel::block_loop(task, 0, nv, 4096);
    // ncol = task.ncollisions();
    for (int i = 0; i < nv; ++i)
    {
      uint n = uncollideVertex(i, lyt, safety, retraction, cphi, cphif);
      ncol += n;
      if (n > 0)
        afv.push_back(i);
    }

    if (ncol > 0)
    {
      log("[i]", ncol, " indirect collisions detected in iteration", j + 1);
    }
    else
    {
      log("[i] All indirect collisions resolved.");
      break;
    }

    // decrease retraction factor in each unsuccessful iteration
    if (j > std::min(8, niter / 2))
      retraction = std::min(rtrarg, std::max(retraction * 0.9, 0.5));
  }

  for (int i = 0; i < nv; ++i)
    lyt[i] = norm(vout[i] - mwall.vertex(i));
  retractNeighbors(afv, lyt);

  // parallel
  for (int i = 0; i < nv; ++i)
    vout[i] = mwall.vertex(i) + lyt[i] * wfn[i] / norm(wfn[i]);

  // if (ncol != 0)
  //   throw Error("Could not resolve all collisions, increase number "
  //               "of collision resolution iterations.");

  clk.stop();
  log("[t] Uncolliding:", clk.elapsed());
}

uint PentaGrow::uncollideVertex(uint i, Vector &lyt, Real safety,
                                Real retraction, Real cphi, Real cphif)
{
  uint ncol = 0;
  int ic = collisions(i, safety, cphi, cphif);
  if (ic > -1)
  {
    Real riw = norm(vout[i] - mwall.vertex(i));
    Real ric = norm(mwall.vertex(ic) - mwall.vertex(i)) * 0.5 / safety;
    if (riw > ric / retraction)
    {
      // vout[i] = mwall.vertex(i) + wfn[i] * (ric/norm(wfn[i]));
      vout[i] = mwall.vertex(i) + wfn[i] * ric;
    }
    else
    {
      lyt[i] *= retraction;
      // vout[i] = mwall.vertex(i) + wfn[i] * (lyt[i]/norm(wfn[i]));
      vout[i] = mwall.vertex(i) + wfn[i] * lyt[i];
    }
    ++ncol;
  }
  return ncol;
}

bool PentaGrow::collisions(Indices &colliding, uint iwall, Real safety,
                           Real nrmdev, Real fnrmdev) const
{
  assert(wfn.size() == vout.size());
  assert(iwall < mwall.nvertices());
  Real height = norm(vout[iwall] - mwall.vertex(iwall)) * safety;
  findNeighbors(mwall.vertex(iwall), height, colliding);

  uint i = 0;
  while (i < colliding.size())
  {
    uint counter = 0;
    TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(iwall);
    for (ite = mwall.v2eBegin(iwall); ite != elast; ++ite)
    {
      if (ite->opposed(iwall) == colliding[i])
        ++counter;
    }
    Real cpn = cosarg(wfn[iwall], wfn[colliding[i]]);
    Real cpfn = cosarg(envNormals[iwall], envNormals[colliding[i]]);
    Vct3 a = mwall.vertex(colliding[i]) - mwall.vertex(iwall);
    Vct3 b = 0.3 * norm(a) * wfn[colliding[i]] + mwall.vertex(colliding[i]) - (0.3 * norm(a) * wfn[iwall] + mwall.vertex(iwall));
    if (iwall == colliding[i]) // Discard my self
      colliding.erase(colliding.begin() + i);
    else if (counter > 0) // Discard local neighbour
      colliding.erase(colliding.begin() + i);
    else if (cpn > nrmdev and cpfn > fnrmdev) // Discard if pointing in similar direction
      colliding.erase(colliding.begin() + i);
    else if (norm(a) < norm(b)) // Discard if convex
      colliding.erase(colliding.begin() + i);
    else
      ++i;
  }
  return (not colliding.empty());
}

int PentaGrow::collisions(uint iwall, Real safety, Real nrmdev,
                          Real fnrmdev) const
{
  assert(wfn.size() == vout.size());
  assert(iwall < mwall.nvertices());
  Real height = norm(vout[iwall] - mwall.vertex(iwall)) * safety;

  Indices colliding;
  findNeighbors(mwall.vertex(iwall), height, colliding);
  std::sort(colliding.begin(), colliding.end());

  // eliminate all directly connected neighbors
  TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(iwall);
  for (ite = mwall.v2eBegin(iwall); ite != elast; ++ite)
  {
    uint opv = ite->opposed(iwall);
    Indices::iterator pos;
    pos = std::lower_bound(colliding.begin(), colliding.end(), opv);
    if (pos != colliding.end() and *pos == opv)
      colliding.erase(pos);
  }

  const PointList<3> &wfnorig(mwall.normals());

  if (colliding.empty())
    return -1;

  uint ndiscard = 0;
  const uint nc = colliding.size();
  Real riw = norm(vout[iwall] - mwall.vertex(iwall));
  int icolide = 0;
  for (uint i = 0; i < nc; ++i)
  {
    const uint ic = colliding[i];
    if (ic == iwall)
    {
      ++ndiscard;
      if (ndiscard >= nc)
        return -1;
      continue;
    }

    // eliminate all neighbor on backside of semi sphere
    if (dot(wfnorig[iwall], vout[ic] - mwall.vertex(iwall)) < 0.)
    {
      ++ndiscard;
      if (ndiscard >= nc)
        return -1;
      continue;
    }

    // Discard if pointing in similar direction
    Real cpn = cosarg(wfn[iwall], wfn[ic]);
    Real cpfn = cosarg(envNormals[iwall], envNormals[ic]);
    if (cpn > nrmdev and cpfn > fnrmdev)
    {
      ++ndiscard;
      if (ndiscard >= nc)
        return -1;
      continue;
    }

    Vct3 a = mwall.vertex(ic) - mwall.vertex(iwall);
    Vct3 b = 0.3 * norm(a) * wfn[ic] + mwall.vertex(ic) - (0.3 * norm(a) * wfn[iwall] + mwall.vertex(iwall));
    //    Vct3 a = vout[iwall] - mwall.vertex(iwall);
    //    Vct3 b = vout[ic] - mwall.vertex(ic);
    //    Vct3 c = mwall.vertex(iwall) - mwall.vertex(ic);
    //    Vct3 d = cross(cross(b,c),b);

    if (norm(a) <= norm(b))
    { // Discard if convex
      //    if ( dot(a,d) >= 0. ){
      ++ndiscard;
      if (ndiscard >= nc)
        return -1;
      continue;
    }

    // Return index most critical point
    Real ric = norm(mwall.vertex(ic) - mwall.vertex(iwall)) * 0.5 / safety;
    if (riw > ric)
    {
      riw = ric;
      icolide = ic;
    }
  }

  return icolide;
}

void PentaGrow::smoothThickness(Vector &lyt, int niter) const
{
  Vector tmpy(lyt);
  const int nv = mwall.nvertices();
  for (int it = 0; it < niter; ++it)
  {

    // parallel
    for (int i = 0; i < nv; ++i)
    {

      tmpy[i] = lyt[i];
      Real counterR = 1.0;

      TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
      int vdeg = mwall.vdegree(i);
      if (isClass(i, Flat))
      {
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          uint opv = ite->opposed(i);
          if (hasClass(opv, ConeTip))
          {
            tmpy[i] += vdeg * lyt[opv];
            counterR += vdeg;
          }
          else
          {
            tmpy[i] += (1.2 - cosarg(wfn[i], wfn[opv])) *
                       lyt[ite->opposed(i)];
            counterR += (1.2 - cosarg(wfn[i], wfn[opv]));
          }
        }
      }
      else if (hasClass(i, ConvexEdge))
      {
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          uint opv = ite->opposed(i);
          uint vto = vtype[opv];
          if ((not hasClass(opv, Trench)) and vto != Flat)
          {
            tmpy[i] += (1.2 - cosarg(wfn[i], wfn[opv])) *
                       lyt[ite->opposed(i)];
            counterR += (1.2 - cosarg(wfn[i], wfn[opv]));
          }
        }
      }
      else if (hasClass(i, Trench))
      {
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          uint opv = ite->opposed(i);
          uint vto = vtype[opv];
          if (hasClass(opv, ConvexEdge) and vto != Flat)
          {
            tmpy[i] += lyt[opv];
            ++counterR;
          }
        }
      }
      else if (hasClass(i, BluntCorner) or hasClass(i, Corner))
      {
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          uint vto = vtype[ite->opposed(i)];
          if (vto != Flat)
          {
            tmpy[i] += lyt[ite->opposed(i)];
            ++counterR;
          }
        }
      }
      tmpy[i] /= counterR;

      // Q: what does this do?
      if ((it > niter * 0.7) and (it < niter * 0.9))
      {
        counterR = 1;
        for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
        {
          if (lyt[ite->opposed(i)] < lyt[i])
          {
            tmpy[i] += lyt[ite->opposed(i)];
            ++counterR;
          }
        }
        tmpy[i] /= counterR;
      }

    } // end of one smoothing iteration

    tmpy.swap(lyt);
  }
}

void PentaGrow::smoothShellNodes(const Vector &lyt, int niter, Real omega)
{
  // initialize working sets
  const int nv = vout.size();
  PointList<3> pl1(nv);
  PointList<3> pl2(nv);

  // mark nodes which should be smoothed
  Indices smv;
  smv.reserve(nv);
  for (int i = 0; i < nv; ++i)
  {
    pl1[i] = mwall.vertex(i) + lyt[i] * wfn[i] / norm(wfn[i]);
    if ((not hasClass(i, ConeTip)) and (not hasClass(i, ConvexEdge)) and (not hasClass(i, Corner)) and (not hasClass(i, BluntCorner)))
      smv.push_back(i);
  }

  const int nsv = smv.size();
  for (int iter = 0; iter < niter; ++iter)
  {
    for (int i = 0; i < nsv; ++i)
    {
      Vct3 bc = nbBarycenter(pl1, smv[i]);
      pl2[smv[i]] = (1.0 - omega) * pl1[smv[i]] + omega * bc;
    }
    pl1.swap(pl2);
  }
}

Vct3 PentaGrow::nbBarycenter(const PointList<3> &pts, size_t k) const
{
  Real arsum = 0.0;
  Vct3 bc;
  TriMesh::nb_face_iterator itf, last = mwall.v2fEnd(k);
  for (itf = mwall.v2fBegin(k); itf != last; ++itf)
  {
    const uint *v = itf->vertices();
    const Vct3 &p0(pts[v[0]]);
    const Vct3 &p1(pts[v[1]]);
    const Vct3 &p2(pts[v[2]]);
    Vct3 fc = (p0 + p1 + p2) / 3.0;
    Real ar2 = norm(cross(p1 - p0, p2 - p0));
    bc += fc * ar2;
    arsum += ar2;
  }
  return bc / arsum;
}

uint PentaGrow::extrude(bool curvedGrowth, bool symmetry, Real y0)
{
  // shortcuts
  Real hi = firstCellHeight;
  int nl = numPrismLayers;

  const int nv = mwall.nvertices();
  mwall.estimateNormals(symmetry, y0);
  wfn = mwall.normals();
  classify(symmetry, y0);

  // setup field of growth exponents which is used if curvedGrowth is enabled
  if (curvedGrowth)
    smoothWallTransition(4);

  // generate all intermediate nodes in parallel
  PointGrid<3> grid(nv, nl + 1);
  ExtrusionTask task(*this, grid, nl, hi, curvedGrowth);
  parallel::block_loop(task, 0, nv, 4096);

  // attempt to untangle grid nodes
  if (attemptGridUntangling)
  {

    size_t nchange = 0;
    for (int jtry = 0; jtry < 3; ++jtry)
    {

      for (int j = 0; j < 16; ++j)
      {
        size_t nc = untangleGrid(grid);
        if (j > 0 and nc > nchange + 3)
        {
          log("[i] Grid untangling found counter-productive, aborting.", j + 1);
          break;
        }
        nchange = nc;
        if (nchange == 0)
        {
          log("[i] No tangled elements in prism grid in iteration", j + 1);
          break;
        }
        else
        {
          log("[i] Prism node changes:",
              nchange, "in grid untangling iteration", j + 1);
        }
      }

      if ((not curvedGrowth) or (nchange == 0))
        break;

      // if we end up here with tangled prisms, *and* we have curved growth
      // directions, then reduce the curvature near the violating nodes
      log("[i] Curved growth directions created tangled prisms, fixing...",
          jtry + 1);
      smoothWallTransition(8);
      parallel::block_loop(task, 0, nv, 4096);
    }
  }

  // add primatic elements to mesh
  return appendPrismLayer(grid);
}

void PentaGrow::extrudeVertex(int i, int nl, Real hi,
                              bool curvedGrowth, PointGrid<3> &grid) const
{
  Vector xpp(nl + 1);

  const Vct3 &base(mwall.vertex(i));
  const Vct3 &top(vout[i]);
  const Real htot = norm(top - base);
  Vct3 topn = (mwall.vertex(i) + htot * wfn[i] / norm(wfn[i]));
  if (hasClass(i, Corner))
    topn = vout[i];

  // Define mean relative height based on neighgours
  TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
  Real lbt = 0.;
  for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
    lbt += norm(mwall.vertex(ite->opposed(i)) - mwall.vertex(i));
  lbt /= mwall.vdegree(i);

  // Set initial prism height and compute distribution
  Real h1;
  Real xpf = 1.1;
  if (1. / hi < nl + 1)
  {
    expand_pattern(nl + 1, 1., xpp);
  }
  else
  {
    h1 = hi;
    // Compute exponential growth ratio
    Real a = h1 / htot;
    Real b = 1.;
    Real r0 = 2.;
    Real n = nl;
    Real f = a * (pow(r0, n) - 1) / (r0 - 1) - b;
    Real df = a * ((n - 1) * pow(r0, (n + 1)) - nl * pow(r0, n) + r0) / (pow((r0 - 1), 2) * r0);
    Real c = a / nl;

    for (int j = 0; j < 512; ++j)
    {
      f = a * (pow(r0, n) - 1) / (r0 - 1) - b;
      if (std::fabs(f) <= c)
        break;
      df = a * ((n - 1) * pow(r0, n + 1) - n * pow(r0, n) + r0) / (sq(r0 - 1.0) * r0);
      r0 = std::max(r0 - f / df, 1.000001);
    }

    // Compute expansion pattern
    xpp[0] = 0.;
    for (int j = 1; j < int(nl); ++j)
      xpp[j] = a * (pow(r0, j) - 1.0) / (r0 - 1.0);
    xpp[nl] = 1.;
  }

  grid(i, 0) = base;
  for (int j = 1; j < int(nl); ++j)
  {
    Real t = xpp[j];
    grid(i, j) = (1. - t) * base + t * top; // what is the utility of this line??
    if (not curvedGrowth)
    {
      grid(i, j) = (1. - t) * base + t * top;
    }
    else
    {
      // Real x = 0.5*(1.0 - pow(t,0.2)+exp(-20.*t));
      Real ige = invGrowthExponent[i];
      Real x = (ige != 0.0) ? exp(-t / ige) : 0.0;
      grid(i, j) = (1. - t) * base + t * (x * topn + (1.0 - x) * top);
    }
  }
  grid(i, nl) = top;
}

void PentaGrow::smoothWallTransition(int niter)
{
  const int nv = mwall.nvertices();
  if (gridBaseTangled.size() != size_t(nv))
    gridBaseTangled.resize(nv, false);

  if (invGrowthExponent.size() != size_t(nv))
  {
    invGrowthExponent.allocate(nv);
    invGrowthExponent = defaultInvGrowthExp;
  }

  // disable curvature near sharp corners
  for (int i = 0; i < nv; ++i)
  {
    if (gridBaseTangled[i] or
        hasClass(i, SaddleCorner) or hasClass(i, CriticalCorner))
      invGrowthExponent[i] = 0.0;
  }

  // avoid too large variation in growth exponent to minimize
  // new collisions in the lower layers
  for (int iter = 0; iter < niter; ++iter)
  {
    Vector tmp(invGrowthExponent);
    for (int i = 0; i < nv; ++i)
    {
      int nnb = 0;
      Real sum(0), igi = invGrowthExponent[i];
      TriMesh::nb_edge_iterator itr, last = mwall.v2eEnd(i);
      for (itr = mwall.v2eBegin(i); itr != last; ++itr)
      {
        sum += invGrowthExponent[itr->opposed(i)];
        ++nnb;
      }
      if (nnb > 0)
      {
        Real igmean = 0.5 * (igi + sum / nnb);
        tmp[i] = std::min(igmean, igi);
      }
    }
    invGrowthExponent.swap(tmp);
  }
}

uint PentaGrow::appendPrismLayer(const PointGrid<3> &grid)
{
  // add new nodes to mesh
  uint voff = MxMesh::nnodes();
  MxMesh::appendNodes(grid.begin(), grid.end());

  // sections for wall triangles
  std::map<int, Indices> wallElms;

  // create penta6 elements from grid
  const int nf = mwall.nfaces();
  const int nl = grid.ncols() - 1;
  const int nv = grid.nrows();
  const int npenta = nf * nl;
  Indices penta(6 * npenta);
  for (int i = 0; i < nf; ++i)
  {
    const uint *vib = mwall.face(i).vertices();
    for (int j = 0; j < int(nl); ++j)
    {
      uint *ep = &penta[6 * (nf * j + i)];
      for (int k = 0; k < 3; ++k)
        ep[k] = voff + (j * nv) + vib[k];
      for (int k = 0; k < 3; ++k)
        ep[k + 3] = voff + ((j + 1) * nv) + vib[k];
    }

    const int itag = mwall.face(i).tag();
    Indices &elix(wallElms[itag]);
    for (int k = 0; k < 3; ++k)
      elix.push_back(vib[k] + voff);
  }

  uint isec = MxMesh::appendSection(Mx::Penta6, penta);
  MxMesh::section(isec).rename("PentaRegion");
  countElements();

  // remove all bocos at this point
  bocos.clear();

  // append farfield section and create corresponding BC
  if (farfieldSection.nelements() > 0)
  {
    uint ffi = appendSection(farfieldSection);
    countElements();

    MxMeshBoco bc(Mx::BcFarfield);
    bc.setRange(section(ffi).indexOffset(),
                section(ffi).indexOffset() + section(ffi).nelements());
    bc.rename(section(ffi).name());
    bc.tag(section(ffi).tag());
    appendBoco(bc);
  }

  // append sections for wall elements
  int eloff = nelements();
  std::map<int, Indices>::const_iterator itm;
  for (itm = wallElms.begin(); itm != wallElms.end(); ++itm)
  {

    // create a wall mesh section
    const Indices &elix(itm->second);
    MxMeshSection sec(this, Mx::Tri3);
    sec.appendElements(elix.size() / 3, &elix[0]);
    sec.tag(itm->first);
    sec.rename(mwall.tagName(itm->first));

    // create a boco for this section
    MxMeshBoco bc(Mx::BcAdiabaticWall);
    const int ne = sec.nelements();
    bc.setRange(eloff, eloff + ne);
    bc.rename(sec.name());
    bc.tag(itm->first);
    eloff += ne;

    appendSection(sec);
    appendBoco(bc);
  }

  countElements();
  return isec;
}

void PentaGrow::edgeLengthStats(uint k,
                                Real &lmean, Real &lmax, Real &lmin) const
{
  lmean = 0.0;
  lmax = -std::numeric_limits<Real>::max();
  lmin = -lmax;
  TriMesh::nb_edge_iterator itr, elast = mwall.v2eEnd(k);
  for (itr = mwall.v2eBegin(k); itr != elast; ++itr)
  {
    Real le = norm(mwall.vertex(itr->source()) - mwall.vertex(itr->target()));
    lmean += le;
    lmax = std::max(lmax, le);
    lmin = std::min(lmin, le);
  }
  lmean /= mwall.edegree(k);
}

void PentaGrow::prismPattern(Real rhfirst, Real rhlast, Vector &xpp) const
{
  const int nlayer = xpp.size() - 1;

  Real f = std::pow(rhlast / rhfirst, 1.0 / nlayer);
  expand_pattern(nlayer + 1, f, xpp);

  // eliminate rounding errors
  xpp.front() = 0.0;
  xpp.back() = 1.0;
}

void PentaGrow::adaptWall(const DVector<uint> &faceTags)
{
  // algorithm
  // look up the vertex i of tetwall in the original (pre-tetgen) outer
  // shell mesh (vout). if found at index inear, set the vertex i of the
  // new wall mesh to inear. the new wall mesh has the same topology as the
  // refined outer shell mesh post-tetgen. if the vertex was not found
  // in the pre-tetgen outer mesh, project it onto the nearest triangle of
  // the pre-tetgen outer mesh and retrieve foot point and index of the
  // corresponding triangle. then, evaluate the triangle with the same
  // index in the original wall mesh at the said foot point in order to
  // obtain the new vertex position on the wall.

  // first step : fetch the faces which contact the last prismatic layer
  // because we call MxMesh::readTetgen() with a non-null argument for the
  // face tag array, there will be only one section with TRI3 elements in
  // *this after readTetgen; hence, we need to
  TriMesh tetwall;
  tetwall.vertices() = nodes();
  Indices farTri, farSec;
  uint boundSec = NotFound;
  const int nsec = nsections();
  for (int i = 0; i < nsec; ++i)
  {
    if (section(i).elementType() != Mx::Tri3)
      continue;

    boundSec = i;
    const int ne = section(i).nelements();
    for (int j = 0; j < ne; ++j)
    {
      const uint *v = section(i).element(j);
      uint secTag = extractSectionTag(faceTags[j]);
      if (binary_search(wallTags.begin(), wallTags.end(), secTag))
        tetwall.addFace(v, faceTags[j]);
      else
      {
        farTri.insert(farTri.end(), v, v + 3);
        farSec.push_back(secTag);
      }
    }
    break;
  }

  // problem is that after re-import, highest bit is unset
  farTags = farSec;
  sort_unique(farTags);
  assert(farTags.size() > 0);

  if (boundSec == NotFound)
    throw Error("No boundary with 3-node triangles found in tetgen output.");

  // at this point, remove all field vertices not used on boundary
  tetwall.fixate(true);

  // generate original outer shell mesh
  if (vout.size() != mwall.nvertices())
    throw Error("PentaGrow::adaptWall - need to generate shell first!");

  // needed to interpolate vertices which tetgen has introduced at the
  // outer shell layer during the tet mesh generation/refinement; this is
  // the topology of the original wall mesh with the vout vertices
  TriMesh mout(mwall);
  mout.vertices() = vout;

  // search tree for fast vertex lookup in outer layer
  rebuildTree();

  // use topology of the actual outer shell mesh as imported from tetgen
  // map vertices of that mesh which are found in tetgen input to the
  // corresponding vertices of the wall surface (known by index)

  // map vertices to wall or interpolate where identical vertex not found
  TriMesh tmp(tetwall);
  const int nos = tetwall.nvertices();
  for (int i = 0; i < nos; ++i)
  {
    const Vct3 &pout = tetwall.vertex(i);
    uint inear = nodeTree.nearest(Vct3f(pout));
    Real sqd = sq(pout - vout[inear]);
    if (sqd < gmepsilon)
    {
      tmp.vertex(i) = mwall.vertex(inear);
    }
    else
    {
      tmp.vertex(i) = findWallVertex(mout, tetwall, i);
    }
  }

  // transfer face tags
  Indices allftags;
  mwall.allTags(allftags);
  for (uint i = 0; i < allftags.size(); ++i)
    tmp.tagName(allftags[i], mwall.tagName(allftags[i]));

  tmp.swap(mwall);
  vout = tetwall.vertices();

  // replace element-id face tags with section tags
  const int nwf = mwall.nfaces();
  for (int i = 0; i < nwf; ++i)
  {
    TriFace &f(mwall.face(i));
    uint ftag = uint(f.tag());
    f.tag(int(extractSectionTag(ftag)));
  }

  // erase outer shell triangles and all existing bocos, which would be
  // inconsistent due to the possible splitting of wall elements
  bocos.clear();
  eraseSection(boundSec);

  // farfield section(s)
  // nearfield boundary tagged with max-1, edge preproc does not like internal
  // boundary; hence, we have to eliminate it here.
  Indices fst;
  fst.reserve(farTri.size());
  const int nffs = farTags.size();
  const int nfft = farTri.size() / 3;
  for (int j = 0; j < nffs; ++j)
  {

    // keep only external farfield
    const uint stag = farTags[j];
    if (int(stag) != PentaGrow::maximumTagValue())
    {
      log("[i] PentaGrow dropped boundary tagged", stag);
      continue;
    }

    fst.clear();
    for (int i = 0; i < nfft; ++i)
    {
      const uint *v = &farTri[3 * i];
      if (farSec[i] == stag)
        fst.insert(fst.end(), v, v + 3);
    }

    // adjust direction of farfield normal vectors
    // so that they point inward
    const size_t nft = fst.size() / 3;
    Vct3 ffCenter;
    Real asum(0.0);
    for (size_t i = 0; i < nft; ++i)
    {
      const uint *v = &fst[3 * i];
      Vct3 r1 = node(v[1]) - node(v[0]);
      Vct3 r2 = node(v[2]) - node(v[0]);
      Real area = norm(cross(r1, r2));
      asum += area;
      ffCenter += (area / 3.0) * (node(v[0]) + node(v[1]) + node(v[2]));
    }
    ffCenter /= asum;
    size_t nswapped(0);
    for (size_t i = 0; i < nft; ++i)
    {
      uint *v = &fst[3 * i];
      Real ori = jrsOrient3d(node(v[0]), node(v[1]), node(v[2]), ffCenter);
      if (ori > 0)
      { // positive if ffCenter below triangle plane
        std::swap(v[1], v[2]);
        ++nswapped;
      }
    }
    if (nswapped > 0)
      log("[i] Farfield triangles reversed: ", nswapped);

    farfieldSection = MxMeshSection(this, Mx::Tri3);
    farfieldSection.appendElements(fst);
    farfieldSection.tag(stag);
    farfieldSection.rename("Farfield");
    break;
  }
  assert(farfieldSection.nelements() > 0);

  countElements();
}

Vct3 PentaGrow::findWallVertex(const TriMesh &oldShell,
                               const TriMesh &newShell, uint niShell) const
{
  // pick the first triangle which contains niShell
  TriMesh::nb_face_iterator itf = newShell.v2fBegin(niShell);
  assert(itf != newShell.v2fEnd(niShell));

  // this triangle is very likely one of the newly split triangles, but its
  // face tag contains the index of the original triangle passed to tetgen
  const uint ftg = uint(itf->tag());
  const uint eid = extractElementTag(ftg);
  // const uint sid = extractSectionTag(ftg);

  uint orgTix = eid;
  assert(orgTix < oldShell.nfaces());

  // face orgTix in newShell has been modified by split, but the old shell
  // mesh is available; project the new vertex on the old shell triangle
  // -- it should be very close indeed -- and evaluate the wall triangle
  // below at the resulting barycentric coordinates
  const TriFace &oldShellTri(oldShell.face(orgTix));
  Vct3 ptn = newShell.vertex(niShell);
  Vct3 uvh = oldShellTri.project(ptn);
  assert(fabs(uvh[2]) < 1e-6);
  assert(orgTix < mwall.nfaces());
  return mwall.face(orgTix).eval(uvh[0], uvh[1]);
}

Vct3 PentaGrow::projectToWall(const TriMesh &mout,
                              const Vct3 &pout, uint inear) const
{
  // collect triangles to check for proximity
  Indices tmp, vert, tri;
  vert.push_back(inear);
  for (int j = 0; j < 3; ++j)
  {
    tmp.clear();
    const int nv = vert.size();
    for (int i = 0; i < nv; ++i)
    {
      TriMesh::nb_face_iterator itf, flast;
      flast = mout.v2fEnd(vert[i]);
      for (itf = mout.v2fBegin(vert[i]); itf != flast; ++itf)
      {
        insert_once(tri, itf.index());
        const uint *vi = itf->vertices();
        tmp.insert(tmp.end(), vi, vi + 3);
      }
    }
    sort_unique(tmp);
    tmp.swap(vert);
  }

  // determine nearest triangles in neighborhood
  Vct2 tfoot, foot;
  Real dst, dmin(huge);
  uint ibest(NotFound);
  const int nt = tri.size();
  for (int i = 0; i < nt; ++i)
  {
    const TriFace &f(mout.face(tri[i]));
    f.minDistance(pout, tfoot);
    dst = sq(pout - f.eval(tfoot[0], tfoot[1]));

    if (dst < dmin)
    {
      dmin = dst;
      foot = tfoot;
      ibest = tri[i];
    }
  }

  // TODO
  // Improve by either evaluating the original surface at the foot point,
  // which requires a MeshComponent background object, or replace the flat
  // evaluation by cubic bubble evaluation.

  // evaluate wall mesh at the projected coordinates
  assert(ibest != NotFound);
  return mwall.face(ibest).eval(foot[0], foot[1]);
}

void PentaGrow::writeShell(const std::string &fname)
{
  TriMesh mshell(mwall);
  mshell.vertices() = vout;

  // tag shell triangles with 1
  const int n1 = mshell.nfaces();
  for (int i = 0; i < n1; ++i)
    mshell.face(i).tag(1);

  mshell.merge(mwall);

  // tag wall layer triangles with 2
  const int n2 = mshell.nfaces();
  for (int i = n1; i < n2; ++i)
    mshell.face(i).tag(2);

  mshell.tagName(1, "LastLayer");
  mshell.tagName(2, "Wall");

  MxMesh mxshell;
  mxshell.appendSection(mshell);

  // add scalar field for effective local heights
  size_t nnw = mwall.nvertices();
  Vector hgt(mxshell.nnodes());
  for (size_t i = 0; i < nnw; ++i)
    hgt[i] = hgt[nnw + i] = norm(vout[i] - mwall.vertex(i));
  mxshell.appendField("LocalHeight", hgt);

  // add vector field containing vertex normals
  PointList<3> vnrm(mxshell.nnodes());
  assert(vnrm.size() >= wfn.size());
  std::copy(wfn.begin(), wfn.end(), vnrm.begin() + wfn.size());
  mxshell.appendField("WallVertexNormals", vnrm);

  // add scalar field containing vertex category
  Vector vcat(mxshell.nnodes(), Real(Undefined));
  std::copy(vtype.begin(), vtype.end(), vcat.begin() + wfn.size());
  mxshell.appendField("VertexCategory", vcat);

  mxshell.writeZml(fname, 0);
}

void PentaGrow::extractWall(const MxMesh &gm)
{
  mwall.clear();
  mwall.vertices() = gm.nodes();

  const int nbc = gm.nbocos();
  for (int i = 0; i < nbc; ++i)
  {
    Indices ielm;
    const MxMeshBoco &bc(gm.boco(i));
    if (bc.bocoType() != Mx::BcFarfield)
    {
      bc.elements(ielm);
      const int ne = ielm.size();
      for (int j = 0; j < ne; ++j)
      {
        uint nv, isec;
        const uint *vi = gm.globalElement(ielm[j], nv, isec);
        assert(vi != 0);
        if (gm.section(isec).elementType() == Mx::Tri3)
        {
          mwall.addFace(vi, i);
        }
      }
    }
  }

  mwall.fixate(true);
}

void PentaGrow::writeTetgen(const std::string &fname,
                            const TriMesh &farf,
                            const PointList<3> &holes,
                            const TriMesh &refr,
                            Real nearBoxEdge,
                            bool symmetry,
                            Real y0)
{
  const int nwall = mwall.nvertices();
  const int nfar = farf.nvertices();
  const int nbox = refr.nvertices();

  // store wall and farfield tags
  wallTags.clear();
  farTags.clear();
  mwall.allTags(wallTags);
  farf.allTags(farTags);

  log("[i] Writing wall mesh with", mwall.nfaces(), "triangles.");

  ofstream os(asPath(fname).c_str());
  os.precision(16);
  os << std::scientific;

  // write wall nodes
  os << endl;
  os << "# node list" << endl;
  uint count = 0, k = 0;
  for (int i = 0; i < nwall; ++i)
  {
    if (symmetry and vout[i][1] < y0 + 0.00001)
    {
      count++;
    }
  }
  os << nwall + nfar - count + nbox << " 3 0 0" << endl;
  cout << "sizes, vout : " << vout.size() << " nwall " << nwall << " nfar " << nfar << "count " << count << endl;
  std::map<uint, uint> vtxshell_to_vtxplane;
  for (int i = 0; i < nwall; ++i)
  {
    if (symmetry and mwall.vertex(i)[1] < y0 + 0.00001)
    {
      for (uint j = 0; j < nfar; j++)
      {
        if (norm(farf.vertex(j) - vout[i]) < 0.001)
        {
          vtxshell_to_vtxplane[i] = nwall - count + j; // put the future nb of the vtx added with farf
          // cout << " for vtx with coord ";
          // print_vector(vout[i]);
          // cout << " linked with new vtx " << nwall - count + j << " and norm " << norm(farf.vertex(j) - vout[i]) << endl;
          break;
        }
        if (j == nfar - 1)
          cout << "Problem found no yplane matching vertex for the vertex in shell : " << vout[i] << endl;
      }
    }
    else
    {
      os << k << ' ' << vout[i][0] << ' '
         << vout[i][1] << ' ' << vout[i][2] << endl;
      vtxshell_to_vtxplane[i] = k;
      k++;
    }
  }

  log("[i] Writing farfield mesh with", farf.nfaces(), "triangles.");
  // write farfield nodes
  for (int i = 0; i < nfar; ++i)
  {
    const Vct3 &p(farf.vertex(i));
    os << nwall - count + i << ' ' << p[0] << ' ' << p[1] << ' ' << p[2] << endl;
  }

  if (nbox > 0)
    log("[i] Writing refinement box mesh with", refr.nfaces(), "triangles.");
  // write nodes of refinement box if present
  for (int i = 0; i < nbox; ++i)
  {
    const Vct3 &p(refr.vertex(i));
    os << nwall + nfar - count + i << ' ' << p[0] << ' ' << p[1] << ' ' << p[2] << endl;
  }

  os << endl;

  // count triangles
  const int nwf = mwall.nfaces();
  const int nff = farf.nfaces();
  const int nrf = refr.nfaces();

  // id maps
  uint idoffset(0), nfaces = nwf + nff + nrf;
  id2index.allocate(nfaces);
  id2section.allocate(nfaces);

  os << "# face list" << endl;
  os << nwf + nff + nrf << " 1" << endl;
  for (int i = 0; i < nwf; ++i)
  {
    const uint *vi = mwall.face(i).vertices();
    os << "3 " << vtxshell_to_vtxplane[vi[0]] << ' ' << vtxshell_to_vtxplane[vi[1]] << ' ' << vtxshell_to_vtxplane[vi[2]]
       << ' ' << i << endl;
    id2index[i] = i;
    id2section[i] = mwall.face(i).tag();
  }
  idoffset += nwf;

  // farfield boundary
  for (int i = 0; i < nff; ++i)
  {
    const uint *vi = farf.face(i).vertices();
    os << "3 " << nwall - count + vi[0] << ' ' << nwall - count + vi[1] << ' ' << nwall - count + vi[2]
       << ' ' << idoffset + i << endl;
    id2index[idoffset + i] = i;
    id2section[idoffset + i] = farf.face(i).tag();
  }
  idoffset += nff;

  // nearfield fence
  for (int i = 0; i < nrf; ++i)
  {
    uint voff = nwall + nfar - count;
    const uint *vi = refr.face(i).vertices();
    os << "3 " << voff + vi[0] << ' ' << voff + vi[1] << ' ' << voff + vi[2]
       << ' ' << idoffset + i << endl;
    id2index[idoffset + i] = i;
    id2section[idoffset + i] = refr.face(i).tag();
  }
  assert(idoffset + nrf == nfaces);

  os << "# hole list" << endl;
  os << holes.size() << endl
     << endl;
  for (uint i = 0; i < holes.size(); ++i)
    os << i << ' ' << holes[i][0] << ' ' << holes[i][1] << ' '
       << holes[i][2] << endl;

  os << "# region attribute list" << endl;
  if (refr.nvertices() > 2 and nearBoxEdge > 0.0)
  {

    // use the first vertex of the nearfield fence,
    // move inward just a tiny little bit
    Vct3 fn, marker = refr.vertex(0);
    TriMesh::nb_face_iterator itf, last = refr.v2fEnd(0);
    for (itf = refr.v2fBegin(0); itf != last; ++itf)
    {
      itf->normal(fn);
      marker -= (fn * nearBoxEdge / Real(refr.vdegree(0)));
    }

    os << '1' << endl;
    os << "1 " << marker << " " << cb(nearBoxEdge) * 0.11785 << endl;
  }
  else
  {
    os << '0' << endl;
    os << endl;
  }
}

void PentaGrow::readTets(const string &basename)
{
  DVector<uint> faceTags;
  MxMesh::readTetgen(basename, &faceTags);
  adaptWall(faceTags);
}

void PentaGrow::mergeNeighbors(Indices &idx) const
{
  size_t n = idx.size();
  Indices nbh;
  nbh.reserve(12 * n);
  for (size_t i = 0; i < n; ++i)
  {
    uint j = idx[i];
    TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(j);
    for (ite = mwall.v2eBegin(j); ite != elast; ++ite)
    {
      nbh.push_back(ite->source());
      nbh.push_back(ite->target());
    }
  }
  std::sort(nbh.begin(), nbh.end());
  nbh.erase(std::unique(nbh.begin(), nbh.end()), nbh.end());
  idx.insert(idx.end(), nbh.begin(), nbh.end());
  std::inplace_merge(idx.begin(), idx.begin() + n, idx.end());
  idx.erase(std::unique(idx.begin(), idx.end()), idx.end());
}

size_t PentaGrow::untangleGrid(PointGrid<3> &grid)
{
  const int nl = grid.ncols() - 1;
  const int nf = mwall.nfaces();
  const int nv = mwall.nvertices();

  gridBaseTangled.clear();
  gridBaseTangled.resize(nv, false);

  size_t nchange = 0;
  for (int i = 0; i < nf; ++i)
  {
    const uint *v = mwall.face(i).vertices();

    // march upward, away from wall
    for (int j = 0; j < nl; ++j)
    {

      // normal of the base triangle
      Vct3 bn = cross(grid(v[1], j) - grid(v[0], j),
                      grid(v[2], j) - grid(v[0], j));
      normalize(bn);

      // shift tangled points upwards just enough
      for (int k = 0; k < 3; ++k)
      {
        Vct3 &pk = grid(v[k], j + 1);
        Real h = dot(bn, pk - grid(v[k], j));
        if (h < 0)
        {
          gridBaseTangled[v[k]] = true;
          pk -= 1.125 * h * bn;
          ++nchange;
        }
      }
    }
  }

  return nchange;
}

void PentaGrow::debugConnect()
{
  fixate();

  ConnectMap e2e;
  e2eMap(e2e);

  for (uint isec = 0; isec < nsections(); ++isec)
  {

    if (not section(isec).surfaceElements())
      continue;

    const int ne = section(isec).nelements();
    const int eloff = section(isec).indexOffset();

    for (int j = 0; j < ne; ++j)
    {
      ConnectMap::const_iterator itr, ilast;
      itr = e2e.begin(eloff + j);
      ilast = e2e.end(eloff + j);
      bool noVol = true;
      while (itr != ilast and noVol)
      {
        if (containsNodesOf(*itr, eloff + j))
        {

          noVol = false;
        }
        ++itr;
      }
      if (noVol)
      {
        std::stringstream ss;
        ss << "Boundary element " << eloff + j
           << " has no volume neighbor." << endl;
        throw Error(ss.str());
      }
    }
  }
}

// helper functions

static inline bool tet4_posvol(const PointList<3> &vtx, const uint v[])
{
  return (jrsOrient3d(vtx[v[0]], vtx[v[1]], vtx[v[2]], vtx[v[3]]) < 0.0);
}

static inline bool penta6_posvol(const PointList<3> &vtx, const uint v[])
{
  bool pv = true;
  pv &= jrsOrient3d(vtx[v[0]], vtx[v[1]], vtx[v[2]], vtx[v[3]]) < 0.0;
  pv &= jrsOrient3d(vtx[v[0]], vtx[v[1]], vtx[v[2]], vtx[v[4]]) < 0.0;
  pv &= jrsOrient3d(vtx[v[0]], vtx[v[1]], vtx[v[2]], vtx[v[5]]) < 0.0;
  return pv;
}

static inline bool berglind_penta6_test(const PointList<3> &vtx, const uint v[])
{
  Vct3 fn1 = cross(vtx[v[1]] - vtx[v[0]], vtx[v[2]] - vtx[v[0]]);
  Vct3 fn2 = cross(vtx[v[4]] - vtx[v[3]], vtx[v[5]] - vtx[v[3]]);
  Vct3 hsum = vtx[v[3]] - vtx[v[0]] + vtx[v[4]] - vtx[v[1]] + vtx[v[5]] - vtx[v[2]];
  Real s1 = dot(fn1, hsum);
  Real s2 = dot(fn2, hsum);
  return std::fabs(std::min(s1, s2)) <= std::fabs(std::max(s1, s2));
}

size_t PentaGrow::countNegativeVolumes(std::ostream &msg)
{
  // do not bother to report more than 4k bad elements
  size_t nneg = 0;
  const size_t reportmax = 4096;

  for (uint isec = 0; isec < nsections(); ++isec)
  {

    Mx::ElementType et = section(isec).elementType();
    size_t ne = section(isec).nelements();
    size_t offs = section(isec).indexOffset();

    if (et == Mx::Tet4)
    {

      for (size_t i = 0; i < ne; ++i)
      {
        const uint *v = section(isec).element(i);
        if (tet4_posvol(vtx, v))
          continue;
        ++nneg;
        msg << "Tet4 " << offs + i << " is tangled" << endl;
        for (int j = 0; j < 4; ++j)
          msg << "  " << v[j] << " : " << vtx[v[j]] << endl;
        if (nneg >= reportmax)
          return nneg;
      }
    }
    else if (et == Mx::Penta6)
    {

      for (size_t i = 0; i < ne; ++i)
      {
        const uint *v = section(isec).element(i);
        if (not berglind_penta6_test(vtx, v))
        {
          ++nneg;
          msg << "Penta6 " << offs + i << " will fail preprocessing test" << endl;
          for (int j = 0; j < 6; ++j)
            msg << "  " << v[j] << " : " << vtx[v[j]] << endl;
        }
        else if (not penta6_posvol(vtx, v))
        {
          ++nneg;
          msg << "Penta6 " << offs + i << " is tangled" << endl;
          for (int j = 0; j < 6; ++j)
            msg << "  " << v[j] << " : " << vtx[v[j]] << endl;
          Vct3 fn = cross(vtx[v[1]] - vtx[v[0]], vtx[v[2]] - vtx[v[0]]);
          normalize(fn);
          msg << "   n: " << fn << endl;
          for (int j = 0; j < 3; ++j)
            msg << "   r: " << vtx[v[3 + j]] - vtx[v[j]]
                << " h: " << dot(fn, vtx[v[3 + j]] - vtx[v[j]]) << endl;

          // additional analysis if called while mwall is still alive
          if (mwall.nfaces() > 0)
          {
            const uint btri = i % mwall.nfaces();
            const uint *v = mwall.face(btri).vertices();
            msg << "   Base triangle: " << endl;
            Vct3 pw[3], pe[3];
            for (int k = 0; k < 3; ++k)
            {
              msg << "   " << v[k] << " : " << (pw[k] = mwall.vertex(v[k]));
              pe[k] = vout[v[k]];
              Vct3 vn = mwall.normal(v[k]).normalized();
              msg << ", vn: " << pe[k] - pw[k];
              msg << ", vn·r: " << dot(vn, pe[k] - pw[k]) << endl;
              msg << ", fn·r: " << dot(fn, pe[k] - pw[k]) << endl;
            }
            Vct3 nw = cross(pw[1] - pw[0], pw[2] - pw[0]);
            Vct3 ne = cross(pe[1] - pe[0], pe[2] - pe[0]);
            msg << "   Normal deviation: " << deg(arg(nw, ne)) << " deg." << endl;
            msg << "   Twist u: " << deg(arg(pe[1] - pe[0], pw[1] - pw[0]))
                << " deg." << endl;
            msg << "   Twist v: " << deg(arg(pe[2] - pe[0], pw[2] - pw[0]))
                << " deg." << endl;
            msg << "   Crit penta ndev: " << deg(arg(fn, nw)) << " deg." << endl;
          }
        }

        if (nneg >= reportmax)
          return nneg;
      }
    }
  }

  return nneg;
}

void PentaGrow::rebuildTree()
{
  PointList<3, float> vf(vout);
#ifndef NDEBUG
  for (size_t i = 0; i < vf.size(); ++i)
  {
    if (not std::isfinite(sq(vf[i])))
      throw Error("PentaGrow::rebuildTree() - Outer shell contains "
                  "NaN node coordinate, point " +
                  str(i));
  }
#endif
  nodeTree.allocate(vf, false, 4);
  nodeTree.sort();
}

void PentaGrow::shrink()
{
  mwall = TriMesh();
  wfn = PointList<3>();
  vout = PointList<3>();
  vtype = DVector<int>();
  nodeTree = NDPointTree<3, float>();
}

void PentaGrow::envelopeBounds(Vct3 &plo, Vct3 &phi) const
{
  if (not vout.empty())
    vout.bounds(plo, phi);
  else
    mwall.vertices().bounds(plo, phi);
}

bool PentaGrow::ellipsoidEncloses(const Vct3 &ctr, const Vct3 &hax) const
{
  const size_t n = vout.size();
  for (size_t i = 0; i < n; ++i)
  {
    Vct3 r(vout[i] - ctr);
    Real rsq = sq(r[0] / hax[0]) + sq(r[1] / hax[1]) + sq(r[2] / hax[2]);
    if (rsq > 1.0 - gmepsilon)
    {
      return false;
    }
  }
  return true;
}

void PentaGrow::envelopeEdgeStats(Real &lmean, Real &lmax) const
{
  assert(vout.size() == mwall.nvertices());

  Real lsum(0.0);
  lmax = 0.0;
  size_t ne = mwall.nedges();
  for (size_t i = 0; i < ne; ++i)
  {
    const TriEdge &e(mwall.edge(i));
    Real elen = norm(vout[e.target()] - vout[e.source()]);
    lsum += elen;
    lmax = std::max(elen, lmax);
  }
  lmean /= ne;
}

Vector PentaGrow::prismQualitySumCos(const std::string &fname,
                                     uint isection, uint nbin) const
{
  const MxMeshSection &sec(MxMesh::section(isection));
  const size_t ne = sec.nelements();

  Vector qual(ne);
  const Real f6 = 1.0 / 6.0;

  // #pragma omp parallel for schedule(static, 1024)
  for (size_t i = 0; i < ne; ++i)
  {
    const uint *v = sec.element(i);
    Vct3 n1 = cross(vtx[v[1]] - vtx[v[0]], vtx[v[2]] - vtx[v[0]]);
    Vct3 n2 = cross(vtx[v[4]] - vtx[v[3]], vtx[v[5]] - vtx[v[3]]);
    Vct3 h1 = vtx[v[3]] - vtx[v[0]];
    Vct3 h2 = vtx[v[4]] - vtx[v[1]];
    Vct3 h3 = vtx[v[5]] - vtx[v[2]];
    qual[i] = deg(f6 * (arg(n1, h1) + arg(n1, h2) + arg(n1, h3) + arg(n2, h1) + arg(n2, h2) + arg(n2, h3)));
  }

  // binning
  std::sort(qual.begin(), qual.end());

  if (nbin == NotFound)
    nbin = uint(log2(ne) + 1);

  Real qmax = 90.0; // qual.back();
  Real qmin = 0.0;  // qual.front();
  Real idq = Real(nbin) / (qmax - qmin);

  Vector qhist(nbin);
  for (size_t i = 0; i < ne; ++i)
  {
    uint idx = (qual[i] - qmin) * idq;
    idx = clamp(idx, 0u, nbin - 1);
    qhist[idx] += 1.0;
  }

  ofstream os(fname);
  os << "Qlo    Qhi    count    percentage" << endl;
  for (uint i = 0; i < nbin; ++i)
  {
    os << qmin + i / idq << " " << qmin + (i + 1) / idq << " "
       << qhist[i] << " " << 100 * qhist[i] / ne << endl;
  }

  return qhist;
}

void PentaGrow::updateShellNormals(bool symmetry, Real y0)
{
  TriMesh envelope(mwall);
  envelope.vertices() = vout;
  // that will create the normal for the points on the outer layer
  envelope.estimateNormals(symmetry, y0);
  envNormals = envelope.normals();
}

void PentaGrow::centerGridNodes(uint niter, PointGrid<3> &grid) const
{
  PointGrid<3> cgrid(grid);
  for (uint i = 0; i < niter; ++i)
  {
    centerGridNodesPass(grid, cgrid);
    cgrid.swap(grid);
  }
}

inline static Real prism_volume(const PointGrid<3> &grid, uint jl,
                                const uint v[], Vct3 &csum)
{
  const Real f(1.0 / 6.0);

  uint vp[6];
  uint nv = grid.nrows();
  for (int k = 0; k < 3; ++k)
  {
    vp[k] = (jl * nv) + v[k];
    vp[k + 3] = (jl + 1) * nv + v[k];
  }

  Vct3 t1 = grid(v[1], jl) - grid(v[0], jl);
  Vct3 t2 = grid(v[2], jl) - grid(v[0], jl);
  Vct3 bn = cross(t1, t2);

  Real vol(0);
  Vct3 ctr;
  for (int k = 0; k < 3; ++k)
  {
    vol += dot(bn, grid(v[k], jl + 1) - grid(v[k], jl));
    ctr += grid(v[k], jl + 1) + grid(v[k], jl);
  }
  ctr *= f;
  vol *= 0.5 * f;
  csum += vol * ctr;

  return vol;
}

void PentaGrow::centerGridNodesPass(const PointGrid<3> &cgrid,
                                    PointGrid<3> &grid) const
{
  const int nl = grid.ncols();
  const int nv = grid.nrows();

  BEGIN_PARLOOP_CHUNK(0, nv, 1024)
  for (int i = a; i < b; ++i)
  {

    TriMesh::nb_face_iterator itf, first, last;
    first = mwall.v2fBegin(i);
    last = mwall.v2fEnd(i);
    for (int jl = 1; jl < nl - 1; ++jl)
    {

      // determine barycenter of both decks
      Vct3 bclo, bchi;
      Real vlo(0.0), vhi(0.0);
      for (itf = first; itf != last; ++itf)
      {
        const uint *v = itf->vertices();
        vlo += prism_volume(cgrid, jl - 1, v, bclo);
        vhi += prism_volume(cgrid, jl, v, bchi);
      }
      Vct3 bct = bclo / vlo + bchi / vhi;
      grid(i, jl) = 0.5 * cgrid(i, jl) + 0.5 * bct;
    }
  }
  END_PARLOOP_CHUNK
}

void PentaGrow::findEnvelopeNeighbors(Indices &interfaceNodes,
                                      Indices &nearTetNodes) const
{
  assert(v2eMap().size() == nnodes());

  // this function is meant to identify tet nodes near the interface to the
  // prismatic layer so that these can be modified with the goal of obtaining
  // a better volumetric transition at the interface

  // find all nodes which are part of the tetrahedral and the pentahedral domain
  Indices tmp, pentaNodes, tetNodes;
  for (uint isec = 0; isec < nsections(); ++isec)
  {
    Mx::ElementType et = section(isec).elementType();
    if (et == Mx::Penta6)
    {
      section(isec).usedNodes(tmp);
      pentaNodes.insert(pentaNodes.end(), tmp.begin(), tmp.end());
    }
    else if (et == Mx::Tet4)
    {
      section(isec).usedNodes(tmp);
      tetNodes.insert(tetNodes.end(), tmp.begin(), tmp.end());
    }
  }
  sort_unique(pentaNodes);
  sort_unique(tetNodes);

  interfaceNodes.clear();
  if (numPrismLayers > 0)
    interfaceNodes.reserve(pentaNodes.size() / numPrismLayers);

  std::set_intersection(tetNodes.begin(), tetNodes.end(),
                        pentaNodes.begin(), pentaNodes.end(),
                        std::back_inserter(interfaceNodes));

  // find tetrahedral nodes which are neighbors to interface layer
  tmp.clear();
  tmp.reserve(interfaceNodes.size());

  const ConnectMap &v2e(v2eMap());
  size_t nif = interfaceNodes.size();
  for (size_t i = 0; i < nif; ++i)
  {
    ConnectMap::const_iterator itr, last = v2e.end(interfaceNodes[i]);
    for (itr = v2e.begin(interfaceNodes[i]); itr != last; ++itr)
    {
      uint nv, isec;
      const uint *v = globalElement(*itr, nv, isec);
      if (section(isec).elementType() == Mx::Tet4)
        tmp.insert(tmp.end(), v, v + nv);
    }
  }
  sort_unique(tmp);

  nearTetNodes.clear();
  nearTetNodes.reserve(tmp.size() - interfaceNodes.size());
  std::set_difference(tmp.begin(), tmp.end(),
                      interfaceNodes.begin(), interfaceNodes.end(),
                      back_inserter(nearTetNodes));

  // add ring-1 neighbors-of-neighbors
  tmp.clear();
  nif = nearTetNodes.size();
  for (size_t i = 0; i < nif; ++i)
  {
    ConnectMap::const_iterator itr, last = v2e.end(nearTetNodes[i]);
    for (itr = v2e.begin(nearTetNodes[i]); itr != last; ++itr)
    {
      uint nv, isec;
      const uint *v = globalElement(*itr, nv, isec);
      if (section(isec).elementType() == Mx::Tet4)
        tmp.insert(tmp.end(), v, v + nv);
    }
  }
  sort_unique(tmp);

  size_t mark = nearTetNodes.size();
  std::set_difference(tmp.begin(), tmp.end(),
                      interfaceNodes.begin(), interfaceNodes.end(),
                      back_inserter(nearTetNodes));

  // just appended another sorted range, merge ranges
  std::inplace_merge(nearTetNodes.begin(), nearTetNodes.begin() + mark,
                     nearTetNodes.end());

  // erase duplicates
  nearTetNodes.erase(std::unique(nearTetNodes.begin(), nearTetNodes.end()),
                     nearTetNodes.end());
}

PointList<3> PentaGrow::getouterlayeryplane_ordered(Real y0)
{
  // We will use the fact that vout[i] is the vtx associated with vtx[i]
  const int nv(vout.size());
  Real y0eps = y0 + 0.0001;
  std::vector<int> list_tags;

  uint start_tag;
  for (uint i = 0; i < nv; i++)
  {
    if (mwall.vertex(i)[1] < y0eps)
    {
      start_tag = i;
      break;
    }
  }
  list_tags.push_back(start_tag);

  bool closed_loop = false;
  uint i;
  while (!closed_loop)
  {
    i = list_tags[list_tags.size() - 1];
    TriMesh::nb_edge_iterator ite, first, last;
    first = mwall.v2eBegin(i);
    last = mwall.v2eEnd(i);
    std::vector<int> neighbours = {};
    for (ite = first; ite != last; ++ite)
    {
      if (mwall.vertex(ite->opposed(i))[1] < y0eps)
      {
        neighbours.push_back(ite->opposed(i));
      }
    }
    if (neighbours.size() != 2)
    {
      cout << " [w] when creating yplane, the border of the shell has a problem (" << neighbours.size() << "=/=2, vertices adjacent for vtx " << i << " )." << endl;
    }
    if (list_tags.size() == 1)
    {
      list_tags.push_back(neighbours[0]);
    }
    else
    {
      if (neighbours[0] == list_tags[list_tags.size() - 2])
      {
        list_tags.push_back(neighbours[1]);
        if (neighbours[1] == start_tag)
          closed_loop = true;
      }
      else
      {
        list_tags.push_back(neighbours[0]);
        if (neighbours[1] == list_tags[list_tags.size() - 2])
          cout << " [w] problem neihbours do not match with the precedent vertex (shell)." << endl;
        if (neighbours[0] == start_tag)
          closed_loop = true;
      }
    }
  }

  PointList<3> coordinates_list;
  for (auto tag : list_tags)
  {
    coordinates_list.push_back(vout[tag]);
  }
  return coordinates_list;
}