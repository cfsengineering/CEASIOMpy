
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

#include "mxmesh.h"
#include "mxmeshfield.h"
#include "ffanode.h"
#include "transformation.h"
#include "plane.h"
#include "cgnssol.h"

using namespace std;

const char *MxMeshField::ValueClass::s_keylist[11] = {
  "field", "eigenmode", "displacement", "rotation",
  "force", "moment", "fomo", "coefpressure",
  "deltacp", "redcp", "imdcp" };

TypeCode MxMeshField::s_fileFloatPrecision = TypeCode(TypeCode::Float64);

size_t MxMeshField::nalloc() const {
  return bNodal ? parent->nnodes() : parent->nelements();
}   

bool MxMeshField::compatible(const MxMeshField & a) const
{
  if (nodal() != a.nodal())
    return false;
  else if (realField() != a.realField())
    return false;
  else if (ndimension() != a.ndimension())
    return false;
  else if (valueClass() != a.valueClass())
    return false;
  else if (solutionIndex() != a.solutionIndex())
    return false;

  return true;
}

bool MxMeshField::merge(const MxMeshField & a)
{
  if ( not compatible(a) )
    return false;

  if (realField())
    rval.insert(rval.end(), a.rval.begin(), a.rval.end());
  else
    ival.insert(ival.end(), a.ival.begin(), a.ival.end());

  return true;
}

void MxMeshField::transform(const Trafo3d &trafo)
{
  if (not realField())
    return;
  if (ndimension() != 3 and ndimension() != 6)
    return;

  Mtx44 tfm;
  trafo.matrix(tfm);

  if (ndimension() == 3) {
    Vct3 p;
    const size_t nval = rval.size() / ndimension();
    for (size_t i=0; i<nval; ++i) {
      value(i, p);
      Trafo3d::transformDirection(tfm, p);
      setValue(i, p);
    }
  } else if (ndimension() == 6) {

    Vct3 p, rot;
    Trafo3d itraf;
    Mtx44 itfm;
    const int nval = rval.size() / ndimension();
    for (int i=0; i<nval; ++i) {

      // process the translation component
      value(i, p);
      Trafo3d::transformDirection(tfm, p);
      setValue(i, p);

      // rotations
      itraf.identity();
      itraf.rotate(  rval[6*i+3], rval[6*i+4], rval[6*i+5] );
      itraf.matrix(itfm);
      itfm = tfm * itfm;
      itraf.reconstruct(itfm);
      rot = itraf.rotation();
      for (int k=0; k<3; ++k)
        rval[6*i+3+k] = rot[k];
    }
  }
}

void MxMeshField::scale(Real f)
{
  if (not realField())
    return;

  rval *= f;
}

void MxMeshField::erase(size_t begin, size_t end)
{
  // do not crash on files with corrupt data
  if (begin >= size())
    return;
  end = std::min(end, size());
  if (begin >= end)
    return;
  if (realField())
    rval.erase(rval.begin()+begin, rval.begin()+end);
  else
    ival.erase(ival.begin()+begin, ival.begin()+end);
}

void MxMeshField::extend(const Indices &idx)
{
  const size_t n = idx.size();
  if (realField()) {
    for (size_t i=0; i<n; ++i) {
      const Real *vx = &rval[ndim*idx[i]];
      rval.insert(rval.end(), vx, vx+ndim);
    }
  } else {
    for (size_t i=0; i<n; ++i) {
      const int *vx = &ival[ndim*idx[i]];
      ival.insert(ival.end(), vx, vx+ndim);
    }
  }
}

void MxMeshField::extend(const Indices &idx, const Plane &pln)
{
  if ( (not realField()) or (ndim != 3 and ndim != 6) ) {
    extend(idx);
    return;
  }

  Vct3 pn = pln.vector();

  const size_t n = idx.size();
  if (ndim == 3) {
    Vct3 p;
    for (size_t i=0; i<n; ++i) {
      value(idx[i], p);
      p -= 2.0*dot(p, pn)*pn;
      rval.insert(rval.end(), p.begin(), p.end());
    }
  } else if (ndim == 6) {
    Vct6 v;
    Vct3 vr, vt;
    for (size_t i=0; i<n; ++i) {
      value(idx[i], v);
      split_vct(v, vt, vr);
      vt -= 2.0*dot(vt, pn)*pn;
      join_vct(vt, vr, v);
      rval.insert(rval.end(), v.begin(), v.end());
    }
  }
}

