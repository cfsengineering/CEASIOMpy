
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
 
#include "defines.h"
#include "dbprint.h"
#include "mxmesh.h"
#include "mxsolutiontree.h"
#include "cgmesh.h"
#include "trimesh.h"
#include "plane.h"
#include "ndpointtree.h"
#include "ioglue.h"
#include <sstream>
#include <set>

using std::string;
using std::stringstream;

TypeCode MxMesh::s_fileFloatPrecision = TypeCode(TypeCode::Float64);

uint MxMesh::appendSection(Mx::ElementType t, const Indices & idx)
{
  sections.push_back( MxMeshSection(this, t) );
  sections.back().appendElements(idx);
  sections.back().indexOffset(nelm);
  nelm += sections.back().nelements();
  v2e.clear();
  return sections.size()-1;
}

uint MxMesh::appendSection(const TriMesh & m)
{
  uint voff = vtx.size();
  uint eloff = nelements();
  appendNodes( m.vertices() );
  
  const int nf(m.nfaces());
  Indices idx(3*nf);
  DVector<int> tags(nf), atg;
  for (int i=0; i<nf; ++i) {
    const uint *vi = m.face(i).vertices();
    tags[i] = m.face(i).tag();
    insert_once(atg, tags[i]);
    for (int k=0; k<3; ++k)
      idx[3*i + k] = vi[k] + voff;
  }
  uint isec = appendSection( Mx::Tri3, idx );
  sections[isec].rename("TriMesh");
  
  // convert tags to named boundary conditions
  const int nbc = atg.size();
  if (nbc > 1) {
    for (int i=0; i<nbc; ++i) {
      Indices bce;
      for (int j=0; j<nf; ++j) {
        if (tags[j] == atg[i])
          bce.push_back(eloff+j);
      }
      
      MxMeshBoco bc;
      bc.appendElements(bce);
      bc.rename(m.tagName(atg[i]));
      bocos.push_back(bc);
    }
  }
  
  return isec;
}

uint MxMesh::appendSection(const PointGrid<3> & pg)
{
  uint voff = vtx.size();
  vtx.insert(vtx.end(), pg.begin(), pg.end());

  const int nr = pg.nrows();
  const int nc = pg.ncols();
  const int nf = (nr-1)*(nc-1);
  assert(nf > 0);
  Indices idx(4*nf);
  uint k(0);
  for (int j=1; j<nc; ++j) {
    for (int i=1; i<nr; ++i) {
      idx[4*k + 0] = voff + nr*(j-1) + (i-1);
      idx[4*k + 1] = voff + nr*(j-1) + i;
      idx[4*k + 2] = voff + nr*j + i;
      idx[4*k + 3] = voff + nr*j + (i-1);
      ++k;
    }
  }
  
  uint isec = appendSection(Mx::Quad4, idx);
  section(isec).rename("PointGrid "+str(nr)+" by "+str(nc));
  
  return isec;
}

uint MxMesh::appendSection(const PointList<3> &pts)
{
  const uint voff = nnodes();
  const int np = pts.size();
  Indices lns( 2*(np - 1) );
  for (int i=0; i<np-1; ++i) {
    lns[2*i+0] = voff + i;
    lns[2*i+1] = voff + i + 1;
  }
  appendNodes(pts);
  return appendSection(Mx::Line2, lns);
}

uint MxMesh::appendSection(const CgMesh &cgm)
{
  const uint offset = nnodes();
  {
    // Microsoft and old gcc compilers require additional copy
    PointList<3> cgv( cgm.vertices() );
    appendNodes(cgv.begin(), cgv.end());
  }

  Indices tri, lns;
  cgm.toTriangles(tri);
  int n = tri.size();
  for (int i=0; i<n; ++i)
    tri[i] += offset;

  cgm.toLines(lns);
  n = lns.size();
  for (int i=0; i<n; ++i)
    lns[i] += offset;
  uint lsec = appendSection(Mx::Line2, lns);
  section(lsec).rename("CgMesh Lines");

  return appendSection(Mx::Tri3, tri);
}

void MxMesh::eraseSection(uint k)
{
  assert(k < sections.size());
  const uint a = section(k).indexOffset();
  const uint b = a + section(k).nelements();

  // remove section elements from fields with
  // element-wise data sets
  const size_t nf = nfields();
  for (size_t i=0; i<nf; ++i) {
    if (not field(i).nodal())
      field(i).erase(a, b);
  }

  // remove erased elements from boco set (keeps even empty sets)
  for (size_t i=0; i<nbocos(); ++i)
    boco(i).eraseElements(a, b);

  dbprint("Erased section",section(k).name());
  sections.erase(sections.begin() + k);
  countElements();
}

