
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
 
#include <cstring>
#include <set>
#include <genua/ioglue.h>
#include <genua/trimesh.h>
#include <genua/strutils.h>
#include <genua/plane.h>
#include <genua/boxsearchtree.h>
#include <genua/ffanode.h>
#include <genua/mxmesh.h>
//#ifdef HAVE_CGNS
#include <genua/cgnsfile.h>
#include <genua/cgnsfwd.h>
//#endif // HAVE_CGNS
#include "tetmesh.h"

using std::string;

// --------------------- file scope ------------------------------------------

static string findTetgenHeader(istream & is)
{
  string line;
  while (getline(is, line)) {
    
    // skip comment lines
    if (strchr(line.c_str(), '#') != 0)
      continue;
    
    line = strip(line);
    if (line.empty())
      continue;
    
    return line;
  }
  
  return string("");
}

template <class Iterator, int n>
static inline void rotateIndex(Iterator first)
{
  Iterator last = first + n;
  Iterator mid = std::min_element(first, last);
  std::rotate(first, mid, last);
}

// ---------------------- TetElement ---------------------------------------------

bool TetElement::cuts(const PointList<3> & vtx, const Plane & p) const
{
  Real dst[4];
  for (int k=0; k<4; ++k)
    dst[k] = p.distance(vtx[v[k]]);
  
  bool cp = false;
  for (int k=1; k<4; ++k)
    cp |= (sign(dst[k]) != sign(dst[0]));
  
  return cp;
}

void TetElement::addFaces(TriMesh & m) const
{
  m.addFace( v[0], v[2], v[1] );
  m.addFace( v[0], v[1], v[3] );
  m.addFace( v[1], v[2], v[3] );
  m.addFace( v[0], v[3], v[2] );
}

// ---------------------- TetMesh ---------------------------------------------

void TetMesh::init(const TriMesh & allb)
{
  Indices alltags;
  allb.allTags(alltags);
  
  // extract wall boundary data
  const int nbt = alltags.size();
  boco.resize(nbt);
  for (int i=0; i<nbt; ++i)
    boco[i] = TetBoundaryGroup(allb, alltags[i]);
  
  // copy vertices
  vtx = allb.vertices();
  
  // copy boundary triangles
  const int nf = allb.nfaces();
  faces.resize(nf);
  for (int i=0; i<nf; ++i) {
    faces[i] = TetFace( allb.face(i).vertices() );
    faces[i].tag( allb.face(i).tag() );
  }
  
  // clear tet element array
  tets.clear();
}

void TetMesh::initBoundaries(const TriMesh & wall, TriMesh & mfarfield)
{
  // mhole = findHolePosition(wall);
  mholes.clear();
  bool hlOk = findHoles(wall, mholes);
  if (not hlOk)
    throw Error("TetMesh::findHoles() find to identify internal volume.");

  // mark farfield mesh with separate marker
  TriMesh allb(wall);
  allb.merge(mfarfield);
  
  // EDGE apparently wants all boundaries reversed
  // allb.reverse();
  
  Indices alltags;
  allb.allTags(alltags);
  
  uint fartag = mfarfield.face(0).tag();
  
  // extract wall boundary data
  const int nbt = alltags.size();
  boco.resize(nbt);
  for (int i=0; i<nbt; ++i) {
    boco[i] = TetBoundaryGroup(allb, alltags[i]);
    if (alltags[i] == fartag)
      boco[i].boundaryCondition( TetBoundaryGroup::BcFarfield );
  }
  
  // copy vertices
  vtx = allb.vertices();
  
  // copy boundary triangles
  const int nf = allb.nfaces();
  faces.resize(nf);
  for (int i=0; i<nf; ++i) {
    faces[i] = TetFace( allb.face(i).vertices() );
    faces[i].tag( allb.face(i).tag() );
  }
  
  // clear tet element array
  tets.clear();
}

