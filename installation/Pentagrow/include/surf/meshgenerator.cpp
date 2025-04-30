
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
 
#include <set>
#include <boost/bind.hpp>
#include <genua/meshfields.h>
#include <genua/threadpool.h>
#include <genua/threadtask.h>
#include <genua/synchron.h>
#include <genua/dbprint.h>
#include "assembly.h"
#include "asycomponent.h"
#include "meshgenerator.h"
#include "wakecomponent.h"

using boost::ref;
using namespace std;

// --------------- local scope --------------------------------------------

class PremeshTask : public ThreadTask
{
public:
  PremeshTask(MeshComponent & mc, TTIntersector & tti) : m(mc), ti(tti) {}
  void work() {
    if (not m.freshMesh())
      m.premesh();
    ti.addMesh(m);
  }
private:
  MeshComponent & m;
  TTIntersector & ti;
};

class RefineTask : public ThreadTask
{
public:
  RefineTask(const TTiTopology & rtop, MeshGenerator & rmg,
             MeshComponent & mc) : topo(rtop),mg(rmg), m(mc), cok(true) {}

  void work() {
    if (not mg.incProgress())
      return;
    PointList<3> ilp;
    PointList<2> ilq;
    const int nlines = topo.nlines();
    m.clearConstraints();
    for (int j=0; j<nlines; ++j) {
      if ( topo.projection(j, &m, ilq, ilp) ) {
        if (ilq.size() < 2)
          continue;
        if (ilq.size() == 2 and sq(ilq[0]-ilq[1]) < gmepsilon)
          continue;
        cok &= m.constrain( ilq, ilp );
        if (not cok)
          break;
      }
    }
    if (not cok) {
      mg.interrupt();
      return;
    }
    DnRefineCriterionPtr rcp(m.criterion());
    Real fstr = rcp->maxStretch();
    if (m.nConstraint() > 0)
      rcp->maxStretch(4*fstr);
    m.refine();
    rcp->maxStretch(fstr);
  }

  bool success() const {return cok;}

private:
  TTiTopology topo;
  MeshGenerator & mg;
  MeshComponent & m;
  bool cok;
};

void append_task(MeshGenerator & mg, AsyComponentPtr & cp)
{
  if (not mg.incProgress())
    return;
  cp->append(mg);
}

void rfpass1_task(MeshGenerator & mg, const TTiTopology & topo, MeshComponentPtr & cp)
{
  if (not mg.incProgress())
    return;
  
  Indices vrl;
  RSpotArray rsa;
  DnRefineCriterionPtr rcp = cp->criterion();
  topo.spotRefinement(cp.get(), rcp->maxStretch(), rsa);
  topo.affectedVertices(cp.get(), vrl);
  uint npre = SpotRefine::append(rsa, 0.1, rcp);
  cp->refineAround(vrl);
  cp->refine();
  SpotRefine::erase(npre, rcp);
}

// --------------- MeshGenerator ------------------------------------------

uint MeshGenerator::findComponent(const std::string & s) const
{
  const int nc = components.size();
  for (int i=0; i<nc; ++i) {
    string id = components[i]->surface()->name();
    if (id == s)
      return i;
  }
  return NotFound;
}

void MeshGenerator::postprocess(uint iter, Real maxStretch,
                                Real maxPhi, Real mtol)
{
  ppIter = iter;
  ppMaxStretch = maxStretch;
  ppMaxPhi = maxPhi;
  ppMergeTol = mtol;
}

void MeshGenerator::process(const CmpAssembly & asy, bool rflocal,
                            ThreadPool *pool)
{
  // set number of processing steps
  const int nasy = asy.ncomponents();
  if (prog) {
    uint nstep(0);
    nstep += nasy;     // preprocessing
    nstep += 4;        // intersection
    if (rflocal)       // refinement and intersection
      nstep += 4 + 3*nasy;
    nstep += 3*nasy;   // global refinement
    nstep += 5;        // finalize
    prog->nsteps(nstep);
  }
  
  preprocess(asy, pool);
  intersect(pool);
  if (rflocal) {
    refineLocally(pool);
    for (int i=0; i<nasy; ++i)
      asy.component(i)->adaptCaps();
    intersect(pool);
  }
  refineGlobally(pool);

  for (int i=0; i<nasy; ++i)
    asy.component(i)->adaptCaps();

  finalize();
}

void MeshGenerator::preprocess(const CmpAssembly & asy, ThreadPool *pool)
{
  TriMesh::clear();
  components.clear();
  const int nasy = asy.ncomponents();
  
  if (pool != 0 and pool->nworker() > 1) {
    TaskContainer tc;
    for (int i=0; i<nasy; ++i)
      tc.pushFunction(boost::bind(append_task, boost::ref(*this), asy.component(i)));
    pool->nrprocess(&tc);
    tc.dispose();
  } else {
    for (int i=0; i<nasy; ++i) {
      if (not incProgress())
        return;
      asy.component(i)->append(*this);
    }
  }
}