uint MxMesh::mirrorCopyNodes(const Indices &snodes, const Plane &pln)
{
  uint voff = vtx.size();

  // generate new nodes
  const size_t nsn = snodes.size();
  for (size_t i=0; i<nsn; ++i) {
    Vct3 pref = pln.reflection( vtx[snodes[i]] );
    vtx.push_back( pref );
  }

  // adapt nodal fields
  for (uint ifi=0; ifi<nfields(); ++ifi) {
    if (field(ifi).nodal())
      field(ifi).extend(snodes, pln);
  }

  return voff;
}

uint MxMesh::mirrorCopySection(uint k, uint voff,
                               const Indices &snodes,
                               bool merge)
{
  assert(k < nsections());

  MxMeshSection &sec(section(k));
  const size_t indexOffset = sec.indexOffset();
  const size_t insElemCount = sec.nelements();

  // generate elements using indices of newly created vertices
  const Indices & se = sec.nodes();
  const size_t nse = se.size();
  Indices mse(nse);
  for (size_t i=0; i<nse; ++i) {
    uint nvi = sorted_index( snodes, se[i] );
    assert(nvi != NotFound);
    mse[i] = voff + nvi;
  }

  // reverse vertex order to make the element normal point in the
  // correct (mirrored) direction
  const int nv = sec.nElementNodes();
  {
    assert(nv <= 32);
    uint vt[32];
    const size_t ne = sec.nelements();
    for (size_t i=0; i<ne; ++i) {
      for (int k=0; k<nv; ++k)
        vt[k] = mse[nv*i+k];
      for (int k=0; k<nv; ++k)
        mse[nv*i+k] = vt[nv-1-k];
    }
  }

  // TODO: Adapt BOCOs to new element indexing
  // bocos.clear();

  uint insec(k);
  if (merge) {

    Indices merged(se);
    merged.insert(merged.end(), mse.begin(), mse.end());
    sec.swapElements(sec.elementType(), merged);

    // up to elixUnchanged, element indices are not modified;
    // above that, they are shifted by insElemCount
    size_t elixUnchanged = indexOffset + insElemCount;
    for (uint j=0; j<nbocos(); ++j)
      boco(j).shiftElementIndices(insElemCount, elixUnchanged);

  } else {

    // section is appended to the end, so that the new element indices
    // are beyond the old ones; hence, old element indices in bocos can be
    // kept without modification
    insec = this->appendSection( sec.elementType(), mse );
    section(insec).rename(section(k).name() + "MirrorCopy");
    countElements();

    // check whether any boco maps k exactly; if so, duplicate it for insec
    for (uint i=0; i<nbocos(); ++i) {
      if (sec.maps( boco(i) )) {
        MxMeshBoco dbc( boco(i) );
        uint sbegin = section(insec).indexOffset();
        uint send  = sbegin + section(insec).nelements();
        dbc.setRange(sbegin, send);
        appendBoco(dbc);
      }
    }
  }

  // FIXME : Check!
  // adjust element-wise data fields by copying element data
  for (uint ifi=0; ifi<nfields(); ++ifi) {
    if (not field(ifi).nodal()) {
      if (field(ifi).realField()) {
        DVector<Real> nval(insElemCount);
        for (size_t i=0; i<insElemCount; ++i)
          field(ifi).scalar( sec.indexOffset()+i, nval[i] );
        field(ifi).insert( sec.indexOffset()+insElemCount,
                           nval.begin(), nval.end() );
      } else {
        DVector<int> nval(insElemCount);
        for (size_t i=0; i<insElemCount; ++i)
          field(ifi).scalar( sec.indexOffset()+i, nval[i] );
        field(ifi).insert( sec.indexOffset()+insElemCount,
                           nval.begin(), nval.end() );
      }
    }
  }

  countElements();
  return insec;
}

void MxMesh::bindFields()
{
  for (uint i=0; i<fields.size(); ++i)
    fields[i].bind(this);
}

uint MxMesh::appendField(const std::string & s, const Vector & v)
{
  bool bNodal(true);
  if (v.size() == nnodes())
    bNodal = true;
  else if (v.size() == nelements())
    bNodal = false;
  else {
    stringstream ss;
    ss << "Data size mismatch in MxMesh::appendField()." << endl;
    ss << "Nodes: " << nnodes() << " Elements: "
       << nelements() << " Values: " << v.size() << endl;
    throw Error(ss.str());
  }
  
  MxMeshField f(this, bNodal);
  f.scalarField(s, v);
  return appendField( std::move(f) );
}

uint MxMesh::appendField(const std::string & s, const DVector<float> & v)
{
  const int n = v.size();
  Vector vd(n);
  for (int i=0; i<n; ++i)
    vd[i] = (Real) v[i];
  return appendField(s, vd);
}

