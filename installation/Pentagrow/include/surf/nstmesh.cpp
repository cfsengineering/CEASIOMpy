
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
 
#include <genua/meshfields.h>
#include <genua/trimesh.h>
#include <genua/mxmesh.h>
#include <genua/mxsolutiontree.h>
#include <genua/dbprint.h>
#include "nstreader.h"
#include "nstmesh.h"

using namespace std;

uint NstMesh::addVertex(const Vct3 & p, uint gid)
{
  Indices::iterator pos;
  pos = lower_bound(gids.begin(), gids.end(), gid);
  size_t offset = std::distance(gids.begin(), pos);

  gids.insert(pos, gid);
  HybridMesh::insertVertex(offset, p);
  return offset;
}

uint NstMesh::addBeam(uint a, uint b, uint pid)
{
  NstBeam *ep = new NstBeam(this, a, b);
  ep->pid(pid);

  // set default orientation
  Vct3 dir, yax, xax;
  yax = vct(0.0, 1.0, 0.0);
  xax = vct(1.0, 0.0, 0.0);
  dir = vertex(b) - vertex(a);
  Real dx, dy, dz;
  dx = fabs(dir[0]);
  dy = fabs(dir[1]);
  dz = fabs(dir[2]);
  if (dx > dy and dx > dz)
    ep->orientation( cross(dir, yax).normalized() );
  else
    ep->orientation( cross(dir, xax).normalized() );

  return HybridMesh::addElement(ep);
}

uint NstMesh::rconnect(uint a, uint b)
{
  NstRigidBar *ep = new NstRigidBar(this, a, b);
  ep->components(0, 123456, 0, 0);
  return HybridMesh::addElement(ep);
}

uint NstMesh::addBeams(const PointList<3> & pts, uint pid)
{
  const uint np(pts.size());
  uint goff, voff = vtx.size();
  if (gids.empty())
    goff = 1;
  else
    goff = gids.back()+1;
  addVertex(pts[0], goff);
  for (uint i=0; i<np-1; ++i) {
    addVertex(pts[i+1], goff+i+1);
    addBeam(voff+i, voff+i+1, pid);
  }
  return voff;
}

uint NstMesh::addTriR(uint a, uint b, uint c, uint pid, uint mcid)
{
  NstTriaR *ep = new NstTriaR(this, a, b, c);
  ep->pid(pid);
  ep->mcid(mcid);
  return HybridMesh::addElement(ep);
}

uint NstMesh::addQuadR(uint a, uint b, uint c, uint d, uint pid, uint mcid)
{
  NstQuadR *ep = new NstQuadR(this, a, b, c, d);
  ep->pid(pid);
  ep->mcid(mcid);
  return HybridMesh::addElement(ep);
}

