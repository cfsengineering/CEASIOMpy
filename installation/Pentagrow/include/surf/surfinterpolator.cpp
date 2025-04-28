
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
#include "surfinterpolator.h"
#include <genua/mxmesh.h>
#include <genua/csrmatrix.h>
#include <genua/ffanode.h>
#include <genua/xcept.h>
#include <genua/dbprint.h>
#include <genua/smallqr.h>
#include <genua/smatrix.h>
#include <genua/synchron.h>
#include <genua/eig.h>
#include <genua/lls.h>
#include <genua/timing.h>
#include <genua/abstractlinearsolver.h>
#include <sstream>

using namespace std;

SurfInterpolator::~SurfInterpolator()
{}

void SurfInterpolator::jumpCriteria(Real nrmDev, Real absDst)
{
  m_maxNrmDev = nrmDev;
  if (absDst > 0) {
    m_maxDistance = absDst;
  } else if (m_mappedNodes.empty()) {
    m_maxDistance = std::numeric_limits<Real>::max();
  } else {
    // use 0.5% of diagonal model dimension
    Vct3 plo, phi;
    boundingBox(plo, phi);
    absDst = 5e-3 * norm(phi - plo);
  }
}

void SurfInterpolator::buildTreeFromSections(const Indices &sections)
{
  if (not sections.empty())
    m_tree.build(*m_pstr, sections);
  else
    m_tree.build(*m_pstr);
}

static void insert_element(MxTriTree::SubsetArray &sba,
                           uint isec, uint idx, uint nel)
{
  MxTriTree::SubsetArray::iterator pos;
#if !defined(_MSC_VER)
  pos = std::lower_bound(sba.begin(), sba.end(), isec);
#else // MSVC 2008 does not find the defined operator< for the above to work
  MxTriTree::SubsetCompare cmp;
  pos = std::lower_bound(sba.begin(), sba.end(), isec, cmp);
#endif
  if (pos != sba.end() and pos->isection == isec) {
    pos->elementList.push_back(idx);
  } else {
    MxTriTree::Subset sub;
    sub.isection = isec;
    sub.elementList.reserve(nel);
    sub.elementList.push_back(idx);
    sba.insert(pos, sub);
  }
}

void SurfInterpolator::buildTreeByPid(const Indices &pidwet,
                                      const Indices &pidintern)
{
  bool bInclude = (pidwet.size() > 0);
  bool bExclude = (pidintern.size() > 0);

  // bailout on logical error
  if (bInclude and bExclude)
    throw Error("Cannot specify both inclusion and exclusion PID set.");

  MxTriTree::SubsetArray sba;
  if (bInclude or bExclude) {

    uint pidfi = m_pstr->findField("PID");
    if (pidfi == NotFound)
      throw Error("PID field not found in structural mesh.");
    const MxMeshField & fpid( m_pstr->field(pidfi) );
    if (fpid.nodal() or fpid.realField())
      throw Error("Field labeled PID does not contain element PIDs");
    // const int *pid = fpid.intPointer();
    DVector<int> pid;
    fpid.fetch(pid);

    for (uint k=0; k<m_pstr->nsections(); ++k) {
      const MxMeshSection & sec( m_pstr->section(k) );
      if (not sec.surfaceElements())
        continue;
      const int offs = sec.indexOffset();
      const int ne = sec.nelements();
      for (int i=0; i<ne; ++i) {
        const uint eix = offs + i;
        const uint p = pid[eix];
        bool incel = binary_search(pidwet.begin(), pidwet.end(), p);
        bool excel = binary_search(pidintern.begin(), pidintern.end(), p);
        if ( bExclude and (not excel) )
          insert_element(sba, k, i, ne);
        else if (bInclude and incel)
          insert_element(sba, k, i, ne);
      }
    }

  } else {

    // no PID lists given, just use all shell elements found
    buildTreeFromSections();
    return;
  }

  m_tree.build(*m_pstr, sba);
}

Vct3f SurfInterpolator::evalDisplacement(uint ifield, const uint v[],
                                         const Mtx33f h[]) const
{
  Vct3f dsp, a;
  const MxMeshField & field( m_pstr->field(ifield) );
  for (int k=0; k<3; ++k) {
    field.value(v[k], dsp);
    a += h[k] * dsp;
  }
  return a;
}

Vct3f SurfInterpolator::evalDisplacement(uint anode, uint ifield,
                                         const uint v[], const float wuv[]) const
{
  // structural mesh nodes
  Vct3f tri[3];
  for (int k=0; k<3; ++k)
    tri[k] = m_pstr->node( v[k] );

  // displacements at triangle nodes
  Vct3f dsp[3];
  const MxMeshField & field( m_pstr->field(ifield) );
  for (int k=0; k<3; ++k)
    field.value(v[k], dsp[k]);

  // displacement of foot point below node a
  Vct3f da;
  for (int k=0; k<3; ++k)
    da += wuv[k] * dsp[k];

  // rotational contribution
  Vct3f Su( tri[1] - tri[0] );
  Vct3f Sv( tri[2] - tri[0] );

  // change of normal caused by nodal displacements
  Vct3f dn = cross(dsp[1]-dsp[0], Sv) + cross(Su, dsp[2]-dsp[0]);
  if (sq(dn) == 0.0f)
    return da;

  // find ax which is orthogonal to face normal *and* change of normal
  Vct3f fn = cross(Su, Sv);
  Vct3f ax = cross(fn, dn);

  // adjust scaling of ax such that cross(ax,fn) has length |dn|
  float naxf = norm(cross(ax, fn));
  if (naxf == 0.0f)
    return da;
  else
    ax *= norm(dn) / norm(cross(ax, fn));

  Vct3f pfoot;
  for (int k=0; k<3; ++k)
    pfoot += wuv[k] * tri[k];
  Vct3f r = Vct3f(m_paer->node(anode)) - pfoot;
  da += cross(ax, r);

  return da;
}

void SurfInterpolator::evalDisplacements(uint anode, const uint v[],
                                         const float wuv[],
                                         float *column) const
{
  // structural mesh nodes
  Vct3f tri[3];
  for (int k=0; k<3; ++k)
    tri[k] = m_pstr->node( v[k] );

  Vct3f pfoot;
  for (int k=0; k<3; ++k)
    pfoot += wuv[k] * tri[k];
  Vct3f r = Vct3f(m_paer->node(anode)) - pfoot;

  // tangents
  Vct3f Su( tri[1] - tri[0] );
  Vct3f Sv( tri[2] - tri[0] );
  Vct3f fn = cross(Su, Sv);

  // displacements at triangle nodes
  Vct3f dsp[3], da, dn, ax;
  const int nfield = m_strFields.size();
  for (int ifield=0; ifield<nfield; ++ifield) {
    const MxMeshField & field( m_pstr->field(m_strFields[ifield]) );
    for (int k=0; k<3; ++k)
      field.value(v[k], dsp[k]);

    // displacement of foot point below node a
    da = 0.0f;
    for (int k=0; k<3; ++k)
      da += wuv[k] * dsp[k];

    // change of normal caused by nodal displacements
    dn = cross(dsp[1]-dsp[0], Sv) + cross(Su, dsp[2]-dsp[0]);

    // find ax which is orthogonal to face normal *and* change of normal
    ax = cross(fn, dn);

    float naxf = norm(cross(ax, fn));
    if (naxf != 0.0f) {
      // adjust scaling of ax such that cross(ax,fn) has length |dn|
      ax *= norm(dn) / naxf;
      da += cross(ax, r);
    }

    for (int k=0; k<3; ++k)
      column[3*ifield+k] = da[k];
  }
}