uint MxMesh::appendField(const std::string & s, const DVector<int> & v)
{
  bool bNodal(true);
  if (v.size() == nnodes())
    bNodal = true;
  else if (v.size() == nelements())
    bNodal = false;
  else {
    stringstream ss;
    ss << "Data size mismatch in MxMesh::appendField()." << endl;
    ss << "Nodes: " << nnodes() << " Elements: " << nelements()
       << " Values: " << v.size() << endl;
    throw Error(ss.str());
  }
  
  MxMeshField f(this, bNodal);
  f.scalarField(s, v);
  return appendField( std::move(f) );
}

uint MxMesh::appendField(const std::string & s, const PointList<3> & v)
{
  bool bNodal(true);
  if (v.size() == nnodes())
    bNodal = true;
  else if (v.size() == nelements())
    bNodal = false;
  else {
    stringstream ss;
    ss << "Data size mismatch in MxMesh::appendField()." << endl;
    ss << "Nodes: " << nnodes() << " Elements: " << nelements()
       << " Values: " << v.size() << endl;
    throw Error(ss.str());
  }
  
  MxMeshField f(this, bNodal);
  f.vectorField(s, v);
  return appendField(std::move(f));
}

uint MxMesh::appendField(const std::string & s,
                         const PointList<3,float> & v)
{
  bool bNodal(true);
  if (v.size() == nnodes())
    bNodal = true;
  else if (v.size() == nelements())
    bNodal = false;
  else {
    stringstream ss;
    ss << "Data size mismatch in MxMesh::appendField()." << endl;
    ss << "Nodes: " << nnodes() << " Elements: " << nelements()
       << " Values: " << v.size() << endl;
    throw Error(ss.str());
  }

  MxMeshField f(this, bNodal);
  f.vectorField(s, v);
  return appendField(std::move(f));
}

uint MxMesh::appendField(const std::string & s, const PointList<6> & v)
{
  bool bNodal(true);
  if (v.size() == nnodes())
    bNodal = true;
  else if (v.size() == nelements())
    bNodal = false;
  else {
    stringstream ss;
    ss << "Data size mismatch in MxMesh::appendField()." << endl;
    ss << "Nodes: " << nnodes() << " Elements: " << nelements()
       << " Values: " << v.size() << endl;
    throw Error(ss.str());
  }

  MxMeshField f(this, bNodal);
  f.vectorField(s, v);
  return appendField(std::move(f));
}

uint MxMesh::appendField(const std::string & s,
                         const PointList<6,float> & v)
{
  bool bNodal(true);
  if (v.size() == nnodes())
    bNodal = true;
  else if (v.size() == nelements())
    bNodal = false;
  else {
    stringstream ss;
    ss << "Data size mismatch in MxMesh::appendField()." << endl;
    ss << "Nodes: " << nnodes() << " Elements: " << nelements()
       << " Values: " << v.size() << endl;
    throw Error(ss.str());
  }

  MxMeshField f(this, bNodal);
  f.vectorField(s, v);
  return appendField(std::move(f));
}

uint MxMesh::appendRigidBodyMode(int mindex, const Vct3 & rotctr,
                                 Real gm, Real gk)
{
  if (mindex < 0 or mindex > 5)
    throw Error("Invalid rigid-body mode index: "+str(mindex));

  const int nv = nnodes();
  PointList<3> mshape( nv );

  if (mindex >= 0 and mindex <= 2) {
    for (int i=0; i<nv; ++i)
      mshape[i][mindex] = 1.0;
  } else if (mindex >= 3 and mindex <= 5) {
    Vct3 omega;
    omega[mindex-3] = 1.0;
    for (int i=0; i<nv; ++i)
      mshape[i] = cross(omega, node(i) - rotctr);
  }

  const char rbm[][3] = {"Tx", "Ty", "Tz", "Rx", "Ry", "Rz"};
  string mdname("RigidBodyMode ");
  mdname += rbm[mindex];
  uint fi = appendField(mdname, mshape);
  field(fi).valueClass(MxMeshField::ValueClass::Eigenmode);

  XmlElement xf("Eigenmode");
  xf["modal_mass"] = str(gm);
  xf["modal_stiffness"] = str(gk);
  field(fi).annotate(xf);

  return fi;
}

uint MxMesh::nDimFields(uint nd) const
{
  uint nvf(0);
  const int nf = nfields();
  for (int i=0; i<nf; ++i)
    nvf += ( field(i).ndimension() == nd );
  return nvf;
}

uint MxMesh::findField(const std::string & s) const
{
  const uint nf = nfields();
  for (uint i=0; i<nf; ++i) {
    if (field(i).name() == s)
      return i;
  }

  return NotFound;
}

void MxMesh::findFields(int valClass, Indices &flds) const
{
  for (uint i=0; i<nfields(); ++i) {
    if (field(i).valueClass() == valClass)
      flds.push_back( i );
  }
}

void MxMesh::eraseField(uint k)
{
  if (k != NotFound) {
    fields.erase( fields.begin() + k );
    if (solutionTree() != nullptr)
      solutionTree()->eraseField(k);
  }
}