Vct3 TetMesh::findHolePosition(const TriMesh & m) const
{
  // identify a point inside the body
  // find a triangle whose neighbor triangles all make have normals which differ
  // by less than 30 deg from its own normal, and use a point which is a small
  // distance below the triangle center
  Vct3 hole, fn;
  const int nf = m.nfaces();
  for (int i=0; i<nf; ++i) {
    const TriFace & f(m.face(i));
    fn = f.normal();
    bool ok(true);
    Real csa, csamin(0.866);
    const uint *vi( f.vertices() );
    TriMesh::nb_face_iterator itf, flast;
    for (int k=0; k<3; ++k) {
      flast = m.v2fEnd(vi[k]);
      for (itf = m.v2fBegin(vi[k]); itf != flast; ++itf) {
        csa = cosarg(fn, itf->normal());
        if (csa < csamin) {
          ok = false;
          break;
        }
      }
      if (not ok)
        break;
    }
    
    // all neighbor normals differ by less than 30deg
    if (ok) {
      Real nfm = normalize(fn);
      Real dst = 1e-3 * sqrt(nfm);
      hole = f.center() - fn * dst;
      break;
    }
  }
  
  return hole;
}

bool TetMesh::findHoles(const TriMesh & m, PointList<3> & holes) const
{
  typedef std::pair<std::set<uint>::const_iterator, bool> InsertResult;

  const int nf = m.nfaces();
  std::set<uint> reached;
  Indices tag;
  while (reached.size() != uint(nf)) {

    Vct3 hole;
    tag.clear();
    for (int i=0; i<nf; ++i) {
      if (reached.find(i) != reached.end())
        continue;
      if (triangleHole(m, i, hole)) {
        holes.push_back(hole);
        tag.push_back(i);
        break;
      }
    }

    // if no suitable continuation was found, exit with failure
    if (tag.empty())
      return false;

    // starting from the newly identified triangle, walk the topological
    // neighborhood and mark faces which can be reached from there
    while (not tag.empty()) {
      uint fix = tag.back();
      tag.pop_back();
      const uint *v = m.face(fix).vertices();
      for (int k=0; k<3; ++k) {
        TriMesh::nb_face_iterator itf, last = m.v2fEnd(v[k]);
        for (itf = m.v2fBegin(v[k]); itf != last; ++itf) {
          InsertResult ins = reached.insert(itf.index());
          if (ins.second)
            tag.push_back(itf.index());
        }
      }
    }

  }

  return true;
}

bool TetMesh::triangleHole(const TriMesh &m, uint fix, Vct3 & hole) const
{
  const Real csamin = 0.866;
  const uint *v = m.face(fix).vertices();
  Vct3 fn = m.face(fix).normal();
  for (uint k=0; k<3; ++k) {
    TriMesh::nb_face_iterator itf, last = m.v2fEnd(v[k]);
    for (itf = m.v2fBegin(v[k]); itf != last; ++itf) {
      Real csa = cosarg(fn, itf->normal());
      if (csa < csamin)
        return false;
    }
  }

  Real nfm = normalize(fn);
  Real dst = 1e-3 * sqrt(nfm);
  hole = m.face(fix).center() - fn * dst;

  return true;
}

uint TetMesh::groupByTag(int t) const
{
  const int ng(boco.size());
  for (int i=0; i<ng; ++i) {
    if (boco[i].tag() == t)
      return i;
  }
  return NotFound;
}

void TetMesh::reverseBoundary(uint k)
{
  assert(k < boco.size());
  const int nf = boco[k].size();
  for (int i=0; i<nf; ++i)
    faces[ boco[k].face(i) ].reverse();
}

