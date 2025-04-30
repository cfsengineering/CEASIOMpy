
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
 
#ifndef SURF_TETMESH_H
#define SURF_TETMESH_H

#include <string>
#include <map>
#include <vector>
#include <genua/point.h>

//#ifdef HAVE_CGNS
#include <genua/cgnsfile.h>
//#endif

#include "tetboundarygroup.h"

class TriMesh;
class Plane;
class MxMesh;

/** Element in a pure tetrahdral mesh.
 * \deprecated
 */
class TetElement
{
  public:
    
    /// empty, undefined tet element
    TetElement() {}
    
    /// create defined tet element
    TetElement(const uint vi[4]) {
      v[0] = vi[0]; v[1] = vi[1]; v[2] = vi[2]; v[3] = vi[3];
    }
    
    /// create defined tet element 
    TetElement(uint a, uint b, uint c, uint d) {
      v[0] = a; v[1] = b; v[2] = c; v[3] = d;
    }
    
    /// access nodes 
    const uint *vertices() const {return v;}
    
    /// access nodes 
    uint *vertices() {return v;}
    
    /// defines a unique ordering 
    bool operator< (const TetElement & a) const {
      for (int k=0; k<4; ++k) {
        if (v[k] < a.v[k])
          return true;
        else if (v[k] > a.v[k])
          return false;
      }        
      return false;
    }
    
    /// identical indices 
    bool operator== (const TetElement & a) const {
      for (int k=0; k<4; ++k) {
        if (v[k] != a.v[k])
          return false;
      }        
      return true;
    }
    
    /// check if plane cuts element
    bool cuts(const PointList<3> & vtx, const Plane & p) const;
    
    /// add element faces to triangular mesh
    void addFaces(TriMesh & m) const;
    
  private:
    
    /// vertex indices
    uint v[4];
};

typedef std::vector<TetElement> TetElementArray;

/** Boundary face in a pure tetrahdral mesh.
 * \deprecated
 */
class TetFace
{
  public:
    
    /// empty, undefined tet face
    TetFace() : itag(-1) {}
    
    /// create defined tet face 
    TetFace(const uint vi[3]) : itag(-1) {
      v[0] = vi[0]; v[1] = vi[1]; v[2] = vi[2];
    }
    
    /// create defined tet face 
    TetFace(uint a, uint b, uint c) : itag(-1) {
      v[0] = a; v[1] = b; v[2] = c;
    }
    
    /// access nodes 
    const uint *vertices() const {return v;}
    
    /// access nodes 
    uint *vertices() {return v;}
    
    /// access boundary tag 
    void tag(int t) {itag = t;}
    
    /// access boundary tag 
    int tag() const {return itag;}
    
    /// reverse normal direction
    void reverse() { std::swap(v[1], v[2]); }
    
  private:
    
    /// vertex indices
    uint v[3];
    
    /// boundary tag
    int itag;
};

typedef std::vector<TetFace> TetFaceArray;

/** Simple tetrahedral volume mesh.
  
  TetMesh is a 'dumb' volume mesh container which does nothing more than 
  support i/o to a few different formats. If the tetgen library libtet.a
  is available, the member function callTetgen() can be used to generate a
  quality-conforming Delaunay tetrahedralization of the domain limited by 
  the given boundary triangles. 

  Note that tetgen may not terminate if excessive quality is called for.

  \deprecated
*/
class TetMesh
{

  public:
    
    typedef DMatrix<int> IndexMatrix;
    typedef DVector<int> IndexVector;
    
    /// create empty mesh 
    TetMesh() {}
    
    /// virtual destructor
    virtual ~TetMesh() {}

    /// initialize from single mesh which contains all boundaries
    void init(const TriMesh & allb);
    
    /// count nodes 
    uint nnodes() const {return vtx.size();}
    
    /// count boundary faces 
    uint nfaces() const {return faces.size();}
    
    /// count tetrahedra
    uint nelements() const {return tets.size();}
    
    /// access nodes 
    const PointList<3> & nodes() const {return vtx;}
    
    /// access triangle i 
    const TetFace & face(uint i) const {
      assert(i < faces.size());
      return faces[i];
    }

    /// access triangle i
    TetFace & face(uint i) {
      assert(i < faces.size());
      return faces[i];
    }
    
    /// access tetrahedron i 
    const TetElement & element(uint i) const {
      assert(i < tets.size());
      return tets[i];
    }
    
    /// number of boundaries identified
    uint nboundaries() const {return boco.size();}
    
    /// access boundary i
    const TetBoundaryGroup & boundaryGroup(uint i) const {
      assert(i < boco.size()); 
      return boco[i];
    }
    
    /// access boundary i
    TetBoundaryGroup & boundaryGroup(uint i) {
      assert(i < boco.size()); 
      return boco[i];
    }
    
    /// compute hole position from wall boundary mesh
    Vct3 findHolePosition(const TriMesh & m) const;
    
    /// determine multiple holes for unconnected components
    bool findHoles(const TriMesh & m, PointList<3> & holes) const;

    /// set location of hole marker
    // void holeMarker(const Vct3 & ph) {mhole = ph;}
    
    /// initialize boundary from wall and farfield mesh
    void initBoundaries(const TriMesh & wall, TriMesh & mfarfield);
    
    /// reverse triangles of boundary k
    void reverseBoundary(uint k);
    
    /// locate boundary group by tag
    uint groupByTag(int t) const;
    
    /// reorder nodes 
    void reorder();
    
    /// generate a plane cut through the tetrahedral mesh
    void cutElements(const Plane & p, TriMesh & tms) const;
    
    /// convert to newer, more flexible mesh representation
    void toMx(MxMesh & mx) const;

#ifdef HAVE_TETGEN
    
    /// call tetgen to create tetrahedra from boundary mesh
    void callTetgen(const std::string & options);
    
#endif
    
    /// read tetgen format files with basename bname 
    void readTetgen(const std::string & bname); 

    /// write tetgen format files
    void writeTetgen(const std::string & bname, int offs=1) const; 
    
    /// write boundary only in smesh format (for tetgen) 
    void writeSmesh(const std::string & bname, int offs=1) const; 
    
//#ifdef HAVE_CGNS

    /// read cgns file
    void readCgns(const std::string & bname);

    /// write all present data to cgns file
    void writeCgns(const std::string & fname, bool bcAsSections=false);
    
//#endif

    /// write to bmsh file (for Edge)
    void writeMsh(const std::string & fname) const;
    
    /// write boundary conditions for Edge to file
    void writeBoc(const std::string & fname) const;
    
    /// clear all data
    void clear();
    
  protected:
    
    /// scan node file and return node index offset 
    int readTetgenNodes(std::istream & is);
    
    /// scan element file
    void readTetgenElements(std::istream & is, int offs=0);
    
    /// scan boundary face file
    void readTetgenFaces(std::istream & is, int offs=0);
  
    /// collect boundary elements for boundary tagged with itag 
    void collectFaces(uint itag, IndexMatrix & ielm) const;
    
    /// collect indices of faces for boundary tagged with itag 
    void collectFaceIndices(uint itag, IndexVector & ielm) const;
    
    /// check whether triangle fix can be used to determine internal point
    bool triangleHole(const TriMesh &m, uint fix, Vct3 & hole) const;

  protected:

    /// nodes 
    PointList<3> vtx;
    
    /// elements 
    TetElementArray tets;
    
    /// boundary triangles  
    TetFaceArray faces;
    
    /// boundary region names
    BGroupArray boco;
    
    /// hole positions
    PointList<3> mholes;
    //Vct3 mhole;
};

#endif
