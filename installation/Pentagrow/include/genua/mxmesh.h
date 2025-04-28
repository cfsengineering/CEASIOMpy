
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
 
#ifndef GENUA_MXMESH_H
#define GENUA_MXMESH_H

#include "defines.h"
#include "point.h"
#include "xmlelement.h"
#include "connectmap.h"
#include "binfilenode.h"
#include "ffanode.h"
#include "mxmeshtypes.h"
#include "mxmeshsection.h"
#include "mxmeshboco.h"
#include "mxmeshfield.h"
#include "mxmeshdeform.h"
#include "mxannotated.h"
#include "typecode.h"
#include "forward.h"

class MeshFields;

/** Mesh with dissimilar elements.

  MxMesh is a simple container for meshes with different element types.
  It is meant to be primarily used as an intermediate data structure for
  conversion between file formats or as a 'dumb' storage after mesh generation.

  TODO:
  - Generalize field data storage to arbitrary data types
  - Use solution index when exporting to CGNS

  \ingroup mesh
  \sa MxMeshSection, MxMeshField, MxMeshBoco, MxMeshDeform
*/
class MxMesh : public MxAnnotated
{
public:
  
  /// construct empty mesh
  MxMesh() : MxAnnotated(), nelm(0) {}

  /// destroy mesh
  virtual ~MxMesh() {}

  /// number of elements in all sections
  uint nelements() const {return nelm;}

  /// number of nodes
  uint nnodes() const {return vtx.size();}

  /// access node
  const Vct3 & node(uint i) const {return vtx[i];}

  /// access node
  Vct3 & node(uint i) {return vtx[i];}

  /// access node array
  const PointList<3> & nodes() const {return vtx;}

  /// access node array
  PointList<3> & nodes() {return vtx;}

  /// append a single vertex
  uint appendNode(const Vct3 & p) {
    vtx.push_back(p);
    return vtx.size()-1;
  }

  /// append nodes, return index of the first new node
  uint appendNodes(const PointList<3> & nds) {
    return appendNodes(nds.begin(), nds.end());
  }

  /// append nodes, return index of the first new node
  template <class NodeIter>
  uint appendNodes(NodeIter nbegin, NodeIter nend) {
    uint offset = vtx.size();
    vtx.insert(vtx.end(), nbegin, nend);
    return offset;
  }

  /// number of sections
  uint nsections() const {return sections.size();}

  /// access mesh section
  const MxMeshSection & section(uint i) const {
    assert(i < sections.size());
    return sections[i];
  }

  /// access mesh section
  MxMeshSection & section(uint i) {
    assert(i < sections.size());
    return sections[i];
  }

  /// determine section of element eix
  uint findSection(uint eix) const {
    if (eix >= nelements())
      return NotFound;
    Mx::IndexOffsetCmp cmp;
    std::vector<MxMeshSection>::const_iterator pos;
    pos = std::upper_bound(sections.begin(),
                           sections.end(), eix, cmp);
    uint idx = std::distance(sections.begin(), pos-1);
    assert(idx < nsections());
    assert(eix >= section(idx).indexOffset());
    assert(idx == nsections()-1 or
           eix < section(idx+1).indexOffset());
    return idx;
  }

  /// determine section index from name
  uint findSection(const std::string &sname) const {
    std::vector<MxMeshSection>::const_iterator pos;
    auto pred = [&](const MxMeshSection &s) {return s.name() == sname;};
    pos = std::find_if(sections.begin(), sections.end(), pred);
    return (pos != sections.end()) ?
          std::distance(sections.begin(), pos) : NotFound;
  }

  /// search global element data
  const uint *globalElement(uint gix, uint & n, uint & isec) const {
    isec = findSection(gix);
    if (isec != NotFound) {
      n = section(isec).nElementNodes();
      return section(isec).globalElement(gix);
    }
    n = 0;
    return nullptr;
  }

  /// assemble section-element connection
  void elementSections(const Indices & gix, ConnectMap & s2e) const;

  /// add mesh section, return index
  uint appendSection(const MxMeshSection & ms) {
    sections.push_back( ms );
    sections.back().indexOffset(nelm);
    nelm += sections.back().nelements();
    v2e.clear();
    return sections.size()-1;
  }

  /// add mesh section, return index
  uint appendSection(Mx::ElementType t, const Indices & idx);

  /// add triangular mesh as section
  uint appendSection(const TriMesh & m);

  /// add point grid as Quad4 elements
  uint appendSection(const PointGrid<3> & pg);

  /// add a set of lines connecting pts
  uint appendSection(const PointList<3> &pts);

  /// add triangles from CgMesh
  uint appendSection(const CgMesh & cgm);

  /// erase a single section
  void eraseSection(uint k);

