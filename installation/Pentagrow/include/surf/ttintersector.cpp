
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
 
#include <iostream>

#include <genua/connectmap.h>
#include <genua/threadtask.h>
#include <genua/threadpool.h>
#include "ttintersector.h"

using namespace std;

class TTIsecTask : public ThreadTask
{
  public:
    
    TTIsecTask(TaskContainer & q, TTIntersector & a, TTIntersector & b) :
      wq(q), tta(a), ttb(b) {}
     
    void work() {
      if (not tta.bbIntersect(ttb))
        return;
      if (tta.samePatch(ttb))
        return;
      if (tta.neighborPatch(ttb))
        return;
      
      tta.guardedSplit();
      ttb.guardedSplit();
      
      // TODO : Decide whether to push new tasks or proceed serially
      if (tta.isLeaf() and ttb.isLeaf()) {
        tta.ttIntersect( ttb );
      } else if (tta.isLeaf()) {
        wq.push( new TTIsecTask(wq, tta, ttb.leftChild()) );
        wq.push( new TTIsecTask(wq, tta, ttb.rightChild()) );
      } else if (ttb.isLeaf()) {
        wq.push( new TTIsecTask(wq, ttb, tta.leftChild()) );
        wq.push( new TTIsecTask(wq, ttb, tta.rightChild()) );
      } else {
        wq.push( new TTIsecTask(wq, tta.leftChild(), ttb.leftChild()) );
        wq.push( new TTIsecTask(wq, tta.rightChild(), ttb.leftChild()) );
        wq.push( new TTIsecTask(wq, tta.leftChild(), ttb.rightChild()) );
        wq.push( new TTIsecTask(wq, tta.rightChild(), ttb.rightChild()) );        
      }
    }
      
  private:
    
    TaskContainer & wq;
    TTIntersector & tta;
    TTIntersector & ttb;
};

// class TTsTask : public ThreadTask
// {
//   public:
//     
//     TTsTask(TaskContainer & q, TTIntersector & a) :
//       wq(q), tta(a) {}
//      
//     void work() {
//       if (tta.isLeaf()) {
//         tta.tsIntersect();
//       } else {
//         wq.push(new TTsTask(wq, tta.leftChild()));
//         wq.push(new TTsTask(wq, tta.rightChild()));
//       }
//     }
//       
//   private:
//     
//     TaskContainer & wq;
//     TTIntersector & tta;
// };

class coord_less 
{
  public:
    
    coord_less(const SharedVector<TriFace> & f, int crd) : faces(f), c(crd) {}
    
    bool operator() (uint a, uint b) const {
      Vct3 ca = faces[a].center();
      Vct3 cb = faces[b].center();
      return ca[c] < cb[c];
    } 
  
  private:
    
    // triangles referenced
    const SharedVector<TriFace> & faces;
    
    // sorting coordinate
    int c;
};

uint TTIntersector::min_node_triangles = 16;

// -------------------- TTIntersector ---------------------------------------

void TTIntersector::addMesh(const MeshComponent & mp)
{
  // add triangles
  guard.lock();
  const int off = ifaces.size();
  const int nf = mp.nfaces();
  for (int i=0; i<nf; ++i) {
    triangles.push_back( mp.face(i) );
    ifaces.push_back(off+i);
  }
  guard.unlock();
}
    
void TTIntersector::sortFaces()
{
  // TODO : use parallel stdlibc++ where available
  global_face_less cmp;
  std::sort(triangles.begin(), triangles.end(), cmp);
}

uint TTIntersector::bsearchFace(const TriFace & f) const
{
  global_face_less cmp;
  global_face_equal eq;
  SharedVector<TriFace>::const_iterator pos;
  pos = std::lower_bound(triangles.begin(), triangles.end(), f, cmp);
  if (pos != triangles.end() and eq(f, *pos))
    return std::distance(triangles.begin(), pos);
  else
    return NotFound;
}

void TTIntersector::updateBox()
{
  // collect extreme points and center
  Vct3 p1, p2;
  p1 = +huge;
  p2 = -huge;
  const int nf = nfaces();
  for (int i=0; i<nf; ++i) {
    const TriFace & f(face(ifaces[i]));
    const uint *vi = f.vertices();
    const TriMesh *msh(f.mesh());
    for (int k=0; k<3; ++k) {
      const Vct3 & p( msh->vertex(vi[k]) );
      for (int j=0; j<3; ++j) {
        p1[j] = std::min(p1[j], p[j]);
        p2[j] = std::max(p2[j], p[j]);
      }
    }
    
    const MeshComponent *mp = dynamic_cast<const MeshComponent*>(msh);
    assert(mp);
    insert_once(patches, mp);
  }
  
  bb = BndBox(p1, p2);
}
    
void TTIntersector::enforce(uint itri1, uint itri2,
                            const Vct3 & psrc, const Vct3 & ptrg)
{
  guard.lock();
  allisec.push_back(TTIntersectionPtr(
      new TTIntersection(this, itri1, itri2, psrc, ptrg)));
  guard.unlock();
}