void NstMesh::addTriangles(const TriMesh & t, NstTypeId tid,
                           uint pid, uint mcid)
{
  // check if requested type is supported
  if (tid != NstCTRIAR and tid != NstCTRIA3 and tid != NstCTRIA6)
    throw Error("Triangle element type not supported yet.");

  // offset for GID numbers
  uint goff(1);
  if (not gids.empty())
    goff = gids.back()+1;

  // add all nodes
  const uint nvoff(nvertices());
  const uint nv(t.nvertices());
  for (uint i=0; i<nv; ++i)
    addVertex(t.vertex(i), goff+i);
  goff += nv;

  // add elements
  uint a, b, c;
  const uint nf(t.nfaces());
  if (tid == NstCTRIAR) {
    for (uint i=0; i<nf; ++i) {
      const uint *vi(t.face(i).vertices());
      a = nvoff+vi[0];
      b = nvoff+vi[1];
      c = nvoff+vi[2];
      NstTriaR *ep = new NstTriaR(this, a, b, c);
      ep->pid(pid);
      ep->mcid(mcid);
      HybridMesh::addElement(ep);
    }
  } else if (tid == NstCTRIA3) {
    for (uint i=0; i<nf; ++i) {
      const uint *vi(t.face(i).vertices());
      a = nvoff+vi[0];
      b = nvoff+vi[1];
      c = nvoff+vi[2];
      NstTria3 *ep = new NstTria3(this, a, b, c);
      ep->pid(pid);
      ep->mcid(mcid);
      HybridMesh::addElement(ep);
    }
  } else if (tid == NstCTRIA6) {

    // generate edge nodes
    const uint enoff = nvertices();
    const int ned = t.nedges();
    for (int i=0; i<ned; ++i) {
      const TriEdge & e(t.edge(i));
      Vct3 p = 0.5*(t.vertex(e.source()) + t.vertex(e.target()));
      addVertex(p, goff+i);
    }

    // create 6-node triangles
    uint fv[6];
    TriMesh::nb_edge_iterator ite;
    for (uint i=0; i<nf; ++i) {
      const uint *vi(t.face(i).vertices());
      fv[0] = nvoff+vi[0];
      fv[1] = nvoff+vi[1];
      fv[2] = nvoff+vi[2];

      ite = t.f2eBegin(i);
      fv[3] = enoff + ite.index();
      ++ite;
      fv[4] = enoff + ite.index();
      ++ite;
      fv[5] = enoff + ite.index();

      NstTria6 *ep = new NstTria6(this, fv);
      ep->pid(pid);
      ep->mcid(mcid);
      HybridMesh::addElement(ep);
    }
  }
}

void NstMesh::addQuads(const PointGrid<3> & pg, NstTypeId tid,
                       uint pid, uint mcid)
{
  // check if requested type is supported
  if (tid != NstCQUADR and tid != NstCQUAD4 and tid != NstCQUAD8)
    throw Error("Quad element type not supported yet.");

  // offset for GID numbers
  uint goff(1);
  if (not gids.empty())
    goff = gids.back()+1;

  // add all nodes
  const uint nvoff(nvertices());
  const uint nr(pg.nrows());
  const uint nc(pg.ncols());
  const uint nv(nr*nc);
  for (uint i=0; i<nv; ++i)
    addVertex(pg[i], goff+i);
  goff += nv;

  // add elements
  uint a, b, c, d;
  if (tid == NstCQUADR) {
    for (uint i=0; i<nr-1; ++i) {
      for (uint j=0; j<nc-1; ++j) {
        a = nvoff + j*nr + i;
        b = nvoff + j*nr + i+1;
        c = nvoff + (j+1)*nr + i+1;
        d = nvoff + (j+1)*nr + i;
        NstQuadR *ep = new NstQuadR(this, a, b, c, d);
        ep->pid(pid);
        ep->mcid(mcid);
        HybridMesh::addElement(ep);
      }
    }
  } else if (tid == NstCQUAD4) {
    for (uint i=0; i<nr-1; ++i) {
      for (uint j=0; j<nc-1; ++j) {
        a = nvoff + j*nr + i;
        b = nvoff + j*nr + i+1;
        c = nvoff + (j+1)*nr + i+1;
        d = nvoff + (j+1)*nr + i;
        NstQuad4 *ep = new NstQuad4(this, a, b, c, d);
        ep->pid(pid);
        ep->mcid(mcid);
        HybridMesh::addElement(ep);
      }
    }
  } else if (tid == NstCQUAD8) {

    // generate mid-edge points
    DMatrix<uint> hzp(nr-1,nc);
    for (uint i=0; i<nr-1; ++i) {
      for (uint j=0; j<nc; ++j) {
        Vct3 p = 0.5*(pg(i,j) + pg(i+1,j));
        hzp(i,j) = addVertex(p, goff);
        ++goff;
      }
    }
    DMatrix<uint> vtp(nr,nc-1);
    for (uint i=0; i<nr; ++i) {
      for (uint j=0; j<nc-1; ++j) {
        Vct3 p = 0.5*(pg(i,j) + pg(i,j+1));
        vtp(i,j) = addVertex(p, goff);
        ++goff;
      }
    }

    uint vi[8];
    for (uint i=0; i<nr-1; ++i) {
      for (uint j=0; j<nc-1; ++j) {
        vi[0] = nvoff + j*nr + i;
        vi[1] = nvoff + j*nr + i+1;
        vi[2] = nvoff + (j+1)*nr + i+1;
        vi[3] = nvoff + (j+1)*nr + i;
        vi[4] = hzp(i,j);
        vi[5] = vtp(i+1,j);
        vi[6] = hzp(i,j+1);
        vi[7] = vtp(i,j);
        NstQuad8 *ep = new NstQuad8(this, vi);
        ep->pid(pid);
        ep->mcid(mcid);
        HybridMesh::addElement(ep);
      }
    }
  }
}