  /// insert mirror copies of nodes in set, return node index offset
  uint mirrorCopyNodes(const Indices &snodes, const Plane &pln);

  /// create a mirror copy of section k (generates new nodes)
  uint mirrorCopySection(uint k, uint voff, const Indices &snodes,
                         bool merge=true);

  /// number of boundary condition sets
  uint nbocos() const {return bocos.size();}

  /// access boundary condition spec
  const MxMeshBoco & boco(uint i) const {
    assert(i < bocos.size());
    return bocos[i];
  }

  /// access boundary condition spec
  MxMeshBoco & boco(uint i) {
    assert(i < bocos.size());
    return bocos[i];
  }

  /// append boundary condition element group
  uint appendBoco(Mx::BocoType t, const Indices & idx) {
    bocos.emplace_back(t, idx);
    return bocos.size()-1;
  }

  /// append boundary condition element group
  uint appendBoco(const MxMeshBoco & bc) {
    bocos.push_back(bc);
    return bocos.size()-1;
  }

  /// append boundary condition element group
  uint appendBoco(MxMeshBoco &&bc) {
    bocos.push_back(bc);
    return bocos.size()-1;
  }

  /// erase element subset
  void eraseBoco(uint k) {
    assert(k < bocos.size());
    bocos.erase(bocos.begin() + k);
  }

  /// erase all boundary condition sets
  void clearBocos() {bocos.clear();}

  /// find boco group by name
  uint findBoco(const std::string & s) const;

  /// determine which, if any, section maps exactly to iboco
  uint mappedSection(uint iboco) const;

  /// determine in which section, if any, iboco is contained
  uint containedInSection(uint iboco) const;

  /// number of fields
  uint nfields() const {return fields.size();}

  /// number of vector-valued fields with dimension nd
  uint nDimFields(uint nd=3) const;

  /// access field i
  const MxMeshField & field(uint i) const {
    assert(i < nfields());
    return fields[i];
  }

  /// access field i
  MxMeshField & field(uint i) {
    assert(i < nfields());
    return fields[i];
  }

  /// bind misassigned fields to this
  void bindFields();

  /// reserve storage for n fields
  void reserveFields(uint n) {
    fields.reserve(n);
  }

  /// add point-data field
  uint appendField(const MxMeshField & f) {
    fields.push_back(f);
    return fields.size()-1;
  }

  /// add point-data field
  uint appendField(MxMeshField &&f) {
    fields.push_back(std::move(f));
    return fields.size()-1;
  }

  /// swap-in point-data field (deprecated)
  uint swapField(MxMeshField & f) {
    fields.push_back( MxMeshField(this, f.nodal(), f.ndimension()) );
    fields.back().swap(f);
    return fields.size()-1;
  }

  /// add scalar real field
  uint appendField(const std::string & s, const Vector & v);

  /// add scalar real field
  uint appendField(const std::string & s, const DVector<float> & v);

  /// add scalar integer field
  uint appendField(const std::string & s, const DVector<int> & v);

  /// add 3-component vector field
  uint appendField(const std::string & s, const PointList<3> & v);

  /// add 3-component vector field
  uint appendField(const std::string & s, const PointList<3,float> & v);

  /// add 6-component vector field
  uint appendField(const std::string & s, const PointList<6> & v);

  /// add 6-component vector field
  uint appendField(const std::string & s, const PointList<6,float> & v);

  /// generate artificial rigid-body modeshapes
  uint appendRigidBodyMode(int mindex, const Vct3 & rotctr,
                           Real gm=1.0, Real gk=0.0);

  /// find field by name, return NotFound otherwise
  uint findField(const std::string & s) const;

  /// find fields of class c
  void findFields(int valClass, Indices & flds) const;

  /// erase a single field
  void eraseField(uint k);

  /// remove all data fields
  void clearFields() {
    fields.clear();
    deforms.clear();
  }

  /// generate maximum value fields across multiple subcases
  bool generateMaxFields(bool useMaxAbs);

  /// access global solution tree which contains hierarchy data for fields
  MxSolutionTreePtr solutionTree() const {return soltree;}

  /// access global solution tree which contains hierarchy data for fields
  void solutionTree(MxSolutionTreePtr p) {soltree = p;}

  /// another mesh, optionally merge fields
  void merge(const MxMesh & a, bool mergeFieldsByName);

  /// number of time-domain subspace nodal deformation fields
  uint ndeform() const {return deforms.size();}

  /// access subspace deformation field
  const MxMeshDeform & deform(uint i) const {
    assert(i < ndeform());
    return deforms[i];
  }

  /// access subspace deformation field
  MxMeshDeform & deform(uint i) {
    assert(i < ndeform());
    return deforms[i];
  }