void MeshGenerator::order()
{
  // not use yet, not tested

  const int n = components.size();
  mgorder.resize(n);
  vector<bool> used(n, false);
  int np = 0;
  for (int i=0; i<n; ++i) {
    if (components[i]->nParents() == 0) {
      mgorder[np] = i;
      used[i] = true;
      ++np;
    }
  }

  // no dependencies
  if (np == n)
    return;

  for (int k=0; k<n; ++k) {
    for (int i=0; i<n; ++i) {
      if (used[i])
        continue;
      MeshComponent & mc( *components[i] );

      // count the number of parent components already meshed
      uint nparused = 0;
      for (int j=0; j<np; ++j)
        nparused += mc.isParent( components[mgorder[j]].get() );
      if (nparused == mc.nParents()) {
        mgorder[np] = i;
        used[i] = true;
        ++np;
      }
      if (np == n)
        break;
    }
    if (np == n)
      break;
  }
  if (np != n)
    throw Error("MeshGenerator: Circular dependency between mesh components.");
}

void MeshGenerator::premesh()
{
  TriMesh::clear();
  const int n = components.size();
  for (int i=0; i<n; ++i) {
    //PointGrid<2> pgi;
    MeshComponent & mc( *components[i] );
    //const DnRefineCriterion & crit( *mc.criterion() );
    //mc.surface()->initGrid(crit.maxLength(), crit.minLength(),
    //                       crit.maxPhi(), pgi);
    //mc.clearConstraints();
    mc.premesh();
  }

  for (int i=0; i<n; ++i)
    components[i]->adapt();
}

void MeshGenerator::intersect(ThreadPool *pool)
{
  if (not incProgress())
    return;
  
  // construct intersector (serial)
  ttip = TTIntersectorPtr(new TTIntersector);
  const int nc = components.size();
  for (int i=0; i<nc; ++i)
    ttip->addMesh( *components[i] );
  ttip->sortFaces();  // needed to allow TTiConnection to bsearch faces
  ttip->updateBox();
  
  if (not incProgress())
    return;
  
  // compute intersections (parallel)
  if (pool != 0 and pool->nworker() > 1)
    ttip->mtIntersect(*pool, *ttip);
  else
    ttip->intersect(*ttip);
  
  // check for interruption again, intersection can take a while
  if (not incProgress())
    return;

  if (not incProgress())
    return;

  // Insert matching-edge constraint segments, this requires that
  // all faces are sorted first.
  for (uint i=0; i<connections.size(); ++i) {
    if (not connections[i].appendSegments(*ttip))
      throw Error("Surface connection failed.");
  }
  
  // compute topology (serial)
  topo = TTiTopology(ttip);
  int nlines = topo.findLines();
  dbprint("Topology search found", nlines, "intersection lines.");

  // filter intersection lines (serial for now)
  for (int i=0; i<nlines; ++i)
    topo.filter(i);

  // debug
#ifndef NDEBUG
  MeshFields mvz;
  for (int i=0; i<nc; ++i)
    mvz.addMesh(*components[i]);
  topo.addLineViz(mvz);
  mvz.toXml().write("intersections.xml", XmlElement::ZippedXml);
#endif
}

void MeshGenerator::refineLocally(ThreadPool *pool)
{
  // at this point, determine regions which need to be refined
  // because the intersection is not accurate enough
  const int nc = components.size();
  if (pool != 0 and pool->nworker() > 1) {
    TaskContainer tc;
    for (int i=0; i<nc; ++i)
      tc.pushFunction(boost::bind(rfpass1_task, boost::ref(*this),
                                  boost::ref(topo), components[i]));
    pool->nrprocess(&tc);
    tc.dispose();
  } else {
    for (int i=0; i<nc; ++i)
      rfpass1_task(*this, topo, components[i]);
  }

  // adaptation performed serially for now
  for (int i=0; i<nc; ++i)
    components[i]->adapt();
}

