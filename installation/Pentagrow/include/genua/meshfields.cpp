
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
 
#include "triangulation.h"
#include "trimesh.h"
#include "meshfields.h"

using namespace std;

// ---------------------------------- file-scope stuff ---------------------

inline static uint string2coords(const string & s, PointList<3> & pts)
{
  uint nread(0);
  stringstream ss;
  ss << s;
  Vct3 vf;
  while (ss >> vf[0] >> vf[1] >> vf[2]) {
    pts.push_back(vf);
    ++nread;
  }
  return nread;
}

inline static uint string2vector(const string & s, Vector & v)
{
  uint nread(0);
  stringstream ss;
  ss << s;
  Real x;
  while (ss >> x) {
    v.push_back(x);
    ++nread;
  }
  return nread;
}

inline static uint findName(const StringArray & names, const string & s)
{
  StringArray::const_iterator pos;
  pos = std::find(names.begin(), names.end(), s);
  if (pos != names.end())
    return std::distance(names.begin(), pos);
  else
    return NotFound;
} 

// --------------------------------------------------------------------------

uint MeshFields::addVertex(const Vct3 & v)
{
  assert(std::isfinite(dot(v,v)));
  vtx.push_back(v);
  return vtx.size()-1;
}

void MeshFields::addVertices(const PointList<3> & v)
{
  vtx.insert(vtx.end(), v.begin(), v.end());
}

uint MeshFields::addNormal(const Vct3 & v)
{
  nrm.push_back(v);
  return nrm.size()-1;
}

uint MeshFields::addMarker(uint ipos)
{
  fpt.push_back(ipos);
  return fpt.size()-1;
}

uint MeshFields::addMarker(const PointList<3> & pts)
{
  const uint off = vtx.size();
  const int nm = pts.size();
  vtx.insert(vtx.end(), pts.begin(), pts.end());
  for (int i=0; i<nm; ++i)
    fpt.push_back(off+i);
  return fpt.size()-1;
}

uint MeshFields::addLine2(uint a, uint b)
{
  assert( a < vtx.size() );
  assert( b < vtx.size() );
  fline2.push_back(a);
  fline2.push_back(b);
  return fline2.size() / 2 - 1;
}

void MeshFields::addLine2(const PointList<3> & polyline)
{
  uint voff = vtx.size();
  uint nv = polyline.size();
  addVertices( polyline );
  for (uint i=0; i<nv-1; ++i)
    addLine2( voff+i, voff+i+1 );
}

uint MeshFields::addTri3(const uint *vix)
{
  ftri3.insert(ftri3.end(), vix, vix+3);
  return ftri3.size() / 3 - 1;
}

uint MeshFields::addTri3(uint a, uint b, uint c)
{
  assert( a < vtx.size() );
  assert( b < vtx.size() );
  assert( c < vtx.size() );
  uint vix[3];
  vix[0] = a;
  vix[1] = b;
  vix[2] = c;
  ftri3.insert(ftri3.end(), vix, vix+3);
  return ftri3.size() / 3 - 1;
}

uint MeshFields::addQuad4(const uint *vix)
{
  fquad4.insert(fquad4.end(), vix, vix+4);
  return fquad4.size() / 4 - 1;
}

uint MeshFields::addQuad4(uint a, uint b, uint c, uint d)
{
  uint vix[4];
  vix[0] = a;
  vix[1] = b;
  vix[2] = c;
  vix[3] = d;
  fquad4.insert(fquad4.end(), vix, vix+4);
  return fquad4.size() / 4 - 1;
}
    
void MeshFields::addMesh(const Triangulation & t)
{
  const uint voff(vtx.size());
  const uint nv(t.nvertices());
  for (uint i=0; i<nv; ++i) {
    addVertex(t.vertex(i));
    addNormal(t.normal(i));
  }

  uint vi[3];
  Triangulation::face_iterator itf;
  for (itf = t.face_begin(); itf != t.face_end(); ++itf) {
    itf->getVertices(vi);
    vi[0] += voff;
    vi[1] += voff;
    vi[2] += voff;
    addTri3(vi);
  }
}

