
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

#include "dispinterpolator.h"
#include <genua/ffanode.h>
#include <genua/forward.h>
#include <genua/mxmesh.h>
#include <genua/csrmatrix.h>
#include <genua/ndpointtree.h>
#include <genua/timing.h>
#include <genua/dbprint.h>
#include <deque>

using namespace std;

static void collect_sec_nodes(const MxMesh &msh, uint isec, Indices &nodes)
{
  Indices tmp;
  msh.section(isec).usedNodes(tmp);

  if (nodes.empty()) {
    nodes.swap(tmp);
  } else {
    Indices mrg;
    mrg.reserve(tmp.size() + nodes.size());
    std::merge(nodes.begin(), nodes.end(), tmp.begin(), tmp.end(),
               back_inserter(mrg));
    mrg.erase( std::unique(mrg.begin(), mrg.end()), mrg.end() );
    nodes.swap(mrg);
  }
}

static Indices collect_bc_nodes(const MxMesh &msh, uint ibc, Indices &nodes)
{
  Indices tmp;
  const MxMeshBoco &bc( msh.boco(ibc) );
  uint isec = msh.mappedSection(ibc);
  if (isec != NotFound) {
    msh.section(isec).usedNodes(tmp);
  } else {
    Indices elix;
    uint nv;
    bc.elements(elix);
    const int ne = elix.size();
    tmp.reserve( 3*ne );
    for (int i=0; i<ne; ++i) {
      const uint *v = msh.globalElement(elix[i], nv, isec);
      tmp.insert(tmp.end(), v, v+nv);
    }
    std::sort(tmp.begin(), tmp.end());
    tmp.erase( std::unique(tmp.begin(), tmp.end()), tmp.end() );
  }

  if (nodes.empty()) {
    nodes.swap(tmp);
  } else {
    Indices mrg;
    mrg.reserve(tmp.size() + nodes.size());
    std::merge(nodes.begin(), nodes.end(), tmp.begin(), tmp.end(),
               back_inserter(mrg));
    mrg.erase( std::unique(mrg.begin(), mrg.end()), mrg.end() );
    nodes.swap(mrg);
  }

  return tmp;
}

void DispInterpolator::collectWallNodes()
{
  for (uint j=0; j<m_paer->nbocos(); ++j) {
    const MxMeshBoco &bc( m_paer->boco(j) );
    Mx::BocoType bct = bc.bocoType();
    if ( bct == Mx::BcAdiabaticWall or
         bct == Mx::BcSlipWall or
         bct == Mx::BcWall )
    {
      m_movingBocos.push_back(j);
    }
  }
  collectWallBocos(m_movingBocos);
}

void DispInterpolator::collectWallBocos(const Indices &movingBc,
                                        const Indices &slidingBc,
                                        const Indices &rubberBc)
{
  m_mappedNodes.clear();
  m_snset.clear();

  m_movingBocos = movingBc;
  sort_unique(m_movingBocos);
  const int nmb = m_movingBocos.size();
  for (int i=0; i<nmb; ++i) {
    //    if (m_paer->boco(m_movingBocos[i]).name() == "JumpElements")
    //      continue;
    collect_bc_nodes(*m_paer, m_movingBocos[i], m_mappedNodes);
    log("Marked as moving boundary: ", m_paer->boco(m_movingBocos[i]).name());
  }

  m_slidingBocos = slidingBc;
  if (not m_slidingBocos.empty()) {
    sort_unique(m_slidingBocos);
    const int nsb = m_slidingBocos.size();
    Indices slidingNodes;
    for (int i=0; i<nsb; ++i) {
      m_snset.push_back( SlidingNodeSet() );
      SlidingNodeSet & sset( m_snset.back() );
      const MxMeshBoco & bc( m_paer->boco(m_slidingBocos[i]) );
      sset.nodes = collect_bc_nodes(*m_paer, m_slidingBocos[i], slidingNodes);
      sset.normal = slidingNormal( bc.firstElement() );
      sset.boundaryName = bc.name();

      log("Marked as sliding boundary: ",
          m_paer->boco(m_slidingBocos[i]).name());
    }

    mergeSlidingNodes(slidingNodes);
  }

  Indices rubberNodes;
  m_rubberBocos = rubberBc;
  if (not m_rubberBocos.empty()) {
    sort_unique(m_rubberBocos);
    const int nsb = m_rubberBocos.size();
    for (int i=0; i<nsb; ++i)
      collect_bc_nodes(*m_paer, m_rubberBocos[i], rubberNodes);
  }
  m_rubberNodes.clear();
  m_rubberNodes.reserve( rubberNodes.size() );
  std::set_difference(rubberNodes.begin(), rubberNodes.end(),
                      m_mappedNodes.begin(), m_mappedNodes.end(),
                      back_inserter(m_rubberNodes));

  m_fixedBocos.clear();
  for (uint i=0; i<m_paer->nbocos(); ++i) {
    const MxMeshBoco & bc( m_paer->boco(i) );
    if (binary_search(m_movingBocos.begin(), m_movingBocos.end(), i))
      continue;
    if (binary_search(m_slidingBocos.begin(), m_slidingBocos.end(), i))
      continue;
    if (binary_search(m_rubberBocos.begin(), m_rubberBocos.end(), i))
      continue;
    m_fixedBocos.push_back(i);
    log("Marked as fixed boco: ", bc.name());
  }
}

