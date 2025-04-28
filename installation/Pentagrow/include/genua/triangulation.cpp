
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
 
#include "pattern.h"
#include "triangulation.h"
#include "edgecurve.h"
#include "facebubble.h"
#include "boxsearchtree.h"
#include "sparse.h"
#include "memberfun.h"
#include <iterator>

using namespace std;

Triangulation::Triangulation(const Triangulation & tg)
    : RFrame(tg), vtx(tg.vtx), nrm(tg.nrm)
{
  // copy construction
  faces.clear();
  face_iterator itf;
  for (itf = tg.face_begin(); itf != tg.face_end(); itf++)
    faces.push_back( Face(this,itf->vertex(1),itf->vertex(2),itf->vertex(3)) );
  fixate();
}

Triangulation::face_iterator Triangulation::nb_face_begin(uint i) const
{
  // return iterator to list of faces sharing vertex i
  FaceMap::const_iterator itm = v2f.find(i);
  assert(itm != v2f.end());
  return itm->second.begin();
}

Triangulation::face_iterator Triangulation::nb_face_end(uint i) const
{
  // return iterator to list of faces sharing vertex i
  FaceMap::const_iterator itm = v2f.find(i);
  assert(itm != v2f.end());
  return itm->second.end();
}

Triangulation::edge_iterator Triangulation::nb_edge_begin(uint i) const
{
  // return iterator to list of faces sharing vertex i
  EdgeMap::const_iterator itm = v2e.find(i);
  assert(itm != v2e.end());
  return itm->second.begin();
}

Triangulation::edge_iterator Triangulation::nb_edge_end(uint i) const
{
  // return iterator to list of faces sharing vertex i
  EdgeMap::const_iterator itm = v2e.find(i);
  assert(itm != v2e.end());
  return itm->second.end();
}

void Triangulation::apply()
{
  // apply frame transformation
  assert(vtx.size() == nrm.size());
  PointList<3>::iterator vit, nit;
  for (vit = vtx.begin(), nit = nrm.begin();
       (vit != vtx.end() and nit != nrm.end()); vit++, nit++) {
    *vit = RFrame::forward(*vit);
    *nit = RFrame::forward(*nit);
  }
}

void Triangulation::addFace(const Face & f)
{
  // add face to triangulation
#ifndef NDEBUG
  if (vtx.size() <= f.vertex(1))
    throw Error("Vertex 0 (" + str(f.vertex(1)) + ") must exist before face can be added.");
  if (vtx.size() <= f.vertex(2))
    throw Error("Vertex 1 (" + str(f.vertex(2)) + ") must exist before face can be added.");
  if (vtx.size() <= f.vertex(3))
    throw Error("Vertex 2 (" + str(f.vertex(3)) + ") must exist before face can be added.");
#endif

  Face f2(f);
  f2.orderCanonical();
  faces.push_back(f2);
  for (uint i=1; i<4; i++)
    edges.push_back(f2.edge(i));
}

void Triangulation::insertFace(const Face & f)
{
  // add face to triangulation
#ifndef NDEBUG
  if (vtx.size() <= f.vertex(1))
    throw Error("Vertex 1 must exist before face can be added.");
  if (vtx.size() <= f.vertex(2))
    throw Error("Vertex 2 must exist before face can be added.");
  if (vtx.size() <= f.vertex(3))
    throw Error("Vertex 3 must exist before face can be added.");
#endif

  Face f2(f);
  f2.orderCanonical();
  faces.insert(lower_bound(faces.begin(), faces.end(), f2), f2);
  for (uint i=1; i<4; i++) {
    edges.insert(lower_bound(edges.begin(), edges.end(), f2.edge(i)), f2.edge(i));
    v2f[f2.vertex(i)].push_back(f2);
    e2f[f2.edge(i)].insert(f2);
    v2e[f2.edge(i).source()].push_back(f2.edge(i));
    v2e[f2.edge(i).target()].push_back(f2.edge(i));
  }
}

set<uint> Triangulation::nbVertices(uint idx) const
  {
    /// find neighbour vertices
    set<uint> nb;

    FaceMap::const_iterator fmpos = v2f.find(idx);
    assert(fmpos != v2f.end());
    FaceList::const_iterator itr;
    for (itr = fmpos->second.begin(); itr != fmpos->second.end(); itr++) {
      nb.insert(itr->vertex(1));
      nb.insert(itr->vertex(2));
      nb.insert(itr->vertex(3));
    }
    nb.erase(idx);

    return nb;
  }

FaceList Triangulation::nbFaces(uint idx) const
{
  /// find faces which contain vertex idx
  FaceMap::const_iterator fmpos = v2f.find(idx);
  assert(fmpos != v2f.end());
  return fmpos->second;
}

set<Face> Triangulation::nbFaces(const Edge & e) const
  {
    // return faces sharing e
    CrossMap::const_iterator itr = e2f.find(e);
    if (itr == e2f.end()) {
      string msg("Edge not found in edge2face map.\n");
      msg += "from: "+str(e.source())+" to: "+str(e.target())+"\n";
      throw Error(msg);
    }
    return itr->second;
  }


const EdgeList & Triangulation::nbEdges(uint idx) const
{
  /// find edges which contain vertex idx
  EdgeMap::const_iterator fmpos = v2e.find(idx);
  if (fmpos == v2e.end())
    throw Error("Vertex not found in edge map.");

  return fmpos->second;
}

uint Triangulation::degree(uint i) const
{
  // vertex degree
  EdgeMap::const_iterator itm = v2e.find(i);
  if (itm == v2e.end())
    return 0;
  else
    return itm->second.size();
}

Vct3 Triangulation::barycenter(uint i) const
{
  // area center of face neighborhood
  Real a, sum(0.0);
  Vct3 ct;
  FaceMap::const_iterator itm = v2f.find(i);
  if (itm == v2f.end())
    throw Error("Unreferenced vertex: "+str(i));

  FaceList::const_iterator itf;
  for (itf = itm->second.begin(); itf != itm->second.end(); itf++) {
    a = norm(itf->normal());
    sum += a;
    ct += a*itf->center();
  }
  return ct/sum;
}