void MeshFields::addMesh(const TriMesh & t)
{
  const uint voff(vtx.size());
  
  // copy mesh
  Indices tri;
  PointList<3> tv, tn;
  t.exportMesh(tv, tn, tri);
  vtx.insert(vtx.end(), tv.begin(), tv.end());
  nrm.insert(nrm.end(), tn.begin(), tn.end());
  
  // create triangles with offsets
  const uint nnt(tri.size());
  for (uint i=0; i<nnt; ++i)
    tri[i] += voff;

  uint trioff = ftri3.size()/3;
  ftri3.insert(ftri3.end(), tri.begin(), tri.end());

  // tag components
  if (fquad4.empty()) {
    Indices tags( ftri3.size()/3 );
    fill(tags.begin(), tags.end(), 0);
    const int nf = t.nfaces();
    for (int i=0; i<nf; ++i) {
      tags[trioff+i] = t.face(i).tag(); 
    }
    addComponentSet("Mesh tags", tags);
  }
}

void MeshFields::addMesh(const PointGrid<3> & pg)
{
  PointGrid<3> empty;
  addMesh(pg, empty);
}

void MeshFields::addMesh(const PointGrid<3> & pg, const PointGrid<3> & ng) 
{
  // copy vertices and normals (if present)
  uint offset = vtx.size();
  vtx.insert(vtx.end(), pg.begin(), pg.end());
  if (ng.size() == pg.size())
    nrm.insert(nrm.end(), ng.begin(), ng.end());
  else
    nrm.clear();
  
  uint qv[4];
  uint a, b, ld = pg.nrows();
  for (uint i=0; i<pg.nrows()-1; ++i) {
    for (uint j=0; j<pg.ncols()-1; ++j) {
      a = j*ld + i;
      b = (j+1)*ld + i;
      qv[0] = offset + a;
      qv[1] = offset + a+1;
      qv[2] = offset + b+1;
      qv[3] = offset + b;
      fquad4.insert(fquad4.end(), qv, qv+4);
    }
  }
}

uint MeshFields::addField(const std::string & fname, const Vector & values)
{
  // expand vector to mesh size
  const uint nval = values.size();
  const uint nv = nvertices();
  Vector vexp(nv);
  memcpy(&vexp[0], &values[0], min(nv,nval)*sizeof(Vector::value_type));
  
  uint idx = findName(sfield, fname);
  if (idx == NotFound) {
    sfield.push_back(fname);
    vfield.push_back(vexp);
    return vfield.size()-1;
  } else {
    sfield[idx] = fname;
    vfield[idx] = vexp;
    return idx;
  }
}

uint MeshFields::addVectorField(const std::string & fname, 
                                const PointList<3> & values)
{
  // expand vector to mesh size
  const uint nval = values.size();
  const uint nv = nvertices();
  PointList<3> vexp(nv);
  memcpy(&vexp[0], &values[0], min(nv,nval)*sizeof(Vct3));
  
  uint idx = findName(vecfnames, fname);
  if (idx == NotFound) {
    vecfnames.push_back(fname);
    vecfields.push_back(vexp);
    return vfield.size()-1;
  } else {
    vecfnames[idx] = fname;
    vecfields[idx] = vexp;
    return idx;
  }
}

uint MeshFields::addComponentSet(const std::string & fname, const Indices & cmp)
{
  const uint nv = ntri3()+nquad4();
  const uint nval = cmp.size();
  Indices cmpx(nv);
  fill(cmpx.begin(), cmpx.end(), 0);
  memcpy(&cmpx[0], &cmp[0], min(nv,nval)*sizeof(Indices::value_type));
  
  uint idx = findName(scomp, fname);
  if (idx == NotFound) {
    scomp.push_back(fname);
    icomp.push_back(cmp);
    return icomp.size()-1;
  } else {
    scomp[idx] = fname;
    icomp[idx] = cmp;
    return idx;
  }
  
}

uint MeshFields::addModeShape(const std::string & sname, const PointList<6> & shape)
{
  const uint nv(vtx.size());
  if (shape.size() != nv)
    throw Error("MeshFields::addModeShape - Eigenmode not compatible with mesh.");
    
  uint idx = findName(modenames, sname);
  if (idx == NotFound) {
    modenames.push_back(sname);
    mds.push_back(PointList<3>());
    PointList<3> & sf(mds.back());
    sf.resize(vtx.size());
    for (uint i=0; i<shape.size(); ++i) {
      sf[i][0] = shape[i][0];
      sf[i][1] = shape[i][1];
      sf[i][2] = shape[i][2];
    }
    return mds.size()-1;
  } else {
    assert(idx < mds.size());
    modenames[idx] = sname;
    PointList<3> & sf(mds[idx]);
    sf.resize(nv);
    for (uint i=0; i<nv; ++i) {
      sf[i][0] = shape[i][0];
      sf[i][1] = shape[i][1];
      sf[i][2] = shape[i][2];
    }
    return idx;
  }
}