void MxMeshField::scalarField(const std::string & s, const DVector<double> & v)
{
  fid = s;
  ndim = 1;
  size_t na = nalloc();
  ival.resize(0);
  rval.resize( ndim*na );
  size_t nval = std::min( na, v.size() );
  memcpy(rval.pointer(), v.pointer(), ndim*nval*sizeof(Vector::value_type));
}

void MxMeshField::scalarField(const std::string & s, const DVector<float> & v)
{
  fid = s;
  ndim = 1;
  size_t na = nalloc();
  ival.resize(0);
  rval.resize( ndim*na );
  std::copy(v.begin(), v.end(), rval.begin());
}

void MxMeshField::scalarField(const std::string & s, const DVector<int> & vi)
{
  fid = s;
  ndim = 1;
  size_t na = nalloc();
  rval.resize(0);
  ival.resize( ndim*na );
  size_t nval = std::min( na, vi.size() );
  memcpy(ival.pointer(), vi.pointer(), ndim*nval*sizeof(int));
}

void MxMeshField::vectorField(const std::string & s, const PointList<3> & v)
{
  fid = s;
  ndim = 3;
  size_t na = nalloc();
  rval.resize( ndim*na );
  size_t nval = std::min( na, (size_t) v.size() );
  memcpy(rval.pointer(), v.pointer(), ndim*nval*sizeof(Real));
}

void MxMeshField::vectorField(const std::string & s,
                              const PointList<3,float> & v)
{
  fid = s;
  ndim = 3;
  size_t na = nalloc();
  rval.resize( ndim*na );
  size_t nval = std::min( na, (size_t) v.size() );
  for (size_t i=0; i<nval; ++i) {
    for (int k=0; k<3; ++k)
      rval[3*i+k] = static_cast<Real>( v[i][k] );
  }
}

void MxMeshField::vectorField(const std::string & s, const PointList<6> & v)
{
  fid = s;
  ndim = 6;
  size_t na = nalloc();
  rval.resize( ndim*na );
  size_t nval = std::min( na, (size_t) v.size() );
  memcpy(rval.pointer(), v.pointer(), ndim*nval*sizeof(Real));
}

void MxMeshField::vectorField(const std::string & s,
                              const PointList<6,float> & v)
{
  fid = s;
  ndim = 6;
  size_t na = nalloc();
  rval.resize( ndim*na );
  size_t nval = std::min( na, (size_t) v.size() );
  for (size_t i=0; i<nval; ++i) {
    for (int k=0; k<6; ++k)
      rval[6*i+k] = static_cast<Real>( v[i][k] );
  }
}


void MxMeshField::fitField(Real t)
{
  int nn = nalloc() * ndimension();
  int nc = std::min(nn, int(size()));

  if (realField()) {
    Vector tmp;
    tmp.allocate(nn);
    copy(rval.begin(), rval.begin()+nc, tmp.begin());
    fill(tmp.begin()+nc, tmp.begin()+nn, t);
    rval.swap(tmp);
  } else {
    DVector<int> tmp;
    tmp.allocate(nn);
    copy(ival.begin(), ival.begin()+nc, tmp.begin());
    fill(tmp.begin()+nc, tmp.begin()+nn, int(t));
    ival.swap(tmp);
  }

  //  if (bNodal) {
  //    const size_t nval = ndim*parent->nnodes();
  //    if (ival.empty()) {
  //      Vector tmp(nval, t);
  //      size_t nbytes = min(nval,rval.size()) * sizeof(Real);
  //      if (nbytes > 0)
  //        memcpy(tmp.pointer(), rval.pointer(), nbytes);
  //      tmp.swap(rval);
  //    } else if (rval.empty()) {
  //      DVector<int> tmp(nval, int(t));
  //      size_t nbytes = min(nval,ival.size()) * sizeof(int);
  //      if (nbytes > 0)
  //        memcpy(tmp.pointer(), ival.pointer(), nbytes);
  //      tmp.swap(ival);
  //    }
  //  }
}

