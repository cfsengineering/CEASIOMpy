
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
 
#ifndef GENUA_MESHFIELDS_H
#define GENUA_MESHFIELDS_H

#include "defines.h"
#include "svector.h"
#include "dvector.h"
#include "xmlelement.h"
#include "boxsearchtree.h"

class Triangulation;
class TriMesh;

/** Holds visualization data.

  MeshFields is used to represent data on a discretized surface, specificially
  for visualization. This class is used to generate and save data for scalar 
  fields on surface meshes, to be read by the visualization tools. 

  \b Note: Use MxMesh instead.

  \deprecated
  */
class MeshFields
{
  public:

    typedef std::vector<PointList<3> > ShapeArray;
    
    /// empty init
    MeshFields() {}

    /// case name
    const std::string & name() const {return csname;}

    /// case name
    void name(const std::string & s) {csname = s;}

    /// number of nodes
    uint nvertices() const {return vtx.size();}

    /// number of point markers
    uint nmarkers() const {return fpt.size();}

    /// number of line elements
    uint nline2() const {return fline2.size()/2;}
    
    /// number of 3-node triangles
    uint ntri3() const {return ftri3.size()/3;}

    /// number of 4-node quads
    uint nquad4() const {return fquad4.size()/4;}
    
    /// number of shell elements
    uint nelements() const {return ntri3()+nquad4()+nline2()+nmarkers();}

    /// number of eigenmodes
    uint nmodes() const {return mds.size();}

    /// number of named shapes
    uint nshapes() const {return nshape.size();}
    
    /// number of scalar datasets
    uint nfields() const {return vfield.size();}
    
    /// number vector fields 
    uint nvfields() const {return vecfields.size();}

    /// number of component sets
    uint ncompsets() const {return icomp.size();}
    
    /// number of trajectories 
    uint ntraject() const {return traject.size();}
    
    /// access numerical value jnode of field ifield
    Real value(uint ifield, uint jnode) const {
      assert(ifield < nfields());
      assert(jnode < vfield[ifield].size());
      return vfield[ifield][jnode];
    }

    /// access vertex j
    const Vct3 & node(uint j) const {
      assert(j < vtx.size());
      return vtx[j];
    }

    /// access normal j
    const Vct3 & normal(uint j) const {
      assert(j < nrm.size());
      return nrm[j];
    }
    
    /// access vertex indices of point markers
    const Indices & markerIndices() const {return fpt;}

    /// access vertex indices of line element i
    const uint *line2Vertices(uint i) const {
      assert(fline2.size() > 2*i+1);
      return &(fline2[2*i]);
    }
    
    /// access vertex indices of triangle element i
    const uint *tri3Vertices(uint i) const {
      assert(ftri3.size() > 3*i+2);
      return &(ftri3[3*i]);
    }

    /// access vertex indices of quad element i
    const uint *quad4Vertices(uint i) const {
      assert(fquad4.size() > 4*i+3);
      return &(fquad4[4*i]);
    }

    /// name of dataset i
    const std::string & fieldname(uint i) const {
      assert(i < sfield.size());
      return sfield[i];
    }
    
    /// name of dataset i
    const std::string & vfieldname(uint i) const {
      assert(i < vecfnames.size());
      return vecfnames[i];
    }
    
    /// name of component set i
    const std::string & csetname(uint i) const {
      assert(i < scomp.size());
      return scomp[i];
    }
    
    /// access field vector
    const Vector & field(uint i) const {
      assert(i < vfield.size());
      return vfield[i];
    }
    
    /// access field vector
    const PointList<3> & vectorField(uint i) const {
      assert(i < vecfields.size());
      return vecfields[i];
    }

    /// access component set
    const Indices & componentSet(uint i) const {return icomp[i];}
    
    /// name of mode i
    const std::string & modename(uint i) const {
      assert(i < modenames.size());
      return modenames[i];
    }
    
    /// name of shape i
    const std::string & shapename(uint i) const {
      assert(i < sshape.size());
      return sshape[i];
    }