void MeshGenerator::refineGlobally(ThreadPool *pool)
{
  const int nc = components.size();
  if (pool != 0 and pool->nworker() > 1) {
    TaskContainer tc;
    for (int i=0; i<nc; ++i)
      tc.push(new RefineTask(topo, *this, *components[i]));
    pool->nrprocess(&tc);
    
    // check for failures
    for (int i=0; i<nc; ++i) {
      RefineTask *rfp = dynamic_cast<RefineTask*>( &tc[i] );
      if (rfp and (not rfp->success())) {
        components[i]->toXml(true).write("failure.xml", XmlElement::ZippedXml);
        string msg = "MeshGenerator: Constraint insertion failed. ";
        msg += components[i]->lastError();
        tc.dispose();
        throw Error(msg);
      }
    }
    tc.dispose();
  } else {
    
    PointList<3> ilp;
    PointList<2> ilq;
    const int nlines = topo.nlines();
    for (int i=0; i<nc; ++i) {
      
      bool cok = true;
      if (not incProgress())
        return;
      
      MeshComponent & m( *components[i] );
      m.clearConstraints();
      for (int j=0; j<nlines; ++j) {
        if ( topo.projection(j, &m, ilq, ilp) ) {

          // intercept edge case
          if (ilq.size() < 2)
            continue;
          if (ilq.size() == 2 and sq(ilq[0]-ilq[1]) < gmepsilon)
            continue;

          cok &= m.constrain( ilq, ilp );
          if (not cok)
            break;
        }
      }
      if (not cok) {
        interrupt();
        return;
      }
      DnRefineCriterionPtr rcp(m.criterion());
      Real fstr = rcp->maxStretch();
      if (m.nConstraint() > 0)
        rcp->maxStretch(4*fstr);
      m.refine();
      rcp->maxStretch(fstr);
    }
  }

  // adaptation performed serially for now
  for (int i=0; i<nc; ++i)
    components[i]->adapt();
}

void MeshGenerator::mergeComponent(const TriMesh & mc)
{
  ScopedLock lock(mgguard);
  TriMesh::merge(mc);
}

void MeshGenerator::finalize()
{
  if (not incProgress())
    return;
  
  // tag components and merge
  TriMesh::clear();
  // Indices exttag;
  const int nc = components.size();
  tagmap.resize(nc);
  for (int i=0; i<nc; ++i) {
    MeshComponent & mc(*components[i]);
    mc.faceTag(i);
    TriMesh::merge(mc);
    tagmap[i] = mc.surface()->name();
    TriMesh::tagName(i, mc.surface()->name());

    // debug
    mc.dbStoreMesh(tagmap[i]+"Merged.msh");
    dbStoreMesh("merged"+tagmap[i]+".msh");
  }

  if (not incProgress())
    return;

  TriMesh::cleanup(1e-6); //16*gmepsilon);
  TriMesh::dropDuplicates();
  if (not incProgress())
    return;

  dbStoreMesh("merged.msh");

  TriMesh wkm;
  extractWakes(wkm);

  dbStoreMesh("nowakes.msh");

  if (bDropOrphanRidges) {

    // identify cap tags
    Indices icaps;
    for (int i=0; i<nc; ++i) {
      string capname = tagmap[i] + "Cap";
      for (int j=i+1; j<nc; ++j) {
        if (tagmap[j].find(capname) != string::npos)
          insert_once(icaps, uint(j));
      }
    }

    dbprint("cap tags list length: ", icaps.size());
    TriMesh::dropOrphanRidges(icaps);

  }

  if (bDropInternal) {
    Indices iext;
    searchExternalInit(iext);
    TriMesh::dropInternalTriangles(iext, true);
  }
  if (not incProgress())
    return;

  // remerge with external part of wakes at this point
  merge(wkm);
  cleanup(16*gmepsilon);
  fixate(true);

  dbStoreMesh("merged_idrop.msh");
  
  TriMesh::dropTriStars();
  if (not incProgress())
    return;
  
  destretch();

  if (ppMergeTol > gmepsilon)
    TriMesh::cleanup(ppMergeTol);

  // reassign face tags (this merges caps with parent surfaces)
  retag();
}

void MeshGenerator::retag()
{
  const int nf = nfaces();
  for (int i=0; i<nf; ++i) {
    uint t = face(i).tag();
    if (t < components.size()) {
      uint ct = components[t]->tag();
      if (ct != NotFound)
        face(i).tag(ct);
    }
  }
}

void MeshGenerator::destretch()
{
  if (ppIter == 0) {
    return;
  }
  
  // pick very moderate destretching parameters
  if (ppMaxStretch < 0 or ppMaxPhi < 0) {
    ppMaxPhi = PI/9.;
    ppMaxStretch = 4.0;
    const int ns(components.size());
    for (int i=0; i<ns; ++i) {
      DnRefineCriterion rc(*(components[i]->criterion()));
      ppMaxPhi = min(ppMaxPhi, 0.5*rc.maxPhi());
      ppMaxStretch = max(ppMaxStretch, rc.maxStretch());
    }
  }
  
  uint nplus, ipass(0);
  do {
    nplus = TriMesh::dropStretchedTriangles(ppMaxStretch, ppMaxPhi);
    TriMesh::dropTriStars();
    ++ipass;
  } while (ipass < ppIter and nplus > 0);
  
  // try to repair flipped triangles
  Indices fflip;
  TriMesh::findFlippedFaces(fflip);
  const int nfe(fflip.size());
  for (int i=0; i<nfe; ++i)
    TriMesh::face(fflip[i]).reverse();
}

bool MeshGenerator::incProgress(uint k)
{
  if (prog) {
    prog->inc(k);
    if (prog->interrupt())
      return false;
    else
      return true;
  } else {
    return true;
  }
}