void  NstMesh::addHinge(const Vct3 & ax, uint dep, uint idep)
{
  // construct two random axes normal to ax
  Vct3 a(ax), b, c;
  //   normalize(a);
  //   random_fill(3, &b[0]);
  //   b -= dot(b, a) * a;
  //   normalize(b);
  //   c = cross(a,b);
  //   normalize(c);
  extend_basis(a, b, c);

  // debug
  //  cout << "Axis " << ax << " b " << b << " c " << c << endl;

  // restrict translational DOFs
  NstSimpleMpc *mpe;
  uint order1[] = {0, 1, 2};
  uint order2[] = {1, 2, 0};
  int ieq(0);
  mpe = new NstSimpleMpc(this, dep, idep);
  for (uint i=0; i<3; ++i) {
    uint k = order1[i];
    if (fabs(b[k]) > gmepsilon)
      mpe->constrain(ieq++, NstDof(k+1), b[k], NstDof(k+1), -b[k] );
  }

  addElement(mpe);
  mpe = new NstSimpleMpc(this, dep, idep);
  ieq = 0;
  for (uint i=0; i<3; ++i) {
    uint k = order2[i];
    if (fabs(c[k]) > gmepsilon)
      mpe->constrain(ieq++, NstDof(k+1), c[k], NstDof(k+1), -c[k] );
  }
  addElement(mpe);
}

void NstMesh::addJoint(uint dep, uint idep)
{
  NstSimpleMpc *ep;
  for (int i=1; i<4; ++i) {
    ep = new NstSimpleMpc(this, dep, idep);
    ep->constrain(NstDof(i), 1.0, NstDof(i), -1.0);
    HybridMesh::addElement(ep);
  }

  //  NstRigidBar *ep = new NstRigidBar(this, dep, idep);
  //  ep->components(456, 123, 0, 0);
  //  HybridMesh::addElement(ep);
}

void NstMesh::addBoltSpider(const PointList<3> & pa, const PointList<3> & pb)
{
  Vct3 ca, cb;
  const int na = pa.size();
  const int nb = pb.size();
  for (int i=0; i<na; ++i)
    ca += pa[i];
  ca *= 1.0 / na;
  for (int i=0; i<nb; ++i)
    cb += pb[i];
  cb *= 1.0 / nb;

  uint gtop = *max_element(gids.begin(), gids.end());
  uint ga = addVertex(ca, gtop+1);
  uint gb = addVertex(cb, gtop+2);

  for (int i=0; i<na; ++i)
    rconnect( nearest(pa[i]), ga );
  for (int i=0; i<nb; ++i)
    rconnect( nearest(pb[i]), gb );
  rconnect(ga, gb);
}

uint NstMesh::addBoltSpider(const PointList<3> & pa)
{
  Vct3 ca;
  const int na = pa.size();
  for (int i=0; i<na; ++i)
    ca += pa[i];
  ca *= 1.0 / na;

  uint gtop = gids.back();
  uint ga = addVertex(ca, gtop+1);

  for (int i=0; i<na; ++i)
    rconnect( nearest(pa[i]), ga );

  return ga;
}