void TTIntersector::ttIntersect(const TTIntersector & other)
{
  const int nsf = nfaces();
  const int nof = other.nfaces();
  
  TTIntersection tti;
  for (int i=0; i<nsf; ++i) {
    for (int j=0; j<nof; ++j) {
      tti = TTIntersection(this, index(i), other.index(j));
      if (tti.intersect()) {
        guard.lock();
        allisec.push_back( TTIntersectionPtr(new TTIntersection(tti)) );
        guard.unlock();
      }
    }
  }  
}
    
void TTIntersector::split()
{
  // split along the longest side of the bounding box
  Real dx = bb.length();
  Real dy = bb.width();
  Real dz = bb.height();
  
  int c(0);
  if (dy > dx and dy > dz)
    c = 1;
  else if (dz > dx and dz > dy)
    c = 2;
  
  // sort triangles along longest box dimension
  Indices fsort(ifaces), ileft, iright;
  coord_less cmp(triangles, c);
  std::sort(fsort.begin(), fsort.end(), cmp);
  
  // create child nodes
  const int imid = fsort.size()/2;
  ileft.insert(ileft.end(), fsort.begin(), fsort.begin()+imid);
  iright.insert(iright.end(), fsort.begin()+imid, fsort.end());
  
  mleft = TTIntersectorPtr( new TTIntersector(triangles, ileft) );
  mright = TTIntersectorPtr( new TTIntersector(triangles, iright) );
}

void TTIntersector::guardedSplit()
{
  ScopedLock lock(guard);
  
  if (not isLeaf())
    return;
  
  if (nfaces() < 2*TTIntersector::minFaceCount())
    return;
  
  split();
}

void TTIntersector::intersect(TTIntersector & other)
{
  if (not bbIntersect(other))
    return;
  if (samePatch(other))
    return;
  if (neighborPatch(other))
    return;
  
  guardedSplit();
  other.guardedSplit();
    
  if (isLeaf() and other.isLeaf()) {
    ttIntersect( other );
  } else if (isLeaf()) {
    intersect( other.leftChild() );
    intersect( other.rightChild() );
  } else if (other.isLeaf()) {
    leftChild().intersect(other);
    rightChild().intersect(other);
  } else {
    leftChild().intersect( other.leftChild() );
    rightChild().intersect( other.leftChild() );
    leftChild().intersect( other.rightChild() );
    rightChild().intersect( other.rightChild() );
  }
  
  // tsRecurse();
}

void TTIntersector::mtIntersect(ThreadPool & pool, TTIntersector & other)
{
  if (not bbIntersect(other))
    return;
  
  guardedSplit();
  other.guardedSplit();
  assert(not isLeaf());
  assert(not other.isLeaf());
  
  TaskContainer wq;
  wq.push( new TTIsecTask(wq, leftChild(), other.leftChild()) );
  wq.push( new TTIsecTask(wq, rightChild(), other.leftChild()) );
  wq.push( new TTIsecTask(wq, leftChild(), other.rightChild()) );
  wq.push( new TTIsecTask(wq, rightChild(), other.rightChild()) );
  pool.nrprocess(&wq);
  
//   wq.push( new TTsTask(wq, leftChild()) );
//   wq.push( new TTsTask(wq, rightChild()) );
//   if (this != &other) {
//     wq.push( new TTsTask(wq, other.leftChild()) );
//     wq.push( new TTsTask(wq, other.rightChild()) );
//   }
//   pool.nrprocess(&wq);
  
  wq.dispose();
}

void TTIntersector::collect(TTIntersectionArray & isc) const
{
  if (isLeaf()) {
    isc.insert(isc.end(), allisec.begin(), allisec.end());
  } else {
    mleft->collect(isc);
    mright->collect(isc);
  }

  // add enforced intersections stored in root node
  if (ifaces.size() == triangles.size()) {
    isc.insert(isc.end(), allisec.begin(), allisec.end());
  }
}

void TTIntersector::addLineViz(MeshFields & mvz) const
{
  if (isLeaf()) {
    const int ni = allisec.size();
    for (int i=0; i<ni; ++i)
      allisec[i]->addViz( mvz );
  } else {
    mleft->addLineViz(mvz);
    mright->addLineViz(mvz);
  }
}

void TTIntersector::addBoxViz(MeshFields & mvz) const
{
  if (isLeaf()) {
    bb.addQuads(mvz);    
  } else {
    mleft->addBoxViz(mvz);
    mright->addBoxViz(mvz);
  }
}

void TTIntersector::setComponents(Indices & idx, uint & inext) const
{
  assert(idx.size() >= triangles.size());
  if (isLeaf()) {
    const int nf = nfaces();
    for (int i=0; i<nf; ++i)
      idx[ ifaces[i] ] = inext;
    ++inext;
  } else {
    mleft->setComponents(idx, inext);
    mright->setComponents(idx, inext);
  }
}