void MeshGenerator::interrupt()
{
  if (prog) {
    prog->interrupt(true);
  }
}

uint MeshGenerator::findTag(const std::string & s) const
{
  const int nc = tagmap.size();
  for (int i=0; i<nc; ++i) {
    if (tagmap[i] == s)
      return i;
  }
  return NotFound;
}

void MeshGenerator::searchExternalInit(Indices & itri) const
{
  // determine which tag is connected to which
  typedef vector< pair<int,int> > IntPairArray;
  IntPairArray pairs;
  IntPairArray::iterator pos;
  pair<int,int> p;
  const int ne = e2f.size();
  for (int i=0; i<ne; ++i) {
    const int edeg = e2f.size(i);
    const uint *nbf = e2f.first(i);
    int tbase = TriMesh::face(nbf[0]).tag();
    for (int k=1; k<edeg; ++k) {
      int tk = face(nbf[k]).tag();
      if (tk != tbase) {
        p.first = min(tk, tbase);
        p.second = max(tk, tbase);
        pos = lower_bound(pairs.begin(), pairs.end(), p);
        if (pos == pairs.end() or *pos != p)
          pairs.insert(pos, p);
      }
    }
  }

#ifndef NDEBUG
  cout << pairs.size() << " component connections: " << endl;
  for (uint i=0; i<pairs.size(); ++i) {
    cout << tagmap[pairs[i].first] << " -to- " << tagmap[pairs[i].second] << endl;
  }
#endif
  
  vector<int> taggroup;
  while (not pairs.empty()) {
    taggroup.clear();
    pair<int,int> pcur = pairs.back();
    pairs.pop_back();
    insert_once(taggroup, pcur.first);
    insert_once(taggroup, pcur.second);
    
    uint np;
    do {
      np = pairs.size();
      for (uint i=0; i<np; ++i) {
        int s = pairs[i].first;
        int t = pairs[i].second;
        if (binary_search(taggroup.begin(), taggroup.end(), s)) {
          insert_once(taggroup, t);
          pairs.erase(pairs.begin() + i);
          break;
        } else if (binary_search(taggroup.begin(), taggroup.end(), t)) {
          insert_once(taggroup, s);
          pairs.erase(pairs.begin() + i);
          break;
        }
      }
    } while (np > pairs.size());
    
    // for each set of tags which make a connected set, add the
    // forwardmost triangle to the set
    if (not taggroup.empty()) {
      uint itx(0);
      Real xmin = huge;
      const int nf = nfaces();
      for (int i=0; i<nf; ++i) {
        const TriFace & f( face(i) );
        if (not binary_search(taggroup.begin(), taggroup.end(), f.tag()) )
          continue;
        Vct3 p = f.center();
        if (p[0] < xmin) {
          xmin = p[0];
          itx = i;
        }
      }
      insert_once(itri, itx);
      
      //#ifndef NDEBUG
      //      cout << "Tag group: " << endl;
      //      for (uint j=0; j<taggroup.size(); ++j)
      //        cout << tagmap[taggroup[j]] << " p " << face(itx).center() << endl;
      //#endif
    }
  }

  if (not itri.empty())
    dbprint("iext size ", itri.size(),
            " first: ", face(itri.front()).center());

}