bool MxMesh::generateMaxFields(bool useMaxAbs)
{
  if (soltree == nullptr)
    return false;
  if (soltree->children() <= 1)
    return false;

  bool success = false;
  for (uint i=0; i<soltree->children(); ++i) {
    MxSolutionTreePtr child = soltree->child(i);

    cout << "Top level child: " << child->name() << endl;

    // stresses as imported from NASTRAN punch file
    if (child->name() == "Stress") {
      MxSolutionTreePtr mxnode = generateMaxFields(child, useMaxAbs);
      if (mxnode->children() > 0 or mxnode->fields().size() > 0) {
        child->append(mxnode);
        success = true;
      }
    }
  }

  return success;
}

MxSolutionTreePtr MxMesh::generateMaxFields(MxSolutionTreePtr root,
                                            bool useMaxAbs)
{
  MxSolutionTreePtr maxnode = MxSolutionTree::create("Maxima");

  // soltree
  // + Displacements
  // | - Displacements 1
  // | - Displacements 2
  // + Stress  <---------- starting here
  //   + Loadcase 1
  //     + Ply 1
  //     | - C|Normal1
  //     | - C|Normal2
  //     | - C|Shear12
  //     | ...
  //     + Ply 2
  //     | - C|Normal1
  //     | ...
  //   + Loadcase 1
  //     + Ply 1
  //     | - C|Normal1
  //     | - C|Normal2
  //     | - C|Shear12
  //     | ...

  VectorArray maxfields;
  StringArray fieldnames;

  if (root->name() == "Stress") {

    // allocate space for max fields
    const int nsub = root->children();
    for (int i=0; i<nsub; ++i) {
      MxSolutionTreePtr pcase = root->child(i);
      const int nply = pcase->children();
      for (int j=0; j<nply; ++j) {
        MxSolutionTreePtr pply = pcase->child(j);
        const Indices & ifields( pply->fields() );
        for (uint kf : ifields) {
          const string & kfield = field( kf ).name();
          auto pos = std::find( fieldnames.begin(), fieldnames.end(), kfield );
          if (pos == fieldnames.end()) {
            const MxMeshField & f( field(kf) );
            if (f.ndimension() != 1)
              continue;
            maxfields.push_back( Vector(f.size()) );
            fieldnames.push_back( kfield );
          }
        }
      }
    }

    cout << "Allocated " << maxfields.size() << " extremal fields." << endl;

    // initialize all fields with impossibly small values
    if (not useMaxAbs) {
      for (Vector &mxa : maxfields)
        mxa = - std::numeric_limits<Real>::max();
    }

    for (int i=0; i<nsub; ++i) {
      MxSolutionTreePtr pcase = root->child(i);
      const int nply = pcase->children();
      for (int j=0; j<nply; ++j) {
        MxSolutionTreePtr pply = pcase->child(j);
        const Indices & ifields( pply->fields() );
        for (uint kf : ifields) {
          const string & kfield = field( kf ).name();
          auto pos = std::find( fieldnames.begin(), fieldnames.end(), kfield );
          if (pos != fieldnames.end()) {
            const MxMeshField & f( field(kf) );
            int idx = std::distance(fieldnames.begin(), pos);
            cout << "Updating " << kfield << " at " << idx << endl;
            if (useMaxAbs)
              f.updateExtremes(maxfields[idx],
                               [&](Real a, Real b)
              {
                return std::max(std::fabs(a),std::fabs(b));
              });
            else
              f.updateExtremes(maxfields[idx],
                               [&](Real a, Real b)
              {
                return std::max(a,b);
              });
          }
        }
      }
    }
  }

  // store results
  assert(maxfields.size() == fieldnames.size());
  string prefix = useMaxAbs ? ("MaxAbs") : ("Max");
  for (size_t i=0; i<fieldnames.size(); ++i) {
    uint fix = appendField(prefix + fieldnames[i], maxfields[i]);
    maxnode->appendField(fix);
  }

  return maxnode;
}

uint MxMesh::findBoco(const std::string & s) const
{
  const uint nb = nbocos();
  for (uint i=0; i<nb; ++i) {
    if (boco(i).name() == s)
      return i;
  }

  return NotFound;
}

uint MxMesh::mappedSection(uint iboco) const
{
  for (uint i=0; i<nsections(); ++i)
    if (section(i).maps(boco(iboco)))
      return i;
  return NotFound;
}

uint MxMesh::containedInSection(uint iboco) const
{
  for (uint i=0; i<nsections(); ++i)
    if (section(i).contains(boco(iboco)))
      return i;
  return NotFound;
}

uint MxMesh::appendTrajectory(const std::string &fn, const Indices &useCols)
{
  MxMeshDeform mdf(this);
  mdf.readPlain(fn, useCols);
  deforms.push_back(mdf);
  deforms.back().buildSpline();
  return deforms.size()-1;
}