Vct3f SurfInterpolator::evalMap(uint anode, const uint v[],
                                const float wuv[], Mtx33f h[]) const
{
  // initialize mapping matrices with diagonal entries
  for (int k=0; k<3; ++k)
    h[k] = wuv[k] * Mtx33f::identity();

  // structural mesh nodes and foot point
  Vct3f tri[3], qfoot;
  for (int k=0; k<3; ++k) {
    tri[k] = m_pstr->node( v[k] );
    qfoot += wuv[k] * tri[k];
  }

  // distance vector foot-to-aerodynamic surface
  Vct3f rpq = Vct3f(m_paer->node(anode)) - qfoot;
  if (sq(rpq) == 0.0f)
    return qfoot;

  // triangle edge vectors
  Vct3f rab = tri[1] - tri[0];
  Vct3f rac = tri[2] - tri[0];

  // unit triangle normal
  Vct3f n = cross(rab, rac);
  float nabc = normalize(n);

  Mtx33f crab = cross_matrix(rab / nabc);
  Mtx33f crac = cross_matrix(rac / nabc);

  Mtx33f Hab = dyadic(n, rpq*crac) - dot(rpq,n)*crac;
  Mtx33f Hac = dot(rpq,n)*crab - dyadic(n, rpq*crab);

  // assemble nodal mapping matrices
  h[0] -= (Hab + Hac);
  h[1] += Hab;
  h[2] += Hac;

  return qfoot;
}

uint SurfInterpolator::map()
{
  Wallclock clk;
  assert(m_pstr);
  assert(m_paer);

  if (m_mappedNodes.empty())
    collectWallNodes();
  if (m_strFields.empty())
    collectDispFields();

  // raw storage for mapped fields
  const int nwall = m_mappedNodes.size();
  const int nmapfield = m_strFields.size();
  DMatrix<float> m(3*nmapfield, nwall);

  // flag indicating whether projection was found within catch radius
  const float sqcr = sq(m_catchRadius);
  std::vector<bool> caught(nwall);
  PointList<3> feet(nwall);

  clk.start();
  Logger::nextStage(nwall);

  // process aerodynamic nodes in parallel
#pragma omp parallel for schedule(dynamic, 128)
  for (int i=0; i<nwall; ++i) {
    Mtx33f h[3];
    float coef[3];
    uint nds[3];

    const uint iwn = m_mappedNodes[i];
    m_tree.projection( m_paer->node(iwn), nds, coef );
    caught[i] = (sqDistance(iwn, nds, coef) < sqcr);

    // determine mapping matrices once
    feet[i] = evalMap(iwn, nds, coef, h);

    for (int j=0; j<nmapfield; ++j) {
      //Vct3f df = evalDisplacement(iwn, m_strFields[j], nds, coef);
      Vct3f df = evalDisplacement(m_strFields[j], nds, h);
      for (int k=0; k<3; ++k)
        m(3*j+k, i) = m_scale * df[k]; // disjoint write access: i
    }

    Logger::increment();
  }

  log("[t] Mapping deformations: ", clk.stop());

  // connectivity of mapped vertices
  ConnectMap v2v;

  // optional postprocessing by smoothing
  if (m_smoothSelective != 0) {

    clk.start();
    DispInterpolator::mapAerTopology(m_mappedNodes, v2v);
    if (m_pstr->v2eMap().size() != m_pstr->nnodes())
      m_pstr->fixate();

    Indices rnodes;
    if (m_maxNrmDev < PI)
      riskyNodes(v2v, rnodes, m_maxNrmDev);
    jumpNodes(rnodes);
    topoNeighbors(v2v, rnodes);

    log("[t] Discontinuity candidate identification: ", clk.stop());

    // insert nodes classified as concave
    if (m_concavityLimit > 0.0) {
      const uint npre = rnodes.size();
      collectConcaveNodes(v2v, feet, rnodes);
      sort_unique(rnodes);
      log("[i] Concavity criterion nodes: ", rnodes.size() - npre);
    }
    log("[i] Nodes to smooth:", rnodes.size());

    //#ifndef NDEBUG
    // DispInterpolator ignores this boundary name by default
    uint ibc = m_paer->findBoco("JumpElements");
    if (ibc != NotFound)
      m_paer->eraseBoco(ibc);
    ibc = appendNodeSet(rnodes);
    m_paer->boco(ibc).rename("JumpElements");
    //#endif

    clk.start();
    if (m_smoothSelective > 0)
      smoothDisplacements(rnodes, v2v, m, m_smoothSelective, m_smOmega);
    else
      diffuseDisplacements(v2v, rnodes, m);
    log("[t] Selective smoothing application: ", clk.stop());
  }

  // optional postprocessing by global smoothing
  if (m_smoothGlobal > 0) {
    size_t nsm = m_mappedNodes.size();
    Indices all(nsm);
    std::iota(all.begin(), all.end(), 0);
    smoothDisplacements(all, v2v, m, m_smoothGlobal, m_smOmega);
  }

  // enforce sliding constraints
  if (not m_snset.empty())
    pinSlidingNodes(m);

  XmlElement xns("SurfMappedNodeSet");
  xns.asBinary(m_mappedNodes.size(), &m_mappedNodes[0]);
  m_paer->annotate(xns);

  appendFields(m);

  return nmapfield;
}

