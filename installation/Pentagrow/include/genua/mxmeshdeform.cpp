
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
 
#include "ioglue.h"
#include "xcept.h"
#include "pattern.h"
#include "rbrotation.h"
#include "mxmesh.h"
#include "mxmeshdeform.h"

using std::string;

// construct rotation matrix for rigid-body motion
//
// assumes x[3,4,5] = [phi, theta, psi] 
inline static void rbrotation(const Real x[], Mtx33 & r)
{
  Real xp[3] = {x[3], x[4], x[5]};
  rbrotation(xp, r.pointer());
}

void MxMeshDeform::elasticOffset()
{
  // figure out the elastic displacement offset
  int nc = bpcoef.nrows();
  int ne = isub.size();
  if (nc == ne)
    moffset = 0;
  else if (nc == 2*ne)
    moffset = 0;
  else if (nc == ne+12)
    moffset = 12;
  else if (nc == 2*ne+12)
    moffset = 12;
  else if (nc == ne+6)
    moffset = 6;
  else if (nc == 2*ne+6)
    moffset = 6;
  else
    throw Error("MxMeshDeform : Cannot determine first elastic state index offset.");
  
  // check if the displacement fields are where they should be
  const int nm = isub.size();
  for (int j=0; j<nm; ++j) {
    uint jm = isub[j];
    if (jm > parent->nfields())
      throw Error("MxMeshDeform : No such mode: "+str(jm));
    const MxMeshField & f(parent->field(jm));
    if (f.ndimension() < 3)
      throw Error("MxMeshDeform : "
          "Not a displacement mode:  "+str(jm));
  }
}

void MxMeshDeform::setDeformation(const Indices & im, const Vector & t, 
                                  const Matrix & tdef)
{
  isub = im; 
  bptime = t; 
  bpcoef = tdef;
  
  elasticOffset();
}

bool MxMeshDeform::interpolateSubspace(Real t, Vector & dss) const
{
  assert(spl.getKnots().size() > 1);
  
  Vct4 b;
  Real to = bptime.front();
  Real tn = bptime.back();
  Real s = (t - to) / (tn - to);
  s -= int(s);
  int span = spl.eval(s, b) - 3;
  
  int nm = cpcoef.ncols();
  dss.resize(nm);
  dss = 0.0;
  for (int j=0; j<nm; ++j) {
    dss[j] = 0.0;
    for (int i=0; i<4; ++i)
      dss[j] += b[i] * cpcoef(span+i,j);
  }

  return (t <= tn);
}

bool MxMeshDeform::interpolateSubspace(Real t, Vector & x,
                                       Vector & xd, Vector & xdd) const
{
  assert(spl.getKnots().size() > 1);

  SMatrix<3,4> b;
  Real to = bptime.front();
  Real tn = bptime.back();
  Real idt = 1.0 / (tn - to);
  Real s = (t - to)*idt;
  s -= int(s);
  int span = spl.derive(s, b) - 3;

  int nm = cpcoef.ncols();
  x.allocate(nm);
  xd.allocate(nm);
  xdd.allocate(nm);
  for (int j=0; j<nm; ++j) {
    x[j] = xd[j] = xdd[j] = 0.0;
    for (int i=0; i<4; ++i) {
      x[j]   += b(0,i) * cpcoef(span+i,j);
      xd[j]  += b(1,i) * cpcoef(span+i,j);
      xdd[j] += b(2,i) * cpcoef(span+i,j);
    }
    xd[j] *= idt;
    xdd[j] *= sq(idt);
  }

  return (t <= tn);
}

void MxMeshDeform::writeTable(uint tid, uint npoints, uint imode,
                              std::ostream & os) const
{
#undef NZNSTR
#define NZNSTR(x)  nstr( (fabs((x)) > 1e-9) ? (x) : 0.0 )

  assert(imode < nmodes());
  os << "TABLED1, " << tid << ", LINEAR, LINEAR" << endl << ", ";
  Real dt = duration() / (npoints - 1);
  Vector x(nmodes());
  for (uint i=0; i<npoints; ++i) {
    Real t = i*dt;
    interpolateSubspace(t, x);
    os << nstr(t) << ", " << NZNSTR(x[imode]) << ", ";
    if ((i+1)%4 == 0)
      os << endl << ", ";
  }
  os << "ENDT" << endl;

#undef NZNSTR
}

void MxMeshDeform::deformElastic(Real scale, const Vector & dss,
                                 PointList<3> & vdef) const
{
  // copy undeformed vertices
  vdef = parent->nodes();
  
  // do nothing if there are no elastic modes
  if (uint(moffset) >= dss.size())
    return;

  // assemble displacement vector
  // const Real *rp;
  const Real *mx = &dss[moffset];
  const int nn = parent->nnodes();
  const int nm = isub.size();
  for (int j=0; j<nm; ++j) {
    const MxMeshField & mfield( parent->field(isub[j]) );
    const int nd = mfield.ndimension();
    DVector<Real> rp(nd*nn);
    mfield.fetch(rp);
#pragma omp parallel for
    for (int i=0; i<nn; ++i)
      for (int k=0; k<3; ++k)
        vdef[i][k] += scale * mx[j] * rp[nd*i+k];
  }
}