void DispInterpolator::collectWallSections(const Indices &movingSec,
                                           const Indices &slidingSec,
                                           const Indices &rubberSec)
{
  m_mappedNodes.clear();
  m_movingSections = movingSec;
  sort_unique(m_movingSections);
  const int nmb = m_movingSections.size();
  for (int i=0; i<nmb; ++i) {
    collect_sec_nodes(*m_paer, m_movingSections[i], m_mappedNodes);
    log("Marked as moving section: ",
        m_paer->section(m_movingSections[i]).name());
  }

  m_slidingSections = slidingSec;
  if (not m_slidingSections.empty()) {
    sort_unique(m_slidingSections);
    const int nsb = m_slidingSections.size();
    Indices slidingNodes;
    for (int i=0; i<nsb; ++i) {
      collect_sec_nodes(*m_paer, m_slidingSections[i], slidingNodes);
      log("Marked as sliding section: ",
          m_paer->section(m_slidingSections[i]).name());
    }
    mergeSlidingNodes(slidingNodes);
  }

  Indices rubberNodes;
  m_rubberSections = rubberSec;
  if (not m_rubberSections.empty()) {
    sort_unique(m_rubberSections);
    const int nsb = m_rubberSections.size();
    for (int i=0; i<nsb; ++i)
      collect_sec_nodes(*m_paer, m_rubberSections[i], rubberNodes);
  }
  m_rubberNodes.clear();
  m_rubberNodes.reserve( rubberNodes.size() );
  std::set_difference(rubberNodes.begin(), rubberNodes.end(),
                      m_mappedNodes.begin(), m_mappedNodes.end(),
                      back_inserter(m_rubberNodes));

  m_fixedSections.clear();
  for (uint i=0; i<m_paer->nsections(); ++i) {
    const MxMeshSection & sec( m_paer->section(i) );
    if (not sec.surfaceElements())
      continue;
    if (binary_search(m_movingSections.begin(), m_movingSections.end(), i))
      continue;
    if (binary_search(m_slidingSections.begin(), m_slidingSections.end(), i))
      continue;
    if (binary_search(m_rubberSections.begin(), m_rubberSections.end(), i))
      continue;
    m_fixedSections.push_back(i);
    log("Marked as fixed section: ", sec.name());
  }
}

void DispInterpolator::mergeSlidingNodes(const Indices &slidingNodes)
{
  // merge node sets
  Indices tmp;
  tmp.reserve(m_mappedNodes.size() + slidingNodes.size());
  std::merge(m_mappedNodes.begin(), m_mappedNodes.end(),
             slidingNodes.begin(), slidingNodes.end(),
             back_inserter(tmp));
  m_mappedNodes.clear();
  m_mappedNodes.reserve(tmp.size());
  std::unique_copy(tmp.begin(), tmp.end(), back_inserter(m_mappedNodes));
}

Vct3 DispInterpolator::slidingNormal(uint eix) const
{
  assert(m_paer);
  uint nv, isec;
  const uint *v = m_paer->globalElement(eix, nv, isec);

  Vct3 fn;
  const PointList<3> & nds( m_paer->nodes() );
  Mx::ElementType etype = m_paer->section(isec).elementType();
  switch ( etype ) {
  case Mx::Tri3:
  case Mx::Tri6:
    fn = cross(nds[v[1]] - nds[v[0]], nds[v[2]] - nds[v[0]]);
    break;
  case Mx::Quad4:
  case Mx::Quad8:
  case Mx::Quad9:
    fn = cross(nds[v[2]] - nds[v[0]], nds[v[3]] - nds[v[1]]);
    break;
  default:
    throw Error("DispInterpolator: Cannot determine sliding plane normal for "
                "elements of type: " + Mx::str(etype));
  }
  return fn.normalized();
}

void DispInterpolator::collectDispFields()
{
  // default strategy: use fields marked as displacements or eigenmodes
  Indices idf;
  for (uint j=0; j<m_pstr->nfields(); ++j) {
    const MxMeshField &fld( m_pstr->field(j) );
    MxMeshField::ValueClass vcl = fld.valueClass();
    if (vcl == MxMeshField::ValueClass::Displacement or
        vcl == MxMeshField::ValueClass::Eigenmode)
      // if (fld.nodal() and (fld.ndimension() == 3 or fld.ndimension() == 6))
      idf.push_back(j);
  }
  if (not idf.empty()) {
    m_strFields.swap(idf);
    return;
  }

  // fallback options for older files: use anything which
  // looks like displacements
  for (uint j=0; j<m_pstr->nfields(); ++j) {
    const MxMeshField &fld( m_pstr->field(j) );
    if (fld.nodal() and (fld.ndimension() == 3 or fld.ndimension() == 6))
      idf.push_back(j);
  }
  m_strFields.swap(idf);
}