void SurfInterpolator::hmap(DispInterpolator::MapMatrix &H)
{
  assert(m_pstr);
  assert(m_paer);

  if (m_mappedNodes.empty())
    collectWallNodes();
  const int nwall = m_mappedNodes.size();

  // nwall for first and second loop together
  Logger::nextStage(2*nwall);

  // determine sparsity pattern first
  DVector<float> coef(nwall*3);
  DVector<uint> nds(nwall*3);
  {
    ConnectMap spty;
    spty.allocate(nwall, 3);
    BEGIN_PARLOOP_CHUNK(0, nwall, 128)
        for (int i=a; i<b; ++i) {
      const uint iwn = m_mappedNodes[i];
      m_tree.projection( m_paer->node(iwn), &nds[3*i], &coef[3*i] );
      spty.set(i, 3, &nds[3*i]);
      Logger::increment();
    }
    END_PARLOOP_CHUNK
        spty.sort();
    H.swap(spty);
  }

  // process aerodynamic nodes in parallel
  BEGIN_PARLOOP_CHUNK(0, nwall, 128)
      for (int i=a; i<b; ++i) {
    Mtx33f hnodal[3];

    // evaluate projection
    const uint iwn = m_mappedNodes[i];
    evalMap(iwn, &nds[3*i], &coef[3*i], hnodal);

    // insert into mapping matrix
    for (int k=0; k<3; ++k) {
      uint lix = H.lindex(i, nds[3*i+k]);
      assert(lix != NotFound);
      float & dst = H.value(lix, 0);
      memcpy(&dst, hnodal[k].pointer(), 9*sizeof(float));
    }
    Logger::increment();
  }
  END_PARLOOP_CHUNK

      //  // optional postprocessing by Laplacian smoothing
      //  if (m_smoothing > 0) {

      //    ConnectMap v2v;
      //    DispInterpolator::mapAerTopology(m_mappedNodes, v2v);

      //    if (m_pstr->v2eMap().size() != m_pstr->nnodes())
      //      m_pstr->fixate();

      //    Indices rnodes;
      //    if (m_maxNrmDev < PI)
      //      riskyNodes(v2v, rnodes, m_maxNrmDev);
      //    jumpNodes(rnodes);
      //    topoNeighbors(v2v, rnodes);

      //    clog << rnodes.size() << " nodes to smooth." << endl;

      //#ifndef NDEBUG
      //    uint ibc = appendNodeSet(rnodes);
      //    m_paer->boco(ibc).rename("JumpElements");
      //#endif

      //    // apply smoothing to mapping matrix
      //    smoothMap(m_smoothing, m_smOmega, rnodes, v2v, H);
      //  }

      // enforce sliding constraints
      if (not m_snset.empty())
      pinSlidingNodes(H);
}

uint SurfInterpolator::map(const DispInterpolator::MapMatrix &H,
                           DMatrix<float> &m)
{
  uint nfield = DispInterpolator::map(H, m);
  if (nfield == 0)
    return 0;

  // connectivity of mapped vertices
  ConnectMap v2v;

  // optional postprocessing by smoothing
  if (m_smoothSelective != 0) {

//    clk.start();
//    DispInterpolator::mapAerTopology(m_mappedNodes, v2v);
//    if (m_pstr->v2eMap().size() != m_pstr->nnodes())
//      m_pstr->fixate();

//    Indices rnodes;
//    if (m_maxNrmDev < PI)
//      riskyNodes(v2v, rnodes, m_maxNrmDev);
//    jumpNodes(rnodes);
//    topoNeighbors(v2v, rnodes);

//    log("[t] Discontinuity candidate identification: ", clk.stop());

//    // insert nodes classified as concave
//    if (m_concavityLimit > 0.0) {
//      const uint npre = rnodes.size();
//      collectConcaveNodes(v2v, feet, rnodes);
//      sort_unique(rnodes);
//      log("[i] Concavity criterion nodes: ", rnodes.size() - npre);
//    }
//    log("[i] Nodes to smooth:", rnodes.size());

//    //#ifndef NDEBUG
//    // DispInterpolator ignores this boundary name by default
//    uint ibc = m_paer->findBoco("JumpElements");
//    if (ibc != NotFound)
//      m_paer->eraseBoco(ibc);
//    ibc = appendNodeSet(rnodes);
//    m_paer->boco(ibc).rename("JumpElements");
//    //#endif

//    clk.start();
//    if (m_smoothSelective > 0)
//      smoothDisplacements(rnodes, v2v, m, m_smoothSelective, m_smOmega);
//    else
//      diffuseDisplacements(v2v, rnodes, m);
//    log("[t] Selective smoothing application: ", clk.stop());
  }

  // optional postprocessing by global smoothing
  if (m_smoothGlobal > 0) {
    size_t nsm = m_mappedNodes.size();
    Indices all(nsm);
    std::iota(all.begin(), all.end(), 0);
    smoothDisplacements(all, v2v, m, m_smoothGlobal, m_smOmega);
  }

  // enforce sliding constraints
  if (not m_snset.empty())
    pinSlidingNodes(m);

  return nfield;
}

FFANodePtr SurfInterpolator::mapToFFA(const DispInterpolator::MapMatrix &H) const
{
  FFANodePtr root = DispInterpolator::mapToFFA(H);

  // add additional data if smoothing is activated
  if (m_smoothSelective != 0) {

    if (m_pstr->v2eMap().size() != m_pstr->nnodes())
      m_pstr->fixate();

    ConnectMap v2v;
    DispInterpolator::mapAerTopology(m_mappedNodes, v2v);

    Indices rnodes;
    jumpNodes(rnodes);
    topoNeighbors(v2v, rnodes);

    FFANodePtr smp = FFANode::create( "displ_smoothing" );
    {
      FFANodePtr rnp = FFANode::create( "jump_map_nodes" );
      rnp->copy( FFAInt4, rnodes.size(), 1, &rnodes[0] );
      smp->append(rnp);
    }

    if (m_smoothSelective > 0) {
      smp->append("smoothing_iterations", m_smoothSelective);
      smp->append("smoothing_relaxation", m_smOmega);
    } else if (not rnodes.empty()) {
      Indices rim;
      smoothedRegionRim(v2v, rnodes, rim);

      FFANodePtr rmp = FFANode::create( "rim_map_nodes" );
      rmp->copy( FFAInt4, rim.size(), 1, &rim[0] );
      smp->append(rmp);

      CsrMatrixD Dff, Dfc;
      log("Assembling surface diffusion operator...");
      smoothingOperator(rnodes, rim, Dff, Dfc);

      FFANodePtr pdff = Dff.toFFA();
      pdff->rename("diffusion_lhs");
      smp->append(pdff);

      FFANodePtr pdfc = Dfc.toFFA();
      pdfc->rename("diffusion_rhs");
      smp->append(pdfc);
    }

    root->append(smp);
  }

  return root;
}

bool SurfInterpolator::mapFromFFA(const FFANodePtr &root,
                                  DispInterpolator::MapMatrix &H)
{
  bool hbasic = DispInterpolator::mapFromFFA(root, H);
  if (not hbasic)
    return hbasic;

  // retrieve smoothing settings etc
  uint itr = root->findChild("displ_smoothing");
  if (itr != NotFound) {
    FFANodePtr smp = root->child(itr);
    int itmp;
    double dtmp;
    if (smp->retrieve("smoothing_iterations", itmp)) {
      m_smoothSelective = itmp;
      if (smp->retrieve("smoothing_relaxation", dtmp))
        m_smOmega = dtmp;
    } else { // not simple iterative smoothing

      // hmmm... where to put sparse matrix operators?

    }
  }

  return true;
}

void SurfInterpolator::writeProjection(const string &fname) const
{
  m_tree.dump(fname);
}