uint NstMesh::addSlidingBearing(const PointList<3> & pts, const Vct3 & pdir)
{
  // append center point
  Vct3 ctr;
  const int np = pts.size();
  for (int i=0; i<np; ++i)
    ctr += pts[i];
  ctr *= 1.0 / np;

  uint gtop = gids.back();
  uint gc = vtx.size();
  // uint gc = addVertex(ctr, gtop+1);

  // create MPC which constrains radial motion only where
  // that direction is a pressure direction
  for (int i=0; i<np; ++i) {
    Vct3 r = pts[i] - ctr;
    if (dot(r,pdir) > 0) {
      normalize(r);
      uint gp = nearest(pts[i]);
      NstSimpleMpc *mpc = new NstSimpleMpc(this, gp, gc);
      for (int k=0; k<3; ++k) {
        if (fabs(r[k]) > gmepsilon)
          mpc->constrain(k, NstDof(k+1), r[k], NstDof(k+1), -r[k]);
      }
      HybridMesh::addElement(mpc);
    }
  }

  // must SPC this vertex
  return addVertex(ctr, gtop+1);
}

void NstMesh::resizeModes(uint n)
{
  if (kgen.size() != n)
    kgen.resize(n);
  if (mgen.size() != n)
    mgen.resize(n);
  mz.resize(n);
}

void NstMesh::swapMode(uint i, Matrix &z)
{
  assert(i < mz.size());
  mz[i].swap(z);
}

void NstMesh::swapMode(uint i, Matrix & z, Real k, Real m)
{
  assert(i < mz.size());
  kgen[i] = k;
  mgen[i] = m;
  mz[i].swap(z);
}

void NstMesh::appendDisp(Matrix & z)
{
  dsp.push_back( Matrix() );
  dsp.back().swap(z);
}

void NstMesh::mergeStressFields()
{
  const size_t nf = sigma.size();
  if (nf < 2)
    return;

  dbprint(nf,"stress fields.");

  for (size_t i=0; i<nf; ++i) {
    NstStressField &fi( sigma[i] );
    if (fi.isMerged())
      continue;
    for (size_t j=i+1; j<nf; ++j) {
      NstStressField &fj( sigma[j] );
      if (fj.isMerged())
        continue;
      if ( fi.merge(fj) ) {
        fj.mergedInto(i);
        dbprint("Merged field",j,"into",i);
      }
    }
  }

  std::vector<NstStressField>::iterator last;
  auto pred = [&](const NstStressField &f){return f.isMerged();};
  last = std::remove_if( sigma.begin(), sigma.end(), pred );
  sigma.erase(last, sigma.end());

  dbprint("Merged ",nf,"into",sigma.size(),"stress fields");
}

void NstMesh::fixate()
{
  HybridMesh::fixate();
  btree = BSearchTree(vtx);
}

void NstMesh::cleanup(Real threshold)
{
  // vertex search tree
  uint nv(vtx.size());
  btree = BSearchTree(vtx);

  // find (nearly) identical vertices
  Indices dupl, repl(nv), idt, gkeep;
  uint count(0);
  PointList<3> kept;
  for (uint i=0; i<nv; i++) {
    if (not binary_search(dupl.begin(), dupl.end(), i)) {
      repl[i] = count;
      idt.clear();
      btree.find(vtx[i], threshold, idt);
      for (uint j=0; j<idt.size(); j++) {
        if (idt[j] > i) {
          dupl.insert(lower_bound(dupl.begin(), dupl.end(), idt[j]), idt[j]);
          repl[idt[j]] = count;
        }
      }
      ++count;
      kept.push_back(vtx[i]);
      gkeep.push_back(gids[i]);
    }
  }

  // eliminate duplicate vertices
  vtx.swap(kept);
  gids.swap(gkeep);

  // apply node index translation to elements
  const uint nf(elements.size());
  for (uint i=0; i<nf; ++i) {
    Element & e(*elements[i]);
    const uint n(e.nvertices());
    uint *vi(e.vertices());
    for (uint j=0; j<n; ++j)
      vi[j] = repl[vi[j]];
  }

  // recompute connectivity
  fixate();
}

void NstMesh::nstread(const std::string & fname)
{
  NstReader r(*this);
  r.read(fname);
}