  /// erase a deformation path
  void eraseDeform(uint i) {
    deforms.erase( deforms.begin()+i );
  }

  /// append externally created subspace deformation
  uint appendDeform(const MxMeshDeform &d) {
    deforms.push_back(d);
    return deforms.size()-1;
  }

  /// load trajectory from file
  uint appendTrajectory(const std::string &fn,
                        const Indices &useCols = Indices());

  /// append a flutter mode based on all currently stored vector fields
  uint appendFlutterMode(Complex p, const CpxVector & z, int nsample=32);

  /// smooth nodes connected to tetrahedral elements
  void smoothTetNodes(uint npass=1, Real omega=0.5);

  /// determine a list of elements which intersect plane p
  uint planeCut(const Plane & p, Indices & ise) const;

  /// determine whether nodes are below plane p
  void nodesBelow(const Plane & p, std::vector<bool> & nbelow) const;

  /// change element index ordering
  virtual void reorder(const Indices & perm);

  /// drop unreferenced nodes from mesh (reorders)
  uint dropUnusedNodes();

  /// eliminate elements with duplicate vertices
  uint dropDegenerateElements();

  /// drop duplicate nodes
  uint mergeNodes(Real threshold=gmepsilon);

  /// try to load any of the supported formats from file
  virtual bool loadAny(const std::string &fname);

  /// import from older MeshFields format
  void importMvz(const MeshFields & mvz);

  /// generate a TriMesh from triangle sections (interfacing)
  TriMeshPtr toTriMesh() const;

  /// generate a CgMesh from surface element sections (for interfacing)
  CgMeshPtr toCgMesh() const;

  /// write in specified format, if possible
  void writeAs(const std::string &fname, int fmt, int compression) const;

  /// dump everything to triangles and export to STL format
  void writeSTL(const std::string & fname, bool binaryStl=false) const;

  /// dump everything to triangles and export to PLY format
  void writePLY(const std::string &fname, bool binary) const;

  /// write 3-node triangles as smesh file for tetgen
  void writeSmesh(const std::string & fname,
                  const PointList<3> & holes = PointList<3>(),
                  const PointList<3> & regionMarkers = PointList<3>(),
                  const Vector &regionAttr = Vector()) const;

  /// import from tetgen volume mesh files
  void readTetgen(const std::string & basename, DVector<uint> *ftags=0);

  /// read from CGNS file
  void readCgns(const std::string & fname);

  /// write to CGNS file
  void writeCgns(const std::string & fname, bool bcAsSections=false) const;

  /// import mesh in ABAQUS text format
  void readAbaqus(const std::string &fname);

  /// write mesh file in ABAQUS text format
  void writeAbaqus(const std::string &fname) const;

  /// write mesh in NASTRAN bulk data format
  void writeNastran(const std::string &fname,
                    size_t nodeOffset=0, size_t eidOffset=0) const;

  /// write mesh in NASTRAN bulk data format
  void writeNastran(std::ostream &os,
                    size_t nodeOffset, size_t eidOffset) const;

  /// create a binary file node
  BinFileNodePtr gbfNode(bool share = true) const;

  /// retrieve data from gbf file node
  void fromGbf(const BinFileNodePtr & np, bool digestNode=false);

  /// convert to xml representation
  virtual XmlElement toXml(bool share=false) const;

  /// retrieve section from xml representation
  virtual void fromXml(const XmlElement & xe);

  /// convenience function : store to zipped xml
  void writeZml(const std::string & fname, int compression=1) const;

  /// convenience function : read from zipped xml
  void readZml(const std::string & fname);

  /// export to VTK xml format (.vtu)
  XmlElement toVTK() const;

  /// write legacy VTK format (version 2.0)
  void writeLegacyVtk(const std::string &fname) const;

  /// read unstructured grid datasets from legacy VTK files
  void readLegacyVtk(const std::string &fname);

  /// read AERELPLOT file
  void readAerel(const std::string &fname);

  /// write mesh in FFA format (bmsh)
  void writeFFA(const std::string & fname) const;

  /// read mesh in FFA format (bmsh)
  void readFFA(const std::string & bmeshFile);

  /// append data fields from .bout file
  bool appendFFAFields(const std::string & boutFile);

  /// write boundary displacement fields in bdis format
  size_t writeFieldsBdis(const std::string &basename) const;

#ifdef HAVE_NETCDF

  /// write mesh for DLR TAU solver
  void writeTau(const std::string & fname) const;

  /// read mesh for DLR TAU solver
  void readTau(const std::string & fname);

#endif

#ifdef HAVE_HDF5

  /// write mesh and fields in HDF5 format
  void writeHdf5(const std::string &fname);