void SurfInterpolator::footPoints(const Indices &nodeSet,
                                  PointList<3> &feet) const
{
  const int np = nodeSet.size();
  feet.resize(np);

#pragma omp parallel for schedule(static,1024)
  for (int i=0; i<np; ++i) {
    float coef[3];
    uint nds[3];
    const uint iwn = nodeSet[i];
    m_tree.projection( m_paer->node(iwn), nds, coef );
    for (int k=0; k<3; ++k)
      feet[i] += Real(coef[k]) * m_pstr->node( nds[k] );
  }
}

void SurfInterpolator::collectConcaveNodes(const ConnectMap &v2v,
                                           const PointList<3> &feet,
                                           Indices &cnodes) const
{
  const size_t n = m_mappedNodes.size();
  assert(feet.size() == n);

  Mutex guard;
  for (size_t i=0; i<n; ++i) {
    Real viol(0);
    const Vct3 & pti( m_paer->node(m_mappedNodes[i]) );
    ConnectMap::const_iterator itr, last = v2v.end(i);
    for (itr = v2v.begin(i); itr != last; ++itr) {
      Real fd = sq(feet[i] - feet[*itr]);
      const uint opv = m_mappedNodes[*itr];
      Real nd = sq(pti - m_paer->node(opv));
      viol = std::max(viol, fd - nd*m_concavityLimit);
    }
    if (viol > 0) {
      guard.lock();
      cnodes.push_back(i);
      guard.unlock();
    }
  }
}

void SurfInterpolator::drawFootLines()
{
  // draw one out of 8 lines
  int nmn = m_mappedNodes.size();
  int nline = nmn / 8;
  Indices samples(nline);
  for (int i=0; i<nline; ++i)
    samples[i] = m_mappedNodes[ std::rand() % nmn ];

  PointList<3> feet;
  footPoints(samples, feet);
  Indices lines(2*nline);
  for (int i=0; i<nline; ++i) {
    lines[2*i+0] = samples[i];
    lines[2*i+1] = m_paer->appendNode( feet[i] );
  }
  uint isec = m_paer->appendSection(Mx::Line2, lines);
  m_paer->section(isec).rename("SampleFeetLines");
}

void SurfInterpolator::addDebugFields()
{
  const int nmn = m_mappedNodes.size();
  PointList<3> feet;
  footPoints(m_mappedNodes, feet);

  Vector dst( m_paer->nnodes() );
  for (int i=0; i<nmn; ++i) {
    const uint iwn = m_mappedNodes[i];
    dst[iwn] = norm( feet[i] - m_paer->node(iwn) );
  }
  m_paer->appendField("ProjectionDistance", dst);
}

void SurfInterpolator::jumpNodes(Indices &rnodes) const
{
  Wallclock clk;
  clk.start();

  // determine connected components of the structural mesh
  // it is important to NOT cross element class boundaries
  // because RBAR, RBE2 elements will be mapped to line elements
  // which would create connections across, say, aileron and wing
  Indices scmp;
  uint nc = m_pstr->connectedComponents(scmp, false);
  log("[t] Identified ", nc, " disjoint structural components:",clk.stop());
  size_t nrpre = rnodes.size();

  // determine the structural component onto which each mapped
  // aerodynamic node is projected
  intptr_t nn = m_mappedNodes.size();
  Indices nodeComponent(nn, NotFound);

  clk.start();

#pragma omp parallel for schedule(static, 256)
  for (intptr_t i=0; i<nn; ++i) {
    uint itri = m_tree.nearestTriangle( m_paer->node(m_mappedNodes[i]) );
    uint gix = m_tree.globalElement(itri);
    assert(gix != NotFound);
    nodeComponent[i] = scmp[gix];
  }

  log("[t] Assigned components: ", clk.stop()); clk.start();

  Indices mappedElements;
  DispInterpolator::findMappedElements(mappedElements);

  log("[t] Mapped elements: ", clk.stop()); clk.start();

  // identify aerodynamic elements which have nodes that end up projected
  // to different structural components
  const intptr_t me = mappedElements.size();
  int njel(0);

#pragma omp parallel
  {
    uint idx[32];
    Indices pnodes;

#pragma omp for schedule(static, 256)
    for (intptr_t i=0; i<me; ++i) {
      uint nv, isec;
      const uint *v = m_paer->globalElement(mappedElements[i], nv, isec);
      assert(v != 0);
      uint cref = NotFound;
      for (uint k=0; k<nv; ++k) {
        idx[k] = sorted_index(m_mappedNodes, v[k]);
        if (cref == NotFound and idx[k] != NotFound) {
          cref = nodeComponent[idx[k]];
        }
      }
      if (cref != NotFound) {
        for (uint i=0; i<nv; ++i) {
          if (idx[i] != NotFound and nodeComponent[idx[i]] != cref) {
            pnodes.insert(pnodes.end(), idx, idx+nv);
            atomic_add(njel, 1);
            break;
          }
        }
      }
    }
    sort_unique(pnodes);

#pragma omp critical
    rnodes.insert(rnodes.end(), pnodes.begin(), pnodes.end());
  }

  // find duplicate nodes, which are topologically different but geometrically
  // very close, in the structural mesh
  Indices unds;
  const size_t nsec = m_pstr->nsections();
  size_t tail(0);
  for (size_t isec=0; isec<nsec; ++isec) {
    const MxMeshSection &sec( m_pstr->section(isec) );
    if (not (sec.surfaceElements()))
      continue;
    Indices tmp;
    sec.usedNodes(tmp);
    if (tmp.empty())
      continue;
    unds.insert(unds.end(), tmp.begin(), tmp.end());
    if (tail != 0)
      std::inplace_merge(unds.begin(), unds.begin()+tail, unds.end());
    unds.erase(std::unique(unds.begin(), unds.end()), unds.end());
    tail = unds.size();
  }
  auto cmp = [&](uint a, uint b) {
    return sq(m_pstr->node(a)) < sq(m_pstr->node(b));
  };
  parallel::sort( unds.begin(), unds.end(), cmp);

  Indices dupnodes;
  const Real sqdlimit = sq(1e-6);
  const size_t np = unds.size();
  size_t k, j = 0;
  while (j < np) {
    const Vct3 &pj = m_pstr->node(unds[j]);
    for (k=j+1; k<np; ++k) {
      const Vct3 &pk = m_pstr->node(unds[k]);
      if ( sq(pk-pj) > sqdlimit  )
        break;
      else
        dupnodes.push_back( unds[k] );
    }
    j = k;
  }
  sort_unique(dupnodes);
  log(dupnodes.size(),"coincident structural nodes.");

  // aerodynamic nodes which are projected onto triangles that contain any of
  // the duplicate nodes are marked as potentially discontinuous as well
#pragma omp parallel
  {
    // thread private copy of nodes
    Indices pnodes;

#pragma omp for schedule(static, 256)
    for (intptr_t i=0; i<nn; ++i) {
      uint itri = m_tree.nearestTriangle( m_paer->node(m_mappedNodes[i]) );
      const uint *v = m_tree.vertices(itri);
      for (int k=0; k<3; ++k) {
        if ( not binary_search(dupnodes.begin(), dupnodes.end(), v[k]) )
          continue;
        else
          pnodes.push_back(i);
      }
    }
    sort_unique(pnodes);

#pragma omp critical
    rnodes.insert(rnodes.end(), pnodes.begin(), pnodes.end());
  }

  if (rnodes.empty())
    return;

  sort_unique(rnodes);
  while (rnodes.back() == NotFound)
    rnodes.pop_back();
  log(njel, "jump elements,", rnodes.size() - nrpre, "nodes tagged.");

  // include additional aerodynamic nodes in the smoothing operation when
  // user specified a non-zero smoothing radius
  if (m_smoothedRadius > 0.0) {
    Indices nbnodes;
    DispInterpolator::nearbyNodes(m_smoothedRadius, rnodes, nbnodes);
    if (not nbnodes.empty()) {
      size_t mid = rnodes.size();
      rnodes.insert(rnodes.end(), nbnodes.begin(), nbnodes.end());
      std::inplace_merge( rnodes.begin(), rnodes.begin() + mid, rnodes.end() );
      sort_unique(rnodes);
      log( rnodes.size() - mid, "additional nodes to smooth in radius",
           m_smoothedRadius);
    }
  }
}