uint Triangulation::nearest(const Vct3 & p, int pos) const
{
  // traverse triangulation to find closest vertex
  uint best, next, idx;
  if (pos < 0 or uint(pos) >= vtx.size())
    next = rand() % vtx.size();
  else
    next = pos;

  Real dist, dmin, delta(1.);
  dmin = norm(p - vertex(next));

  EdgeMap::const_iterator itm;
  EdgeList::const_iterator ite;
  do {
    best = next;
    itm = v2e.find(best);
    assert(itm != v2e.end());
    for (ite = itm->second.begin(); ite != itm->second.end(); ite++) {
      idx = ite->opposed(best);
      dist = norm(p - vertex(idx));
      if (dist < dmin) {
        next = idx;
        dmin = dist;
        delta = dmin - dist;
      }
    }
  } while (next != best and delta > gmepsilon);

  return best;
}

Real Triangulation::solidAngle(uint idx) const
{
  // compute solid angle at vertex idx
  FaceMap::const_iterator fmi = v2f.find(idx);
#ifndef NDEBUG
  if (nrm.size() < idx)
    throw Error("No such normal index "+str(idx));
  if (fmi == v2f.end())
    throw Error("Vertex not found in face neighbour list.");
#endif

  Real sum(0.0);
  FaceList::const_iterator itf;
  for (itf = fmi->second.begin(); itf != fmi->second.end(); itf++) {
    sum += itf->solidAngle(idx);
  }

  return (sum > 0) ? sum : 4*PI+sum;
}

Real Triangulation::edgeAngleTrans(const Edge & e) const
{
  // compute angle between faces containing e
  CrossMap::const_iterator cmi = e2f.find(e);
  if (cmi == e2f.end())
    throw Error("No such edge in neighbourhood map.");

  if (cmi->second.size() < 2)
    throw Error("Angle undefined for singly connected edges.");
  else if (cmi->second.size() > 2)
    throw Error("More than two faces connected to this edge.");

  set<Face>::const_iterator left, right;
  left = right = cmi->second.begin(); right++;
  Vct3 n1 = left->normal();
  Vct3 n2 = right->normal();
  return arg(n1,n2);
}

Real Triangulation::edgeAngleLong(const Edge & e) const
{
  // compute angle between vertex normals
  Vct3 n1, n2, np, nmid;
  n1 = nrm[e.source()];
  n2 = nrm[e.target()];
  nmid = 0.5*(n1+n2);
  np = cross(nmid, vtx[e.target()]-vtx[e.source()]).normalized();
  n1 = n1 - np*dot(n1,np);
  n2 = n2 - np*dot(n2,np);
  return arg(n1,n2);
}

istream & Triangulation::readGTS(istream & is)
{
  // read surface in GTS format (http://gts.sf.net)
  string buf;
  uint nvertex, nedge, nface;
  is >> nvertex >> nedge >> nface;
  getline(is, buf);

  // clear everything
  vtx.clear();
  nrm.clear();
  edges.clear();
  faces.clear();
  v2e.clear();
  v2f.clear();

  Vct3 v;
  for (uint i=0; i<nvertex; i++) {
    is >> v[0] >> v[1] >> v[2];
    vtx.push_back(v);
  }

  // read edges
  uint from, to;
  for (uint i=0; i<nedge; i++) {
    is >> from >> to;
    from--; to--;         // GTS uses 1-based indexing
    Edge e(this, from, to);
    edges.push_back(e);
    v2e[from].push_back(e);
    v2e[to].push_back(e);
  }

  // read faces
  int ie1, ie2, ie3;
  EdgeList::const_iterator eit1, eit2, eit3;
  for (uint i=0; i<nface; i++) {
    is >> ie1 >> ie2 >> ie3;
    ie1--; ie2--; ie3--;

    eit1 = eit2 = eit3 = edges.begin();
    advance(eit1, ie1);
    advance(eit2, ie2);
    advance(eit3, ie3);

    Face f(this, *eit1, *eit2, *eit3);
    faces.push_back(f);

    v2f[f.vertex(1)].push_back(f);
    v2f[f.vertex(2)].push_back(f);
    v2f[f.vertex(3)].push_back(f);
    e2f[*eit1].insert(f);
    e2f[*eit2].insert(f);
    e2f[*eit3].insert(f);
  }
  recompNormals();

  return is;
}

ostream & Triangulation::writeGTS(ostream & os) const
{
  // write output which is compatible with the GNU triangularization library
  os << vtx.size() << "  " << edges.size() << "  " << faces.size() << endl;
  PointList<3>::const_iterator vit;
  for (vit = vtx.begin(); vit != vtx.end(); vit++)
    os << (*vit)[0] << "  " << (*vit)[1] << "  " << (*vit)[2] << endl;

  EdgeList::const_iterator eit;
  for (eit = edges.begin(); eit != edges.end(); eit++)
    os << "  " << (*eit).source()+1 << "  " << (*eit).target()+1  << endl;

  // copy to vector because we need the indices for the GTS format
  std::vector<Edge> etmp(edges.begin(), edges.end());
  std::sort(etmp.begin(), etmp.end());
  std::vector<Edge>::iterator ite;

  FaceList::const_iterator fit;
  for (fit = faces.begin(); fit != faces.end(); fit++) {
    ite = lower_bound(etmp.begin(), etmp.end(), fit->edge(1));
    os << distance(etmp.begin(), ite) + 1 << "  ";
    ite = lower_bound(etmp.begin(), etmp.end(), fit->edge(2));
    os << distance(etmp.begin(), ite) + 1 << "  ";
    ite = lower_bound(etmp.begin(), etmp.end(), fit->edge(3));
    os << distance(etmp.begin(), ite) + 1 << endl;
  }

  return os;
}

