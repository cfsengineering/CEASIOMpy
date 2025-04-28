
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
 
#include "flapspec.h"
#include <genua/mxmesh.h>
#include <genua/mxmeshboco.h>
#include <genua/dbprint.h>
#include <set>

using namespace std;

namespace {

class FlapSegBox
{
public:

  FlapSegBox() {}

  void init(uint iseg,
            const PointList<3> & pfwd,
            const PointList<3> & paft, Real balex = 0.0)
  {
    const Vct3 & pfl( pfwd[iseg] );
    const Vct3 & pfr( pfwd[iseg+1] );
    const Vct3 & pal( paft[iseg] );
    const Vct3 & par( paft[iseg+1] );

    Real clr = norm(par-pfr);
    Real cll = norm(pal-pfl);
    Real clen = 0.5*(clr + cll);
    Real zlen = 0.5*clen;

    Vct3 pmid = 0.25*(pfl+pfr+pal+par);
    Vct3 nplane = cross(pal-pfl, par-pfl).normalized()
        + cross(pfl-pfr, par-pfr).normalized();
    normalize(nplane);

    // bottom and top plane
    pn[0] = nplane;
    pd[0] = dot(pn[0], pmid - zlen*nplane);
    pn[1] = -nplane;
    pd[1] = dot(pn[1], pmid + zlen*nplane);

    // front and rear plane
    pn[2] = cross(nplane, pfl-pfr).normalized();
    pd[2] = dot(pn[2], (1.0 + balex)*pfl - balex*pal);
    pn[3] = cross(nplane, par-pal).normalized();
    pd[3] = dot(pn[3], pal);

    // left and right plane
    pn[4] = cross(nplane, pal-pfl).normalized();
    pd[4] = dot(pn[4], pal);
    pn[5] = cross(nplane, pfr-par).normalized();
    pd[5] = dot(pn[5],pfr);

    // swap normal directions if necessary
    for (int k=0; k<6; ++k) {
      if (dot(pn[k],pmid)-pd[k] < 0.0)
        pn[k] *= -1.;
    }
  }

  /// check if a vertex is inside
  bool isInside(const Vct3 & p) const {
    bool inside(true);
    for (int k=0; k<6; ++k) {
      inside &= (dot(pn[k],p)-pd[k] > 0.0);
    }
    return inside;
  }

private:

  /// six plane normal vectors
  Vct3 pn[6];

  /// plane distances so that dot(pn,p) == pd
  Real pd[6];
};

}

void FlapSpec::createBoco(MxMesh &mx, FlapSpec::NodeIndexSet & segNodes) const
{
  // create boxes which are used to determine whether an element will move
  // when the flap segment is rotated
  const int nseg = nsegments();
  std::vector<FlapSegBox> box(nseg);
  for (int i=0; i<nseg; ++i)
    box[i].init(i, hp, ep, balanceExtension);

  // collect nodes which are used by surface elements marked by wall bocos
  Indices sfeElements, sfeNodes;
  collectBcElements(mx, Mx::BcWall, sfeElements);
  collectBcElements(mx, Mx::BcAdiabaticWall, sfeElements);
  if (sfeElements.empty())
    collectSurfaceElements(mx, sfeElements);
  nodesFromElements(mx, sfeElements, sfeNodes);

  // sfeNodes is sorted

  // test nodes used by surface elements
  segNodes.resize(nseg);
  const int nsn = sfeNodes.size();
  for (int i=0; i<nsn; ++i) {
    const Vct3 & p( mx.node(sfeNodes[i]) );
    for (int k=0; k<nseg; ++k) {
      if (box[k].isInside(p))
        segNodes[k].push_back(sfeNodes[i]);
    }
  }

  // each segNodes is sorted, processed in order of sfeNodes

  // create element groups for each segment
  if (mx.v2eMap().size() != mx.nnodes())
    mx.fixate();

  const ConnectMap & v2e( mx.v2eMap() );
  for (int i=0; i<nseg; ++i) {
    std::set<uint> tmp;
    const int nn = segNodes[i].size();
    for (int j=0; j<nn; ++j)
      tmp.insert( v2e.begin(segNodes[i][j]), v2e.end(segNodes[i][j]) );

    // assign elements with more than nv/2 nodes inside segment
    Indices segElements;
    std::set<uint>::const_iterator itr, last = tmp.end();
    for (itr = tmp.begin(); itr != last; ++itr) {

      // skip elements not in the identified set
      if (not binary_search(sfeElements.begin(), sfeElements.end(), *itr))
        continue;

      uint nv, isec;
      const uint *vi = mx.globalElement(*itr, nv, isec);
      uint ninside = 0;
      for (uint k=0; k<nv; ++k)
        ninside += binary_search(segNodes[i].begin(), segNodes[i].end(), vi[k]);
      if (ninside*2 > nv)
        segElements.push_back(*itr);
    }

    MxMeshBoco bc;
    if (nseg > 1)
      bc.rename(name() + "S" + str(i+1));
    else
      bc.rename(name());
    bc.appendElements(segElements.begin(), segElements.end());
    mx.appendBoco(bc);
  }
}