uint DispInterpolator::useEigenmodes(uint maxModeCount,
                                     Real minFreq, Real maxFreq)
{
  m_strFields.clear();
  m_modalMass.clear();
  m_modalStiffness.clear();

  Indices idf;
  XmlElement::const_iterator itr, last;
  for (uint j=0; j<m_pstr->nfields(); ++j) {
    MxMeshField & field( m_pstr->field(j) );
    last = field.noteEnd();
    for (itr = field.noteBegin(); itr != last; ++itr) {
      if (itr->name() == "Eigenmode") {
        field.valueClass( MxMeshField::ValueClass::Eigenmode );
        Real f = itr->attr2float("frequency", 0.0);
        if (f >= minFreq and f <= maxFreq) {
          idf.push_back(j);
          Real mm = itr->attr2float("modal_mass", 1.0);
          Real mk = itr->attr2float("modal_stiffness", mm*sq(2*PI*f));
          m_modalMass.push_back(mm);
          m_modalStiffness.push_back(mk);
        }
      }
    }
    if (idf.size() >= maxModeCount)
      break;
  }
  m_strFields.insert(m_strFields.end(), idf.begin(), idf.end());
  return m_strFields.size();
}

uint DispInterpolator::map(const DispInterpolator::MapMatrix &H,
                           DMatrix<float> &m)
{
  if (m_mappedNodes.empty())
    collectWallNodes();
  if (m_strFields.empty())
    collectDispFields();

  // raw storage for mapped fields
  const int nwall = m_mappedNodes.size();
  const int nmapfield = m_strFields.size();
  m.resize(3*nmapfield, nwall);
  if (m.size() == 0)
    return 0;
  if (size_t(nwall) != H.nrows())
    return 0;

  Logger::nextStage(nwall);

#pragma omp parallel for schedule(dynamic, 128)
  for (int i=0; i<nwall; ++i) {

    const uint nc = H.sparsity().size(i);
    const uint *col = H.sparsity().first(i);
    const uint rowOffset = H.sparsity().offset(i);

    Vct3f dsp, df;
    for (int j=0; j<nmapfield; ++j) {
      const MxMeshField &field( m_pstr->field(m_strFields[j]) );
      for (uint kc=0; kc<nc; ++kc) {
        field.value(col[kc], dsp);
        df += Mtx33f( H.pointer() + 9*(kc+rowOffset) ) * dsp;
      }
      for (int k=0; k<3; ++k)
        m(3*j+k, i) = m_scale * df[k]; // disjoint write access: i
    }

    Logger::increment();
  }

  return nmapfield;
}

void DispInterpolator::maxBenignScale(Vector &maxscale) const
{
  const ConnectMap &v2e( m_paer->v2eMap() );
  if (v2e.size() < m_paer->nnodes())
    throw Error("Node-to-element connectivity not available in "
                "DispInterpolator::maxBenignScale().");

  // collect nodes of aerodynamic wall elements to check
  Indices wtri;
  {
    const size_t nwall = m_mappedNodes.size();
    wtri.reserve(3*nwall);
    std::vector<bool> tagged(m_paer->nelements(), false);
    for (size_t i=0; i<nwall; ++i) {
      const size_t mni = m_mappedNodes[i];
      ConnectMap::const_iterator itr, last = v2e.end(mni);
      for (itr = v2e.begin(mni); itr != last; ++itr) {
        if (tagged[*itr])
          continue;
        uint nv, isec;
        const uint *vi = m_paer->globalElement(*itr, nv, isec);
        if ( m_paer->section(isec).elementType() == Mx::Tri3 )
          wtri.insert(wtri.end(), vi, vi+3);
        tagged[*itr] = true;
      }
    }
  }

  const int ntri = wtri.size() / 3;
  const int naf = m_aerFields.size();
  maxscale.resize(naf);
  maxscale = std::numeric_limits<Real>::max();

  cout << "Checking " << ntri << " triangles for interference..." << endl;

  BEGIN_PARLOOP_CHUNK(0, ntri, 256)
      for (int j=a; j<b; ++j) {
    Vct3 tri[3], dsp[3];
    for (int k=0; k<3; ++k)
      tri[k] = m_paer->node( wtri[3*j+k] );

    // undeformed triangle normal
    Vct3 fn = cross(tri[1]-tri[0], tri[2]-tri[0]);

    // check each field separately
    for (int ifield=0; ifield<naf; ++ifield) {

      const MxMeshField &field( m_paer->field(m_aerFields[ifield]) );

      for (int k=0; k<3; ++k)
        field.value( wtri[3*j+k], dsp[k] );

      // change in triangle normal for small deformation
      Vct3 dn = cross(dsp[1]-dsp[0], tri[2]-tri[0])
          + cross(tri[1]-tri[0], dsp[2]-dsp[0]);

      // compute f s.th.  fn^T (fn + f*dn) = 0, that is, the deformation
      // factor where triangle is turned 90 degree or area collapses to zero
      Real dtn = dot(fn,dn);
      Real fmax = maxscale[ifield];
      if (dtn < 0)
        fmax = std::min(fmax, -dot(fn,fn)/dtn);

      // check quadratic form: half f unless area of deformed triangle is
      // at least 1% of the area of the undeformed one
      const Real sqalim = 1e-4 * sq(fn);
      while (sq(fn + fmax*dn) < sqalim)
        fmax *= 0.5;
      atomic_min(maxscale[ifield], fmax);
    }
  }
  END_PARLOOP_CHUNK
}