void MeshGenerator::extractWakes(TriMesh & wkm)
{
  // split mesh into
  // (a) triangles which are known not to be on wakes.
  //     this submesh in itself must be watertight and can use the mesh
  //     merge procedure used for manifold surfaces
  // (b) the external part of all wakes, i.e. the part of all wakes which is
  //     beyond

  // collect tags of all wake components
  Indices wtags;
  Vct3 fartg;     // farfield tangent
  const int nc = components.size();
  for (int i=0; i<nc; ++i) {
    WakeComponentPtr wcp;
    wcp = boost::dynamic_pointer_cast<WakeComponent>( components[i] );
    if (not wcp)
      continue;
    insert_once(wtags, (uint) i);
    WakeSurfPtr wsp;
    wsp = boost::dynamic_pointer_cast<WakeSurf>( wcp->surface() );
    assert(wsp);
    fartg = wsp->farfieldTangent();
  }

  if (wtags.empty())
    return;

  // determine triangle from which to start walking
  // pick the triangle which is farthest downstream with respect
  // to the farfield flow direction
  const int nwake = wtags.size();
  Indices fstart(nwake, NotFound);
  const int nf = nfaces();
  Vector xfar(nwake, -huge);
  Indices nowtri; // non-wake triangles
  for (int i=0; i<nf; ++i) {
    uint iwk = sorted_index(wtags, (uint) face(i).tag());
    if (iwk == NotFound) {
      nowtri.push_back(i);
      continue;
    }
    Real x = dot(fartg, face(i).center());
    if ( x > xfar[iwk] ) {
      xfar[iwk] = x;
      fstart[iwk] = i;
    }
  }

  // for crossing wakes, we need to add more starting points because
  // we need at least one point on each side of the joining line.
  // look at edges with degree 1 which make a large angle with the
  // freestream direction
  const Real maxcosphi = cos(rad(60.));
  const Real minxwake = 0.75;
  const int ne = nedges();
  for (int i=0; i<ne; ++i) {

    // look for boundary edges only
    if (e2f.size(i) != 1)
      continue;

    // exclude edges which make a smaller angle with farfield tangent
    const Vct3 & ps( vertex(edge(i).source()) );
    const Vct3 & pt( vertex(edge(i).target()) );
    Real cosphi = cosarg(fartg, pt - ps);
    if (fabs(cosphi) > maxcosphi)
      continue;

    // determine which wake we are on, if any
    uint nbf = *(e2f.first(i));
    uint iwk = sorted_index(wtags, (uint) face(nbf).tag());
    if (iwk == NotFound)  // not a wake triangle
      continue;

    // exclude trailing edges by comparing the downstream coordinate
    // to the maximum value found on this wake
    Real x = dot(fartg, face(nbf).center());
    if ( x < minxwake*xfar[iwk] )
      continue;

    cout << "Marked as external: " << face(nbf).center()
         << " on " << iwk << " cosphi " << cosphi << endl;
    fstart.push_back(nbf);
  }

  // walk along edges with degree 2 only
  // this makes sure that we do not include internal triangles, i.e. wake
  // triangles inside the bodies
  set<uint> ixternal;
  deque<uint> queue(fstart.begin(), fstart.end());
  while (not queue.empty()) {

    uint fcur = queue.front();
    queue.pop_front();

    // ignore triangle which is already marked as external
    if ( ixternal.find(fcur) != ixternal.end() )
      continue;

    ixternal.insert(fcur);
    nb_edge_iterator ite, first, last;
    first = f2eBegin(fcur);
    last = f2eEnd(fcur);
    for (ite = first; ite != last; ++ite) {
      uint fnext(NotFound);
      uint ei = ite.index();
      uint edeg = e2f.size(ei);

      if (edeg != 2)
        continue;

      // move across edge if edge has degree 2
      const uint *nbf(e2f.first(ei));
      assert(fcur == nbf[0] or fcur == nbf[1]);
      if (fcur == nbf[0])
        fnext = nbf[1];
      else
        fnext = nbf[0];

      // if its tag indicates that the triangle across the edge is a
      // wake triangle, put it at the end of the queue, unless it is
      // already marked as external and therefore has been processed
      int tag = face(fnext).tag();
      if ( binary_search(wtags.begin(), wtags.end(), tag)
           and (ixternal.find(fnext) == ixternal.end())  ) {
        queue.push_back(fnext);
      }
    } // nb edge loop
  }

  // copy external part of the wake to wkm
  wkm.clear();
  wkm.vertices() = vertices();
  set<uint>::const_iterator itr, ilast = ixternal.end();
  for (itr = ixternal.begin(); itr != ilast; ++itr) {
    const TriFace & f( face(*itr) );
    wkm.addFace(f.vertices(), f.tag());
  }
  wkm.fixate(true);

  // now, remove *all* wake faces from *this before running the internal
  // triangle removal step
  const int nwf = nowtri.size();
  TriFaceArray fkeep(nwf);
  for (int i=0; i<nwf; ++i)
    fkeep[i] = face(nowtri[i]);

  faces.swap(fkeep);
  fixate(true);
}

#ifndef NDEBUG
void MeshGenerator::dbStoreMesh(const std::string & fname) const
{
  TriMesh::toXml(true).write(fname, XmlElement::ZippedXml);
}
#else
void MeshGenerator::dbStoreMesh(const std::string &) const
{}
#endif

void MeshGenerator::loadCollection(const std::string & fname)
{
  components.clear();
  
  XmlElement xe;
  xe.read(fname);
  
  XmlElement::const_iterator itr, ilast;
  ilast = xe.end();
  for (itr = xe.begin(); itr != ilast; ++itr) {
    SurfacePtr sfp = Surface::createFromXml(*itr);
    if (sfp) {
      XmlElement::const_iterator imc;
      imc = itr->findChild("MeshCriterion");
      if (imc != itr->end()) {
        DnRefineCriterionPtr rfc = DnRefineCriterion::createFromXml(*imc);
        if (rfc) {
          MeshComponentPtr mcp(new MeshComponent(sfp, rfc));
          PointGrid<2> pgi;
          sfp->initGrid(rfc->maxLength(), rfc->minLength(), rfc->maxPhi(), pgi);
          mcp->premesh(pgi);
          addComponent(mcp);
        }
      }
    }
  }
}

// ------- deprecated -------------------------------------------------------