uint MeshFields::addModeShape(const std::string & sname, const PointList<3> & shape)
{
  const uint nv(vtx.size());
  if (shape.size() != nv)
    throw Error("MeshFields::addModeShape - Eigenmode not compatible with mesh.");
  
  uint idx = findName(modenames, sname);
  if (idx == NotFound) {
    modenames.push_back(sname);
    mds.push_back(shape);
    return mds.size()-1;
  } else {
    assert(idx < mds.size());
    modenames[idx] = sname;
    mds[idx] = shape;
    return idx;
  }
}

uint MeshFields::addModeShape(const std::string & sname, const Matrix & shape)
{
  const uint nv(vtx.size());
  if (shape.nrows() != nv)
    throw Error("MeshFields::addModeShape - Eigenmode not compatible with mesh.");
    
  uint idx = findName(modenames, sname);
  if (idx == NotFound) {
    modenames.push_back(sname);
    mds.push_back(PointList<3>());
    PointList<3> & sf(mds.back());
    sf.resize(nv);
    for (uint i=0; i<nv; ++i) {
      sf[i][0] = shape(i,0);
      sf[i][1] = shape(i,1);
      sf[i][2] = shape(i,2);
    }
    return mds.size()-1;
  } else {
    assert(idx < mds.size());
    modenames[idx] = sname;
    PointList<3> & sf(mds[idx]);
    sf.resize(nv);
    for (uint i=0; i<nv; ++i) {
      sf[i][0] = shape(i,0);
      sf[i][1] = shape(i,1);
      sf[i][2] = shape(i,2);
    }
    return idx;
  }
}

uint MeshFields::addNamedShape(const std::string & fname, const Vector & values)
{
  uint idx = findName(sshape, fname);
  if (idx == NotFound) {
    sshape.push_back(fname);
    nshape.push_back(values);
    return nshape.size()-1;
  } else {
    nshape[idx] = values;
    return idx;
  }
}

uint MeshFields::addTrajectory(const std::string & tname, const Matrix & m)
{
  uint ndof = m.ncols();
  if (ndof < 13)
    throw Error("Trajectory matrix must contain at least 13 columns.");
  
  uint idx = findName(tjnames, tname);
  if (idx == NotFound) {
    tjnames.push_back(tname);
    traject.push_back(m);
    return traject.size()-1;
  } else {
    assert(idx < traject.size());
    traject[idx] = m;
    return idx;
  }
}

void MeshFields::mergePayload(const MeshFields & a)
{
  if (a.nvertices() != nvertices())
    throw Error("MeshFields::mergePayload() - Different node count, cannot merge data.");

  // add fields
  if (a.nfields() > 0) {
    sfield.insert(sfield.end(), a.sfield.begin(), a.sfield.end());
    vfield.insert(vfield.end(), a.vfield.begin(), a.vfield.end());
  }

  // add eigenmodes
  if (a.nmodes() > 0) {
    modenames.insert(modenames.end(),
                     a.modenames.begin(), a.modenames.end() );
    mds.insert(mds.end(), a.mds.begin(), a.mds.end());
  }

  // add named shapes
  if (a.nshapes() > 0) {
    sshape.insert(sshape.end(), a.sshape.begin(), a.sshape.end());
    nshape.insert(nshape.end(), a.nshape.begin(), a.nshape.end());
  }
}
    
void MeshFields::clear()
{
  *this = MeshFields();
}