Mtx33 MxMeshDeform::rbTransform(const Vct3 & CoG, Real scale,
                                const Vector & dss, PointList<3> & vdef) const
{
  // assemble rotation matrix
  Mtx33 R;
  rbrotation(dss.pointer(), R);

  Vct3 cgx(CoG);
  for (int k=0; k<3; ++k)
    cgx[k] += scale * dss[k];

  const int n = vdef.size();
#pragma omp parallel for
  for (int i=0; i<n; ++i)
    vdef[i] = cgx + R*(vdef[i] - CoG);

  return R;
}

void MxMeshDeform::flightPath(const Vct3 & CoG, Real width,
                              Real scale, PointList<3,float> & path) const
{
  const int n = bptime.size();
  if (not isFlightPath())
    return;

  Mtx33 R;
  path.resize(2*n);

  Vct3 r1, r2, cgx;
  r1[1] = width;
  r2[1] = -width;

#pragma omp parallel for private(cgx,R)
  for (int i=0; i<n; ++i) {
    rbrotation(bpcoef.colpointer(i), R);
    for (int k=0; k<3; ++k)
      cgx[k] = CoG[k] + scale*bpcoef(k,i);
    convert(cgx + R*r1, path[2*i+0]);
    convert(cgx + R*r2, path[2*i+1]);
  }
}

Real MxMeshDeform::estimateMaxDisplacement() const
{
  Real dmax(0.0);
  const int nm = isub.size();
  const int nt = bpcoef.ncols();
  for (int i=0; i<nm; ++i) {

    // compute maximum displacement of mode
    Real mmax(0.0);
    const MxMeshField & f(parent->field(isub[i]));
    const int ndim = f.ndimension();
    // const Real *rp = f.realPointer();
    const int np = ndim * parent->nnodes();
    DVector<Real> rp;
    rp.allocate(np);
    f.fetch(rp);
    for (int k=0; k<np; ++k)
      mmax = std::max(mmax, fabs(rp[k]));

    // obtain maximum scale applied to this mode
    Real fmax(0.0);
    for (int j=0; j<nt; ++j)
      fmax = std::max( fmax, fabs(bpcoef(moffset+i,j)) );

    dmax = std::max(dmax, fmax*mmax);
  }
  return dmax;
}

void MxMeshDeform::fromFlutterMode(const Indices & im, Complex p, 
                                   const CpxVector & z, uint nsample)
{
  const int nz = z.size();
  isub = im;
  moffset = 0;
  
  Real wabs = std::abs(p);
  bptime = equi_pattern(nsample);
  bpcoef.resize(nz, nsample);
  
  if (wabs > 0) {
    Real T = 2*PI/wabs;
    bptime *= T;
    for (uint j=0; j<nsample; ++j) {
      for (int i=0; i<nz; ++i)
        bpcoef(i,j) = std::real(z[i] * std::exp(bptime[j] * p));
    }

  } else {
    for (uint j=0; j<nsample; ++j) {
      for (int i=0; i<nz; ++i)
        bpcoef(i,j) = z[i].real();
    }
  }

  XmlElement xe("FlutterMode");
  xe["eigenvalue"] = str(p);
  xe.append("Fields", im.size(), &im[0]);
  xe.append("Participation", z.size(), z.pointer());
  annotate(xe);
}

XmlElement MxMeshDeform::toXml(bool share) const
{
  XmlElement xe("MxMeshDeform");
  xe["name"] = id;
  xe["firstelastic"] = str(moffset);
  
  XmlElement xt("TimePoints");
  xt["count"] = str(bptime.size());
  xt.asBinary(bptime.size(), bptime.pointer(), share);
  xe.append(std::move(xt));
  
  XmlElement xd("Deformation");
  xd["modes"] = str(bpcoef.nrows());
  xd["npoints"] = str(bpcoef.ncols());
  xd.asBinary(bpcoef.size(), bpcoef.pointer(), share);
  xe.append(std::move(xd));
  
  XmlElement xi("EigenmodeFields");
  xi["count"] = str(isub.size());
  xi.asBinary(isub.size(), &isub[0], share);
  xe.append(std::move(xi));
  
  if (not xnote.name().empty())
    xe.append(xnote);
  
  return xe;
}