void SurfInterpolator::riskyNodes(const ConnectMap &v2v,
                                  Indices &rn, Real maxphi) const
{
  PointList<3> feet;
  footPoints(m_mappedNodes, feet);
  const size_t np = m_mappedNodes.size();

#ifndef NDEBUG
  // debugging : write normal deviation and distance fields
  {
    const size_t nn = m_paer->nnodes();
    Vector ndev(nn), pdst(nn);
    for (size_t i=0; i<np; ++i) {
      const size_t mni = m_mappedNodes[i];
      Vct3 ri = feet[i] - m_paer->node( mni );
      pdst[mni] = std::max( pdst[mni], norm(ri) );
      ConnectMap::const_iterator itr, last = v2v.end(i);
      for (itr = v2v.begin(i); itr != last; ++itr) {
        Vct3 rj = feet[*itr] - m_paer->node( m_mappedNodes[*itr] );
        Real phi = acos(fabs(cosarg(ri,rj)));
        ndev[mni] = std::max(ndev[mni], deg(phi));
      }
    }
    m_paer->appendField( "MapNormalDeviation", ndev );
    m_paer->appendField( "MapProjectionDistance", pdst );
  }
#endif

  rn.clear();
  rn.reserve( m_mappedNodes.size() / 2 );
  const Real mincphi = std::cos(maxphi);
  const Real sqmd = sq( m_maxDistance );
  for (size_t i=0; i<np; ++i) {
    Vct3 ri = feet[i] - m_paer->node( m_mappedNodes[i] );
    if (sq(ri) < sqmd) {
      ConnectMap::const_iterator itr, last = v2v.end(i);
      for (itr = v2v.begin(i); itr != last; ++itr) {
        Vct3 rj = feet[*itr] - m_paer->node( m_mappedNodes[*itr] );
        if (fabs(cosarg(ri,rj)) < mincphi) {
          rn.push_back(i);
          rn.push_back(*itr);
        }
      }
    } else {
      // distance exceeds maximum
      rn.push_back(i);
    }
  }
  sort_unique(rn);

  log(rn.size(), " nodes exceed normal/distance criterion.");
}

void SurfInterpolator::topoNeighbors(const ConnectMap &v2v, Indices &rn) const
{
  if (m_smoothedRing != 0)
    log("Appending ring-",m_smoothedRing,"neighborhood.");

  for (int i=0; i<m_smoothedRing; ++i) {
    Indices tmp;
    for (size_t i=0; i<rn.size(); ++i) {
      const uint idx = rn[i]; // sorted_index(m_mappedNodes, rn[i]);
      assert(idx != NotFound);
      ConnectMap::const_iterator itr, last = v2v.end(idx);
      for (itr = v2v.begin(idx); itr != last; ++itr) {
        if (*itr != idx)
          tmp.push_back(*itr);
      }
    }
    std::sort(tmp.begin(), tmp.end());
    tmp.erase( std::unique(tmp.begin(), tmp.end()), tmp.end() );

    size_t mid = rn.size();
    rn.insert(rn.end(), tmp.begin(), tmp.end());
    std::inplace_merge(rn.begin(), rn.begin()+mid, rn.end());
    sort_unique(rn);
  }
}

void SurfInterpolator::smoothDisplacements(const Indices &rn,
                                           const ConnectMap &v2v,
                                           DMatrix<float> &m,
                                           int niter, float omega) const
{
  // work space
  DMatrix<float> w(m);

  const int ndisp = m.nrows();
  const int nsm = rn.size();
  for (int iter=0; iter<niter; ++iter) {
    for (int i=0; i<nsm; ++i) {
      const uint rni = rn[i];
      for (int k=0; k<ndisp; ++k)
        w(k,rni) = (1.0 - omega)*m(k,rni);
      ConnectMap::const_iterator itr, last = v2v.end(rni);
      const int nnb = v2v.size(rni);
      for (itr = v2v.begin(rni); itr != last; ++itr) {
        const int j = *itr;
        for (int k=0; k<ndisp; ++k)
          w(k,rni) += omega*m(k,j)/nnb;
      }
    }
    m.swap(w);
  }
}

void SurfInterpolator::diffuseDisplacements(const ConnectMap &v2v,
                                            const Indices &rnodes,
                                            DMatrix<float> &m)
{
  Wallclock clk;
  if (rnodes.empty())
    return;

  Indices rim;
  smoothedRegionRim(v2v, rnodes, rim);

  clk.start();
  CsrMatrixD Dff, Dfc;

  smoothingOperator(rnodes, rim, Dff, Dfc);
  // averagingOperator(rnodes, rim, Dff, Dfc);
  log("[t] Assembling surface diffusion operator: ", clk.stop());
  clk.start();

  // construct RHS : r = - Dfc * xc
  const size_t nf = rnodes.size();
  const size_t nc = rim.size();
  const size_t nrhs = m.nrows(); // displacement components stored in rows
  Matrix rhs(nf, nrhs), x(nf, nrhs);

  {
    Matrix xc(nc, nrhs);
    for (size_t i=0; i<nc; ++i)
      for (size_t k=0; k<nrhs; ++k)
        xc(i,k) = - m(k, rim[i]);
    Dfc.muladd(xc, rhs);
  }
  log("[t] Constructing right-hand side:", clk.stop());
  clk.start();

  // solve for internal dofs
  // Dff * xf + Dfc * xc = 0

  log("[i] Solving diffusion problem...");
  DSparseSolverPtr dss;
  // dss = DSparseSolver::create(SpMatrixFlag::RealPositiveDefinite);
  dss = DSparseSolver::create(SpMatrixFlag::RealUnsymmetric);
  if (dss != nullptr) {
    log("[i] Direct sparse solver: ", dss->name());
    dss->factor(&Dff);
    dss->solve(rhs, x);
  } else {
    throw Error("SurfInterpolator::diffuseDisplacements() requires direct"
                " sparse solver support: None found on this platform.");
  }

  // insert solution into m
  for (size_t i=0; i<nf; ++i) {
    for (size_t k=0; k<nrhs; ++k)
      m(k, rnodes[i]) = x(i, k);
  }
}

