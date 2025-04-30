
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
 
#include "configparser.h"
#include "triangulation.h"
#include "trimesh.h"
#include "lu.h"
#include "meshslice.h"

using namespace std;

// -------------- local scope ---------------------------------------------

// Defines an ordering along the baseline of the slice window
class LfiSorter
{
  public:
    LfiSorter(const Vct3 & p1, const Vct3 & p2) : bline(p1,p2) {}
    bool operator() (const LineFaceIsec & a, const LineFaceIsec & b) const
    {
      Real ta = bline.footPar(a.position());
      Real tb = bline.footPar(b.position());
      return ta < tb;
    }
  private:
    Line<3> bline;
};

// -------------- LineFaceIsec --------------------------------------------

LineFaceIsec::LineFaceIsec(const PointList<3> & vtx, const uint *vix,
                           const Line<3> & ln)
{
  // copy indices
  for (int k=0; k<3; ++k)
    vi[k] = vix[k];
  
  // extract corner points
  const Vct3 & q0(vtx[vi[0]]);
  const Vct3 & q1(vtx[vi[1]]);
  const Vct3 & q2(vtx[vi[2]]);

  // compute intersection parameters
  Vct3 p1, p2, rhs, uvt;
  p1 = ln.eval(0.0);
  p2 = ln.eval(1.0);
  Mtx33 m;
  for (uint i=0; i<3; ++i) {
    m(i,0) = q1[i] - q0[i];
    m(i,1) = q2[i] - q0[i];
    m(i,2) = p1[i] - p2[i];
    rhs[i] = p1[i] - q0[i];
  }
  uvt = lu_solve_copy(m, rhs);
  u = uvt[0];
  v = uvt[1];
  w = 1-u-v;
  t = uvt[2];
  pos = p1 + t*(p2-p1);
}

// -------------- MeshSlice -----------------------------------------------

void MeshSlice::configure(const ConfigParser & cfg)
{
  // read specification for slicing plane
  p1 = cfg.getVct3("Origin");
  p2 = cfg.getVct3("Base");
  p3 = cfg.getVct3("Top");
  nxp = cfg.getInt("RayCount", 100);  
}

uint MeshSlice::cut(const Triangulation & tg)
{
  // construct intersecting plane
  Plane pln(p3-p1, p2-p1, p1);

  // collect faces which intersect plane at all
  std::vector<Face> af;
  const uint *vi;
  Triangulation::face_iterator itf;
  for (itf = tg.face_begin(); itf != tg.face_end(); ++itf) {
    vi = itf->vertices();
    uint left(0);
    for (uint i=0; i<3; ++i) {
      if ( pln.distance(tg.vertex(vi[i])) < 0 )
        ++left;
    }
    if (left > 0 and left < 3)
      af.push_back(*itf);
  }

  // project points onto affected triangles
  LfiArray tmp;
  Vct3 pup, plo;
  for (uint i=0; i<nxp; ++i) {
    Real t = Real(i)/(nxp-1);
    pup = p3 + t*(p2-p1);
    plo = p1 + t*(p2-p1);
    Line<3> ln(plo, pup);
    for (uint j=0; j<af.size(); ++j) {
      LineFaceIsec f(tg.vertices(), af[j].vertices(), ln);
      if ( f.inside() )
        tmp.push_back(f);
    }
  }
  
#ifndef NDEBUG
  cerr << "MeshSlice::cut() - " << af.size() << " faces in range. " << endl;
  cerr << "MeshSlice::cut() - " << tmp.size() << " intersections detected." << endl;
#endif

  // sort intersections along the base line of the slice window
  LfiSorter cmp(p1, p2);
  std::sort(tmp.begin(), tmp.end(), cmp);

  // identify upper/lower pairs
  LfiArray unassigned;
  Line<3> lbase(p1, p2);
  lfupper.clear();
  lflower.clear();

  uint ki(0), ni(tmp.size());
  while (ki+1 < ni) {

    const LineFaceIsec & f1(tmp[ki]);
    const LineFaceIsec & f2(tmp[ki+1]);
    
    // check if f1 and f2 make a pair
    Real t1 = lbase.footPar(f1.position());
    Real t2 = lbase.footPar(f2.position());
    if ( fabs(t2-t1) < gmepsilon ) {
      ki += 2;
      if (f1.foot() < f2.foot()) {
        lflower.push_back(f1);
        lfupper.push_back(f2);
      } else {
        lflower.push_back(f2);
        lfupper.push_back(f1);
      }
    } else {
      unassigned.push_back(f1);
      ++ki;
    }

    // catch special case where next loop's f1 will be last element
    if (ki == ni-1) 
      unassigned.push_back(tmp.back());
  }

  // copy the unidentified intersections into the 'upper' set
  lfupper.insert(lfupper.end(), unassigned.begin(), unassigned.end());

  return lfupper.size() + lflower.size(); 
}