void TetMesh::toMx(MxMesh &mx) const
{
  mx.clear();
  mx.appendNodes( vtx );

  {
    const int nt4 = tets.size();
    Indices tix(4*nt4);
    memcpy(&tix[0], tets[0].vertices(), sizeof(uint)*tix.size());
    uint isec = mx.appendSection( Mx::Tet4, tix );
    mx.section(isec).rename( "FluidDomain" );
    mx.countElements();
  }

  const int nt3 = faces.size();
  Indices tri(3*nt3);
  std::vector<int> tags(nt3);
  {
    const int nt3 = faces.size();
    for (int i=0; i<nt3; ++i) {
      const uint *vi = faces[i].vertices();
      for (int k=0; k<3; ++k)
        tri[3*i+k] = vi[k];
      tags[i] = faces[i].tag();
    }
    // uint isec = mx.appendSection( Mx::Tri3, tri );
    // mx.section( isec ).rename( "Boundaries" );
  }

  std::vector<int> atags(tags);
  sort_unique(atags);
  const int ntags = atags.size();
  Indices subtri;
  Indices range(2*ntags);
  for (int j=0; j<ntags; ++j) {
    subtri.clear();
    range[2*j+0] = mx.nelements();
    int jtag = atags[j];
    for (int i=0; i<nt3; ++i) {
      if (tags[i] == jtag) {
        const uint *vi = faces[i].vertices();
        subtri.insert(subtri.end(), vi, vi+3);
      }
    }
    uint isec = mx.appendSection( Mx::Tri3, subtri );
    mx.section( isec ).rename( "Tag "+str(jtag) );
    mx.section( isec ).tag( jtag );
    range[2*j+1] = range[2*j+0] + mx.section(isec).nelements();
  }

  const int nbc = boco.size();
  for (int i=0; i<nbc; ++i) {

    MxMeshBoco bc;
    bc.rename( boco[i].name() );
    for (uint j=1; j<mx.nsections(); ++j) {
      if (mx.section(j).tag() == boco[i].tag()) {
        mx.section(j).rename( boco[i].name() );
        bc.setRange( range[2*(j-1)+0], range[2*(j-1)+1] );
        break;
      }
    }

    switch (boco[i].boundaryCondition()) {
    case TetBoundaryGroup::BcWall:
      bc.bocoType( Mx::BcWall );
      break;
    case TetBoundaryGroup::BcFarfield:
      bc.bocoType( Mx::BcFarfield );
      break;
    case TetBoundaryGroup::BcMassFlowOutlet:
      bc.bocoType( Mx::BcMassflowOut );
      break;
    case TetBoundaryGroup::BcMassFlowInlet:
      bc.bocoType( Mx::BcMassflowIn );
      break;
    case TetBoundaryGroup::BcUser:
      bc.bocoType( Mx::BcUserDefined );
      break;
    default:
      bc.bocoType( Mx::BcUndefined );
      break;
    }

    mx.appendBoco( bc );
  }
}

// void TetMesh::boundaryTags(Indices & tags) const
// {
//   tags = ftag;
//   sort_unique(tags);
// }
// 
// void TetMesh::setBoundary(const TriMesh & m)
// {
//   Indices btags(m.nfaces());
//   fill(btags.begin(), btags.end(), 1);
//   setBoundary(m, btags);
//   bnames.clear();
//   bnames[1] = "Wall";
// }
// 
// void TetMesh::setBoundary(const TriMesh & m, const Indices & btags)
// {
//   vtx = m.vertices();
//   const int nf(m.nfaces());
//   assert(btags.size() == uint(nf));
//   faces.resize(nf);
//   for (int i=0; i<nf; ++i) {
//     faces[i] = TetFace(m.face(i).vertices());
//   }
//   ftag = btags;
//   tets.clear();
//   
//   // determine mesh center and hope the hole is there
//   Vct3 fn;
//   Real a, asum(0);
//   for (int i=0; i<nf; ++i) {
//     const TriFace & f(m.face(i));
//     a = f.normal(fn);
//     asum += a;
//     mctr += a*f.center();
//   }
//   mctr /= asum;
//   
//   
//   
//   // generate default boundary names
//   bnames.clear();
//   Indices utags(ftag);
//   sort_unique(utags); 
//   for (uint i=0; i<utags.size(); ++i)
//     bnames[utags[i]] = string("Boundary") + str(utags[i]);
// }
// 
// void TetMesh::addSphericalFarfield(Real radius, int nref)
// {
//   TriMesh ffm;
//   ffm.sphere(mctr, radius, nref);
//   const int nnv = ffm.nvertices();
//   const int nnf = ffm.nfaces();
//   const int voff = vtx.size();
//   const int foff = faces.size();
//   
//   {
//     PointList<3> vnew(voff+nnv);
//     for (int i=0; i<voff; ++i)
//       vnew[i] = vtx[i];
//     for (int i=0; i<nnv; ++i)
//       vnew[voff+i] = ffm.vertex(i);
//     vnew.swap(vtx);
//   }
//   
//   Indices btag(foff+nnf);
//   copy(ftag.begin(), ftag.end(), btag.begin());
//   int fftag = 1 + *max_element(ftag.begin(), ftag.end());
//   bnames[fftag] = "FarfieldSphere";
//   faces.reserve(faces.size()+nnf);
//   for (int i=0; i<nnf; ++i) {
//     const uint *vi = ffm.face(i).vertices();
//     faces.push_back( TetFace(vi[0]+voff, vi[1]+voff, vi[2]+voff) );
//     btag[foff+i] = fftag;
//   }
//   btag.swap(ftag);
// }