void MxMeshField::condensed(int vfm, DVector<float> & vf) const
{
  assert(realField());
  const int n = (rval.size() / ndim);
  vf.resize(n);
  
  if (ndim == 1) {
    for (int i=0; i<n; ++i)
      vf[i] = float( rval[i] );
    return;
  }
  
  int ic = 0;
  switch (vfm) {
  case 0:
    for (int i=0; i<n; ++i) {
      vf[i] = 0.0f;
      for (int k=0; k<int(ndim); ++k)
        vf[i] += sq( float( rval[i*ndim+k] ) );
      vf[i] = std::sqrt(vf[i]);
    }
    break;
  default:
    ic = vfm - 1;
    for (int i=0; i<n; ++i)
      vf[i] = static_cast<float>( rval[i*ndim+ic] );
    break;
  }
}

void MxMeshField::stats(Real & minval, Real & maxval, Real & meanval) const
{
  minval =  huge;
  maxval = -huge;
  meanval = 0.0;
  
  if (ndim > 1 or (not realField()))
    return;
  
  const int n = rval.size();
  for (int i=0; i<n; ++i) {
    minval = std::min(minval, rval[i]);
    maxval = std::max(maxval, rval[i]);
    meanval += fabs( rval[i] );
  }
  meanval /= n;
}

void MxMeshField::stats(int condensation, Real & minval,
                        Real & maxval, Real & meanval) const
{
  minval = huge;
  maxval = -huge;
  meanval = 0.0;
  
  if (not realField())
    return;
  
  DVector<float> vf;
  condensed(condensation, vf);
  const int n = vf.size();
  for (int i=0; i<n; ++i) {
    minval = std::min(minval, (double) vf[i]);
    maxval = std::max(maxval, (double) vf[i]);
    meanval += fabs( vf[i] );
  }
  meanval /= n;
}

// utility
template <class Sequence>
void reorder_sequence(const Indices & perm, int nd, Sequence & s)
{
  const int n = perm.size();
  Sequence tmp(n*nd);
  for (int i=0; i<n; ++i)
    for (int k=0; k<nd; ++k)
      tmp[i*nd + k] = s[perm[i]*nd + k];
  s.swap(tmp);
}

void MxMeshField::reorder(const Indices & perm)
{
  if (bNodal) {
    if (realField())
      reorder_sequence(perm, ndim, rval);
    else
      reorder_sequence(perm, ndim, ival);
  }
}

string MxMeshField::componentName(uint k) const
{
  // default component names if nothing else is provided
  const std::string cn3[3] = {"X", "Y", "Z"};
  const std::string cn6[6] = {"XX", "XY", "XZ", "YY", "YZ", "ZZ"};

  if (k < ndim) {
    if (k < compNames.size()) {
      return compNames[k];
    } else {
      if (ndim == 3)
        return cn3[k];
      else if (ndim == 6)
        return cn6[k];
      return string("Comp "+str(k+1));
    }
  }
  return string("Undefined");
}

void MxMeshField::componentNames(const std::initializer_list<const char*> &namelist)
{
  if (namelist.size() != ndim)
    throw Error("Number of component names does not match field dimension.");
  compNames.clear();
  compNames.reserve(ndim);
  for (const char *pname : namelist )
    compNames.push_back( string(pname) );
}

BinFileNodePtr MxMeshField::gbfNode(bool share) const
{
  BinFileNodePtr np(new BinFileNode("MxMeshField"));
  np->attribute("content_type", rval.empty() ? "int32" : "float64");
  np->attribute("name", fid);
  np->attribute("nodal_field", bNodal ? "true" : "false");
  np->attribute("dimension", str(ndim));
  if (rval.empty())
    np->assign( ival.size(), &ival[0], share );
  else
    np->assign( rval.size(), &rval[0], share );
  return np;
}

void MxMeshField::fromGbf(const BinFileNodePtr & np, bool digestNode)
{
  fid = np->attribute("name");
  bNodal = np->attribute("nodal_field")  == "true";
  string ctype = np->attribute("content_type");
  if (ctype == "int32") {
    assert(np->blockTypeWidth() == sizeof(int));
    rval.resize(0);
    ival.resize(np->blockElements());
    memcpy(&ival[0], np->blockPointer(), np->blockBytes());
  } else if (ctype == "float64") {
    assert(np->blockTypeWidth() == sizeof(double));
    ival.resize(0);
    rval.resize(np->blockElements());
    memcpy(&rval[0], np->blockPointer(), np->blockBytes());
  } else {
    throw Error("Incompatible field content type in binary file.");
  }
  np->digest(digestNode);
}