void DispInterpolator::autoScale()
{
  maxBenignScale(m_autoScales);
  const int naf = m_autoScales.size();
  for (int i=0; i<naf; ++i) {
    m_autoScales[i] = std::min(1.0, 0.8*m_autoScales[i]);
    m_paer->field( m_aerFields[i] ).scale( m_autoScales[i] );
  }

  log("Automatically determined scaling factors:");
  for (int i=0; i<naf; ++i)
    log("Field ", i+1, ": ", m_scale*m_autoScales[i]);
}

void DispInterpolator::pinSlidingNodes(DMatrix<float> &dsp) const
{
  assert(dsp.nrows() == 3*m_strFields.size());
  assert(dsp.ncols() == m_mappedNodes.size());

  const int nsf = m_strFields.size();
  const int nset = m_snset.size();

#pragma omp parallel
  {
    for (int j=0; j<nset; ++j) {
      const int nn = m_snset[j].nodes.size();
      const Vct3 & sn( m_snset[j].normal );

#pragma omp for
      for (int i=0; i<nn; ++i) {
        const uint jcol = m_snset[j].nodes[i];
        for (int im=0; im<nsf; ++im) {
          Vct3 def( dsp(3*im+0,jcol), dsp(3*im+1,jcol), dsp(3*im+2,jcol) );
          def -= dot(def, sn)*sn;
          for (int k=0; k<3; ++k)
            dsp(3*im+k, jcol) = def[k];
        } // field
      } // node
    }
  } // omp parallel
}

void DispInterpolator::pinSlidingNodes(MapMatrix &H) const
{
  const int nset = m_snset.size();

#pragma omp parallel
  {
    for (int j=0; j<nset; ++j) {
      const int nn = m_snset[j].nodes.size();
      Vct3f sn( m_snset[j].normal );
      Mtx33f pjm = Mtx33f::identity();
      pjm -= dyadic(sn, sn);

#pragma omp for
      for (int i=0; i<nn; ++i) {
        const uint sni = m_snset[j].nodes[i];
        const uint offs = H.sparsity().offset(sni);
        const int nc = H.sparsity().size(sni);
        for (int jc=0; jc<nc; ++jc) {
          float & m = H.value(offs+jc, 0);
          Mtx33f mp = pjm * Mtx33f( &m );
          memcpy( &m, mp.pointer(), 9*sizeof(float) );
        }
      } // node
    }
  } // omp parallel
}

void DispInterpolator::appendFields(const DMatrix<float> &m)
{
  // generate fields in aerodynamic mesh
  const int nwall = m_mappedNodes.size();
  const int nands = m_paer->nnodes();
  const int nmapfield = m_strFields.size();

  // identify sliding nodes just once
  Indices slidingNodes;
  XmlElement xslplanes("sliding_planes");
  if (not m_snset.empty()) {
    for (uint i=0; i<m_snset.size(); ++i) {
      const Indices & sn( m_snset[i].nodes );
      slidingNodes.insert(slidingNodes.end(), sn.begin(), sn.end());
      xslplanes.append("boundary_name", m_snset[i].boundaryName);
    }
    sort_unique(slidingNodes);
  }

  PointList<3> fdef( nands );
  for (int j=0; j<nmapfield; ++j) {
    for (int i=0; i<nwall; ++i) {
      const uint iwn = m_mappedNodes[i];
      fdef[iwn] = Vct3(m(3*j+0, i), m(3*j+1, i), m(3*j+2, i));
    }
    const MxMeshField & sf(  m_pstr->field( m_strFields[j] ) );
    uint fix = m_paer->appendField( sf.name(), fdef );
    MxMeshField::ValueClass vcl = sf.valueClass();
    // cout << "Field " << sf.name() << " class: " << vcl << endl;
    if (vcl != MxMeshField::ValueClass::Field)
      m_paer->field(fix).valueClass( vcl );
    else
      m_paer->field(fix).valueClass( MxMeshField::ValueClass::Displacement );

    // extract annotation from original mode dataset and add additional data
    XmlElement xn( sf.note() );
    xn["identifier"] = str(j+1);
    if (m_modalMass.size() > uint(j)) {
      xn["generalized_mass"] = str(m_modalMass[j]);
      xn["generalized_stiffness"] = str(m_modalStiffness[j]);
      xn["frequency_hz"] = str(sqrt(m_modalStiffness[j]/m_modalMass[j])/(2*PI));
    }

    // store the scale used by surfmap
    Real s = m_scale;
    if (m_autoScales.size() == size_t(nmapfield))
      s *= m_autoScales[j];
    xn["surfmap_scale"] = str(s);

    // dataset which allows exporting each field in bdis format even
    // after round-trip through native file format
    XmlElement xbd("bdis_data");
    xbd.append("nodes_moving", m_mappedNodes.size(), &m_mappedNodes[0]);
    if (not slidingNodes.empty()) {
      xbd.append("sliding_nodes", slidingNodes.size(), &slidingNodes[0]);
      xbd.append(xslplanes);
    }
    {
      // to maintain compatibility with earlier code, we need to add
      // modal data one more time.
      XmlElement xm("mode");
      xm["identifier"] = str(j+1);
      if (m_modalMass.size() > uint(j)) {
        xm["generalized_mass"] = str(m_modalMass[j]);
        xm["generalized_stiffness"] = str(m_modalStiffness[j]);
        xm["frequency_hz"] = str(sqrt(m_modalStiffness[j]/m_modalMass[j])/(2*PI));
      }
      xbd.append(std::move(xm));
    }

    auto app_bocos = [&](const Indices &bcs, XmlElement &xbg) {
      for (uint ibc : bcs)
        xbg.append( "boundary_name", m_paer->boco(ibc).name() );
    };
    auto app_sections = [&](const Indices &secs, XmlElement &xbg) {
      for (uint isec : secs)
        xbg.append( "boundary_name", m_paer->section(isec).name() );
    };

    {
      XmlElement xbg("moving_surfaces");
      app_bocos(m_movingBocos, xbg);
      app_sections(m_movingSections, xbg);
      if (not xbg.empty())
        xbd.append(std::move(xbg));
    }

    {
      XmlElement xbg("sliding_surfaces");
      app_bocos(m_slidingBocos, xbg);
      app_sections(m_slidingSections, xbg);
      if (not xbg.empty())
        xbd.append(std::move(xbg));
    }

    {
      XmlElement xbg("fixed_surfaces");
      app_bocos(m_fixedBocos, xbg);
      app_sections(m_fixedSections, xbg);
      if (not xbg.empty())
        xbd.append(std::move(xbg));
    }

    xn.append(std::move(xbd));
    m_paer->field(fix).note( xn );
    m_aerFields.push_back(fix);
  }

  XmlElement xn("DispInterpolation");
  for (uint i=0; i<m_movingBocos.size(); ++i) {
    const string &bn =  m_paer->boco(m_movingBocos[i]).name();
    xn.append("moving_surface", bn);
  }
  for (uint i=0; i<m_movingSections.size(); ++i) {
    const string &bn =  m_paer->section(m_movingSections[i]).name();
    xn.append("moving_surface", bn);
  }
  m_paer->annotate(xn);
}