ostream & Triangulation::writeOogl(ostream & os) const
{
  // write output for geomview

  if (nrm.size() == vtx.size()) {
    os << "{ NOFF " << endl;
    os << vtx.size() << "  " << faces.size() << "  " << edges.size() << endl;
    for (uint i=0; i<vtx.size(); i++) {
      Vct3 v = vtx[i], n = nrm[i];
      os << "  " << v[0] << "  " << v[1] << "  " << v[2]
      << "  " << n[0] << "  " << n[1] << "  " << n[2] << endl;
    }
  } else {
    os << "{ OFF " << endl;
    os << vtx.size() << "  " << faces.size() << "  " << edges.size() << endl;

    for (uint i=0; i<vtx.size(); i++) {
      Vct3 v = vtx[i];
      os << "  " << v[0] << "  " << v[1] << "  " << v[2] << endl;
    }
  }

  FaceList::const_iterator fit;
  for (fit = faces.begin(); fit != faces.end(); fit++)
    os << "  3 " << fit->vertex(1) << "  " << fit->vertex(2) << "  "
    << fit->vertex(3) << endl;
  os << "}" << endl;

  return os;
}

ostream & Triangulation::writeObj(std::ostream & os) const
{
  // write output in .OBJ format (Alias Wavefront text)

  os << "# file written by genua/Triangulation" << endl
     << "# " << nvertices() << " vertices, " 
     << nfaces() << " elements" << endl;
  for (uint i=0; i<vtx.size(); ++i)
    os << "v " << vtx[i] << endl;
  
  uint vi[3];
  face_iterator itf;
  for (itf = face_begin(); itf != face_end(); ++itf) {
    itf->getVertices(vi);
    os << "f " << vi[0]+1 << " " << vi[1]+1 << " " << vi[2]+1 << endl;
  }
  
  return os;
}

void Triangulation::triangulate(const PointGrid<3> & pg)
{
  // create surface triangularization
  vtx.clear();
  nrm.clear();
  edges.clear();
  faces.clear();
  v2e.clear();
  v2f.clear();

  // compute vertices
  for (uint j=0; j<pg.ncols(); j++)
    for (uint i=0; i<pg.nrows(); i++)
      vtx.push_back(pg(i,j));

  uint p1, p2, p3, p4;
  for (uint i=0; i<pg.nrows()-1; i++) {
    for (uint j=0; j<pg.ncols()-1; j++) {
      p1 = i + j*pg.nrows();
      p2 = i+1 + j*pg.nrows();
      p3 = i+1 + (j+1)*pg.nrows();
      p4 = i + (j+1)*pg.nrows();

      Edge e1(this, p1, p2);
      Edge e2(this, p2, p3);
      Edge e4(this, p4, p3);
      Edge e5(this, p1, p4);

      if (i%2 == j%2) {
        Edge e3(this, p1, p3);
        faces.push_back( Face(this, e3, e1, e2) );
        faces.push_back( Face(this, e5, e3, e4) );
      } else {
        Edge e3(this, p4, p2);
        faces.push_back( Face(this, e5, e1, e3) );
        faces.push_back( Face(this, e4, e3, e2) );
      }
    }
  }
}

void Triangulation::updateNeighbours()
{
  // recompute neighbourhood lists
  v2e.clear();
  v2f.clear();
  e2f.clear();

  EdgeList::const_iterator itedge;
  for (itedge = edges.begin(); itedge != edges.end(); itedge++) {
    v2e[itedge->source()].push_back(*itedge);
    v2e[itedge->target()].push_back(*itedge);
  }

  EdgeMap::iterator itm;
  for (itm = v2e.begin(); itm != v2e.end(); itm++) {
    itm->second.sort();
    itm->second.unique();
  }

  FaceList::const_iterator itface;
  for (itface = faces.begin(); itface != faces.end(); itface++) {
    v2f[itface->vertex(1)].push_back(*itface);
    v2f[itface->vertex(2)].push_back(*itface);
    v2f[itface->vertex(3)].push_back(*itface);
    e2f[itface->edge(1)].insert(*itface);
    e2f[itface->edge(2)].insert(*itface);
    e2f[itface->edge(3)].insert(*itface);
  }

  FaceMap::iterator itr;
  for (itr = v2f.begin(); itr != v2f.end(); itr++) {
    itr->second.sort();
    itr->second.unique();
  }
}

void Triangulation::recompNormals()
{
  // recompute normal vectors, requires that neighbour lists are up-to-date!
  nrm.clear();

  Vct3 vn;
  face_iterator itf;
  for (uint i=0; i<v2f.size(); i++) {
    vn.clear();
    for (itf = v2f[i].begin(); itf != v2f[i].end(); itf++) {
      vn += itf->corner(i) * itf->normal().normalized();
    }
    if (norm(vn) != 0)
      vn /= norm(vn);

    nrm.push_back(vn);
  }
}

bool Triangulation::invalidFace(const Face & f) const
{
  uint v[3];
  f.getVertices(v);
  if (v[0] == v[1])
    return true;
  if (v[0] == v[2])
    return true;
  if (v[1] == v[2])
    return true;

  Vct3 pt1, pt2, pt3, n;
  pt1 = vertex(v[0]);
  pt2 = vertex(v[1]);
  pt3 = vertex(v[2]);
  n = cross(pt2-pt1, pt3-pt1);
  return (norm(n) < gmepsilon);
}

bool Triangulation::invalidEdge(const Edge & e) const
{
  if (e.target() == e.source())
    return true;

  Vct3 pt1, pt2;
  pt1 = vertex(e.source());
  pt2 = vertex(e.target());
  return (norm(pt2-pt1) < gmepsilon);
}