XmlElement MeshFields::toXml() const
{
  XmlElement xe("MeshViz");
  if (csname != "")
    xe.attribute("case") = csname;
  
  XmlElement xv("Nodes");
  stringstream ss;
  ss.precision(16);
  ss << scientific;
  uint nv = vtx.size();
  for (uint i=0; i<nv; ++i)
    ss << vtx[i] << endl;
  xv.text(ss.str());
  ss.str("");
  xe.append(std::move(xv));

  if (nrm.size() == nv) {
    XmlElement xn("Normals");
    for (uint i=0; i<nv; ++i)
      ss << nrm[i] << endl;
    xn.text(ss.str());
    ss.str("");
    xe.append(std::move(xn));
  }

  const uint npm(fpt.size());
  const uint nl2(nline2());
  const uint nt3(ftri3.size()/3);
  const uint nq4(fquad4.size()/4);

  if (npm > 0) {
    XmlElement xf("Elements");
    xf.attribute("type") = "ptmarker";
    for (uint i=0; i<npm; ++i)
      ss << fpt[i] << endl;
    xf.text(ss.str());
    ss.str("");
    xe.append(std::move(xf));
  }

  if (nl2 > 0) {
    XmlElement xf("Elements");
    xf.attribute("type") = "line2";
    for (uint i=0; i<nl2; ++i)
      ss << fline2[2*i] << " " << fline2[2*i+1] << endl;
    xf.text(ss.str());
    ss.str("");
    xe.append(std::move(xf));
  }
  
  if (nt3 > 0) {
    XmlElement xf("Elements");
    xf.attribute("type") = "tri3";
    for (uint i=0; i<nt3; ++i)
      ss << ftri3[3*i] << " " << ftri3[3*i+1] << " "
         << ftri3[3*i+2] << endl;
    xf.text(ss.str());
    ss.str("");
    xe.append(std::move(xf));
  }

  if (nq4 > 0) {
    XmlElement xf("Elements");
    xf.attribute("type") = "quad4";
    for (uint i=0; i<nq4; ++i)
      ss << fquad4[4*i] << " " << fquad4[4*i+1] << " "
          << fquad4[4*i+2] << " " << fquad4[4*i+3] << endl;
    xf.text(ss.str());
    ss.str("");
    xe.append(std::move(xf));
  }

  // write modeshapes, if present
  if (!mds.empty()) {
    assert(mds.size() == modenames.size());
    XmlElement xmds("EigenModes");
    xmds["count"] = str(mds.size());
    for (uint i=0; i<mds.size(); ++i) {
      XmlElement xmode("EigenModeShape");
      xmode["index"] = str(i);
      xmode["id"] = modenames[i];
      assert(mds[i].size() == nv);
      for (uint j=0; j<nv; ++j)
        ss << mds[i][j] << endl;
      xmode.text(ss.str());
      ss.str("");
      xmds.append(std::move(xmode));
    }

    // write named deformation shapes
    assert(sshape.size() == nshape.size());
    for (uint i=0; i<nshape.size(); ++i) {
      XmlElement xns("NamedShape");
      xns.attribute("name") = sshape[i];
      xns.array2text(nshape[i].size(), nshape[i].pointer());
      xmds.append(std::move(xns));
    }

    xe.append(std::move(xmds));
  }

  for (uint j=0; j<vfield.size(); ++j) {

    XmlElement xvf("Field");
    xvf.attribute("name") = sfield[j];

    const Vector & val(vfield[j]);
    uint nfv = val.size();
    uint top = 6*(nfv/6);
    for (uint i=0; i<top; i+=6) {
      ss << val[i] << " " << val[i+1] << " " << val[i+2] << " ";
      ss << val[i+3] << " " << val[i+4] << " " << val[i+5];
      ss << endl;
    }
    for (uint i=top; i<nfv; ++i)
      ss << " " << val[i];
    ss << endl;
    xvf.text(ss.str());
    xe.append(std::move(xvf));
    ss.str("");
  }
  
  const uint nvf(vecfields.size());
  for (uint j=0; j<nvf; ++j) {
    XmlElement xvf("VectorField");
    xvf["name"] = vecfnames[j];
    ss << vecfields[j];
    xvf.text( ss.str() );
    xe.append(std::move(xvf));
    ss.str("");
  }
  
  const int nc(icomp.size());
  for (int j=0; j<nc; ++j) {
    XmlElement xcf("ComponentSet");
    xcf.attribute("name") = scomp[j];
    const Indices & idx(icomp[j]);
    const int ncv(idx.size());
    const int top = 16*(ncv/16);
    for (int i=0; i<top; i+=16) {
      for (int k=0; k<16; ++k)
        ss << " " << idx[i+k];
      ss << endl;
    }
    for (int i=top; i<ncv; ++i)
      ss << " " << idx[i];
    ss << endl;
    xcf.text(ss.str());
    xe.append(xcf);
    ss.str("");
  }
  
  const int ntj(traject.size());
  for (int j=0; j<ntj; ++j) {
    XmlElement xtj("Trajectory");
    xtj["name"] = tjnames[j];
    xtj["ndof"] = str(traject[j].ncols());
    xtj["nstep"] = str(traject[j].nrows());
    ss << traject[j];
    xtj.text( ss.str() );
    xe.append(xtj);
    ss.str("");
  }
  
  return xe;
}