void DispInterpolator::writeBdis(const string &prefix) const
{
  // write one file for each mode (strangely enough)
  const int nfield = m_aerFields.size();
  const int nmapped = m_mappedNodes.size();
  bool useMM = (uint(nfield) == m_modalMass.size());

  // data for the .amop file
  FFANodePtr amop = FFANode::create("modal_parameters");
  amop->append("default_damping", 0.001);
  FFANodePtr amop_set = FFANode::create("mode_set");

  Matrix disp(nmapped,3);
  Real scale = m_scale;
  for (int j=0; j<nfield; ++j) {

    // field to export
    const MxMeshField & af( m_paer->field(m_aerFields[j]) );

    // determine total scaling factor relative to structural mode
    if (m_autoScales.size() == size_t(nfield))
      scale = m_scale * m_autoScales[j];

    // generate header
    FFANodePtr root = FFANode::create("surface_movement");
    root->append("brand", "surfmap, libsurf, www.larosterna.com");
    root->append("title", "extrapolated nodal surface displacements");

    FFANodePtr moving_surfaces = FFANode::create("moving_surfaces");
    for (uint i=0; i<m_movingBocos.size(); ++i) {
      const string &bn =  m_paer->boco(m_movingBocos[i]).name();
      moving_surfaces->append("boundary_name", bn);
    }
    for (uint i=0; i<m_movingSections.size(); ++i) {
      const string &bn =  m_paer->section(m_movingSections[i]).name();
      moving_surfaces->append("boundary_name", bn);
    }
    root->append(moving_surfaces);

    Indices slidingNodes;
    FFANodePtr sliding_planes = FFANode::create("sliding_planes");
    if (not m_snset.empty()) {

      for (uint i=0; i<m_snset.size(); ++i) {
        const Indices & sn( m_snset[i].nodes );
        slidingNodes.insert(slidingNodes.end(), sn.begin(), sn.end());
        sliding_planes->append("boundary_name", m_snset[i].boundaryName);
      }

      sort_unique(slidingNodes);
    }

    // append node even if it's empty
    root->append( sliding_planes );

    // TODO : free nodes (wakes etc)
    root->append( FFANode::create("free_surfaces") );

    FFANodePtr fixed_surfaces = FFANode::create("fixed_surfaces");
    for (uint i=0; i<m_fixedBocos.size(); ++i) {
      const string &bn =  m_paer->boco(m_fixedBocos[i]).name();
      fixed_surfaces->append("boundary_name", bn);
    }
    for (uint i=0; i<m_fixedSections.size(); ++i) {
      const string &bn =  m_paer->section(m_fixedSections[i]).name();
      fixed_surfaces->append("boundary_name", bn);
    }
    root->append(fixed_surfaces);

    // translate indices
    {
      Indices tmp;
      if (not slidingNodes.empty()) {
        tmp.reserve( m_mappedNodes.size() - slidingNodes.size() );
        std::set_difference( m_mappedNodes.begin(), m_mappedNodes.end(),
                             slidingNodes.begin(), slidingNodes.end(),
                             back_inserter(tmp) );
      } else {
        tmp = m_mappedNodes;
      }

      const int nt = tmp.size();
      for (int i=0; i<nt; ++i)
        ++tmp[i];
      root->append("nodes_moving", nt, 1, (const int*) &tmp[0]);

      const int ns = slidingNodes.size();
      for (int i=0; i<ns; ++i)
        ++slidingNodes[i];
      if (ns > 0)
        root->append("nodes_sliding", ns, 1, (const int *) &slidingNodes[0]);
    }

    FFANodePtr mode = FFANode::create("mode");
    mode->append("identifier", 1+j);
    if (useMM) {
      Real mm = m_modalMass[j] * sq(scale);
      Real mk = m_modalStiffness[j] * sq(scale);
      mode->append("frequency_hz", sqrt(mk/mm)/(2*PI));
      mode->append("generalized_mass", mm);
      mode->append("generalized_stiffness", mk);
      mode->append("surfmap_scale", scale);
      mode->append("init_velocity", 0.0);
      mode->append("damping_ratio", 0.0);
    }
    root->append(mode);
    amop_set->append(mode);

    // extract displacements for mapped nodes
    for (int i=0; i<nmapped; ++i) {
      Vct3 idef;
      af.value(m_mappedNodes[i], idef);
      for (int k=0; k<3; ++k)
        disp(i,k) = idef[k];
    }
    root->append("displacement", disp.nrows(), disp.ncols(), disp.pointer());

    stringstream ss;
    ss << prefix << '_' << j+1 << ".bdis";
    root->write(ss.str());
  }

  amop->append(amop_set);
  amop->write(prefix + ".amop");
}