void Triangulation::unify(Real threshold, bool bonly)
{
  // make vertex list unique
  Indices bdv;

  // if necessary, identify boundary vertices
  if (bonly) {
    Indices tmp;
    edge_iterator ite;
    for (ite = edge_begin(); ite != edge_end(); ++ite)
      if (ite->degree() < 2) {
        tmp.push_back(ite->source());
        tmp.push_back(ite->target());
      }
    std::sort(tmp.begin(), tmp.end());
    std::unique_copy(tmp.begin(), tmp.end(), back_inserter(bdv));
  }

  // construct search tree
  BSearchTree tree(vtx);

  // find (near) identical vertices
  set<uint> dupl;
  Indices repl(vtx.size()), idt;
  uint count(0);
  PointList<3> kept;
  for (uint i=0; i<vtx.size(); i++) {
    if (dupl.find(i) == dupl.end()) {
      repl[i] = count;
      if (!bonly or binary_search(bdv.begin(), bdv.end(), i)) {
        idt.clear();
        tree.find(vtx[i], threshold, idt);
        // idt = tree.equal(vtx[i], threshold);
        if (idt.size() > 1) {
          for (uint j=0; j<idt.size(); j++) {
            if (idt[j] > i) {
              dupl.insert(idt[j]);
              repl[idt[j]] = count;
            }
          }
        }
      }
      count++;
      kept.push_back(vtx[i]);
    }
  }
  vtx.swap(kept);

  // change face list
  FaceList ftmp;
  FaceList::iterator itf;
  uint p[3];
  for (itf = faces.begin(); itf != faces.end(); itf++) {
    for (uint i=0; i<3; i++)
      p[i] = repl[ itf->vertex(i+1) ];
    ftmp.push_back( Face(this, p[0], p[1], p[2]) );
  }
  faces = ftmp;

  // drop unreferenced vertices
  v2f.clear();
  set<uint> iset;
  for (itf = faces.begin(); itf != faces.end(); itf++)
    for (uint i=1; i<4; i++) {
      iset.insert(itf->vertex(i));
      v2f[itf->vertex(i)].push_back(*itf);
    }

  Indices idx(iset.begin(), iset.end());
  rename(idx);

  // invalidate normals
  nrm.clear();
}

ostream & Triangulation::check(ostream & os) const
{
  // check for internal consistency
  uint count(0);
  edge_iterator ite;
  cout << "Vertices: " << vtx.size() << endl;
  cout << "Edges: " << edges.size() << endl;
  cout << "Faces: " << faces.size() << endl;
  for (ite = edge_begin(); ite != edge_end(); ite++) {
    if (ite->source() >= vtx.size())
      cout << "Edge " << count << " invalid source index " << ite->source() << endl;
    if (ite->target() >= vtx.size())
      cout << "Edge " << count << " invalid target index " << ite->target() << endl;
    count++;
  }

  count = 0;
  uint ip[3];
  Edge eg[3];
  face_iterator itf;
  for (itf = face_begin(); itf != face_end(); itf++) {
    for (uint i=0; i<3; i++) {
      ip[i] = itf->vertex(i+1);
      eg[i] = itf->edge(i+1);
      if (ip[i] >= vtx.size())
        cout << "Face " << count << " invalid vertex " << ip[i] << endl;
      if (find(edge_begin(), edge_end(), eg[i]) == edges.end())
        cout << "Face " << count << " edge " << i+1 << " not in edge list." << endl;
    }
    count++;
  }

  count = 0;
  CrossMap::const_iterator itc;
  if (e2f.size() != edges.size())
    os << "Edge2Face map inconsistent. Size: " << e2f.size() << endl;
  for (itc = e2f.begin(); itc != e2f.end(); itc++) {
    if (itc->second.size() < 2)
      os << ++count << " Singly connected edge. " << endl;
    else if (itc->second.size() > 2) {
      os << ++count << " Non-plane edge connection at ";
      os << str(0.5*(vtx[itc->first.source()]+vtx[itc->first.target()])) << endl;
    }
  }

  return os;
}

void Triangulation::rebuildEdgeList()
{
  // create edges from face list
  edges.clear();
  face_iterator itf;
  Edge e[3];
  for (itf = face_begin(); itf != face_end(); itf++) {
    itf->getEdges(e);
    edges.insert(edges.end(), e, e+3);
  }
  edges.sort();
  edges.unique();
}

void Triangulation::cleanup(Real threshold, bool bonly)
{
  // remove duplicates and update
  unify(threshold, bonly);

  FaceList::iterator itf;
  set<uint> iset;
  for (itf = faces.begin(); itf != faces.end(); itf++) {
    itf->setSurface(this);
    itf->orderCanonical();
    for (uint i=1; i<4; i++)
      iset.insert(itf->vertex(i));
  }
  Indices idx(iset.begin(), iset.end());
  rename(idx);

  faces.remove_if( unMemFun(&Triangulation::invalidFace,this) );
  faces.sort();
  faces.unique();

  rebuildEdgeList();
  edges.remove_if( unMemFun(&Triangulation::invalidEdge,this) );

  updateNeighbours();
  recompNormals();
}

void Triangulation::fixate()
{
  // update connectivity and normals
  FaceList::iterator itf;
  Indices idx;
  const uint *vi;
  for (itf = faces.begin(); itf != faces.end(); itf++) {
    itf->setSurface(this);
    itf->orderCanonical();
    vi = itf->vertices();
    idx.insert(idx.end(), vi, vi+3);
  }
  sort_unique(idx);
  
  faces.remove_if( unMemFun(&Triangulation::invalidFace,this) );
  faces.sort();
  faces.unique();
  
  rename(idx);
  rebuildEdgeList();
  updateNeighbours();
  recompNormals();
}

bool Triangulation::onBoundary(const Edge & e) const
{
  // check if e lies on boundary
  CrossMap::const_iterator itc = e2f.find(e);
  if (itc == e2f.end())
    throw Error("Edge not in map, update neighbourhood information!");
  if (itc->second.size() == 1)
    return true;
  else
    return false;
}