void SurfInterpolator::diffusionStencil(const ConnectMap &v2v,
                                        const Indices &rnodes,
                                        ConnectMap &spty) const
{
  spty.clear();

  Indices rimset;
  smoothedRegionRim(v2v, rnodes, rimset);
  log(rimset.size(), "rim nodes.");

  Indices srow;
  const Real sqlmax = sq( 3.0*m_smoothedRadius );
  const size_t nrn = rnodes.size();
  size_t nnb(0);
  for (size_t i=0; i<nrn; ++i) {
    bfsWalk(rnodes[i], sqlmax, v2v, rimset, srow);

    // append compressed row
    spty.appendRow(srow.begin(), srow.end());
    nnb += srow.size();
  }

  log("Average stencil width: ", Real(nnb) / nrn);
}

void SurfInterpolator::smoothingOperator(const Indices &rnodes,
                                         const Indices &rim,
                                         CsrMatrixD &Dff,
                                         CsrMatrixD &Dfc) const
{
  // collect elements which touch any of the internal nodes
  const ConnectMap & v2e( m_paer->v2eMap() );
  assert(v2e.size() == m_paer->nnodes());
  assert(std::is_sorted(m_mappedNodes.begin(), m_mappedNodes.end()));
  const size_t nf = rnodes.size();
  const size_t nc = rim.size();

  // early exit if there are no nodes to smooth
  if (nf == 0 or nc == 0)
    return;

  Indices elix;
  elix.reserve(4*nf);
  for (size_t i=0; i<nf; ++i) {
    const uint gni = m_mappedNodes[rnodes[i]];
    size_t nnb = 0;
    ConnectMap::const_iterator itr, last = v2e.end(gni);
    for (itr = v2e.begin(gni); itr != last; ++itr) {
      uint isec = m_paer->findSection(*itr);
      assert(isec != NotFound);
      const MxMeshSection &sec( m_paer->section(isec) );
      if (sec.elementType() != Mx::Tri3)
        continue;

      // consider only triangles which are entirely within the
      // mapped domain for the dissipation problem
      const uint *v = sec.globalElement(*itr);
      bool ismapped = true;
      for (int k=0; k<3; ++k)
        ismapped &= binary_search(m_mappedNodes.begin(),
                                  m_mappedNodes.end(), v[k]);
      if (ismapped) {
        elix.push_back(*itr);
        ++nnb;
      }
    }

    // cannot work: node to smooth has no incoming elements
    if (hint_unlikely(nnb == 0))
      throw Error("Ill-posed smoothing problem: Node "+str(gni)+
                  " has no movable neighbor elements.");
  }
  sort_unique(elix);
  if (m_useGalerkin)
    log(elix.size(), "Galerkin elements.");
  else
    log(elix.size(), "diffusion elements.");

  // extract mapped triangle vertex indices and element matrices
  const intptr_t ne = elix.size();
  Indices itri(3*ne, NotFound);
  std::vector<Mtx33> vde(ne);

#pragma omp parallel for schedule(dynamic, 128)
  for (intptr_t i=0; i<ne; ++i) {
    uint nv, isec;
    const uint *vi = m_paer->globalElement(elix[i], nv, isec);

    Vct3 ptri[3];
    for (int k=0; k<3; ++k)
      ptri[k] = m_paer->node(vi[k]);

    if (m_useGalerkin)
      massMatrix(ptri, vde[i]);
    else
      diffusionMatrix(ptri, vde[i]);

    // vi contains indices into the global aerodynamic mesh
    for (int k=0; k<3; ++k)
      itri[3*i + k] = sorted_index(m_mappedNodes, vi[k]);
  }

  // catch impossible problem where diffusion elements reference nodes
  // outside the mapped domain (not possible)
  if (binary_search(itri.begin(), itri.end(), NotFound))
    throw Error("Incompatible boundary condition for diffusion problem: "
                "Gap displacement smoothing insufficiently constrained.");

  // row- and column mapping
  const size_t nmn = m_mappedNodes.size();
  Indices fmap(nmn, NotFound), cmap(nmn, NotFound);
  for (size_t i=0; i<nf; ++i)
    fmap[rnodes[i]] = i;
  for (size_t i=0; i<nc; ++i)
    cmap[rim[i]] = i;

  // construct sparsity patterns
  {
    ConnectMap fspty, cspty;
    fspty.beginCount(nf);
    cspty.beginCount(nf);
    for (intptr_t i=0; i<ne; ++i) {
      const uint *vi = &itri[3*i];
      fspty.incCountElement<3>(fmap, vi);
      cspty.incCountElement<3>(fmap, vi);
    }
    fspty.endCount();
    cspty.endCount();
    for (intptr_t i=0; i<ne; ++i) {
      const uint *vi = &itri[3*i];
      if (m_buildSymmetric)
        fspty.appendElement<3, ConnectMap::UpperTriangular>(fmap, fmap, vi);
      else
        fspty.appendElement<3, ConnectMap::Unsymmetric>(fmap, fmap, vi);
      cspty.appendElement<3, ConnectMap::Unsymmetric>(fmap, cmap, vi);
    }
    fspty.compress();
    cspty.compress();
    Dff.swap(fspty);
    Dfc.swap(cspty);
  }

  assert(Dff.nrows() == Dff.ncols());
  assert(Dff.nrows() == Dfc.nrows());

  // check for structurally well-posed operator
  size_t nzsum = 0;
  const size_t nr = Dff.nrows();
  for (size_t i=0; i<nr; ++i) {
    nzsum += (Dff.sparsity().size(i) == 0);
    if (Dff.sparsity().size(i) == 0)
      cout << i << " rn " << rnodes[i] << " glob " << m_mappedNodes[rnodes[i]] << endl;
  }
  if (nzsum != 0)
    throw Error("Ill-posed smoothing problem: "+str(nzsum)+" empty rows.");

  // assemble matrices
#pragma omp parallel for schedule(static, 512)
  for (intptr_t i=0; i<ne; ++i) {
    const uint *vi = &itri[3*i];
    Dff.assemble<3>(fmap, fmap, vi, vde[i]);
    Dfc.assemble<3>(fmap, cmap, vi, vde[i]);
  }

  if (m_useGalerkin) {
    const intptr_t nrow = Dff.nrows();
#pragma omp parallel for schedule(static, 512)
    for (intptr_t i=0; i<nrow; ++i) {

      // normalize to unit row sums
      Real irsum = 1.0 / (Dff.rowSum(i) + Dfc.rowSum(i));
      Dff.scaleRow(i, irsum);
      Dfc.scaleRow(i, irsum);

      // substract 1 from diagonal after scaling
      uint lix = Dff.lindex(i,i);
      if (lix != NotFound)
        Dff[lix] -= 1.0;
    }
  }

#ifndef NDEBUG
  // check for numerically well-posed operator
  const DVector<Real> &v( Dff.nzarray() );
  for (size_t i=0; i<nr; ++i) {
    size_t off = Dff.offset(i);
    size_t n = Dff.sparsity().size(i);
    float rsum = 0.0f;
    for (size_t j=0; j<n; ++j)
      rsum += std::fabs( v[off+j] );
    nzsum += (rsum == 0.0f);
  }
  if (nzsum != 0)
    throw Error("Ill-posed smoothing problem: "+str(nzsum)+" zero rows.");
#endif
}