uint MxMesh::appendFlutterMode(Complex p, const CpxVector & z, int nsample)
{
  Indices ivf;
  for (uint i=0; i<fields.size(); ++i)
    if (fields[i].ndimension() == 3 or fields[i].ndimension() == 6)
      ivf.push_back(i);
  
  if (ivf.size() != z.size())
    throw Error("MxMesh::appendFlutterMode: Mode count mismatch.");
  
  deforms.push_back( MxMeshDeform(this) );
  deforms.back().fromFlutterMode(ivf, p, z, nsample);
  return deforms.size()-1;
}

void MxMesh::elementSections(const Indices & gix,
                             ConnectMap & s2e) const
{
  s2e.clear();
  const int ne = gix.size();
  s2e.beginCount(nsections());

  for (int i=0; i<ne; ++i) {
    uint isec = findSection(gix[i]);
    assert(isec != NotFound);
    s2e.incCount(isec);
  }
  s2e.endCount();

  for (int i=0; i<ne; ++i) {
    uint isec = findSection(gix[i]);
    s2e.append(isec, gix[i] - section(isec).indexOffset());
  }

  s2e.compress();
}

void MxMesh::merge(const MxMesh & a, bool mergeFieldsByName)
{
  int voff = vtx.size();
  vtx.insert(vtx.end(), a.vtx.begin(), a.vtx.end());

  int eloff = nelements();
  const int ns = a.nsections();
  for (int i=0; i<ns; ++i) {
    const MxMeshSection & t(a.section(i));
    MxMeshSection s(this, t.elementType());
    sections.push_back(s);
    MxMeshSection & sr(sections.back());
    sr.rename(t.name());
    sr.appendElements(t.nodes());
    sr.shiftVertexIndices(voff);
  }
  countElements();

  const int nbc = a.nbocos();
  for (int i=0; i<nbc; ++i) {
    const MxMeshBoco & bc( a.boco(i) );
    MxMeshBoco b( bc );
    b.shiftElementIndices( eloff );
    bocos.push_back(b);
  }

  const size_t nf = nfields();
  if (mergeFieldsByName) {

    // try to match fields even if number of fields does not match
    for (size_t i=0; i<nf; ++i) {
      uint ifx = a.findField( field(i).name() );
      bool mg = (ifx != NotFound);
      if (mg)
        mg &= field(i).merge( a.field(ifx) );
      if (not mg)
        field(i).fitField();
    }

  } else if (nf == a.nfields()) {

    // ignore field names, just merge by index as long as fields
    // are compatible, else extend field with zeros
    for (size_t i=0; i<nf; ++i) {
      bool mg = field(i).merge( a.field(i) );
      if (not mg)
        field(i).fitField();
    }

  } else {

    // fields are not merged by names, and not by index either
    fields.clear();
    deforms.clear();

  }
}

void MxMesh::smoothTetNodes(uint npass, Real omega)
{
  Indices idx;
  const int nsec = nsections();
  {
    std::set<uint> icl, xcl;
    for (int i=0; i<nsec; ++i) {
      const MxMeshSection & sec( section(i) );
      const uint *v = sec.element(0);
      const uint nv = sec.nElementNodes() * sec.nelements();
      if (sec.elementType() == Mx::Tet4)
        icl.insert(v, v+nv);
      else
        xcl.insert(v, v+nv);
    }
    idx.reserve(icl.size());
    std::set_difference(icl.begin(), icl.end(), xcl.begin(), xcl.end(),
                        back_inserter(idx));
  }

  // connectivity
  const int n = idx.size();
  ConnectMap v2t;
  v2t.beginCount(n);
  for (int is=0; is<nsec; ++is) {
    if (section(is).elementType() != Mx::Tet4)
      continue;
    const int ne = section(is).nelements();
    for (int i=0; i<ne; ++i) {
      const uint *v = section(is).element(i);
      for (int k=0; k<4; ++k) {
        const uint mix = sorted_index(idx, v[k]);
        if (mix != NotFound)
          v2t.incCount(mix);
      }
    }
  }
  v2t.endCount();
  for (int is=0; is<nsec; ++is) {
    if (section(is).elementType() != Mx::Tet4)
      continue;
    const int offs = section(is).indexOffset();
    const int ne = section(is).nelements();
    for (int i=0; i<ne; ++i) {
      const uint *v = section(is).element(i);
      for (int k=0; k<4; ++k) {
        const uint mix = sorted_index(idx, v[k]);
        if (mix != NotFound)
          v2t.append(mix, offs+i);
      }
    }
  }
  v2t.compress();

  for (uint ipass=0; ipass<npass; ++ipass) {

    PointList<3> pts(vtx);

    //#pragma omp parallel for
    for (int i=0; i<n; ++i) {
      Vct3 bc;
      Real bvol = 0.0;
      const uint ik = idx[i];
      ConnectMap::const_iterator itr, last = v2t.end(i);
      for (itr = v2t.begin(i); itr != last; ++itr) {
        uint nv, isec;
        const uint *v = globalElement(*itr, nv, isec);
        const Vct3 & p0( vtx[v[0]] );
        const Vct3 & p1( vtx[v[1]] );
        const Vct3 & p2( vtx[v[2]] );
        const Vct3 & p3( vtx[v[3]] );
        Vct3 ctr = 0.25*( p0+p1+p2+p3 );
        Real vol6 = dot(p1-p0, cross(p3-p0, p2-p0));
        bvol += vol6;
        bc += vol6*ctr;
      }
      bc /= bvol;
      pts[ik] = (1.0-omega)*vtx[ik] + omega*bc;
    }
    pts.swap(vtx);
  }
}