  /// write mesh and fields and append into existing HDF5 group
  void writeHdf5(Hdf5Group &parent);

  /// fetch mesh from HDF5 group
  void readHdf5(Hdf5Group &parent);

#endif

  /// write in SU2 plain text format
  void writeSU2(const std::string & fname) const;

  /// read from SU2 plain text format
  void readSU2(const std::string &fname);

  /// write Ensight 7/gold format files
  void writeEnsight(const std::string &basename) const;

  /// read Ensight 7/gold format files
  void readEnsight(const std::string &casename);

  /// write a faked bulk data / modal result file (nastran .f06 format)
  void fakeNastran(const std::string & fname) const;

  /// update section element counts after change
  void countElements();

  /// compute connectivity data
  void fixate();

  /// access vertex-to-element connectivity map
  const ConnectMap & v2eMap() const {return v2e;}

  /// update an external vertex-vertex connectivity map
  void v2vMap(ConnectMap & v2v) const;

  /// generate an external element-to-element map
  void e2eMap(ConnectMap & e2e) const;

  /// test whether element e1 contains all vertices of e2
  bool containsNodesOf(uint e1, uint e2) const;

  /** Compute connected components.
    Assign a component index to each element, spread component index to
    all reachable elements until all elements have been assigned to a
    component. Returns number of connected components. If crossTypes is
    true, than the walk will jump between element classes (volume/surface/line),
    otherwise, element class bondaries are component boundaries. */
  uint connectedComponents(Indices &ecmp, bool crossTypes=false) const;

  /// clear out all data
  virtual void clear() {
    vtx.clear();
    sections.clear();
    bocos.clear();
    fields.clear();
    deforms.clear();
    xnote = XmlElement();
    v2e.clear();
    nelm = 0;
  }

  /// memory requirements
  virtual float megabytes() const;

  /// return the number of node for element type t
  static uint nElementNodes(Mx::ElementType t) {
    return MxMeshSection::nElementNodes(t);
  }

  /// set rotating colors for sections
  int resetSectionColors(int hue, int sat=120, int val=140);

  /// set rotating colors for boundary conditions
  int resetBocoColors(int hue, int sat=160, int val=170);


protected:

  typedef std::vector<Indices> ElementCollector;

  /// reassemble three-dimensional vector field after reading from cgns
  void assembleVectorFields();

  /// read vertex coordinates from tetgen .node file
  virtual int readTetgenNodes(std::istream & is);

  /// read boundary triangles from tetgen .face file
  virtual void readTetgenFaces(std::istream & is,
                               int offset, DVector<uint> *ptags = 0);

  /// read tet elements from tetgen .ele file
  virtual void readTetgenElements(std::istream & is, int offset);

  /// recover all sections from a FFA file region
  void readFFARegion(const FFANode & node);

  /// recover a section from a bmesh boundary section
  void readFFABoundary(const FFANode & node);

  /// create a subcase with a set of fields from EDGE solution
  MxSolutionTreePtr appendSubcase(FFANodePtr pregion);

  /// read node coordinates and node ID numbers from Abaqus mesh file
  std::string readAbaqusNodes(std::istream &in, DVector<int> &gid);

  /// create an element section while reading Abaqus mesh file
  std::string readAbaqusElements(const std::string &header,
                                 std::istream &in, DVector<int> &eid);

  /// create an element set/boco reading Abaqus mesh file
  std::string readAbaqusSet(const std::string &header,
                            const DVector<int> &eid,
                            std::istream &in);

  /// store Abaqus keyword line in XML annotation
  std::string readAbaqusKeyword(const std::string &header,
                                std::istream &in,
                                XmlElement &xabq);

  /// generate maximum value fields across multiple subcases, start with tree
  MxSolutionTreePtr generateMaxFields(MxSolutionTreePtr root, bool useMaxAbs);

  /// globally change the precision stored in files that support conversion
  static void fileFloatPrecision(TypeCode tc) {
    s_fileFloatPrecision = tc;
  }

protected:

  /// mesh vertices
  PointList<3> vtx;

  /// mesh sections
  std::vector<MxMeshSection> sections;

  /// boundary condition specs
  std::vector<MxMeshBoco> bocos;

  /// node- or element-centered data fields
  std::vector<MxMeshField> fields;

  /// time-domain mesh deformation spec
  std::vector<MxMeshDeform> deforms;

  /// global structure for solution fields (optional)
  MxSolutionTreePtr soltree;

  /// vertex-to-element connectivity
  ConnectMap v2e;

  /// mesh id
  std::string meshName;

  /// number of elements present
  uint nelm;

  /// global setting - store vertex data in single precision?
  static TypeCode s_fileFloatPrecision;
};

#endif