//void Triangulation::filterNormals(uint niter, Real kappa, Real lambda)
//{
//  // normal vector filtering without edge elimination
//  Vct3 m;
//  set<uint> nb;
//  set<uint>::const_iterator itv;
//  Real cphi, w, d;
//  for (uint iter=0; iter<niter; iter++) {
//    for (uint i=0; i<vtx.size(); i++) {
//      nb = nbVertices(i);
//      Real minarg(1.0), maxarg(-1.0);
//      for (itv = nb.begin(); itv != nb.end(); itv++) {
//        cphi = dot(nrm[i],nrm[*itv]);
//        minarg = min(minarg, cphi);
//        maxarg = max(maxarg, cphi);
//      }
//      w = pow(minarg,kappa);
//      m = nrm[i];
//      for (itv = nb.begin(); itv != nb.end(); itv++) {
//        cphi = dot(nrm[i],nrm[*itv]);
//        d = norm(vtx[i] - vtx[*itv]);
//        m += w/d * pow(cphi/maxarg, lambda) * nrm[*itv];
//      }
//      nrm[i] = m.normalized();
//    }
//  }
//}
//
//void Triangulation::smooth(uint niter)
//{
//  // geometric improvement
//  set<uint> nbv;
//  set<uint>::const_iterator itv;
//  face_iterator itf, best;
//  Vct3 pjt, vn;
//  Real xi, eta, mindist;
//  for (uint iter=0; iter<niter; iter++) {
//    // move local vertices to barycenters of surrounding
//    Vct3 ctr;
//    for (uint i=0; i<10; i++) {
//      nbv = nbVertices(i);
//      for (itv=nbv.begin(); itv != nbv.end(); itv++)
//        ctr += vtx[*itv];
//      ctr /= nbv.size();
//      mindist = 1e18;
//      for (itf = v2f[i].begin(); itf != v2f[i].end(); itf++) {
//        pjt = itf->project(ctr);
//        if (pjt[0] >= 0 and pjt[0] <= 1 and
//            pjt[1] >= 0 and pjt[1] <= 1 and
//            pjt[0]+pjt[1] <= 1 and fabs(pjt[2]) < mindist) {
//          xi = pjt[0];
//          eta = pjt[1];
//          mindist = fabs(pjt[2]);
//          best = itf;
//        }
//      }
//
//      if (mindist == 1e18)
//        throw Error("No projection face found.");
//
//      FaceBubble fb(*best);
//      vtx[i] = fb.eval(xi,eta);
//      // compute new normal vector at i
//      for (itf = v2f[i].begin(); itf != v2f[i].end(); itf++)
//        vn += itf->normal().normalized() / norm(vtx[i]-itf->center());
//      nrm[i] = vn.normalized();
//    }
//  }
//}

BndBox Triangulation::bbox() const
{
  // compute bounding box
  Vct3 plo, phi, p;
  plo = point(huge, huge, huge);
  phi = point(-huge, -huge, -huge);
  for (uint i=0; i<vtx.size(); i++) {
    p = vtx[i];
    plo[0] = min(plo[0], p[0]);
    plo[1] = min(plo[1], p[1]);
    plo[2] = min(plo[2], p[2]);
    phi[0] = max(phi[0], p[0]);
    phi[1] = max(phi[1], p[1]);
    phi[2] = max(phi[2], p[2]);
  }

  return BndBox(plo,phi);
}

void Triangulation::merge(const Triangulation & tg)
{
  // merge in other surface
  uint offset = vtx.size();
  for (uint i=0; i<tg.nvertices(); i++)
    addVertex(tg.vertex(i));

  const uint *vi;
  face_iterator itf;
  for (itf = tg.face_begin(); itf != tg.face_end(); itf++) {
    vi = itf->vertices();
    addFace( Face(this, vi[0]+offset, vi[1]+offset, vi[2]+offset) );
  }
}

void Triangulation::rename(const Indices & idx)
{
  // change vertex indices, drop unreferenced vertices

  if (vtx.size() == nrm.size()) {
    PointList<3> tv(idx.size()), tn(idx.size());
    for (uint i=0; i<idx.size(); i++) {
      tv[i] = vtx[idx[i]];
      tn[i] = nrm[idx[i]];
    }
    tv.swap(vtx);
    tn.swap(nrm);
    assert(vtx.size() == idx.size());
  } else {
    PointList<3> tv(idx.size());
    for (uint i=0; i<idx.size(); i++)
      tv[i] = vtx[idx[i]];
    tv.swap(vtx);
    assert(vtx.size() == idx.size());
  }

  uint red, green, blue;
  FaceList::iterator itf;
  Indices::const_iterator pos;
  for (itf = faces.begin(); itf != faces.end(); itf++) {
    red = itf->vertex(v_red);
    green = itf->vertex(v_green);
    blue = itf->vertex(v_blue);

    pos = lower_bound(idx.begin(), idx.end(), red);
    assert(*pos == red);
    red = distance(idx.begin(), pos);
    pos = lower_bound(idx.begin(), idx.end(), green);
    assert(*pos == green);
    green = distance(idx.begin(), pos);
    pos = lower_bound(idx.begin(), idx.end(), blue);
    assert(*pos == blue);
    blue = distance(idx.begin(), pos);
    *itf = Face(this, red, green, blue);
  }
}

ostream & Triangulation::writeSTL(ostream & os) const
{
  // write to STL file
  os << "solid" << endl;
  face_iterator itf;
  Vct3 v;
  for (itf = face_begin(); itf != face_end(); itf++) {
    v = itf->normal().normalized();
    os << "facet normal " << v[0] << "  " << v[1] << "  " << v[2] << endl;
    os << " outer loop" << endl;
    for (uint i=0; i<3; i++) {
      v = vertex(itf->vertex(i+1));
      os << "  vertex " << v[0] << "  " << v[1] << "  " << v[2] << endl;
    }
    os << " endloop" << endl;
    os << "endfacet" << endl;
  }
  os << "endsolid" << endl;
  return os;
}

ostream & Triangulation::writeTec(ostream & os) const
{
  // write tecplot file (ascii)
  os << "VARIABLES = \"X\", \"Y\", \"Z\"" << endl;
  os << "ZONE N = " << vtx.size() << ", E = " << faces.size()
  << ", F = FEPOINT, ET = TRIANGLE" << endl;

  os.precision(16);
  for (uint i=0; i<vtx.size(); ++i)
    os << vtx[i][0] << " " << vtx[i][1] << " " << vtx[i][2] << endl;
  os << endl;

  uint v[3];
  face_iterator itf;
  for (itf = face_begin(); itf != face_end(); ++itf) {
    itf->getVertices(v);
    os << v[0]+1 << " " << v[1]+1 << " " << v[2]+1 << endl;
  }

  return os;
}