XmlElement MxMeshField::toXml(bool share) const
{
  XmlElement xe("MxMeshField");
  xe["name"] = fid;
  xe["nodal_field"] = bNodal ? "true" : "false";
  xe["dimension"] = str(ndim);
  xe["solution_index"] = str(solindex);
  xe["class"] = vclass.str();
  if (not compNames.empty()) {
    for (const string &s : compNames)
      xe.append("ComponentName", s);
  }

  if (rval.empty())
    xe.asBinary(ival.size(), ival.pointer(), share);
  else
    xe.asBinary(rval.size(), rval.pointer(), share);
  
  if (not xnote.name().empty())
    xe.append(xnote);
  
  return xe;
}

void MxMeshField::fromXml(const XmlElement & xe)
{
  fid = xe.attribute("name");
  bNodal = xe.attribute("nodal_field")  == "true";
  ndim = xe.attr2int("dimension", 1);
  string ctype = xe.attribute("bdata_type");
  if (ctype == "Int32") {
    size_t n = genua_strtol(xe.attribute("bdata_bytes").c_str(), 0, 10) / 4;
    ival.resize(n);
    rval.resize(0);
    xe.fetch(n, ival.pointer());
  } else if (ctype == "Float64") {
    size_t n = genua_strtol(xe.attribute("bdata_bytes").c_str(), 0, 10) / 8;
    rval.resize(n);
    ival.resize(0);
    xe.fetch(n, rval.pointer());
  } else {
    throw Error("Incompatible field content type in xml file.");
  }
  
  vclass = ValueClass();
  if (xe.hasAttribute("class"))
    vclass.parse( xe.attribute("class") );

  solindex = xe.attr2int("solution_index", 0);

  compNames.clear();
  for (const auto &child : xe) {
    if (child.name() == "MxNote")
      xnote = child;
    else if (child.name() == "ComponentName")
      compNames.push_back(child.text());
  }
}

bool MxMeshField::fromFFA(const FFANode &node)
{
  rename( node.name() );
  const size_t nv = node.nrows();
  const size_t nd = node.ncols();
  if ( size_t(nv) != nalloc() )
    return false;

  FFADataType tp = node.contentType();
  DVector<float> tmpf;
  DVector<double> tmpd;
  switch ( tp ) {
  case FFAInt4:
    rval.allocate(0);
    ival.allocate(nv*nd);
    ndim = nd;
    node.retrieve( &ival[0] );
    break;
  case FFAFloat4:
    ndim = nd;
    tmpf.allocate(nd*nv);
    node.retrieve(tmpf.pointer());
    ival.allocate(0);
    rval.allocate(nv*nd);
    if (ndim == 1) {
      std::copy(tmpf.begin(), tmpf.end(), rval.begin());
    } else {
      // transposition necessary
      for (size_t i=0; i<nv; ++i)
        for (size_t j=0; j<nd; ++j)
          rval[i*nd+j] = tmpf[j*nv+i];
    }
    break;
  case FFAFloat8:
    ndim = nd;
    tmpd.allocate(nd*nv);
    node.retrieve(tmpd.pointer());
    ival.allocate(0);
    rval.allocate(nv*nd);
    if (ndim == 1) {
      std::copy(tmpd.begin(), tmpd.end(), rval.begin());
    } else {
      // transposition necessary
      for (size_t i=0; i<nv; ++i)
        for (size_t j=0; j<nd; ++j)
          rval[i*nd+j] = tmpd[j*nv+i];
    }
    break;
  default:
    clog << "[w] Cannot handle data type " << tp << " in FFA node: "
         << node.name() << endl;
    return false;
  }

  return true;
}