    /// access named shape i
    const Vector & namedshape(uint i) const {
      assert(i < nshape.size());
      return nshape[i];
    }

    /// access modeshape
    const PointList<3> & eigenmode(uint imode) const {
      assert(imode < mds.size());
      return mds[imode];
    }
    
    /// check if field i contains nodal values 
    bool isNodalField(uint i) const {
      assert(i < nfields());
      return (vfield[i].size() == vtx.size());
    }
    
    /// access trajectory name 
    const std::string & trajectoryName(uint i) const {
      assert(i < tjnames.size());
      return tjnames[i];
    } 
    
    /// inquire if vertex normals are present
    bool hasVertexNormals() const {return vtx.size() == nrm.size();}

    /// general: create vertex, return its index
    uint addVertex(const Vct3 & v);

    /// add vertex list 
    void addVertices(const PointList<3> & v);
    
    /// general: create normal, return its index
    uint addNormal(const Vct3 & n);

    /// place a point marker at vertex ipos and return its index
    uint addMarker(uint ipos);
    
    /// add marker nodes
    uint addMarker(const PointList<3> & pts);
    
    /// create a simplex triangle, return its index
    uint addTri3(const uint *vix);

    /// create a simplex triangle, return its index
    uint addTri3(uint a, uint b, uint c);
    
    /// create a 4-node quad, return its index
    uint addQuad4(const uint *vix);
    
    /// create a 4-node quad, return its index
    uint addQuad4(uint a, uint b, uint c, uint d);

    /// add a line element, return its index
    uint addLine2(uint a, uint b);
    
    /// add polyline (Line2 elements)
    void addLine2(const PointList<3> & polyline);
    
    /// create geometry data from triangulation
    void addMesh(const Triangulation & t);
    
    /// create geometry data from triangulation
    void addMesh(const TriMesh & t);
    
    /// create quad elements from point grid
    void addMesh(const PointGrid<3> & pg);
    
    /// create quad elements from point grid and normals
    void addMesh(const PointGrid<3> & pg, const PointGrid<3> & ng);

    /// add field data, return field index
    uint addField(const std::string & fname, const Vector & values);
    
    /// add vector field data, return field index
    uint addVectorField(const std::string & fname, const PointList<3> & values);
    
    /// add a set of component definitions 
    uint addComponentSet(const std::string & fname, const Indices & cmp);
    
    /// add modeshape
    uint addModeShape(const std::string & sname, const PointList<6> & shape);

    /// add modeshape
    uint addModeShape(const std::string & sname, const PointList<3> & shape);
    
    /// add modeshape
    uint addModeShape(const std::string & sname, const Matrix & shape);

    /// add named shape (in modal subspace coordinates)
    uint addNamedShape(const std::string & fname, const Vector & values);

    /// add a named trajectory (first column is time, min. 12 DOF)
    uint addTrajectory(const std::string & tname, const Matrix & m);
    
    /// merge in data from object containing the same mesh
    void mergePayload(const MeshFields & a);

    /// clear all data
    void clear();

    /// create XML representation
    XmlElement toXml() const;

    /// construct from XML representation
    void fromXml(const XmlElement & xe);

  protected:
    
    /// name for the case
    std::string csname;
    
    /// vertex and normal coordinates
    PointList<3> vtx, nrm;

    /// modeshapes and 3-component vector fields
    ShapeArray mds, vecfields;
    
    /// vector field names 
    StringArray vecfnames;

    /// edges, point markers, line elements, simplex triangles, 4-node quads
    Indices fpt, fline2, ftri3, fquad4;
    
    /// element to component assignments 
    std::vector<Indices> icomp;
    
    /// component set names 
    StringArray scomp;
    
    /// values to visualize
    VectorArray vfield;

    /// names of the data fields
    StringArray sfield;

    /// names of the modes
    StringArray modenames;  
    
    /// named special shapes
    VectorArray nshape;
        
    /// names for these shapes
    StringArray sshape;
    
    /// trajectories 
    MatrixArray traject;
    
    /// trajectory names 
    StringArray tjnames;
};

#endif