void Triangulation::splitEdge(const Edge & e, bool ipol)
{
  // local refinement
  set<Face> fs = e2f[e];
  if (fs.size() > 2) {
    string msg("Cannot split triply connected edge\n");
    msg += "from: "+str(vertex(e.source()));
    msg += " to: "+str(vertex(e.target()));
    throw Error(msg);
  }

  if (ipol) {
    EdgeCurve ec(e);
    vtx.push_back(ec.eval(0.5));
  } else {
    vtx.push_back(0.5*(vtx[e.source()] + vtx[e.target()]));
  }
  Vct3 nn = 0.5*(normal(e.source()) + normal(e.target()));
  nrm.push_back( nn/norm(nn) );

  if (fs.size() == 1) {
    return;

    cout << "single connection." << endl;
    Face f = *(fs.begin());
    uint p[4];
    for (uint i=0; i<3; i++)
      p[i] = f.vertex(i+1);
    p[3] = vtx.size()-1;

    Face f1(this, p[0], p[3], p[2]);
    Face f2(this, p[1], p[2], p[3]);

    for (uint i=1; i<4; i++)
      e2f[f.edge(i)].erase(f);

    faces.remove(f);
    faces.push_back(f1);
    faces.push_back(f2);

    Edge e03(this, min(p[0],p[3]), max(p[0],p[3]) );
    Edge e23(this, min(p[2],p[3]), max(p[2],p[3]) );
    Edge e02(this, min(p[0],p[2]), max(p[0],p[2]) );
    Edge e13(this, min(p[1],p[3]), max(p[1],p[3]) );
    Edge e12(this, min(p[1],p[2]), max(p[1],p[2]) );

    edges.push_back(e23);
    e2f[e23].insert(f1);
    e2f[e23].insert(f2);
    e2f[e03].insert(f1);
    e2f[e02].insert(f1);
    e2f[e13].insert(f2);
    e2f[e12].insert(f2);
  } else if (fs.size() == 2)  {

    Face fl, fr;
    set<Face>::iterator sfi = fs.begin();
    fl = *sfi;
    sfi++;
    fr = *sfi;

    uint p1, p2, p3, p4, p5;
    p1 = e.source();
    p2 = fr.opposed(e);
    p3 = e.target();
    p4 = fl.opposed(e);
    p5 = vtx.size()-1;                   Triangulation rr;

    Edge e15(this, p1,p5);
    Edge e35(this, p3,p5);
    edges.push_back(e15);
    edges.push_back(e35);

    Vct3 nr, nl;
    nr = cross(vtx[p2]-vtx[p1], vtx[p3]-vtx[p1]);
    nl = cross(vtx[p3]-vtx[p1], vtx[p4]-vtx[p1]);
    Face f1, f2, f3, f4;
    if ( dot(nl,fl.normal()) < 0) {
      f1 = Face(this, p4,p5,p1);
      f2 = Face(this, p5,p4,p3);
    } else {
      f1 = Face(this, p1,p5,p4);
      f2 = Face(this, p3,p4,p5);
    }
    if ( dot(nr,fr.normal()) < 0) {
      f3 = Face(this, p5,p2,p1);
      f4 = Face(this, p5,p3,p2);
    } else {
      f3 = Face(this, p1,p2,p5);
      f4 = Face(this, p2,p3,p5);
    }

    for (uint i=1; i<4; i++) {
      e2f[fl.edge(i)].erase(fl);
      e2f[fr.edge(i)].erase(fr);
    }
    faces.remove(fl);
    faces.remove(fr);

    faces.push_back(f1);
    faces.push_back(f2);
    faces.push_back(f3);
    faces.push_back(f4);

    Edge e14(this, min(p1,p4), max(p1,p4));
    Edge e34(this, min(p3,p4), max(p3,p4));
    Edge e23(this, min(p2,p3), max(p2,p3));
    Edge e12(this, min(p1,p2), max(p1,p2));
    Edge e25(this, min(p2,p5), max(p2,p5));
    Edge e45(this, min(p4,p5), max(p4,p5));

    e2f[e15].insert(f1);
    e2f[e15].insert(f3);
    e2f[e35].insert(f2);
    e2f[e35].insert(f4);
    e2f[e25].insert(f3);
    e2f[e25].insert(f4);
    e2f[e45].insert(f1);
    e2f[e45].insert(f2);
    e2f[e14].insert(f1);
    e2f[e34].insert(f2);
    e2f[e23].insert(f4);
    e2f[e12].insert(f3);
  }
  edges.remove(e);
  e2f.erase(e);
}

void Triangulation::collapseEdge(const Edge & e)
{
  // collapse edge, delete faces
  EdgeList::iterator pos;
  pos = lower_bound(edges.begin(), edges.end(), e);
  if (pos == edges.end() or *pos != e)
    return;

  uint src, trg, ni;
  src = e.source();
  trg = e.target();
  ni = vtx.size();

  
  vtx.push_back(0.5*(vtx[src]+vtx[trg]));
  Vct3 nn = 0.5*(nrm[src] + nrm[trg]);
  normalize(nn);
  nrm.push_back(nn);
  removeEdge(e);

  FaceList aff;
  std::copy(v2f[src].begin(), v2f[src].end(), back_inserter(aff));
  std::copy(v2f[trg].begin(), v2f[trg].end(), back_inserter(aff));
  aff.sort();
  aff.unique();

  Edge etp;
  Face tmp;
  FaceList::iterator itf;
  for (itf = aff.begin(); itf != aff.end(); ++itf) {
    nn = itf->normal();
    removeFace(*itf);
    tmp = *itf;
    tmp.replace(src, ni);
    tmp.replace(trg, ni);
    if (dot(nn,tmp.normal()) < 0)
      tmp.reverse();
    if (not invalidFace(tmp))
      insertFace(tmp);
  }
}