void FlapSpec::createDisplacement(MxMesh &mx,
                                  const FlapSpec::NodeIndexSet & segNodes) const
{
  const int nseg = segNodes.size();
  PointList<3> dsp( mx.nnodes() );
  for (int i=0; i<nseg; ++i) {

    std::fill(dsp.begin(), dsp.end(), Vct3());
    createDisplacement(mx, i, segNodes[i], dsp, 1.0);

    string fname;
    if (nseg > 1)
      fname = name() + "S" + str(i+1);
    else
      fname = name();
    uint ifield = mx.appendField(fname, dsp);
    mx.field(ifield).valueClass( MxMeshField::ValueClass::Displacement );
  }
}

void FlapSpec::createDisplacement(const MxMesh & mx, uint iseg,
                                  const Indices & idx,
                                  PointList<3> & dsp, Real fseg) const
{
  const int ni = idx.size();

  // segment geometry
  const Vct3 & hp1(hp[iseg]);
  const Vct3 & hp2(hp[iseg+1]);
  Vct3 hline = (hp2 - hp1).normalized();

  for (int j=0; j<ni; ++j) {
    const Vct3 & pt( mx.node(idx[j]) );
    Real fp = dot(pt - hp1, hline);
    Vct3 rl = pt - ((1-fp)*hp1 + fp*hp2);
    dsp[idx[j]] += fseg * cross(hline, rl);
  }
}

void FlapSpec::collectBcElements(const MxMesh &mx, int bc, Indices &ielm)
{
  const int nbc = mx.nbocos();
  std::set<uint> tmp;
  for (int i=0; i<nbc; ++i) {
    Indices elix;
    if (mx.boco(i).bocoType() == bc)
      mx.boco(i).elements(elix);
    else
      continue;
    tmp.insert(elix.begin(), elix.end());
  }
  ielm.insert(ielm.end(), tmp.begin(), tmp.end());
}

void FlapSpec::collectSurfaceElements(const MxMesh &mx, Indices &ielm)
{
  const int nsec = mx.nsections();
  for (int i=0; i<nsec; ++i) {
    const MxMeshSection & sec( mx.section(i) );
    if (sec.surfaceElements()) {
      const int eloff = sec.indexOffset();
      const int ne = sec.nelements();
      const int ioff = ielm.size();
      ielm.resize(ielm.size() + ne);
      for (int j=0; j<ne; ++j)
        ielm[ioff+j] = eloff+j;
    }
  }
}

void FlapSpec::nodesFromElements(const MxMesh &mx, const Indices & ielm,
                                 Indices &inodes)
{
  std::set<uint> tmp;
  const int ne = ielm.size();
  for (int i=0; i<ne; ++i) {
    uint nv, isec;
    const uint *vi = mx.globalElement(ielm[i], nv, isec);
    tmp.insert(vi, vi+nv);
  }
  inodes.assign(tmp.begin(), tmp.end());
}