/*

void MeshGenerator::process()
{
  if (prog)
    prog->nsteps(2*components.size() + 8);

  TriMesh::clear();
  ttip = TTIntersectorPtr(new TTIntersector);
  
  // perform premeshing
  const int nc = components.size();
  for (int i=0; i<nc; ++i) {
    MeshComponent & mc( *components[i] );
    if (not mc.freshMesh())
      mc.premesh();
    ttip->addMesh(mc);
    if (not incProgress())
      return;
}
  ttip->updateBox();
  
  // compute intersections
  ttip->intersect(*ttip);
  
  if (not incProgress())
    return;

  // compute topology
  topo = TTiTopology(ttip);
  int nlines = topo.findLines();
  
  // filter intersection lines
  for (int i=0; i<nlines; ++i)
    topo.filter(i);

  if (not incProgress())
    return;

  // debug
#ifndef NDEBUG
  MeshFields mvz;
  for (int i=0; i<nc; ++i)
    mvz.addMesh(*components[i]);
  topo.addLineViz(mvz);
  uint icmp(1);
  Indices comp(ttip->nfaces());
  std::fill(comp.begin(), comp.end(), 0);
  ttip->setComponents(comp, icmp);
  mvz.addComponentSet("Leaf box index", comp);
  mvz.toXml().write("intersections.xml");
#endif

  // constrain patches with intersection lines
  PointList<3> ilp;
  PointList<2> ilq;
  bool cok;
  for (int i=0; i<nc; ++i) {
    MeshComponent & mc( *components[i] );
    mc.clearConstraints();
    for (int j=0; j<nlines; ++j) {
      if ( topo.projection(j, components[i].get(), ilq, ilp) ) {
        cok = mc.constrain( ilq, ilp );
        if (not cok) {
          mc.toXml().write("failure.xml");
          throw Error("MeshGenerator: Constraint insertion failed.");
}
}
}

    // refine component mesh after constraints inserted
    mc.refine();
    //mc.faceTag(i+1);
    //TriMesh::merge(mc);
    if (not incProgress())
      return;
}

  // finalize
}

void MeshGenerator::process(ThreadPool & pool)
{  
  TriMesh::clear();
  ttip = TTIntersectorPtr(new TTIntersector);
  
  // container for meshing tasks
  TaskContainer tc;
  
  // perform premeshing
  const int nc = components.size();
  for (int i=0; i<nc; ++i)
    tc.push( new PremeshTask(*components[i], *ttip) );
    
  // perform premeshing in parallel
  pool.nrprocess(&tc);
  tc.dispose();
  
  ttip->updateBox();
  
  // compute intersections
  ttip->mtIntersect(pool, *ttip);
  
  // compute topology
  topo = TTiTopology(ttip);
  int nlines = topo.findLines();
  
  // filter intersection lines
  for (int i=0; i<nlines; ++i)
    topo.filter(i);

  // constrain patches with intersection lines
  for (int i=0; i<nc; ++i)
    tc.push( new RefineTask(topo, *this, *components[i]) );
    
  // perform premeshing in parallel
  pool.nrprocess(&tc);
  
  // see if any of the refinement tasks failed
  for (uint jt=0; jt<tc.size(); ++jt) {
    const RefineTask & t = dynamic_cast<const RefineTask&>( tc[jt] );
    if (&t and (not t.success())) {
      throw Error("MeshGenerator: Constraint insertion failed.");
}
}
  tc.dispose();

  // finalize
}

void MeshGenerator::process(const CmpAssembly & asy)
{
  if (prog)
    prog->nsteps(4*asy.ncomponents() + 9);

  TriMesh::clear();
  ttip = TTIntersectorPtr(new TTIntersector);

  if (not incProgress())
    return;

  // populate components
  components.clear();
  const int nasy = asy.ncomponents();
  for (int i=0; i<nasy; ++i) {
    asy.component(i)->append(*this);
    if (not incProgress())
      return;
}

  if (not incProgress())
    return;

  // perform premeshing
  const int nc = components.size();
  for (int i=0; i<nc; ++i) {
    MeshComponent & mc( *components[i] );
    if (not mc.freshMesh())
      mc.premesh();
    ttip->addMesh(mc);
}
  ttip->updateBox();
  
  // compute intersections
  ttip->intersect(*ttip);
  
  if (not incProgress())
    return;

  // compute topology
  topo = TTiTopology(ttip);
  int nlines = topo.findLines();
  
  // refine intersections
  //
  // Disabled because the refinement procedure can move intersection
  // nodes such that intersection lines will cross on the surface,
  // which introduces the necessity of another constraint splitting
  // pass -- too complex. Need to refine without change of topology!
  //topo.refine();
  
  // filter intersection lines
  for (int i=0; i<nlines; ++i)
    topo.filter(i);

  if (not incProgress())
    return;

  // debug
#ifndef NDEBUG
  MeshFields mvz;
  for (int i=0; i<nc; ++i)
    mvz.addMesh(*components[i]);
  topo.addLineViz(mvz);
  uint icmp(1);
  Indices comp(ttip->nfaces());
  std::fill(comp.begin(), comp.end(), 0);
  ttip->setComponents(comp, icmp);
  mvz.addComponentSet("Leaf box index", comp);
  mvz.toXml().write("intersections.xml");
#endif

  // constrain patches with intersection lines
  PointList<3> ilp;
  PointList<2> ilq;
  bool cok;
  for (int i=0; i<nc; ++i) {
    MeshComponent & mc( *components[i] );
    mc.clearConstraints();
    for (int j=0; j<nlines; ++j) {
      if ( topo.projection(j, components[i].get(), ilq, ilp) ) {
        cok = mc.constrain( ilq, ilp );
        if (not cok) {
          mc.toXml().write("failure.xml");
          string msg = "MeshGenerator: Constraint insertion failed. ";
          msg += mc.lastError();
          throw Error(msg);
}
}
}

    DnRefineCriterionPtr rcp(mc.criterion());
    
//     // append refinement regions if necessary
//     RSpotArray rsa;
//     topo.spotRefinement(&mc, rcp->maxStretch(), rsa);
//     
//     // debug
//     cout << "Surface " << mc.surface()->name() << ": " << rsa.size() << " regions." << endl;
//     for (uint ir=0; ir<rsa.size(); ++ir)
//       rsa[ir].write(cout);

    // refine component mesh after constraints inserted
    // but disable refinement of stretched triangles because that
    // is futile in the presence of non-flippable constraints
    //uint npre = SpotRefine::append(rsa, 0.1, rcp);
//     Real fstr = rcp->maxStretch();
//     if (mc.nConstraint() > 0) {
//       rcp->maxStretch(2*fstr);
//     }
    mc.refine();
    
    // reset previous state
    //rcp->maxStretch(fstr);
    //SpotRefine::erase(npre, rcp);

    if (not incProgress())
      return;
}

  // rebuild cap surfaces after constraint insertion
  for (int i=0; i<nasy; ++i)
    asy.component(i)->adaptCaps();
}

void MeshGenerator::xprocess(const CmpAssembly & asy)
{
  if (prog)
    prog->nsteps(4*asy.ncomponents() + 11);

  TriMesh::clear();
  
  // populate components
  components.clear();
  const int nasy = asy.ncomponents();
  for (int i=0; i<nasy; ++i) {
    asy.component(i)->append(*this);
    if (not incProgress())
      return;
}

  if (not incProgress())
    return;

  // construct intersector
  ttip = TTIntersectorPtr(new TTIntersector);
  const int nc = components.size();
  for (int i=0; i<nc; ++i) {
    MeshComponent & mc( *components[i] );
    if (not mc.freshMesh())
      mc.premesh();
    ttip->addMesh(mc);
}
  ttip->updateBox();
  
  // compute intersections
  ttip->intersect(*ttip);
  
  if (not incProgress())
    return;

  // compute topology
  topo = TTiTopology(ttip);
  int nlines = topo.findLines();
  
  // refine intersections
  //
  // Disabled because the refinement procedure can move intersection
  // nodes such that intersection lines will cross on the surface,
  // which introduces the necessity of another constraint splitting
  // pass -- too complex. Need to refine without change of topology!
  //topo.refine();
  
  // filter intersection lines
  for (int i=0; i<nlines; ++i)
    topo.filter(i);

  if (not incProgress())
    return;

  // at this point, determine regions which need to be refined
  // because the intersection is not accurate enough, refine
  // locally and reset the criterion to its original value
  for (int i=0; i<nc; ++i) {
    Indices vrl;
    RSpotArray rsa;
    DnRefineCriterionPtr rcp = components[i]->criterion();
    topo.spotRefinement(components[i].get(), rcp->maxStretch(), rsa);
    topo.affectedVertices(components[i].get(), vrl);
    uint npre = SpotRefine::append(rsa, 0.1, rcp);
    components[i]->refineAround(vrl);
    components[i]->refine();
    SpotRefine::erase(npre, rcp);
}

  if (not incProgress())
    return;

  // now, recompute all intersections on the locally refined meshes
  ttip.reset(new TTIntersector);
  for (int i=0; i<nc; ++i)
    ttip->addMesh( *components[i] );
  ttip->updateBox();
  ttip->intersect(*ttip);
  
  if (not incProgress())
    return;

  // compute intersection topology again
  topo = TTiTopology(ttip);
  nlines = topo.findLines();
  
  // filter intersection lines
  for (int i=0; i<nlines; ++i)
    topo.filter(i);

  if (not incProgress())
    return;

    // debug
#ifndef NDEBUG
  MeshFields mvz;
  for (int i=0; i<nc; ++i)
    mvz.addMesh(*components[i]);
  topo.addLineViz(mvz);
  uint icmp(1);
  Indices comp(ttip->nfaces());
  std::fill(comp.begin(), comp.end(), 0);
  ttip->setComponents(comp, icmp);
  mvz.addComponentSet("Leaf box index", comp);
  mvz.toXml().write("intersections.xml");
#endif

  // finally, constrain patches with intersection lines
  PointList<3> ilp;
  PointList<2> ilq;
  bool cok;
  for (int i=0; i<nc; ++i) {
    MeshComponent & mc( *components[i] );
    mc.clearConstraints();
    for (int j=0; j<nlines; ++j) {
      if ( topo.projection(j, components[i].get(), ilq, ilp) ) {
        cok = mc.constrain( ilq, ilp );
        if (not cok) {
          mc.toXml().write("failure.xml");
          string msg = "MeshGenerator: Constraint insertion failed. ";
          msg += mc.lastError();
          throw Error(msg);
}
}
}

    DnRefineCriterionPtr rcp(mc.criterion());
    
    // refine component mesh after constraints inserted
    // but disable refinement of stretched triangles because that
    // is futile in the presence of non-flippable constraints
    Real fstr = rcp->maxStretch();
    if (mc.nConstraint() > 0) {
      rcp->maxStretch(4*fstr);
}
    mc.refine();
    rcp->maxStretch(fstr);

    if (not incProgress())
      return;
}

  // rebuild cap surfaces after constraint insertion
  for (int i=0; i<nasy; ++i)
    asy.component(i)->adaptCaps();
}

void MeshGenerator::xprocess(const CmpAssembly & asy, ThreadPool & pool)
{
  const int nasy = asy.ncomponents();
  if (prog)
    prog->nsteps(7*nasy + 9);

  TriMesh::clear();

  // task list
  TaskContainer tc;
  
  // populate components
  components.clear();
  for (int i=0; i<nasy; ++i)
    tc.pushFunction(boost::bind(append_task, ref(*this), asy.component(i)));
  pool.nrprocess(&tc);
  tc.dispose();
  
  // construct intersector (serial)
  ttip = TTIntersectorPtr(new TTIntersector);
  const int nc = components.size();
  for (int i=0; i<nc; ++i) {
    MeshComponent & mc( *components[i] );
    if (not mc.freshMesh())
      mc.premesh();
    ttip->addMesh(mc);
}
  ttip->updateBox();

  // check once before, next step will take long
  if (not incProgress())
    return;

  // compute intersections (parallel)
  ttip->mtIntersect(pool, *ttip);

  // check for interruption again, intersection can take a while
  if (not incProgress())
    return;

  // compute topology (serial)
  topo = TTiTopology(ttip);
  int nlines = topo.findLines();
  
  // filter intersection lines (serial for now)
  for (int i=0; i<nlines; ++i)
    topo.filter(i);
    
  // at this point, determine regions which need to be refined
  // because the intersection is not accurate enough, refine
  // locally and reset the criterion to its original value
  for (int i=0; i<nc; ++i)
    tc.pushFunction(boost::bind(rfpass1_task, ref(*this),
                    ref(topo), components[i]));
  pool.nrprocess(&tc);
  tc.dispose();

  if (not incProgress())
    return;

  // now, recompute all intersections on the locally refined meshes
  ttip.reset(new TTIntersector);
  for (int i=0; i<nc; ++i)
    ttip->addMesh( *components[i] );
  ttip->updateBox();
  ttip->mtIntersect(pool, *ttip);
  
  if (not incProgress())
    return;

  // compute intersection topology again
  topo = TTiTopology(ttip);
  nlines = topo.findLines();
  
  // filter intersection lines (serial for now)
  for (int i=0; i<nlines; ++i)
    topo.filter(i);
    
  // debug
#ifndef NDEBUG
  MeshFields mvz;
  for (int i=0; i<nc; ++i)
    mvz.addMesh(*components[i]);
  topo.addLineViz(mvz);
  uint icmp(1);
  Indices comp(ttip->nfaces());
  std::fill(comp.begin(), comp.end(), 0);
  ttip->setComponents(comp, icmp);
  mvz.addComponentSet("Leaf box index", comp);
  mvz.toXml().write("intersections.xml");
#endif

  // final refinement pass (parallel)
  for (int i=0; i<nc; ++i)
    tc.push(new RefineTask(topo, *this, *components[i]));
  pool.nrprocess(&tc);
  
  // after refinement pass 2, check for failures
  for (int i=0; i<nc; ++i) {
    RefineTask *rfp = dynamic_cast<RefineTask*>( &tc[i] );
    if (rfp and (not rfp->success())) {
      components[i]->toXml().write("failure.xml");
      string msg = "MeshGenerator: Constraint insertion failed. ";
      msg += components[i]->lastError();
      tc.dispose();
      throw Error(msg);
}
}
  tc.dispose();
  
  // rebuild cap surfaces after constraint insertion (serial)
  for (int i=0; i<nasy; ++i)
    asy.component(i)->adaptCaps();
}

*/