FFANodePtr DispInterpolator::mapToFFA(const DispInterpolator::MapMatrix &H) const
{
  FFANodePtr root = boost::make_shared<FFANode>("mapping_matrix");
  root->append("sparse_format", "block_csr");

  // intent is to for file to be read by fortran code, hence, we
  // convert indices to 1-based
  const int nwn = m_mappedNodes.size();
  {
    DVector<int> wn( nwn );
    for (int i=0; i<nwn; ++i)
      wn[i] = m_mappedNodes[i] + 1;
    root->append("mapped_nodes", nwn, 1, wn.pointer());
  }

  // sparse block matrix H
  root->append( H.toFFA() );

  // check whether the structural mesh contains annotations claiming to be
  // mass- and stiffness matrix; if so, append them to root
  if (m_pstr != nullptr) {
    XmlElement::const_iterator itr;
    const XmlElement & note( m_pstr->note() );
    itr = note.findChild("MassMatrix");
    if (itr != note.end()) {
      CsrMatrix<Real,1> M;
      M.fromXml(*itr);
      FFANodePtr pmat = M.toFFA();
      pmat->rename("MassMatrix");
      root->append( pmat );
    }
    itr = note.findChild("StiffnessMatrix");
    if (itr != note.end()) {
      CsrMatrix<Real,1> M;
      M.fromXml(*itr);
      FFANodePtr pmat = M.toFFA();
      pmat->rename("StiffnessMatrix");
      root->append( pmat );
    }
  }

  return root;
}

bool DispInterpolator::mapFromFFA(const FFANodePtr &root,
                                  DispInterpolator::MapMatrix &H)
{
  // NOTE: all indices are 1-based (fortran...)
  uint ip = NotFound;
  {
    DVector<int> wn;
    ip = root->findChild("mapped_nodes");
    if (ip == NotFound)
      return false;
    FFANodePtr ptr = root->child(ip);
    const size_t nwn = ptr->numel();
    wn.allocate(nwn);
    ptr->retrieve(wn.pointer());

    m_mappedNodes.resize(nwn);
    for (size_t i=0; i<nwn; ++i)
      m_mappedNodes[i] = wn[i]-1;
  }

  ip = root->findChild("csr_matrix");
  if (ip == NotFound)
    return false;

  bool ok = true;
  ok = H.fromFFA(root->child(ip));
  if (not ok)
    return false;

  // TODO: Extract optional data from H matrix file

  return true;
}

void DispInterpolator::mapAerTopology(const Indices &nodeSet,
                                      ConnectMap &v2v) const
{
  if (m_paer->v2eMap().size() != m_paer->nnodes())
    m_paer->fixate();

  // construct connectivity
  const ConnectMap & v2e( m_paer->v2eMap() );
  std::vector<uint64_t> gpack;
  const size_t nf = nodeSet.size();

#pragma omp parallel
  {
    // thread-private copies
    std::vector<uint64_t> ppack;
    size_t ptail(0);

#pragma omp for schedule(static, 512)
    for (intptr_t i=0; i<intptr_t(nf); ++i) {

      ppack.push_back( ConnectMap::packpair(i,i) );
      const uint gni = nodeSet[i];
      ConnectMap::const_iterator itr, last = v2e.end(gni);
      for (itr = v2e.begin(gni); itr != last; ++itr) {
        uint nv, isec;
        const uint *v = m_paer->globalElement(*itr, nv, isec);
        for (uint j=0; j<nv; ++j) {
          uint mvj = sorted_index(nodeSet, v[j]);
          if ( mvj != NotFound )
            ppack.push_back( ConnectMap::packpair(i, mvj) );
        }

        // compress pack array every now and then to reduce memory pressure
        if (ppack.size() - ptail > 1024*1024)
          ptail = unique_merge_tail(ptail, ppack);
      }
    }

#pragma omp critical
    gpack.insert(gpack.end(), ppack.begin(), ppack.end());
  }

  parallel::sort(gpack.begin(), gpack.end());
  gpack.erase(std::unique(gpack.begin(), gpack.end()), gpack.end());

  v2v.clear();
  v2v.assign(nf, gpack.size(), &gpack[0]);
}