int TetMesh::readTetgenNodes(std::istream & is)
{
  int nnodes(0), offs(0);
  
  // analyse header line
  string line = findTetgenHeader(is);
  const char *pos;
  char *tail;
  pos = line.c_str();
  
  nnodes = strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("TetMesh::readTetgenNodes() cannot find valid node file header.");
  
  vtx.resize(nnodes);
  if (nnodes == 0)
    return 0;
  
  // read first node line to determine node index offset
  getline(is, line);
  pos = line.c_str();
  offs = strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("TetMesh::readTetgenNodes() invalid first node line.");
  
  for (int k=0; k<3; ++k) {
    pos = tail;
    vtx[0][k] = strtod(pos, &tail);
    assert(pos != tail);
  }
  
  int j(1), tmp;
  while (getline(is,line)) {

    pos = line.c_str();
    tmp = strtol(pos, &tail, 10);
    assert(pos != tail);
    for (int k=0; k<3; ++k) {
      pos = tail;
      vtx[j][k] = strtod(pos, &tail);
      assert(pos != tail);
    }

    ++j;
    if (j == nnodes)
      break;
  }
  
  return offs;
}

void TetMesh::readTetgenElements(std::istream & is, int offs)
{
  int nele(0);
  
  // analyse header line
  string line = findTetgenHeader(is);
  const char *pos;
  char *tail;
  pos = line.c_str();
  
  nele = strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("TetMesh::readTetgenElements() cannot find "
                "valid element file header.");
  
  tets.resize(nele);
  if (nele == 0)
    return;
  
  uint v[4];
  int j(0), tmp;
  while (getline(is,line)) {

    pos = line.c_str();
    tmp = strtol(pos, &tail, 10);
    assert(pos != tail);
    for (int k=0; k<4; ++k) {
      pos = tail;
      v[k] = strtol(pos, &tail, 10) - offs;
      assert(pos != tail);
    }
    tets[j] = TetElement(v);

    ++j;
    if (j == nele)
      break;
  }
}

void TetMesh::readTetgenFaces(std::istream & is, int offs)
{
  int nface(0), nbm(0);
  
  // analyse header line
  string line = findTetgenHeader(is);
  const char *pos;
  char *tail;
  pos = line.c_str();
  
  nface = strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("TetMesh::readTetgenFaces() cannot find "
                "valid face file header.");
  
  pos = tail;
  nbm = strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("TetMesh::readTetgenFaces() cannot find "
                "valid face file header.");
  
  faces.resize(nface);
  if (nface == 0)
    return;
  
  uint v[3];
  int j(0), tmp;
  while (getline(is,line)) {

    pos = line.c_str();
    tmp = strtol(pos, &tail, 10);
    assert(pos != tail);
    for (int k=0; k<3; ++k) {
      pos = tail;
      v[k] = strtol(pos, &tail, 10) - offs;
      assert(pos != tail);
    }
    faces[j] = TetFace(v);
    if (nbm > 0) {
      pos = tail;
      faces[j].tag( strtol(pos, &tail, 10) );
    }
    
    ++j;
    if (j == nface)
      break;
  }
  
  // update boundary groups
  const int nb = boco.size();
  for (int i=0; i<nb; ++i)
    boco[i].capture(faces);
}