void NstMesh::nstwrite(std::ostream & os, int gidoffset, int eidoffset) const
{
  const uint nv(nvertices());
  const uint ne(nelements());

  os << "$\n$ Nastran bulk data file generated by libsurf/NstMesh" << endl;
  os << "$ " << nv << " nodes, " << ne << " elements.\n$" << endl;
  os << std::showpoint;
  for (uint i=0; i<nv; ++i) {
    os << "GRID, " << gids[i]+gidoffset << ", 0, ";
    for (uint k=0; k<3; ++k) {
      if (fabs(vtx[i][k]) < gmepsilon)
        os << nstr(0.0) << ", ";
      else
        os << nstr(vtx[i][k]) << ", ";
    }
    os << endl;
  }

  NstElementBase::indexOffsets(gidoffset, eidoffset);
  const NstElementBase *bp;
  for (uint i=0; i<ne; ++i) {
    if ( as(i, &bp) and bp->pid() != PID_DONT_USE)
      element(i).nstwrite(os);
  }
}

void NstMesh::add2viz(MeshFields & mvz) const
{
  // add element topology
  HybridMesh::add2viz(mvz);

  const NstElementBase *eb;
  const int ne(nelements());
  //  const int nve(mvz.nelements());
  Indices pid3, pid4, mcid3, mcid4;

  //   Indices cpid(nve), cmcid(nve);
  //   fill(cpid.begin(), cpid.end(), 0);
  //   fill(cmcid.begin(), cmcid.end(), 0);
  //
  //   for (int i=0; i<ne; ++i) {
  //     uint ibeg = eidx[i];
  //     uint iend = eidx[i+1];
  //     if (ibeg == NotFound or iend == NotFound)
  //       continue;
  //
  //     eb = dynamic_cast<const NstElementBase *>(elementptr(i).get());
  //     if (eb == 0)
  //       continue;
  //
  //     // debug
  //     cout << "Element " << element(i).id() << " pid " << eb->pid()
  //          << " mvz " << ibeg << " to " << iend << endl;
  //
  //
  //     for (uint j=ibeg; j<=iend; ++j) {
  //       cpid[j] = eb->pid();
  //       cmcid[j] = eb->mcid();
  //     }
  //   }
  //
  //   mvz.addComponentSet("Property ID", cpid);
  //   mvz.addComponentSet("Material coordinate ID", cmcid);

  for (int i=0; i<ne; ++i) {
    const HybElementPtr & ep(elementptr(i));
    int idt = ep->idtype();
    if (idt >= NstCTRIA3 and idt <=NstCQUAD8) {
      eb = dynamic_cast<const NstElementBase *>(ep.get());
      if (eb != 0) {
        if (idt <= NstCTRIA6) {
          pid3.push_back(eb->pid());
          mcid3.push_back(eb->mcid());
        } else {
          pid4.push_back(eb->pid());
          mcid4.push_back(eb->mcid());
        }
      }
    }
  }

  // merge ids : triangular elements first
  pid3.insert(pid3.end(), pid4.begin(), pid4.end());
  mcid3.insert(mcid3.end(), mcid4.begin(), mcid4.end());

  if (not pid3.empty())
    mvz.addComponentSet("Property ID", pid3);
  if (not mcid3.empty())
    mvz.addComponentSet("Material coordinate ID", mcid3);

  // add modeshapes
  string s;
  const uint nm(mz.size());
  for (uint i=0; i<nm; ++i) {
    stringstream ss;
    ss.precision(4);
    ss << "Eigenmode " << i+1;
    ss << " f = " << sqrt(kgen[i])/(2*PI);
    mvz.addModeShape(ss.str(), mz[i]);
  }
}