bool MxMeshField::readBdis(const string &fname)
{
  if (parent == nullptr)
    return false;

  FFANodePtr root = boost::make_shared<FFANode>();
  root->read(fname);
  if (root->name() != "surface_movement")
    return false;

  uint inode = root->findChild("nodes_moving");
  if (inode == NotFound or root->child(inode)->contentType() != FFAInt4)
    return false;

  FFANodePtr node = root->child(inode);
  DVector<int> mappedNodes( node->numel() );
  node->retrieve(&mappedNodes[0]);

  inode = root->findChild("displacement");
  if (inode == NotFound)
    return false;

  node = root->child(inode);
  Matrix disp(node->nrows(), node->ncols());
  node->retrieve(disp.pointer());
  if (disp.nrows() != mappedNodes.size())
    throw Error(".bdis file displacement field does not match index set size.");

  bNodal = true;
  vclass = ValueClass(ValueClass::Eigenmode);
  const size_t np = disp.nrows();
  ndim = disp.ncols();
  if (ndim == 3)
    componentNames({"UX", "UY", "UZ"});
  ival.clear();
  rval.resize( parent->nnodes()*ndim );
  for (size_t j=0; j<np; ++j) {
    uint idx = mappedNodes[j] - 1;
    assert(idx < parent->nnodes());
    for (uint k=0; k<ndim; ++k)
      rval[idx*ndim+k] = disp(j,k);
  }

  // scan for additional information that is not strictly needed, but kept in
  // annotations so that it can be stored again
  XmlElement xbdis("bdis_data");
  const char *surfgroup_names[] = {"moving_surfaces", "sliding_planes",
                                   "fixed_surfaces", "free_surfaces"};
  for (int k=0; k<4; ++k) {
    inode = root->findChild(surfgroup_names[k]);
    if (inode != NotFound) {
      string bname;
      XmlElement xboundaries(surfgroup_names[k]);
      for (const FFANodePtr &node : root->child(inode)->siblings()) {
        if (node->name() == "boundary_name")
          xboundaries.append("boundary_name", bname);
      }
      xbdis.append(std::move(xboundaries));
    }
  }

  inode = root->findChild("nodes_sliding");
  if (inode != NotFound)  {
    node = root->child(inode);
    if (node->contentType() == FFAInt4) {
      DVector<int> nds(node->numel());
      node->retrieve(nds.pointer());
      for (int &idx : nds)
        --idx;
      XmlElement xn("nodes_sliding");
      xn["count"] = str(nds.size());
      xn.asBinary(nds.size(), nds.pointer());
      xbdis.append(std::move(xn));
    }
  }

  inode = root->findChild("mode");
  if (inode != NotFound) {
    XmlElement xmode;
    for (const FFANodePtr &child : root->child(inode)->siblings()) {
      int id;
      double x;
      if (child->numel() == 1) {
        if (child->contentType() == FFAInt4) {
          child->retrieve(id);
          xmode[child->name()] = str(id);
          this->rename("Mode "+str(id));
        } else if (child->contentType() == FFAFloat8) {
          child->retrieve(x);
          xmode[child->name()] = str(x);
        }
      }
    }
    xbdis.append(std::move(xmode));
  }

  annotate(xbdis);
  return true;
}

bool MxMeshField::writeBdis(const string &fname) const
{
  if ((ndim < 3) or (not bNodal))
    return false;

  XmlElement::const_iterator itn = note().findChild("bdis_data");
  if (itn == note().end())
    return false;

  const XmlElement &xbdis(*itn);
  XmlElement::const_iterator itr = xbdis.findChild("nodes_moving");
  if (itr == xbdis.end())
    return false;

  DVector<int> mappedNodes(itr->attr2int("count", 0));
  itr->fetch(mappedNodes.size(), mappedNodes.pointer());

  // transpose displacements
  Vct3 ui;
  Matrix disp(mappedNodes.size(), 3);
  for (size_t i=0; i<mappedNodes.size(); ++i) {
    this->value(mappedNodes[i], ui);
    for (int k=0; k<3; ++k)
      disp(i, k) = ui[k];
  }

  // shift indices for fortran
  for (int &idx : mappedNodes)
    ++idx;

  FFANodePtr root = boost::make_shared<FFANode>("surface_movement");
  root->append("nodes_moving", mappedNodes.size(), 1, mappedNodes.pointer());
  root->append("displacement", disp.nrows(), disp.ncols(), disp.pointer());

  const char *surfgroup_names[] = {"moving_surfaces", "sliding_planes",
                                   "fixed_surfaces", "free_surfaces"};

  // add optional data which is stored in annotation
  for (const XmlElement &child : xbdis) {

    if (child.name() == "nodes_sliding") {
      DVector<int> nds( child.attr2int("count", 0) );
      child.fetch(nds.size(), nds.pointer());
      if (nds.size() > 0)
        root->append("nodes_sliding", nds.size(), 1, nds.pointer());
      continue;
    } else if (child.name() == "mode") {
      FFANodePtr node = root->append(FFANode::create("mode"));
      XmlElement::attr_iterator alast = child.attrEnd();
      for (XmlElement::attr_iterator atr = child.attrBegin();
           atr != alast; ++atr)
      {
        if (atr->first == "identifier")
          node->append(atr->first, std::stoi(atr->second));
        else
          node->append(atr->first, std::stod(atr->second));
      }
    }

    for (int k=0; k<4; ++k) {
      if (child.name() == surfgroup_names[k]) {
        FFANodePtr node = root->append(FFANode::create(surfgroup_names[k]));
        for (const XmlElement &gchild : child) {
          if (gchild.name() == "boundary_name")
            node->append("boundary_name", gchild.text());
        }
      }
    }
  }

  root->write( append_suffix(fname, ".bdis") );
  return true;
}