void TetMesh::readTetgen(const std::string & bname)
{
  string nodefile = bname + ".node";
  string elefile = bname + ".ele";
  string facefile = bname + ".face";
  
  ifstream nis(asPath(nodefile).c_str(), std::ios::binary);
  int offs = readTetgenNodes(nis);
  nis.close();
  
  ifstream fis(asPath(facefile).c_str(), std::ios::binary);
  readTetgenFaces(fis, offs);
  fis.close();
  
  ifstream eis(asPath(elefile).c_str(), std::ios::binary);
  if (eis) {
    readTetgenElements(eis, offs);
    eis.close();
  }
} 

void TetMesh::writeTetgen(const std::string & bname, int offs) const
{
  string nodefile = bname + ".node";
  string elefile = bname + ".ele";
  string facefile = bname + ".face";
  
  int nv(vtx.size());
  ofstream nos(asPath(nodefile).c_str(), std::ios::binary);
  nos.precision(16);
  nos << std::scientific;
  nos << nv << " 3 0 0" << endl;
  for (int i=0; i<nv; ++i)
    nos << "    " << i+offs << " " << vtx[i] << endl;
  nos.close();
  
  int ne(tets.size());
  if (ne > 0) {
    ofstream eos(asPath(elefile).c_str(), std::ios::binary);
    eos << ne << " 4 0" << endl;
    for (int i=0; i<ne; ++i) {
      const uint *vi = tets[i].vertices();
      eos << "    " << i+offs << " " << vi[0]+offs << " " << vi[1]+offs
          << " " << vi[2]+offs << " " << vi[3]+offs << endl;
    }
    eos.close();
  }
  
  int nf(faces.size());
  ofstream fos(asPath(facefile).c_str(), std::ios::binary);
  fos << nf << " 1" << endl;
  for (int i=0; i<nf; ++i) {
    const uint *vi = faces[i].vertices();
    fos << "    " << i+offs << " " << vi[0]+offs << " " << vi[1]+offs
        << " " << vi[2]+offs << " " << faces[i].tag() << endl;
  }
  fos.close();
}

void TetMesh::writeSmesh(const std::string & fname, int offs) const
{
  int nv(vtx.size());
  ofstream os(asPath(fname).c_str(), std::ios::binary);
  os.precision(16);
  os << std::scientific;
  
  os << endl;
  os << "# node list" << endl;
  os << nv << " 3 0 0" << endl;
  for (int i=0; i<nv; ++i)
    os << i+offs << " " << vtx[i] << endl;
  os << endl;
  
  int nf(faces.size());
  os << "# face list" << endl;
  os << nf << " 1" << endl;
  for (int i=0; i<nf; ++i) {
    const uint *vi = faces[i].vertices();
    os << "3  " << vi[0]+offs << " " << vi[1]+offs
       << " " << vi[2]+offs << " " << faces[i].tag() << endl;
  }
  os << endl;
  
  os << "# hole list" << endl;
  //  os << "1" << endl;
  //  os << "1 " << mhole << endl;
  //  os << endl;
  os << mholes.size() << endl;
  for (uint i=0; i<mholes.size(); ++i)
    os << i+offs << ' ' << mholes[i] << endl;
  
  os << "# region attribute list" << endl;
  os << "0" << endl;
  os << endl;
}

void TetMesh::clear()
{
  vtx.clear();
  tets.clear();
  faces.clear();
  boco.clear();
}