void Triangulation::removeFace(const Face & f)
{
  // find and erase face from connectivity lists
  FaceList::iterator pos;
  pos = lower_bound(faces.begin(), faces.end(), f);
  if (pos != faces.end() and *pos == f)
    faces.erase(pos);
  else
    return;
  
  for (uint i=1; i<4; i++)
    v2f[f.vertex(i)].remove(f);
  for (uint i=1; i<4; i++)
    e2f[f.edge(i)].erase(f);
}

void Triangulation::removeEdge(const Edge & e)
{
  // find and erase edge from connectivity lists
  EdgeList::iterator pos;
  pos = lower_bound(edges.begin(), edges.end(), e);
  if (pos != edges.end() and *pos == e)
    edges.erase(pos);
  else
    return;

  v2e[e.source()].remove(e);
  v2e[e.target()].remove(e);
  e2f.erase(e);
}

void Triangulation::relax(uint ni)
{
  // geometric vertex shift to reduce sharp edges
  PointList<3> tmp(vtx.size());
  for (uint k=0; k<ni; k++) {
    for (uint i=0; i<vtx.size(); i++) {
      tmp[i] = barycenter(i);
    }
    vtx.swap(tmp);
  }
  return;
}

Real Triangulation::ridgeCriterion(const Edge & e) const
{
  // compute ridge criterion
  CrossMap::const_iterator itm = e2f.find(e);
  if (itm == e2f.end() or itm->second.size() != 2)
    return 0;

  set<Face>::const_iterator itf;
  itf = itm->second.begin();
  Face f1(*itf); itf++;
  Face f2(*itf);

  Vct3 ne = nrm[e.source()]+nrm[e.target()];
  ne /= norm(ne);
  Vct3 em = 0.5*(vtx[e.source()]+vtx[e.target()]);
  Vct3 cg = 0.5*(f1.center()+f2.center());
  Real phi = fabs(arg(f1.normal(),f2.normal()));
  if (dot(cg-em,ne) > 0)
    return -phi;
  else
    return phi;
}

Real Triangulation::vertexArea(uint i) const
{
  // compute area of the dual mesh cell assigned to i
  Real va(0);
  FaceMap::const_iterator itm = v2f.find(i);
  if (itm == v2f.end())
    return va;
  face_iterator itf, first, last;
  first = itm->second.begin();
  last = itm->second.end();
  for (itf = first; itf != last; itf++)
    va += norm(itf->normal())/6.;
  return va;
}

Vector Triangulation::intersectingEdges(const Plane & pln, EdgeList & el) const
{
  // find edges intersecting plane and corresponding parameters
  Vector lp;
  edge_iterator ite;

  // find all edges which intersect
  for (ite = edge_begin(); ite != edge_end(); ++ite) {
    Vct3 p1, p2;
    p1 = vertex(ite->source());
    p2 = vertex(ite->target());
    Line<3> ln(p1,p2);
    PlnIts its = pln.pierce(ln);
    if (its.pierces and its.parm >= 0 and its.parm <= 1) {
      el.push_back(*ite);
      lp.push_back(its.parm);
    }
  }
  return lp;
}

Real Triangulation::area() const
{
  // sum of face areas
  Real sum(0);
  face_iterator itf;
  for (itf = face_begin(); itf != face_end(); itf++)
    sum += norm(itf->normal());
  return 0.5*sum;
}

Real Triangulation::volume() const
{
  Vct3 a, b, c;
  Real sum(0);
  const uint *vi;
  face_iterator itf;
  for (itf = face_begin(); itf != face_end(); itf++) {
    vi = itf->vertices();
    a = vtx[vi[0]];
    b = vtx[vi[1]];
    c = vtx[vi[2]];
    sum += dot(cross(a,b),c);
  }
  return 0.5*sum;
}

Real Triangulation::shortestEdgeLength() const
{
  // find sortest edge and return its length
  Real elen, slen(huge);
  edge_iterator ite;
  for (ite = edge_begin(); ite != edge_end(); ite++) {
    elen = norm(vertex(ite->source()) - vertex(ite->target()));
    slen = min(slen,elen);
  }
  return slen;
}

Real Triangulation::estimCurvature(uint i, const Vct3 & s) const
{
  // estimate curvature tensor at i
  FaceMap::const_iterator itm = v2f.find(i);
  if (itm == v2f.end())
    throw Error("Vertex not found in face map: ", i);
  FaceList::const_iterator itf;

  Real sum(0), w, wsum(0);
  for (itf = itm->second.begin(); itf != itm->second.end(); ++itf) {
    Vct3 r = itf->center() - vtx[i];
    Vct3 dn = itf->normal().normalized() - nrm[i];
    w = itf->corner(i);
    wsum += w;
    sum += w*dot(dn,s) / norm(r);
  }
  return sum / wsum;
}

void Triangulation::reverse()
{
  FaceList::iterator itf;
  for (itf = faces.begin(); itf != faces.end(); ++itf)
    itf->reverse();
  fixate();
}

SpMatrix Triangulation::gradient(uint i) const
{
  assert(i < vtx.size());
  SpMatrix gm(3,vtx.size());
  face_iterator itf, first, last;
  first = nb_face_begin(i);
  last = nb_face_end(i);
  uint vi[3];
  Real wsum(0), wf;
  Mtx33 fgm;
  for (itf = first; itf != last; ++itf) {
    itf->getVertices(vi);
    wf = itf->corner(i);
    itf->gradient(fgm);
    for (uint j=0; j<3; ++j)
      for (uint k=0; k<3; ++k)
        gm(k, vi[j]) += wf*fgm(k,j);
    wsum += wf;
  }
  wsum = 1./wsum;
  gm *= wsum;
  return gm;
}