uint MeshSlice::cut(const TriMesh & tg)
{
  // construct intersecting plane
  Plane pln(p3-p1, p2-p1, p1);

  // collect faces which intersect plane at all
  Indices afi;
  const uint *vi;
  const uint nf(tg.nfaces());
  for (uint j=0; j<nf; ++j) {
    
    // count vertices to the left of plane
    vi = tg.face(j).vertices();
    uint left(0);
    for (uint k=0; k<3; ++k) {
      if ( pln.distance(tg.vertex(vi[k])) < 0 )
        ++left;
    }
    if (left > 0 and left < 3)
      afi.push_back(j);
  }

  // project points onto affected triangles
  LfiArray tmp;
  Vct3 pup, plo;
  const uint nfi(afi.size());
  for (uint i=0; i<nxp; ++i) {
    Real t = Real(i)/(nxp-1);
    pup = p3 + t*(p2-p1);
    plo = p1 + t*(p2-p1);
    Line<3> ln(plo, pup);
    for (uint j=0; j<nfi; ++j) {
      vi = tg.face(afi[j]).vertices();
      LineFaceIsec f(tg.vertices(), vi, ln);
      if ( f.inside() )
        tmp.push_back(f);
    }
  }
  
  // sort intersections along the base line of the slice window
  LfiSorter cmp(p1, p2);
  std::sort(tmp.begin(), tmp.end(), cmp);

  // identify upper/lower pairs
  LfiArray unassigned;
  Line<3> lbase(p1, p2);
  lfupper.clear();
  lflower.clear();

  uint ki(0), ni(tmp.size());
  while (ki+1 < ni) {

    const LineFaceIsec & f1(tmp[ki]);
    const LineFaceIsec & f2(tmp[ki+1]);
    
    // check if f1 and f2 make a pair
    Real t1 = lbase.footPar(f1.position());
    Real t2 = lbase.footPar(f2.position());
    if ( fabs(t2-t1) < gmepsilon ) {
      ki += 2;
      if (f1.foot() < f2.foot()) {
        lflower.push_back(f1);
        lfupper.push_back(f2);
      } else {
        lflower.push_back(f2);
        lfupper.push_back(f1);
      }
    } else {
      unassigned.push_back(f1);
      ++ki;
    }

    // catch special case where next loop's f1 will be last element
    if (ki == ni-1) 
      unassigned.push_back(tmp.back());
  }

  // copy the unidentified intersections into the 'upper' set
  lfupper.insert(lfupper.end(), unassigned.begin(), unassigned.end());

  return lfupper.size() + lflower.size(); 
}

void MeshSlice::positions(PointList<3> & plower, PointList<3> & pupper) const
{
  uint nu(lfupper.size()), nl(lflower.size());
  plower.resize(nl);
  pupper.resize(nu);
  for (uint i=0; i<nu; ++i)
    pupper[i] = lfupper[i].position();
  for (uint i=0; i<nl; ++i)
    plower[i] = lflower[i].position();
}