void TetMesh::reorder()
{
  Indices perm, iperm;
  BSearchTree btree(vtx);
  btree.proximityOrdering(perm);
  
  const int np(perm.size());
  iperm.resize(np);
  for (int i=0; i<np; ++i)
    iperm[perm[i]] = i;
  
  const int nv(vtx.size());
  {
    PointList<3> tmp(nv);
    for (int i=0; i<nv; ++i)
      tmp[i] = vtx[perm[i]];
    vtx.swap(tmp);
  }
  
  const int ne(tets.size());
  for (int i=0; i<ne; ++i) {
    uint *v = tets[i].vertices();
    for (int k=0; k<4; ++k)
      v[k] = iperm[v[k]];
  }
  std::sort(tets.begin(), tets.end());
  
  const int nf(faces.size());
  for (int i=0; i<nf; ++i) {
    uint *v = faces[i].vertices();
    for (int k=0; k<3; ++k)
      v[k] = iperm[v[k]];
  }
}

void TetMesh::cutElements(const Plane & p, TriMesh & tms) const
{
  tms.clear();
  
  tms.vertices() = vtx;
  const int ne = tets.size();
  for (int i=0; i<ne; ++i) {
    const TetElement & t(tets[i]);
    if (t.cuts(vtx, p))
      t.addFaces(tms);
  }
}

void TetMesh::writeMsh(const std::string & fname) const
{
  FFANodePtr root(new FFANode("unstr_grid_data"));
  
  FFANode *title = new FFANode("title");
  title->copy("Unstructured mesh generated by sumo+tetgen");
  root->append(title);
  
  FFANode *region = new FFANode("region");
  FFANode *region_name = new FFANode("region_name");
  region_name->copy("volume_elements");
  region->append(region_name);

  // convert coordinate format
  const int nv = vtx.size();
  Vector xyz(3*nv);
  for (int i=0; i<nv; ++i) {
    xyz[i] = vtx[i][0];
    xyz[nv+i] = vtx[i][1];
    xyz[2*nv+i] = vtx[i][2];
  }
  
  FFANode *coord = new FFANode("coordinates");
  coord->copy(nv, 3, &xyz[0]);
  region->append(coord);

  FFANode *element_group = new FFANode("element_group");
  FFANode *element_type = new FFANode("element_type");
  element_type->copy("tetra4");
  element_group->append(element_type);
  
  const int ne = tets.size();
  IndexMatrix ielm(ne,4), itmp;
  for (int i=0; i<ne; ++i) {
    const uint *vi = tets[i].vertices();
    for (int k=0; k<4; ++k)
      ielm(i,k) = vi[k] + 1;
  }
  FFANode *element_nodes = new FFANode("element_nodes");
  element_nodes->copy(tets.size(), 4, &ielm[0]);
  element_group->append(element_nodes);
  region->append(element_group);
  root->append(region);
  
  //   // append boundaries
  //   BNameMap::const_iterator bitr, blast = bnames.end();
  //   for (bitr = bnames.begin(); bitr != blast; ++bitr) {
  //     collectFaces(bitr->first, itmp);
  //     const int nbf = itmp.ncols();
  //     ielm.resize(nbf,3);
  //     for (int i=0; i<nbf; ++i)
  //       for (int k=0; k<3; ++k)
  //         ielm(i,k) = itmp(k,i);
  //     FFANode *boundary = new FFANode("boundary");
  //     FFANode *boundary_name = new FFANode("boundary_name");
  //     boundary_name->copy(bitr->second.c_str());
  //     boundary->append(boundary_name);
  //     FFANode *belem_group = new FFANode("belem_group");
  //     FFANode *bound_elem_type = new FFANode("bound_elem_type");
  //     bound_elem_type->copy("tria3");
  //     belem_group->append(bound_elem_type);
  //     FFANode *bound_elem_nodes = new FFANode("bound_elem_nodes");
  //     bound_elem_nodes->copy(nbf, 3, &ielm[0]);
  //     belem_group->append(bound_elem_nodes);
  //     boundary->append(belem_group);
  //     root->append(boundary);
  //   }
  
  const int nb = boco.size();
  for (int i=0; i<nb; ++i)
    boco[i].ffamsh(faces, *region);
  
  root->write(fname);
}

void TetMesh::writeBoc(const std::string & fname) const
{
  FFANodePtr root(new FFANode("boundary_data"));

  FFANodePtr region(new FFANode("region"));
  FFANodePtr region_name(new FFANode("region_name"));
  region_name->copy("fluid domain");
  region->append(region_name);
  root->append(region);

  for (uint i=0; i<boco.size(); ++i)
    boco[i].ffaboc(*region);
  root->write(fname);
}