//#ifdef HAVE_CGNS

bool MxMeshField::readCgns(CgnsSol & sol, int i)
{
  size_t nval(0);
  if (sol.location() == cgns::Vertex)
    nval = parent->nnodes();
  else if (sol.location() == cgns::CellCenter)
    nval = parent->nelements();
  else
    return false;

  int imin(1), imax(nval);
  cgns::DataType_t dtype;
  sol.fieldInfo(i, fid, dtype);
  if (dtype == cgns::RealDouble or dtype == cgns::RealSingle) {
    ival.resize(0);
    rval.resize(nval);
    sol.readField(fid.c_str(), imin, imax, rval.pointer());
  } else if (dtype == cgns::Integer) {
    ival.resize(nval);
    rval.resize(0);
    sol.readField(fid.c_str(), imin, imax, ival.pointer());
  } else {
    return false;
  }

  return true;
}

void MxMeshField::writeCgns(CgnsSol & sol) const
{
  if (ndim == 1) {
    if (not rval.empty())
      sol.writeField(fid, rval.pointer(), cgns::RealDouble);
    else if (not ival.empty())
      sol.writeField(fid, ival.pointer());
  } else if (ndim == 3) {
    const char sfx[] = "XYZ";
    const int n = parent->nnodes();
    Vector tmp(n);
    for (int k=0; k<3; ++k) {
      tmp = 0.0;
      for (int i=0; i<n; ++i)
        tmp[i] = rval[3*i+k];
      sol.writeField(fid+sfx[k], tmp.pointer(), cgns::RealDouble);
    }
  } else {
    const int n = parent->nnodes();
    Vector tmp(n);
    for (int k=0; k<int(ndim); ++k) {
      for (int i=0; i<n; ++i)
        tmp[i] = rval[ndim*i+k];
      sol.writeField(fid+str(k+1), tmp.pointer(), cgns::RealDouble);
    }
  }
}

//#endif

XmlElement MxMeshField::toVTK(const Indices & ipts) const
{
  XmlElement xe("DataArray");
  xe["Name"] = fid;
  if (not rval.empty())
    xe["type"] = "Float64";
  else if (not ival.empty())
    xe["type"] = "Int32";
  xe["format"] = "ascii";
  xe["NumberOfComponents"] = str(ndim);
  
  if (not rval.empty()) {
    if (ipts.size() == rval.size()) {
      xe.array2text(rval.size(), rval.pointer());
    } else {
      const int np = ipts.size();
      Vector tmp(np*ndim);
      for (int i=0; i<np; ++i)
        for (int k=0; k<int(ndim); ++k)
          tmp[i*ndim+k] = rval[ndim*ipts[i] + k];
      xe.array2text(tmp.size(), tmp.pointer());
    }
  } else if (not ival.empty()) {
    if (ipts.size() == ival.size()) {
      xe.array2text(ival.size(), ival.pointer());
    } else {
      const int np = ipts.size();
      DVector<int> tmp(np);
      for (int i=0; i<np; ++i)
        tmp[i] = ival[ipts[i]];
      xe.array2text(tmp.size(), tmp.pointer());
    }
  }
  
  return xe;
}