void SurfInterpolator::diffusionMatrix(const Vct3 tri[], Mtx33 &De)
{
  // surface diffusion operator:
  // compute inverse element Jacobian
  Mtx33 tmp, ijac = Mtx33::identity();
  const Vct3 & p0( tri[0] );
  const Vct3 & p1( tri[1] );
  const Vct3 & p2( tri[2] );
  Vct3 nrm = cross(p1-p0, p2-p0);
  for (int k=0; k<3; ++k) {
    tmp(k,0) = p1[k] - p0[k];
    tmp(k,1) = p2[k] - p0[k];
    tmp(k,2) = nrm[k];
  }

  Real tau[3];
  qr<3,3>(tmp.pointer(), tau);
  for (int k=0; k<3; ++k)
    qrsolve<3,3>(tmp.pointer(), tau, ijac.colpointer(k));

  // obtain shape function derivatives, which are constant
  // across the element
  const int M(3);
  Real Nv[4*M];
  for (int k=0; k<3; ++k) {
    Real *Nk = &Nv[3*(k+1)];
    Nk[0] = -ijac(0,k) - ijac(1,k);  // 1 - xi - eta
    Nk[1] = ijac(0,k);               // xi
    Nk[2] = ijac(1,k);               // eta
  }

  // alias for clarity
  const Real *Nx = &Nv[1*M];
  const Real *Ny = &Nv[2*M];
  const Real *Nz = &Nv[3*M];
  Real detJ = norm(nrm);
  for (int j=0; j<M; ++j)
    for (int i=0; i<M; ++i)
        De(i,j) = detJ*(Nx[i]*Nx[j] + Ny[i]*Ny[j] + Nz[i]*Nz[j]);
}

void SurfInterpolator::massMatrix(const Vct3 tri[], Mtx33 &De)
{
  // mass-based averaging
  const Vct3 & p0( tri[0] );
  const Vct3 & p1( tri[1] );
  const Vct3 & p2( tri[2] );
  Real detJ = norm( cross(p1-p0, p2-p0) );

  static const Real w(1./6.);
  static const Real x[] = {1./6., 2./3., 1./6.};
  static const Real y[] = {1./6., 1./6., 2./3.};

  const int M(3);
  Real Nv[M];
  De = 0.0;
  for (int k=0; k<3; ++k) {
    Nv[0] = 1.0 - x[k] - y[k];
    Nv[1] = x[k];
    Nv[2] = y[k];
    for (int j=0; j<M; ++j)
      for (int i=0; i<M; ++i)
        De(i,j) += w*detJ*Nv[i]*Nv[j];
  }
}

void SurfInterpolator::averagingOperator(const Indices &rnodes,
                                         const Indices &rim,
                                         CsrMatrixD &Dff,
                                         CsrMatrixD &Dfc) const
{
  Wallclock clk;
  clk.start();

  // collect elements which touch any of the internal nodes
  const ConnectMap & v2e( m_paer->v2eMap() );
  assert(v2e.size() == m_paer->nnodes());
  assert(std::is_sorted(m_mappedNodes.begin(), m_mappedNodes.end()));
  const size_t nf = rnodes.size();
  const size_t nc = rim.size();

  // early exit if there are no nodes to smooth
  if (nf == 0 or nc == 0)
    return;

  // construct connectivity
  std::vector<uint64_t> ffpack, fcpack;

#pragma omp parallel
  {
    // thread-private copies
    std::vector<uint64_t> pfpack, pcpack;
    size_t ftail(0), ctail(0);

#pragma omp for schedule(static, 512)
    for (intptr_t i=0; i<intptr_t(nf); ++i) {

      pfpack.push_back( ConnectMap::packpair(i,i) );
      const uint gni = m_mappedNodes[rnodes[i]];
      ConnectMap::const_iterator itr, last = v2e.end(gni);
      for (itr = v2e.begin(gni); itr != last; ++itr) {
        uint nv, isec;
        const uint *v = m_paer->globalElement(*itr, nv, isec);
        for (uint j=0; j<nv; ++j) {
          uint mvj = sorted_index(m_mappedNodes, v[j]);
          if ( mvj == NotFound )
            continue;
          uint fcol = sorted_index(rnodes, mvj);
          if (fcol != NotFound) {
            pfpack.push_back( ConnectMap::packpair(i, fcol) );
          } else {
            uint ccol = sorted_index(rim, mvj);
            if (ccol != NotFound)
              pcpack.push_back( ConnectMap::packpair(i, ccol) );
          }
        }
      }

      // compress pack array every now and then to reduce memory pressure
      if (pfpack.size() - ftail > 1024*1024)
        ftail = unique_merge_tail(ftail, pfpack);
      if (pcpack.size() - ctail > 1024*1024)
        ctail = unique_merge_tail(ctail, pcpack);
    }

#pragma omp critical
    {
      ffpack.insert(ffpack.end(), pfpack.begin(), pfpack.end());
      fcpack.insert(fcpack.end(), pcpack.begin(), pcpack.end());
    }
  }

  // weed out global duplicates
  parallel::sort(ffpack.begin(), ffpack.end());
  ffpack.erase(std::unique(ffpack.begin(), ffpack.end()), ffpack.end());
  parallel::sort(fcpack.begin(), fcpack.end());
  fcpack.erase(std::unique(fcpack.begin(), fcpack.end()), fcpack.end());

  {
    ConnectMap ffmap;
    ffmap.assign(nf, ffpack.size(), &ffpack[0]);
    Dff.swap(ffmap, nf);
  }

  {
    ConnectMap fcmap;
    fcmap.assign(nf, fcpack.size(), &fcpack[0]);
    Dfc.swap(fcmap, nc);
  }

  log("[i] Dff rows: ", nf);
  log("[i] Dff nonzero entries: ", Dff.nonzero());
  log("[i] Dfc nonzero entries: ", Dfc.nonzero());

  log("[t] Operator sparsity evaluation: ",clk.stop());
  clk.start();

  // check for structurally well-posed operator
  size_t nzsum = 0;
  const size_t nr = Dff.nrows();
  for (size_t i=0; i<nr; ++i) {
    nzsum += (Dff.sparsity().size(i) == 0);
    if (Dff.sparsity().size(i) == 0)
      cout << i << " rn " << rnodes[i] << " glob "
           << m_mappedNodes[rnodes[i]] << endl;
  }
  if (nzsum != 0)
    throw Error("Ill-posed smoothing problem: "+str(nzsum)+" empty rows.");

#pragma omp parallel for schedule(dynamic, 256)
  for (intptr_t i=0; i<intptr_t(nf); ++i)
    linearSmoothingRow(i, rnodes, rim, Dff, Dfc);

  log("[t] Operator assembly:", clk.stop());

#ifndef NDEBUG
  // check for numerically well-posed operator
  const DVector<Real> &v( Dff.nzarray() );
  for (size_t i=0; i<nr; ++i) {
    size_t off = Dff.offset(i);
    size_t n = Dff.sparsity().size(i);
    float rsum = 0.0f;
    for (size_t j=0; j<n; ++j)
      rsum += std::fabs( v[off+j] );
    nzsum += (rsum == 0.0f);
  }
  if (nzsum != 0)
    throw Error("Ill-posed smoothing problem: "+str(nzsum)+" zero rows.");
#endif
}