Vct3 Triangulation::gradient(uint i, const Vector & x) const
{
  assert(i < vtx.size());
  Vct3 gradx;
  face_iterator itf, first, last;
  first = nb_face_begin(i);
  last = nb_face_end(i);
  Real wsum(0), wf;
  for (itf = first; itf != last; ++itf) {
    wf = itf->corner(i);
    wsum += wf;
    gradx += wf*itf->gradient(x);
  }
  wsum = 1./wsum;
  gradx *= wsum;
  return gradx;
}

Indices Triangulation::nearest(const PointList<3> & pts) const
{
  cerr << "Building search tree.. " << endl;
  cerr.flush();
  BSearchTree btree(vtx);
  cerr << "done." << endl;
  Indices found(pts.size());
  for (uint i=0; i<pts.size(); ++i)
    found[i] = btree.nearest(pts[i]);
  return found;  
}

XmlElement Triangulation::toXml() const
{
  // create xml representation
  XmlElement xv("Vertices");
  xv["count"] = str(vtx.size());
  stringstream ss;
  ss.precision(15);
  for (uint i=0; i<vtx.size(); ++i)
    ss << vtx[i][0] << " " << vtx[i][1] << " " << vtx[i][2] << endl;
  xv.text() = ss.str();

  XmlElement xf("Faces");
  xf["count"] = str(faces.size());
  uint v[3];
  face_iterator itf;
  stringstream st;
  for (itf = face_begin(); itf != face_end(); ++itf) {
    itf->getVertices(v);
    st << v[0] << " " << v[1] << " " << v[2] << endl;
  }
  xf.text() = st.str();

  XmlElement xe("Triangulation");
  xe.append(std::move(xv));
  xe.append(std::move(xf));

  return xe;
}

void Triangulation::fromXml(const XmlElement & xe)
{
  // interpret xml element
  if (xe.name() != "Triangulation")
    throw Error("This is not a 'Triangulation' XML element.");

  XmlElement::const_iterator ite;
  for (ite = xe.begin(); ite != xe.end(); ++ite) {
    if (ite->name() == "Vertices") {
      uint n = atol( ite->attribute("count").c_str() );
      vtx.resize(n);
      stringstream ss;
      ss << ite->text();
      for (uint i=0; i<n; ++i)
        ss >> vtx[i][0] >> vtx[i][1] >> vtx[i][2];
    } else if (ite->name() == "Faces") {
      uint n = atol( ite->attribute("count").c_str() );
      stringstream ss;
      ss << ite->text();
      uint r,g,b;
      for (uint i=0; i<n; ++i) {
        ss >> r >> g >> b;
        addFace( Face(this,r,g,b) );
      }
    }
  }
  fixate();
}

void Triangulation::writeBin(ostream & os) const
{
  // write to binary stream
  uint nv = vtx.size();
  uint nf = faces.size();
  os.write((const char*) &nv, sizeof(uint));
  os.write((const char*) &nf, sizeof(uint));

  vector<double> va(3*vtx.size());
  for (uint i=0; i<vtx.size(); ++i) {
    va[3*i] = vtx[i][0];
    va[3*i+1] = vtx[i][1];
    va[3*i+2] = vtx[i][2];
  }
  os.write((const char*) &va[0], va.size()*sizeof(double));

  const uint *v;
  uint k(0);
  vector<uint> vf(3*faces.size());
  face_iterator itf;
  for (itf = face_begin(); itf != face_end(); ++itf) {
    v = itf->vertices();
    vf[3*k] = v[0];
    vf[3*k+1] = v[1];
    vf[3*k+2] = v[2];
    k++;
  }
  os.write((const char*) &vf[0], vf.size()*sizeof(uint));
}

void Triangulation::readBin(istream & is)
{
  // read from binary stream
  uint nv, nf;
  is.read((char*) &nv, sizeof(uint));
  is.read((char*) &nf, sizeof(uint));

  vtx.resize(nv);
  vector<double> va(3*nv);
  is.read((char *) &va[0], va.size()*sizeof(double));
  for (uint i=0; i<nv; ++i) {
    vtx[i][0] = va[3*i];
    vtx[i][1] = va[3*i+1];
    vtx[i][2] = va[3*i+2];
  }

  faces.clear();
  vector<uint> vf(3*nf);
  is.read((char *) &vf[0], vf.size()*sizeof(uint));
  for (uint i=0; i<nf; ++i)
    addFace( Face(this, vf[3*i], vf[3*i+1], vf[3*i+2]) );

  fixate();
}

Real Triangulation::megabytes() const
{
  const uint nbListItem = 2*sizeof(char*);
  const uint nbTreeItem = 3*sizeof(char*) + sizeof(int);
  
  Real b;
  b  = sizeof(Triangulation);
  b += (vtx.capacity() + nrm.capacity())*sizeof(Vct3);
  b += faces.size() * (nbListItem + sizeof(Face));
  b += edges.size() * (nbListItem + sizeof(Edge));
  
  // e2f map
  b += e2f.size() * (nbTreeItem + sizeof( std::set<Face> ));
  CrossMap::const_iterator itm;
  for (itm = e2f.begin(); itm != e2f.end(); ++itm)
    b += sizeof(Edge) + nbTreeItem + itm->second.size() * (nbTreeItem + sizeof(Face));
  
  // v2e map
  b += v2e.size() * (nbTreeItem + sizeof(EdgeList));
  EdgeMap::const_iterator ite;
  for (ite = v2e.begin(); ite != v2e.end(); ++ite)
    b += sizeof(uint) + nbTreeItem + ite->second.size() * (nbListItem + sizeof(Edge));
  
  // v2f map
  b += v2f.size() * (nbTreeItem + sizeof(FaceList));
  FaceMap::const_iterator itf;
  for (itf = v2f.begin(); itf != v2f.end(); ++itf)
    b += sizeof(uint) + nbTreeItem + itf->second.size() * (nbListItem + sizeof(Face));
  
  return 1e-6*b;
}

void Triangulation::clear()
{
  vtx.clear();
  nrm.clear();
  faces.clear();
  edges.clear();
  v2e.clear();
  v2f.clear();
  e2f.clear();
}