void NstMesh::toMx(MxMesh & mx) const
{
  mx.clear();

  // register mesh vertices
  mx.appendNodes( vertices() );

  // convert elements to sections
  Indices idx[ (int) Mx::NElmTypes ];

  // map nastran element types to MxMesh types
  // CHEXA requires special treatment - it can have 8 or 20 nodes
  // CTETRA requires special treatment - it can have 4 or 10 nodes
  const Mx::ElementType typmap[] = {
    Mx::Undefined, // NstCMASS
    Mx::Point, //  NstCONM
    Mx::Undefined, // NstCELAS,
    Mx::Line2, // NstCBEAM,
    Mx::Tri3, // NstCTRIA3,
    Mx::Tri3, // NstCTRIAR,
    Mx::Tri6, // NstCTRIA6,
    Mx::Quad4, // NstCQUAD4,
    Mx::Quad4, // NstCQUADR,
    Mx::Quad8, // NstCQUAD8,
    Mx::Undefined, // NstCHEXA,
    Mx::Undefined, // NstCTETRA,
    Mx::Line2, // NstRBAR,
    Mx::Undefined, // NstRBE2,
    Mx::Line2, // NstMPC,
    Mx::Undefined, // NstUndefined
  };
  int chexaix = int( NstCHEXA - NstCMASS );
  int ctetraix = int( NstCTETRA - NstCMASS );

  // put element indices into sections and keep record
  // of section and position in order to map PIDs
  const int nel = nelements();
  Indices i2sec(nel), i2idx(nel), pid(nel,0), mcid(nel,0), eid(nel,0);
  for (int i=0; i<nel; ++i) {

    // copy element indices into appropriate index container
    int typix = element(i).idtype() - NstCMASS;
    Mx::ElementType mxtype = typmap[typix];
    const int nv = element(i).nvertices();
    const uint *vi = element(i).vertices();

    Indices *pix(0);
    if (typix == chexaix) {
      if (nv == 8) {
        mxtype = Mx::Hex8;
        pix = &idx[Mx::Hex8];
      } else if (nv == 20) {
        mxtype = Mx::Hex20;
        pix = &idx[Mx::Hex20];
      }
    } else if (typix == ctetraix) {
      if (nv == 4) {
        mxtype = Mx::Tet4;
        pix = &idx[Mx::Tet4];
      } else if (nv == 10) {
        mxtype = Mx::Tet10;
        pix = &idx[Mx::Tet10];
      }
    } else if (mxtype != Mx::Undefined) {
      pix = &idx[int(mxtype - Mx::Undefined)];
    }

    if (pix != 0) {
      i2sec[i] = std::distance(&idx[0], pix);
      i2idx[i] = pix->size() / MxMeshSection::nElementNodes(mxtype);
      pix->insert(pix->end(), vi, vi+nv);
    } else {
      i2sec[i] = NotFound;
      i2idx[i] = NotFound;
    }

    // store PID and MCID
    eid[i] = element(i).id();
    const NstElementBase *ebp(0);
    if (as(i, &ebp)) {
      pid[i] = ebp->pid();
      mcid[i] = ebp->mcid();
    } else {
      pid[i] = NotFound;
      mcid[i] = NotFound;
    }
  }

  // create sections in MxMesh, record element index offsets
  Indices eloff(int(Mx::NElmTypes)+1);
  eloff[0] = 0;
  for (int isec=0; isec<int(Mx::NElmTypes); ++isec) {
    const Indices & six( idx[isec] );
    if (six.empty()) {
      eloff[isec+1] = eloff[isec];
    } else {
      uint js = mx.appendSection(Mx::ElementType(isec), six);
      eloff[isec+1] = eloff[isec] + mx.section(js).nelements();
    }
  }

  // finally, append RBE2 element section (will yield multiple lines per
  // RBE2 element)
  Indices rbelines;
  for (int i=0; i<nel; ++i) {
    if (element(i).idtype() != NstRBE2)
      continue;
    const uint *vi = element(i).vertices();
    const int nlines = element(i).nvertices() - 1;
    for (int j=0; j<nlines; ++j) {
      rbelines.push_back(vi[0]);
      rbelines.push_back(vi[j+1]);
    }
  }

  uint irbesec = NotFound;
  if (not rbelines.empty()) {
    irbesec = mx.appendSection(Mx::Line2, rbelines);
    mx.section(irbesec).rename("RBE2");
    mx.countElements();
  }

  // create element groups (as bocos) for pids and mcids
  Indices allpid(pid), allmcid(mcid);
  sort_unique(allpid);
  sort_unique(allmcid);
  if (allpid.back() == NotFound)
    allpid.pop_back();
  if (allmcid.back() == NotFound)
    allmcid.pop_back();

  const int npid = allpid.size();
  const int nmcid = allmcid.size();

  DVector<int> fpid(mx.nelements()), feid(mx.nelements()), fmcid(mx.nelements());
  std::vector<Indices> pidboco(npid), mcidboco(nmcid);
  Indices::iterator itr;
  for (int i=0; i<nel; ++i) {
    uint ityp = i2sec[i];
    uint ipos = i2idx[i];
    if (ityp == NotFound or ipos == NotFound)
      continue;
    if (pid[i] == NotFound or mcid[i] == NotFound)
      continue;

    // compute the MxMesh index of the current element i and figure
    // out which element group this should be dumped into
    uint je = eloff[ityp] + ipos;
    itr = lower_bound(allpid.begin(), allpid.end(), pid[i]);
    if (itr == allpid.end() or *itr != pid[i])
      continue;
    uint jg = std::distance(allpid.begin(), itr);
    pidboco[jg].push_back(je);
    fpid[je] = pid[i];
    feid[je] = eid[i];

    itr = lower_bound(allmcid.begin(), allmcid.end(), mcid[i]);
    if (itr == allmcid.end() or *itr != mcid[i])
      continue;
    jg = std::distance(allmcid.begin(), itr);
    mcidboco[jg].push_back(je);
    fmcid[je] = mcid[i];
  }

  // turn element index lists into bocos
  for (int ib=0; ib<npid; ++ib) {
    if (pidboco[ib].empty())
      continue;
    uint jb = mx.appendBoco(Mx::BcUndefined, pidboco[ib]);
    mx.boco(jb).rename("PID "+str(allpid[ib]));
  }
  for (int ib=0; ib<nmcid; ++ib) {
    if (mcidboco[ib].empty())
      continue;
    uint jb = mx.appendBoco(Mx::BcUndefined, mcidboco[ib]);
    mx.boco(jb).rename("MCID "+str(allmcid[ib]));
  }

  // store pid/mcid as cell-based integer fields as well
  mx.appendField("PID", fpid);
  mx.appendField("EID", feid);
  mx.appendField("MCID", fmcid);

  // create a solution tree if there is none
  MxSolutionTreePtr ptree = mx.solutionTree();
  if (ptree == nullptr) {
    ptree = MxSolutionTree::create("Results");
    mx.solutionTree(ptree);
  }

  // store modes/solutions as 6D arrays
  const int nm = nmodes();
  const int nd = dsp.size();
  const int nv = nvertices();
  const int nfz = flutterEvals.size();
  assert(size_t(nfz) <= flutterEigs.size());
  PointList<6> mp(nv);

  // store modeshapes
  MxSolutionTreePtr pmodes;
  if (nm > 0)
    pmodes = ptree->append("Eigenmodes");
  Indices modeFieldIndex;
  for (int j=0; j<nm; ++j) {

    // copy into point list
    for (int i=0; i<nv; ++i) {
      for (int k=0; k<6; ++k)
        mp[i][k] = mz[j](i,k);
    }

    Real f = sqrt(kgen[j]/mgen[j])/(2*PI);
    stringstream ss;
    ss.precision(2);
    ss << "Mode " << j+1 << ", " << f << " Hz";
    uint mdi = mx.appendField(ss.str(), mp);
    pmodes->appendField(mdi);
    modeFieldIndex.push_back(mdi);

    XmlElement note("Eigenmode");
    note["frequency"] = str(f);
    note["modal_stiffness"] = str(kgen[j]);
    note["modal_mass"] = str(mgen[j]);
    mx.field(mdi).annotate(note);
    mx.field(mdi).valueClass( MxMeshField::ValueClass::Eigenmode );
  }

  // store displacement fields
  MxSolutionTreePtr pdisp;
  if (nd > 0)
    pdisp = ptree->append("Displacements");
  for (int j=0; j<nd; ++j) {

    // copy into point list
    Real fn = 0;
    for (int i=0; i<nv; ++i) {
      for (int k=0; k<6; ++k)
        mp[i][k] = dsp[j](i,k);
      fn += sq(mp[i]);
    }

    stringstream ss;
    ss << "Displacement " << j+1;
    uint mdi = mx.appendField(ss.str(), mp);
    pdisp->appendField(mdi);
    mx.field(mdi).valueClass( MxMeshField::ValueClass::Displacement );

    dbprint(ss.str(), fn);
  }

  // store flutter modes
  MxSolutionTreePtr pfmodes;
  if (nfz > 0)
    pfmodes = ptree->append("Flutter Modes");
  PointList<6> fmr(nv), fmi(nv);
  for (int j=0; j<nfz; ++j) {

    const CpxVector & z( flutterEvals[j] );
    string jname = "Flutter "+str(j+1)+" p: "+str(flutterEigs[j]);
    MxMeshDeform flumo(&mx);
    flumo.fromFlutterMode(modeFieldIndex, flutterEigs[j], z);
    flumo.rename(jname);
    mx.appendDeform(flumo);

    // generate additional fields for expanded real/imag part
#pragma omp parallel for
    for (int i=0; i<nv; ++i)
      fmr[i] = fmi[i] = 0.0;

    for (int im=0; im<nm; ++im) {
      const MxMeshField & mfield( mx.field(modeFieldIndex[im]) );
#pragma omp parallel for
      for (int i=0; i<nv; ++i) {
        Vct6 idef;
        mfield.value(i, idef);
        fmr[i] += z[im].real() * idef;
        fmi[i] += z[im].imag() * idef;
      }
    }

    uint fir = mx.appendField("Re"+jname, fmr);
    uint fii = mx.appendField("Im"+jname, fmi);
    pfmodes->appendField(fir);
    pfmodes->appendField(fii);

    // let visualization program show these as eigenmodes
    mx.field(fir).valueClass( MxMeshField::ValueClass::Eigenmode );
    mx.field(fii).valueClass( MxMeshField::ValueClass::Eigenmode );
  }

  // store additional solution data in a mesh annotation
  if (gids.size() > 0) {
    XmlElement xg("NastranGID");
    xg["count"] = str(gids.size());
    xg.asBinary(gids.size(), &gids[0]);
    mx.annotate(xg);
  }

  // stress
  // + subcase 1
  // | + ply 1
  // | | - Normal-1
  // | | - Normal-2
  // | + ply 2
  // | | - Normal-1
  // | | - Normal-2

  // generate stress fields : count subcases etc
  Indices strSubcases, strPlies;
  for (const NstStressField &f : sigma) {
    insert_once( strSubcases, f.subcase() );
    insert_once( strPlies, f.laminateIndex() );
  }

  // create tree structure to put fields in
  MxSolutionTreePtr psroot = MxSolutionTree::create("Stress");
  for (uint k : strSubcases) {
    MxSolutionTreePtr pssub = psroot->append( "Subcase "+str(k) );
    for (uint j : strPlies)
      pssub->append( "Ply "+str(j) );
  }

  // create stress fields, all scalar
  Vector jstress( mx.nelements() );
  for (const NstStressField &f : sigma) {
    uint icase = sorted_index( strSubcases, f.subcase() );
    assert(icase != NotFound);
    uint jply = sorted_index( strPlies, f.laminateIndex() );
    assert(jply != NotFound);

    MxSolutionTreePtr psub = psroot->child(icase);
    if (not f.label().empty())
      psub->rename(f.label());

    // create an EID map for this field
    Indices eidmap;
    f.mapEid(feid, eidmap);

    MxSolutionTreePtr pij = psub->child(jply);
    for (uint k=0; k<f.ncomponents(); ++k) {
      jstress = 0.0;
      f.inject(k, eidmap, jstress);
      uint fix = mx.appendField( f.componentName(k), jstress );
      pij->appendField( fix );
    }
  }

  if (not sigma.empty())
    ptree->append(psroot);
}