//#ifdef HAVE_CGNS

void TetMesh::readCgns(const std::string & bname)
{
  CgnsFile file;
  file.ropen(bname);

  if (file.nzones() > 1)
    clog << "TetMesh::readCgns() Warning: will only read first zone!" << endl;

  // import nodes
  CgnsZone zone = file.readZone(1);
  zone.readNodes( vtx );

  // import elements
  uint v[4];
  int ne, nsec, ecount(0), bndoff(0);
  faces.clear();
  tets.clear();
  CgnsIntMatrix ielm;
  nsec = zone.nsections();
  for (int sindex = 1; sindex <= nsec; ++sindex) {
    CgnsSection section = zone.readSection(sindex);
    switch (section.elementType()) {
    case cgns::TRI_3:
      section.readElements( ielm );
      ne = ielm.ncols();
      for (int i=0; i<ne; ++i) {
        for (int k=0; k<3; ++k)
          v[k] = ielm(k,i) - 1;
        faces.push_back(TetFace(v));
        faces.back().tag(0);
      }

      // this works if either all boundary triangles come
      // first (bndoff = 0) or all boundaries come after the
      // volume elements, but not if they are intermixed wildly
      if (bndoff == 0)
        bndoff = ecount;
      ecount += ne;
      break;
    case cgns::TETRA_4:
      section.readElements( ielm );
      ne = ielm.ncols();
      for (int i=0; i<ne; ++i) {
        for (int k=0; k<4; ++k)
          v[k] = ielm(k,i) - 1;
        tets.push_back(TetElement(v));
      }
      ecount += ne;
      break;
    default:
      break;
    }
  }

  // import boundary conditions
  boco.clear();
  CgnsIntVector elix;
  int nbc = zone.nbocos();
  for (int bcindex = 1; bcindex <= nbc; ++bcindex) {
    CgnsBoco bc = zone.readBoco( bcindex );
    if (bc.pointSet() == cgns::ElementList) {

      boco.push_back(TetBoundaryGroup());
      TetBoundaryGroup & bg(boco.back());

      bg.rename( bc.name() );
      bg.tag( bcindex );
      bg.cgnsBoundaryCondition( bc.bcType() );

      bc.readPoints(elix);
      bg.facelist(elix, bndoff+1);
      bg.enforce(faces);

    } else {
      cout << "TetMesh::readCgns() Warning: BCs must use ElementLists." << endl;
    }
  }
}

void TetMesh::writeCgns(const std::string & fname, bool bcAsSections)
{
  const int nv(vtx.size());
  const int ne(tets.size());
  const int nf(faces.size());
  if (ne == 0 and nf == 0)
    return;

  CgnsFile cgf;
  cgf.wopen(fname);

  // create zone to which to attach vertices
  CgnsZone cgz = cgf.newZone("TetMesh", nv, ne);
  cgz.writeNodes(vtx);

  int elmOffset = 0;
  IndexMatrix ielm;
  if (ne > 0) {

    // write field mesh
    ielm.resize(4,ne);
    for (int i=0; i<ne; ++i) {
      const uint *vi = tets[i].vertices();
      for (int k=0; k<4; ++k)
        ielm(k,i) = vi[k] + 1;
    }

    CgnsSection cgs(cgz.findex(), cgz.bindex(), cgz.index(), 1);
    cgs.rename("FluidDomain");
    cgs.elementType( cgns::TETRA_4 );
    cgs.writeElements(ielm);

    elmOffset = ne;
  }

  if (nf > 0) {

    if (bcAsSections) {

      const int nbc = boco.size();
      for (int i=0; i<nbc; ++i) {

        // assemble element indices
        const int nbe = boco[i].size();
        ielm.resize(3,nbe);
        for (int j=0; j<nbe; ++j) {
          const uint *vi = faces[boco[i].face(j)].vertices();
          for (int k=0; k<3; ++k)
            ielm(k,j) = vi[k] + 1;
        }

        CgnsSection cgs(cgz.findex(), cgz.bindex(), cgz.index(), 2+i);
        cgs.rename( boco[i].name() );
        cgs.elementOffset(elmOffset);
        cgs.elementType( cgns::TRI_3 );
        cgs.writeElements(ielm);
        elmOffset += nbe;
      }

    } else {

      ielm.resize(3,nf);
      for (int i=0; i<nf; ++i) {
        const uint *vi = faces[i].vertices();
        for (int k=0; k<3; ++k)
          ielm(k,i) = vi[k]+1;
      }

      CgnsSection cgs(cgz.findex(), cgz.bindex(), cgz.index(), 2);
      cgs.rename("Boundaries");
      cgs.elementOffset(elmOffset);
      cgs.elementType( cgns::TRI_3 );
      cgs.writeElements(ielm);
      elmOffset += nf;

    }
  }

  // write boundary conditions
  if (not bcAsSections) {
    const int nbc = boco.size();
    for (int i=0; i<nbc; ++i)
      boco[i].writeCgnsBoco(cgz, ne);
  }
}