XmlElement FlapSpec::toXml(bool) const
{
  XmlElement xe("FlapSpec");
  xe["name"] = name();
  xe["balex"] = str(balanceExtension);
  xe["hinge_count"] = str(hp.size());
  assert(hp.size() == ep.size());
  for (uint i=0; i<hp.size(); ++i) {
    XmlElement xp("Hinge");
    xp["hp"] = str(hp[i]);
    xp["ep"] = str(ep[i]);
    xe.append(std::move(xp));
  }
  return xe;
}

void FlapSpec::fromXml(const XmlElement &xe)
{
  assert(xe.name() == "FlapSpec");
  rename( xe.attribute("name") );
  balanceExtension = xe.attr2float("balex", 0.0);
  hp.clear();
  ep.clear();

  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "Hinge") {
      Vct3 hpi, epi;
      fromString(itr->attribute("hp"), hpi);
      fromString(itr->attribute("ep"), epi);
      hp.push_back(hpi);
      ep.push_back(epi);
    }
  }

  if (hp.size() < 2)
    throw Error("Invalid flap geometry specified: Need at least "
                "two hinges, found "+str(hp.size()));
}

// -------------------- FlapSpecSet::Pattern ----------------------------

XmlElement FlapSpecSet::Pattern::toXml(bool) const
{
  XmlElement xe("FlapPattern");
  xe["name"] = name;
  const int n = flaps.size();
  xe["count"] = str(n);
  for (int i=0; i<n; ++i) {
    XmlElement xi("Participation");
    xi["flap"] = flaps[i];
    xi["segment"] = str(segments[i]);
    xi["factor"] = str(factors[i]);
    xe.append(std::move(xi));
  }
  return xe;
}

void FlapSpecSet::Pattern::fromXml(const XmlElement &xe)
{
  assert(xe.name() == "FlapPattern");
  name = xe.attribute("name");
  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "Participation") {
      flaps.push_back( itr->attribute("flap") );
      segments.push_back( itr->attr2int("segment",0) );
      factors.push_back( itr->attr2float("factor",1.0) );
    }
  }
}

// --------------- FlapSpecSet -------------------------------------------

uint FlapSpecSet::findFlap(const std::string & s) const
{
  const int n = flaps.size();
  for (int i=0; i<n; ++i) {
    if (flaps[i].name() == s)
      return i;
  }
  return NotFound;
}

void FlapSpecSet::createDisplacements(MxMesh &mx) const
{
  const int nf = flaps.size();
  std::vector<FlapSpec::NodeIndexSet> segNodes(nf);
  for (int i=0; i<nf; ++i)
    flaps[i].createBoco(mx, segNodes[i]);

  const int npat = patterns.size();
  for (int i=0; i<npat; ++i) {
    PointList<3> dsp(mx.nnodes());
    const Pattern & pat(patterns[i]);
    const int nseg = pat.flaps.size();
    for (int j=0; j<nseg; ++j) {
      uint jseg = pat.segments[j];
      uint jf = findFlap( pat.flaps[j] );
      if (jf == NotFound) {
        dbprint("Flap", pat.flaps[j], "not stored in FlapSpecSet.");
        continue;
      }
      flaps[jf].createDisplacement(mx, jseg, segNodes[jf][jseg],
                                   dsp, pat.factors[j]);
    }

    uint ifield = mx.appendField(pat.name, dsp);
    mx.field(ifield).valueClass( MxMeshField::ValueClass::Displacement );
  }
}

XmlElement FlapSpecSet::toXml(bool share) const
{
  XmlElement xe("FlapSpecSet");
  for (uint i=0; i<flaps.size(); ++i)
    xe.append( flaps[i].toXml(share) );
  for (uint i=0; i<patterns.size(); ++i)
    xe.append( patterns[i].toXml(share) );
  return xe;
}

void FlapSpecSet::fromXml(const XmlElement &xe)
{
  assert(xe.name() == "FlapSpecSet");

  flaps.clear();
  patterns.clear();
  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "FlapSpec") {
      FlapSpec spec;
      spec.fromXml(*itr);
      flaps.push_back(spec);
    } else if (itr->name() == "FlapPattern") {
      Pattern pat;
      pat.fromXml(*itr);
      patterns.push_back(pat);
    }
  }
}