void SurfInterpolator::linearSmoothingRow(size_t row,
                                          const Indices &fnodes,
                                          const Indices &cnodes,
                                          CsrMatrixD &Dff, CsrMatrixD &Dfc) const
{
  const uint gni = m_mappedNodes[fnodes[row]];
  const Vct3 & pti = m_paer->node( gni );

  const ConnectMap & sff( Dff.sparsity() );
  const ConnectMap & sfc( Dfc.sparsity() );

  const uint nfr = sff.size(row);
  const uint ncr = sfc.size(row);
  const uint nc = nfr + ncr;
  assert(nc > 0);

  bool usePlane = (nc >= 3);

  if (usePlane) {

    // construct a local coordinate system - covariance h
    SMatrix<3,3> h;
    for (uint i=0; i<nfr; ++i) {
      Vct3 r = m_paer->node( m_mappedNodes[fnodes[i]] ) - pti;
      h += dyadic(r,r);
    }
    for (uint i=0; i<ncr; ++i) {
      Vct3 r = m_paer->node( m_mappedNodes[cnodes[i]] ) - pti;
      h += dyadic(r,r);
    }

    // compute principal directions, first eigenvalue is always the smallest
    // - pick the shortest principal axis as the normal
    // of the local tangent plane
    Vct3 eval, tpn;
    sym_eig3(h, eval);
    extract_eigenvector(h, eval[0], tpn);

    Vct3 uax;
    for (uint i=0; i<nfr; ++i) {
      uint ki = fnodes[i];
      if (ki != i) {
        uax = m_paer->node( m_mappedNodes[ki] ) - pti;
        break;
      }
    }

    if (sq(uax) != 0 and sq(tpn) != 0) {

      normalize(uax);
      Vct3 vax = cross(tpn, uax).normalized();

      Matrix B(nc,3), P(nc,nc);
      for (uint i=0; i<nfr; ++i) {
        Vct3 r = m_paer->node( m_mappedNodes[fnodes[i]] ) - pti;
        B(i,0) = 1.0;
        B(i,1) = dot(r, uax);
        B(i,2) = dot(r, vax);
      }
      for (uint i=0; i<ncr; ++i) {
        Vct3 r = m_paer->node( m_mappedNodes[cnodes[i]] ) - pti;
        B(nfr+i,0) = 1.0;
        B(nfr+i,1) = dot(r, uax);
        B(nfr+i,2) = dot(r, vax);
      }
      unity(P);

      int stat = lls_solve(B, P);
      if (stat == 0) {
        const uint foff = sff.offset(row);
        for (uint i=0; i<nfr; ++i)
          Dff[foff+i] = P(0,i);
        const uint coff = sfc.offset(row);
        for (uint i=0; i<ncr; ++i)
          Dfc[coff+i] = P(0,nfr+i);
      } else {
        usePlane = false;
      }

    } else {
      usePlane = false;
    }
  }

  if (not usePlane) {

    // not enough neighbor nodes to establish an approximant; use a plain
    // mean value across all neighbors instead (not so good)
    const Real frc = 1.0 / nc;
    const uint foff = sff.offset(row);
    for (uint j=0; j<nfr; ++j)
      Dff[foff + j] = frc;
    const uint coff = sfc.offset(row);
    for (uint j=0; j<ncr; ++j)
      Dfc[coff + j] = frc;

  }

  // switch sign of LHS for compatibility with diffusion operator
  const uint ljj = Dff.lindex(row, row);
  assert(ljj != NotFound);
  Dff[ljj] -= 1.0;
}

//void SurfInterpolator::evalLeastSquares(const Indices &itri,
//                                        const Indices &inodes,
//                                        const MapMatrix &H,
//                                        CsrMatrixD &A,
//                                        Vector &b) const
//{
//  const float *hptr = H.pointer();
//  const size_t ne = itri.size() / 3;
//  const size_t naf = m_strFields.size();
//  b.resize(ne);

//  for (size_t i=0; i<ne; ++i) {
//    Vct3 tri[3], dsp[3];
//    for (int k=0; k<3; ++k) {
//      tri[k] = m_paer->node( itri[3*i+k] );
//      // m_tree.projection( tri[k], &nds[3*k], coef );
//    }

//    // undeformed triangle normal
//    Vct3 fn = cross(tri[1]-tri[0], tri[2]-tri[0]);

//    // sum contributions from each field
//    for (size_t ifield=0; ifield<naf; ++ifield) {

//      const MxMeshField &field( m_pstr->field(m_strFields[ifield]) );

//      Mtx33 hkj;
//      Vct3 dkj;
//      for (int k=0; k<3; ++k) {
//        const uint krow = sorted_index(m_mappedNodes, itri[3*i+k]);
//        const uint ncol = H.sparsity().size(krow);
//        const uint *pcol = H.sparsity().first(krow);
//        const uint offs = H.sparsity().offset(krow);
//        for (uint j=0; j<ncol; ++j) {
//          const float *hp = hptr + 9*(offs + j);
//          std::copy(hp, hp+9, hkj.begin());
//          field.value(pcol[j], dkj);
//          dsp[k] += dkj;
//        }
//      }

//      // change in triangle normal for small deformations
//      Vct3 dn = cross(dsp[1]-dsp[0], tri[2]-tri[0])
//          + cross(tri[1]-tri[0], dsp[2]-dsp[0]);

//      Real db = dot(fn,dn) / sq(fn);
//      b[i] += sq(db);

//      // contributions to derivatives
//      // d/dH1 = 2*db * ddb/dH1
//      // ddb/dH1 = 1/sq(fn) * dot(fn, ddn/dH1)
//      // ddn/dH1 = cross( ddsp[1]/dH1 - ddsp[0]/dH1, tri[2]-tri[0] )
//      //         + cross(tri[1]-tri[0], ddsp[2]/dH1 - ddsp[0]/dH1);
//      // ddsp[i]/dH1 = sum_j H_ij
//    }
//  }
//}