uint MxMesh::planeCut(const Plane & p, Indices & ise) const
{
  // determine on which side of p each vertex is located
  std::vector<bool> vbelow;
  nodesBelow(p, vbelow);
  
  // walk through all elements and append to ise when
  // the plane side flag differs between nodes
  uint count(0);
  const int ns = nsections();
  for (int j=0; j<ns; ++j) {
    const MxMeshSection & sec(section(j));
    const int ne = sec.nelements();
    const int nn = sec.nElementNodes();
    const int off = sec.indexOffset();
#pragma omp parallel for
    for (int i=0; i<ne; ++i) {
      const uint *vi = sec.element(i);
      bool cuts(false), first = vbelow[vi[0]];
      for (int k=1; k<nn; ++k)
        cuts |= (vbelow[vi[k]] != first);
      if (cuts) {
#pragma omp critical
        {
          ise.push_back(off + i);
          ++count;
        }
      }
    }
  }
  return count;
}

void MxMesh::nodesBelow(const Plane & p, std::vector<bool> & nbelow) const
{
  const int nv = nnodes();
  nbelow.resize(nv);

#pragma omp parallel for schedule(static,512)
  for (int i=0; i<nv; ++i)
    nbelow[i] = (p.distance(node(i)) <= 0.0);
}


void MxMesh::fixate()
{
  // vertex-element connectivity : counting phase
  v2e.clear();
  v2e.beginCount( nnodes() );
  const int nsec = nsections();
  for (int j=0; j<nsec; ++j) {
    const MxMeshSection & sec( sections[j] );
    const int ne = sec.nelements();
    const int nv = nElementNodes( sec.elementType() );
    for (int i=0; i<ne; ++i) {
      const uint *vi = sec.element(i);
      for (int k=0; k<nv; ++k)
        v2e.incCount( vi[k] );
    }
  }
  v2e.endCount();

  // vertex-element connectivity : assignment phase
  for (int j=0; j<nsec; ++j) {
    const MxMeshSection & sec( sections[j] );
    const int ne = sec.nelements();
    const int nv = nElementNodes( sec.elementType() );
    const uint offset = sec.indexOffset();
    for (int i=0; i<ne; ++i) {
      const uint *vi = sec.element(i);
      for (int k=0; k<nv; ++k)
        v2e.append( vi[k], offset+i );
    }
  }
  v2e.compress();
}

void MxMesh::v2vMap(ConnectMap & v2v) const
{
  assert(v2e.size() == nnodes());

  // conservative estimate for number of neighbor nodes
  v2v.clear();
  v2v.beginCount( nnodes() );
  const int nsec = nsections();
  for (int j=0; j<nsec; ++j) {
    const MxMeshSection & sec( sections[j] );
    const int ne = sec.nelements();
    const int nv = nElementNodes( sec.elementType() );
    for (int i=0; i<ne; ++i) {
      const uint *vi = sec.element(i);
      for (int k=0; k<nv; ++k)
        v2v.incCount( vi[k], nv );
    }
  }
  v2v.endCount();

  // assignemnt, includes duplicates
  for (int j=0; j<nsec; ++j) {
    const MxMeshSection & sec( sections[j] );
    const int ne = sec.nelements();
    const int nv = nElementNodes( sec.elementType() );
    for (int i=0; i<ne; ++i) {
      const uint *vi = sec.element(i);
      for (int ki=0; ki<nv; ++ki) {
        for (int kj=0; kj<nv; ++kj)
          v2v.append( vi[ki], vi[kj] );
      }
    }
  }
  v2v.compress();
}