void DispInterpolator::nearbyNodes(Real threshold,
                                   const Indices &src, Indices &nbnodes) const
{
  // construct point search tree
  const size_t nmapped = m_mappedNodes.size();
  PointList<3,float> mnodes(nmapped);
  for (size_t i=0; i<nmapped; ++i)
    mnodes[i] = Vct3f( m_paer->node(m_mappedNodes[i]) );

  NDPointTree<3,float> ptree;
  ptree.allocate( mnodes, true, 4 );
  ptree.sort();

  const int ns = src.size();
#pragma omp parallel
  {
    // thread-private node set
    Indices tset;

#pragma omp for schedule(static, 128)
    for (int i=0; i<ns; ++i) {
      ptree.find( mnodes[src[i]], threshold, tset );
    }

    std::sort(tset.begin(), tset.end());
    tset.erase( std::unique(tset.begin(), tset.end()), tset.end() );

#pragma omp critical
    nbnodes.insert(nbnodes.end(), tset.begin(), tset.end());
  }

  // TODO: Use parallel sort?
  std::sort(nbnodes.begin(), nbnodes.end());
  nbnodes.erase( std::unique(nbnodes.begin(), nbnodes.end()),
                 nbnodes.end() );
}

void DispInterpolator::rubberTriangles(Indices &tri) const
{
  tri.clear();
  for (size_t i=0; i<m_rubberSections.size(); ++i) {
    const MxMeshSection &sec(m_paer->section(m_rubberSections[i]));
    assert(sec.elementType() == Mx::Tri3);
    const Indices & vix( sec.nodes() );
    tri.insert(tri.end(), vix.begin(), vix.end());
  }

  for (size_t i=0; i<m_rubberBocos.size(); ++i) {
    uint isec = m_paer->mappedSection( m_rubberBocos[i] );
    if (isec != NotFound) {
      const MxMeshSection &sec(m_paer->section(isec));
      assert(sec.elementType() == Mx::Tri3);
      const Indices & vix( sec.nodes() );
      tri.insert(tri.end(), vix.begin(), vix.end());
    } else {
      Indices elix;
      const MxMeshBoco &bc( m_paer->boco(m_rubberBocos[i]) );
      bc.elements(elix);
      const int ne = elix.size();
      for (int j=0; j<ne; ++j) {
        uint nv, isec;
        const uint *v = m_paer->globalElement(elix[j], nv, isec);
        assert(m_paer->section(isec).elementType() == Mx::Tri3);
        tri.insert(tri.end(), v, v+nv);
      }
    }
  }
}

void DispInterpolator::smoothMap(int niter, float omega,
                                 const Indices &rnodes,
                                 const ConnectMap &v2v,
                                 MapMatrix &H) const
{
  MapMatrix hsm;
  const int nwall = H.nrows();
  const int nrn = rnodes.size();

  // determine final sparsity pattern after smoothing
  {
    ConnectMap hsp( H.sparsity() );
    for (int j=0; j<niter; ++j) {

      ConnectMap map;
      map.beginCount(nwall);
      for (int i=0; i<nwall; ++i)
        map.incCount(i, hsp.size(i));
      for (int i=0; i<nrn; ++i) {
        const uint rni = rnodes[i];
        ConnectMap::const_iterator itr, last = v2v.end(rni);
        for (itr = v2v.begin(rni); itr != last; ++itr)
          map.incCount(rni, hsp.size(*itr));
      }

      map.endCount();

      for (int i=0; i<nwall; ++i)
        map.append(i, hsp.size(i), hsp.first(i));
      for (int i=0; i<nrn; ++i) {
        const uint rni = rnodes[i];
        ConnectMap::const_iterator itr, last = v2v.end(rni);
        for (itr = v2v.begin(rni); itr != last; ++itr)
          map.append(rni, hsp.size(*itr), hsp.first(*itr));
      }

      map.compress();
      hsp.swap(map);
    }

    hsm.swap(hsp);
  }

  // sparsity pattern complete, initialize map with H
  const ConnectMap &hsp( H.sparsity() );
  uint offs = 0;
  for (int i=0; i<nwall; ++i) {
    const int nc = hsp.size(i);
    const uint *cip = hsp.first(i);
    for (int jc=0; jc<nc; ++jc) {
      uint lix = hsm.lindex( i, cip[jc] );
      assert(lix != NotFound);
      float & dst = hsm.value(lix, 0);
      float & src = H.value(offs, 0);
      memcpy(&dst, &src, 9*sizeof(float));
      ++offs;
    }
  }

  // Gauss-Seidel smoothing iterations
  for (int si=0; si<niter; ++si) {
    for (int i=0; i<nrn; ++i) {
      const uint rni = rnodes[i];
      hsm.scaleRow(rni, (1.0f - omega));
      const float frow = omega / v2v.size(rni);
      ConnectMap::const_iterator itr, last = v2v.end(rni);
      for (itr = v2v.begin(rni); itr != last; ++itr)
        hsm.addRow(*itr, rni, frow);
    }
  }

  H.swap(hsm);
}