//#endif // HAVE_CGNS

#ifdef HAVE_TETGEN

#include <tetgen.h>

void TetMesh::callTetgen(const std::string & options)
{
  // check if boundary is defined
  if (vtx.empty() or faces.empty())
    throw Error("Boundary must be defined before tetgen is called.");
  
  // fill input data
  tetgenio in, out;
  
  int nv(vtx.size());
  int nf(faces.size());
  
  // copy input vertices
  in.numberofpoints = nv;
  in.pointlist = new double[3*nv];
  memcpy(in.pointlist, &vtx[0], 3*nv*sizeof(double));
  
  // set hole
  in.numberofholes = 1;
  in.holelist = new double[3];
  memcpy(in.holelist, &mhole[0], 3*sizeof(double));
  
  // copy boundary triangles
  in.numberoffacets = nf;
  in.facetlist = new tetgenio::facet[nf];
  in.facetmarkerlist = new int[nf];
  for (int i=0; i<nf; ++i) {
    in.facetmarkerlist[i] = faces[i].tag();
    tetgenio::init(&in.facetlist[i]);
    tetgenio::facet & f( in.facetlist[i] );
    f.numberofpolygons = 1;
    f.polygonlist = new tetgenio::polygon[1];
    tetgenio::init(&f.polygonlist[0]);
    tetgenio::polygon & p( f.polygonlist[0] );
    p.numberofvertices = 3;
    p.vertexlist = new int[3];
    const uint *vi = faces[i].vertices();
    for (int k=0; k<3; ++k)
      p.vertexlist[k] = vi[k];
  }

  // should redirect stdout into stringstream or something so that
  // we can catch the output of tetgen (and possible error messages)
  try {
    tetrahedralize( (char *) options.c_str(), &in, &out);
  } catch (int & erx) {
    throw Error("Tetgen terminated with error code "+str(erx));
  }
  
  // copy vertices from tetgen output
  nv = out.numberofpoints;
  vtx.resize(nv);
  memcpy(&vtx[0], out.pointlist, nv*sizeof(Vct3));
  
  // retrieve tetrahedral elements
  int ne = out.numberoftetrahedra;
  tets.resize(ne);
  int skip = out.numberofcorners;
  for (int i=0; i<ne; ++i) {
    const int *b = &out.tetrahedronlist[skip*i];
    tets[i] = TetElement(b[0], b[1], b[2], b[3]);
  }
  
  // retrieve boundary triangles
  nf = out.numberoftrifaces;
  faces.resize(nf);
  for (int i=0; i<nf; ++i) {
    const int *b = &out.trifacelist[3*i];
    faces[i] = TetFace(b[0], b[1], b[2]);
    if (out.trifacemarkerlist != 0)
      faces[i].tag( out.trifacemarkerlist[i] );
  }
  
  // update boundary groups
  const int nb = boco.size();
  for (int i=0; i<nb; ++i)
    boco[i].capture(faces);
}

#endif