void MxMesh::e2eMap(ConnectMap & e2e) const
{
  assert(v2e.size() == nnodes());

  const int nsec = nsections();
  e2e.clear();
  e2e.beginCount( nelements() );
  for (int j=0; j<nsec; ++j) {
    const MxMeshSection & sec( sections[j] );
    const int eloff = sec.indexOffset();
    const int ne = sec.nelements();
    const int nv = nElementNodes( sec.elementType() );
    for (int i=0; i<ne; ++i) {
      const uint *vi = sec.element(i);
      for (int k=0; k<nv; ++k)
        e2e.incCount(eloff+i, v2e.size(vi[k]));
    }
  }
  e2e.endCount();

  for (int j=0; j<nsec; ++j) {
    const MxMeshSection & sec( sections[j] );
    const int eloff = sec.indexOffset();
    const int ne = sec.nelements();
    const int nv = nElementNodes( sec.elementType() );
    for (int i=0; i<ne; ++i) {
      const uint *vi = sec.element(i);
      for (int k=0; k<nv; ++k)
        e2e.append(eloff+i, v2e.size(vi[k]), v2e.first(vi[k]));
    }
  }

  e2e.compress();
}

bool MxMesh::containsNodesOf(uint e1, uint e2) const
{
  uint nv1, nv2, isec1, isec2;
  const uint *vi1 = globalElement(e1, nv1, isec1);
  const uint *vi2 = globalElement(e2, nv2, isec2);
  if (vi1 == 0 or vi2 == 0)
    return false;
  for (uint i=0; i<nv2; ++i) {
    if (not std::find(vi1, vi1+nv1, vi2[i]))
      return false;
  }
  return true;
}

uint MxMesh::connectedComponents(Indices &ecmp, bool crossTypes) const
{
  assert(v2e.size() == nnodes());
  const size_t ne = nelements();
  if (ne == 0)
    return 0;

  ecmp.clear();
  ecmp.resize(ne, NotFound);

  std::vector<size_t> queue;
  queue.reserve(4096);
  queue.push_back(0);

  // create a map of element classes first
  // if type crossing is allowed, then the initialization of eclass with
  // zero is sufficien because the test below will always pass
  DVector<int> eclass(ne);
  if (not crossTypes) {
    for (uint i=0; i<nsections(); ++i) {
      int ec = 0;
      if ( section(i).lineElements() )
        ec = 1;
      else if ( section(i).surfaceElements() )
        ec = 2;
      else if ( section(i).volumeElements() )  // volume-surface coupling
        ec = 2;
      size_t offs = section(i).indexOffset();
      for (size_t j=0; j<section(i).nelements(); ++j)
        eclass[offs+j] = ec;
    }
  }

  // as long as there are unreached elements..
  uint ci = 0;
  do {

    // pick next element from queue (assigned to ci)
    size_t eix = queue.back();
    queue.pop_back();

    // put all unassigned elements reachable from eix into queue
    uint isec, nv;
    const uint *vi = globalElement(eix, nv, isec);
    assert(vi != 0);
    for (uint j=0; j<nv; ++j) {
      ConnectMap::const_iterator itr, last = v2e.end(vi[j]);
      for (itr = v2e.begin(vi[j]); itr != last; ++itr) {
        if (ecmp[*itr] == NotFound) {
          if (eclass[eix] == eclass[*itr]) {
            queue.push_back(*itr);
            ecmp[*itr] = ci;
          }
        }
      }
    }

    // if no element is left which is reachable from eix,
    // start a new component
    if (queue.empty()) {
      ++ci;
      for (size_t i=0; i<ne; ++i) {
        if (ecmp[i] == NotFound) {
          queue.push_back(i);
          ecmp[i] = ci;
          break;
        }
      }
    }

  } while (not queue.empty());

  // return number of connected components
  return ci;
}

void MxMesh::reorder(const Indices & perm)
{
  const int nprev = vtx.size();
  const int nperm = perm.size();

  // exchange nodes
  {
    PointList<3> tmp(nperm);
    for (int i=0; i<nperm; ++i)
      tmp[i] = vtx[perm[i]];
    vtx.swap(tmp);
  }

  Indices iperm(nprev, NotFound);
  for (int i=0; i<nperm; ++i)
    iperm[perm[i]] = i;
  for (uint i=0; i<nsections(); ++i)
    section(i).ipreorder(iperm);

  for (uint i=0; i<nfields(); ++i) {
    if (field(i).nodal())
      field(i).reorder(perm);
  }
}

uint MxMesh::dropUnusedNodes()
{
  Indices perm;
  size_t itail = 0;
  const int nsec = sections.size();
  for (int i=0; i<nsec; ++i) {
    const Indices & nds( section(i).nodes() );
    perm.insert(perm.end(), nds.begin(), nds.end());
    itail = unique_merge_tail(itail, perm);
  }

  uint ndrop = vtx.size() - perm.size();
  if (ndrop == 0)
    return 0;

  reorder(perm);
  return ndrop;
}

uint MxMesh::dropDegenerateElements()
{
  uint count = 0;
  for (MxMeshSection &sec : sections)
    count += sec.dropDegenerateElements();
  if (count > 0)
    countElements();
  return count;
}