void DispInterpolator::boundingBox(Vct3 &plo, Vct3 &phi) const
{
  plo = std::numeric_limits<Real>::max();
  phi = - plo;
  const size_t n = m_mappedNodes.size();
  for (size_t i=0; i<n; ++i) {
    const Vct3 & p( m_paer->node(m_mappedNodes[i]) );
    for (int k=0; k<3; ++k) {
      plo[k] = std::min( plo[k], p[k] );
      phi[k] = std::min( phi[k], p[k] );
    }
  }
}

void DispInterpolator::findMappedElements(Indices &elix) const
{
  assert(m_paer->v2eMap().size() == m_paer->nnodes());

  elix.clear();
  std::vector<bool> emapped(m_paer->nelements(), false);
  const size_t nn = m_mappedNodes.size();
  const ConnectMap & v2e( m_paer->v2eMap() );
  for (size_t i=0; i<nn; ++i) {
    ConnectMap::const_iterator itr, last = v2e.end( m_mappedNodes[i] );
    for (itr = v2e.begin(m_mappedNodes[i]); itr != last; ++itr) {
      uint eix = *itr;
      if (not emapped[eix]) {
        emapped[eix] = true;
        elix.push_back(eix);
      }
    }
  }
  std::sort(elix.begin(), elix.end());
}

uint DispInterpolator::appendNodeSet(const Indices &rnodes)
{
  // create element group (for validation)
  Indices elix;
  const ConnectMap &v2e( m_paer->v2eMap() );
  for (size_t i=0; i<rnodes.size(); ++i) {
    uint rni = m_mappedNodes[rnodes[i]];
    elix.insert(elix.end(), v2e.begin(rni), v2e.end(rni));
  }
  sort_unique(elix);
  uint ibc = m_paer->appendBoco( Mx::BcElementSet, elix );
  // m_paer->boco(ibc).rename("JumpElements");

  dbprint(elix.size(), "elements around discontinuity.");
  return ibc;
}

void DispInterpolator::smoothedRegionRim(const ConnectMap &v2v,
                                         const Indices &rnodes,
                                         Indices &rim) const
{
  rim.clear();

  // create sorted set of nodes which are neighbors of jump nodes
  Indices tmp;
  const size_t nrn = rnodes.size();
  for (size_t i=0; i<nrn; ++i) {
    uint rni = rnodes[i];
    const uint *pnb = v2v.first(rni);
    tmp.insert(tmp.end(), pnb, pnb + v2v.size(rni));
  }
  std::sort(tmp.begin(), tmp.end());
  tmp.erase( std::unique(tmp.begin(), tmp.end()), tmp.end() );

  // exclude jump nodes from index set
  rim.reserve(tmp.size() - rnodes.size());
  std::set_difference( tmp.begin(), tmp.end(), rnodes.begin(), rnodes.end(),
                       back_inserter(rim) );

  sort_unique(rim);
}

void DispInterpolator::bfsWalk(uint k, Real sqlmax, const ConnectMap &v2v,
                               const Indices &subset, Indices &vnb) const
{
  vnb.clear();

  // flag set to break infinite iteration
  std::vector<bool> touched( v2v.size(), false );

  assert(m_paer != nullptr);
  const Vct3 & pk( m_paer->node(m_mappedNodes[k]) );
  std::deque<uint> q;
  q.push_back(k);
  while (not q.empty()) {
    uint j = q.front();
    q.pop_front();

    ConnectMap::const_iterator itr, last = v2v.end(j);
    for (itr = v2v.begin(j); itr != last; ++itr) {
      uint m = *itr;
      if (touched[m])
        continue;
      touched[m] = true;

      // skip vertex entirely if too far away
      const Vct3 & pm( m_paer->node(m_mappedNodes[m]) );
      if ( sq(pk - pm) < sqlmax ) {

        // if m in subset, put into vnb; otherwise, append to search queue
        if ( binary_search(subset.begin(), subset.end(), m) )
          vnb.push_back(m);
        else
          q.push_back(m);
      } // distance
    }

    // debug trap
    if (vnb.size() > subset.size())
      abort();
  }

  std::sort(vnb.begin(), vnb.end());
  vnb.erase( std::unique(vnb.begin(), vnb.end()), vnb.end() );
}

bool DispInterpolator::isMappedElement(uint k) const
{
  uint nv, isec;
  const uint *v = m_paer->globalElement(k, nv, isec);
  if ( std::find(m_movingSections.begin(),
                 m_movingSections.end(), isec) != m_movingSections.end() )
    return true;

  for (uint i=0; i<nv; ++i) {
    if (not binary_search(m_mappedNodes.begin(),
                          m_mappedNodes.end(), v[i]))
      return false;
  }

  return true;
}