void MeshFields::fromXml(const XmlElement & xe)
{
  if (xe.name() != "MeshViz")
    throw Error("MeshFields::fromXml() - Incompatible XML representation: "
                +xe.name());

  if (xe.hasAttribute("case"))
    name(xe.attribute("case"));
  
  clear();
  XmlElement::const_iterator ite;
  for (ite = xe.begin(); ite != xe.end(); ++ite) {
    stringstream ss;
    ss << ite->text();
    if (ite->name() == "Nodes") {
      Vct3 vf;
      while (ss >> vf)
        vtx.push_back(vf);
    } else if (ite->name() == "Normals") {
      Vct3 vf;
      while (ss >> vf)
        nrm.push_back(vf);
    } else if (ite->name() == "Elements") {
      string etype = ite->attribute("type");
      if (etype == "tri3" or etype == "TRI3") {
        uint vix[3];
        while (ss >> vix[0] >> vix[1] >> vix[2])
          ftri3.insert(ftri3.end(), vix, vix+3);
      } else if (etype == "quad4" or etype == "QUAD4") {
        uint vix[4];
        while (ss >> vix[0] >> vix[1] >> vix[2] >> vix[3])
          fquad4.insert(fquad4.end(), vix, vix+4);
      } else if (etype == "line2" or etype == "LINE2") {
        uint vix[2];
        while (ss >> vix[0] >> vix[1])
          fline2.insert(fline2.end(), vix, vix+2);
      } else if (etype == "ptmarker" or etype == "PTMARKER") {
        uint vi;
        while (ss >> vi)
          fpt.push_back(vi);
      } else
        throw Error("MeshFields::fromXml() - Unknown element type: "+etype);
    } else if (ite->name() == "Field") {
      
      Real v;
      Vector tmp;
      while (ss >> v)
        tmp.push_back(v);
      addField(ite->attribute("name"), tmp);
    
    } else if (ite->name() == "VectorField") {
      
      Vct3 v;
      PointList<3> tmp;
      while (ss >> v)
        tmp.push_back(v);
      addVectorField(ite->attribute("name"), tmp);
    
    } else if (ite->name() == "ComponentSet") {
      
      uint v;
      Indices tmp;
      while (ss >> v)
        tmp.push_back(v);
      addComponentSet(ite->attribute("name"), tmp);
      
    } else if (ite->name() == "EigenModes") {
      mds.resize(Int(ite->attribute("count")));
      modenames.resize(mds.size());
      XmlElement::const_iterator imode;
      ss.str("");
      for (imode = ite->begin(); imode != ite->end(); ++imode) {
        if (imode->name() == "EigenModeShape") {
          uint midx = Int(imode->attribute("index"));
          if (imode->hasAttribute("id"))
            modenames[midx] = imode->attribute("id");
          else
            modenames[midx] = "Eigenmode " + str(midx+1);
          mds[midx].reserve(vtx.size());
          uint nread = string2coords(imode->text(), mds[midx]);
          if (nread != vtx.size()) {
            string msg("MeshFields::fromXml - Modeshape is not compatible with mesh.");
            msg += "\nHave " + str(vtx.size()) + " nodes, found " + str(nread);
            msg += " displacement values for '" + modenames[midx] + "'.";
            throw Error(msg);
          }
        } else if (imode->name() == "NamedShape") {
          sshape.push_back(imode->attribute("name"));
          nshape.push_back(Vector());
          string2vector(imode->text(), nshape.back());
        }
      }
    } else if (ite->name() == "Trajectory") {
      string s = ite->attribute("name");
      uint ndof = Int(ite->attribute("ndof"));
      uint nstep = Int(ite->attribute("nstep"));
      Matrix m(nstep, ndof);
      ss.str( ite->text() );
      for (uint i=0; i<nstep; ++i) {
        for (uint j=0; j<ndof; ++j) {
          ss >> m(i,j);
          if (not ss) {
            stringstream sm;
            sm << "Trajectory size mismatch. ";
            sm << "Expected " << nstep << " time steps width " << ndof
               << " states, stopped at " << i+1 << " steps." << endl;
            throw Error(sm.str()); 
          }
        }
      }
      tjnames.push_back(s);
      traject.push_back(m);
    }
  }

  // after reading everyting, check the correct dimensions of NamedShapes
  for (uint i=0; i<nshape.size(); ++i) {
    if (nshape[i].size() < mds.size()) {
//       string msg("MeshFields::fromXml - Named shape not compatible with modal subspace.");
//       msg += "\nShape vector named '" + shapename(i) + "' has " + str(nshape[i].size());
//       msg += " elements, while subspace size is " + str(mds.size()) + ".";
//       throw Error(msg);
         
      // fill up with zeros
      Vector tmp(mds.size());
      memcpy(tmp.pointer(), nshape[i].pointer(), nshape[i].size()*sizeof(Real));
      nshape[i].swap(tmp);
    }
  }
}