uint MxMesh::mergeNodes(Real threshold)
{
  Indices repl, keep;
  const uint nov = vtx.size();
  {
    NDPointTree<3,Real> tree;
    tree.allocate(vtx, true, 4);
    tree.sort();
    tree.repldup(threshold, repl, keep);
  }

  {
    size_t nk = keep.size();
    PointList<3> kept(nk);
    for (size_t i=0; i<nk; ++i)
      kept[i] = vtx[keep[i]];
    vtx.swap(kept);
  }

  // apply node index translation to elements
  const uint ndpl = nov - keep.size();
  if (ndpl > 0) {
    Indices perm(nov);
    for (uint i=0; i<nov; ++i)
      perm[repl[i]] = i;
    size_t nedrop = 0;
    for (uint i=0; i<nsections(); ++i) {
      section(i).ipreorder(repl);
      nedrop += section(i).dropCollapsedElements();
    }
    if (nedrop > 0)
      countElements();
    for (uint i=0; i<nfields(); ++i)
      fields[i].reorder(perm);
  }

  // TODO
  // dropCollapsedElements() can delete elements which can be referenced
  // by element-wise fields -> need some sort of renaming of elemental fields

  return ndpl;
}

void MxMesh::countElements()
{
  nelm = 0;
  const int ns = nsections();
  for (int i=0; i<ns; ++i) {
    sections[i].indexOffset(nelm);
    nelm += sections[i].nelements();
  }
}

void MxMesh::assembleVectorFields()
{
  int ik = 3, ifirst = 0, nkill = 0;
  const int nf = fields.size();
  while (ik == 3) {

    // search for vector fields stored by components

    int ixyz[3];

    ik = 0;
    ixyz[0] = ixyz[1] = ixyz[2] = -1;
    string base, fb;
    for (int i=ifirst; i<nf; ++i) {
      const std::string & s( fields[i].name() );
      if (s.empty())
        continue;
      fb = s.substr(0, s.size()-1);
      if (s.find_last_of('X') == s.size()-1) {
        base = fb;
        ixyz[0] = i;
        ik++;
      } else if (s.find_last_of('Y') == s.size()-1 and fb == base) {
        ixyz[1] = i;
        ik++;
      } else if (s.find_last_of('Z') == s.size()-1 and fb == base) {
        ixyz[2] = i;
        ik++;
      }
      if (ik == 3)
        break;
    }

    if (ik == 3) {

      MxMeshField & fx( fields[ixyz[0]] );
      MxMeshField & fy( fields[ixyz[1]] );
      MxMeshField & fz( fields[ixyz[2]] );
      // const Real *px = fx.realPointer();
      // const Real *py = fy.realPointer();
      // const Real *pz = fz.realPointer();

      const size_t nv = fx.size();
      assert(fy.size() == nv);
      assert(fz.size() == nv);
      DVector<Real> px(nv), py(nv), pz(nv);
      fx.fetch(px);
      fy.fetch(py);
      fz.fetch(pz);

      MxMeshField tmp(this, fx.nodal());
      const int np = fx.nodal() ? nnodes() : nelements();
      PointList<3> vf(np);
      for (int i=0; i<np; ++i) {
        vf[i][0] = px[i];
        vf[i][1] = py[i];
        vf[i][2] = pz[i];
      }
      tmp.vectorField(base, vf);
      fx.swap(tmp);

      fy.rename("erase");
      fz.rename("erase");
      nkill += 2;

      // next field to check
      ifirst = ixyz[2]+1;
    }

  }

  // drop duplicate fields
  for (int i=0; i<nf-1; ++i) {
    if (fields[i].name() == "erase") {
      int j = i+1;
      for (; j<nf; ++j) {
        if (fields[j].name() != "erase") {
          fields[i].swap(fields[j]);
          break;
        }
      }
      if (j == nf)
        break;
    }
  }

  fields.erase(fields.end()-nkill, fields.end());
}

float MxMesh::megabytes() const
{
  float mb = 1e-6f*sizeof(MxMesh);
  for (uint i=0; i<nsections(); ++i)
    mb += section(i).megabytes();
  for (uint i=0; i<nfields(); ++i)
    mb += field(i).megabytes();
  for (uint i=0; i<nbocos(); ++i)
    mb += boco(i).megabytes();

  mb += 1e-6f*vtx.capacity()*sizeof(Vct3);
  mb += 1e-6f*v2e.megabytes();
  return mb;
}

int MxMesh::resetBocoColors(int hue, int sat, int val)
{
  Color clr;
  const int nb = nbocos();
  for (int i=0; i<nb; ++i) {
    hue = (hue + 53) % 360;
    clr.hsv2rgb(hue, sat, val);
    boco(i).displayColor(clr);
  }
  return hue;
}

int MxMesh::resetSectionColors(int hue, int sat, int val)
{
  Color clr;
  const int nb = nsections();
  for (int i=0; i<nb; ++i) {
    hue = (hue + 53) % 360;
    clr.hsv2rgb(hue, sat, val);
    section(i).displayColor(clr);
  }
  return hue;
}