void MxMeshDeform::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "MxMeshDeform");
  
  bptime.resize(0);
  bpcoef.resize(0,0);
  cpcoef.resize(0,0);
  id = xe.attribute("name");
  moffset = Int(xe.attribute("firstelastic"));
  XmlElement::const_iterator itr, last;
  last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    const string & s = itr->name();
    if (s == "TimePoints") {
      bptime.resize( Int(itr->attribute("count")) );
      itr->fetch(bptime.size(), bptime.pointer());
    } else if (s == "Deformation") {
      bpcoef.resize( Int(itr->attribute("modes")), 
                     Int(itr->attribute("npoints")) );
      itr->fetch(bpcoef.size(), bpcoef.pointer());
    } else if (s == "EigenmodeFields") {
      isub.resize(Int(itr->attribute("count")));
      itr->fetch(isub.size(), &isub[0]);
    } else if (s == "MxNote") {
      xnote = *itr;
    }
  }
  
  // input checking 
  for (uint i=0; i<isub.size(); ++i) {
    const MxMeshField & f( parent->field(isub[i]) );
    if (not f.realField() )
      throw Error("MxMeshDeform::fromXml() "
                  " Field index points to an integer-valued field, "
                  "can't be a mesh deformation mode.");
    if (f.ndimension() < 3)
      throw Error("MxMeshDeform::fromXml() "
          " Field index does not point to a 3-dimensional field, "
          "can't be a mesh deformation mode.");
    if (bpcoef.ncols() != bptime.size())
      throw Error("MxMeshDeform::fromXml() Time data does not match deformation data size.");
  }

  elasticOffset();
}

static inline void xreduce(const Indices &idx, const Vector &x, Vector &y)
{
  const int ny = idx.size();
  assert(y.size() == uint(ny));
  for (int i=0; i<ny; ++i)
    y[i] = x[idx[i]];
}

void MxMeshDeform::readPlain(const std::string & fname,
                             const Indices &useCols)
{
  bptime.resize(0);
  bpcoef.clear();
  cpcoef.clear();
  moffset = 0;
  
  // set deformation id from filename
  string::size_type p1, p2;
  p1 = fname.find_last_of("/\\");
  p2 = fname.find_last_of('.');
  if (p1 == string::npos) {
    if (p2 == string::npos)
      id = fname;
    else
      id = fname.substr(0, p2);
  } else {
    id = fname.substr(p1+1, p2-p1-1);
  }
  
  ifstream in(asPath(fname).c_str());
  
  string line;
  Vector x;
  VectorArray xh;
  Real v;
  
  // read first line 
  while (getline(in,line)) {
    line = strip(line);
    if (line.empty())
      continue;
    if (line[0] == '#' or line[0] == '%')
      continue;
    std::stringstream ss;
    ss << line;
    while (ss >> v)
      x.push_back(v);
    if (not x.empty())
      break;
  }
  
  const int nc = x.size();
  if (nc < 13) {
    string msg;
    msg += "Could not load trajectory file";
    msg += "Incompatible data in file\n";
    msg += fname;
    msg += "\nExpected at least (time + 12) states, found " + str(nc);
    throw Error(msg);
  }
  
  Indices cols(useCols);
  if (cols.empty()) {
    cols.resize(nc);
    for (int i=0; i<nc; ++i)
      cols[i] = i;
  }

  Vector y(cols.size());
  xreduce(cols, x, y);

  xh.push_back(y);
  
  // read more lines
  while (getline(in,line)) {
    line = strip(line);
    if (line.empty())
      continue;
    if (line[0] == '#' or line[0] == '%')
      continue;
    std::stringstream ss;
    ss << line;
    for (int k=0; k<nc; ++k)
      ss >> x[k];

    xreduce(cols, x, y);
    xh.push_back(y);
  }
  
  if (not xh.empty()) {
    const int nt(xh.size());
    bptime.resize(nt);
    bpcoef.resize(nc-1,nt);
    for (int j=0; j<nt; ++j) {
      bptime[j] = xh[j][0];
      for (int i=0; i<nc-1; ++i)
        bpcoef(i,j) = xh[j][i+1];
    }
  }

  // need to relate rows in bpcoef to vector fields of parent
  // vector fields for eigenmodes must be annotated
  if (nc > 13) {

    // indices of eigenmode fields
    isub.clear();
    const int nf = parent->nfields();
    for (int i=0; i<nf; ++i) {
      const XmlElement & fn( parent->field(i).note() );
      if (fn.findChild("Eigenmode") != fn.end())
        isub.push_back(i);
    }

    if (isub.size() > uint(nc-13))
      throw Error("Trajectory in "+fname+" incompatible with eigenmode set.");

//
//    const XmlElement & xe(parent->note());
//    XmlElement::const_iterator itr;
//    itr = xe.findChild("EigenmodeFields");
//    if (itr == xe.end())
//      throw Error("Cannot load trajectory: No vector fields marked as eigenmodes.");
//    isub.resize( Int(itr->attribute("count")) );
//    if (isub.size() > uint(nc-13))
//      throw Error("Trajectory in "+fname+" incompatible with eigenmode set.");
//    itr->fetch(isub.size(), &isub[0]);
  }
  
  // now that everything is loaded, determine the index of the first elastic
  // mode and check if the referenced modes are actually present
  elasticOffset();
}
