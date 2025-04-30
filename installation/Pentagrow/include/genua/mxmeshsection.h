
/* Copyright (C) 2016 David Eller <david@larosterna.com>
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
 
#ifndef GENUA_MXMESHSECTION_H
#define GENUA_MXMESHSECTION_H

#include "forward.h"
#include "binfilenode.h"
#include "mxmeshtypes.h"
#include "xmlelement.h"
#include "point.h"
#include "color.h"

class CgnsSection;
class MxMesh;
class MxMeshBoco;
class Plane;
class FFANode;

/** Section of a mixed-element mesh.

  Each section of a MxMesh contains only one element type. This restriction
  is necessary to allow one-to-one writing to CGNS. Furthermore, different 
  sections can be used to communicate areas to be treated differently, for 
  example to mark surfaces for which separate force integration is to be 
  performed.

  \ingroup mesh
  \sa MxMesh
 */
class MxMeshSection
{
  public:
    
    /// tag to indicate which domain this section belongs to
    enum DomainType { Undefined=0, Interface=1, Fluid=2,
                      FluidInterface=3, Structure=4,
                      StructureInterface=5 };

    /// construct empty section 
    MxMeshSection(const MxMesh *pmesh = 0, 
                  Mx::ElementType t = Mx::Undefined) : 
      parent(pmesh), etype(t), secid(str(t)), xnote("MxNote"),
      dispColor(0.5f,0.5f,0.5f), domainType(Undefined), itag(0) {}
    
    /// access element type 
    Mx::ElementType elementType() const {return etype;}

    /// domain type flag
    DomainType domain() const {return domainType;}
    
    /// domain type flag
    void domain(DomainType t) {domainType = t;}

    /// set integer tag
    void tag(int t) {itag = t;}

    /// access integer tag
    int tag() const {return itag;}

    /// number of nodes in elements in this section
    uint nElementNodes() const {
      return nElementNodes(etype);
    }
    
    /// number of elements 
    uint nelements() const {
      return inodes.empty() ? 0 : (inodes.size() / nElementNodes(etype));
    }
    
    /// element count offset
    uint indexOffset() const {return eloff;}
    
    /// access section name 
    const std::string & name() const {return secid;}
    
    /// change section name 
    void rename(const std::string & s) {secid = s;}
    
    /// apply an vertex index offset to all elements
    void shiftVertexIndices(int offset);

    /// in element eix, replace iold with inew
    uint replaceVertex(uint eix, uint iold, uint inew) {
      const int npe = nElementNodes(etype);
      uint *v = &inodes[eix*npe];
      uint repcount(0);
      for (int k=0; k<npe; ++k) {
        if (v[k] == iold) {
          v[k] = inew;
          ++repcount;
        }
      }
      return repcount;
    }

    /// restrict from P2 to P1 elements if possible, return success
    bool dropOrder();

    /// access node array
    const Indices & nodes() const {return inodes;}

    /// access node array
    Indices & nodes() {return inodes;}

    /// add element nodes  
    void appendElements(const Indices & elm) {
      assert(elm.size() % nElementNodes(etype) == 0);
      inodes.insert(inodes.end(), elm.begin(), elm.end());
    }
    
    /// add element nodes, ne is the number of elements 
    void appendElements(uint ne, const uint idx[]) {
      inodes.insert(inodes.end(), idx, idx + npelm[ int(etype) ]*ne);
    }
    
    /// access pointer to nodes of element i 
    const uint *element(uint i) const {
      assert(i*nElementNodes(etype) < inodes.size());
      return &inodes[ i*nElementNodes(etype) ];
    }

    /// access pointer to nodes of element i 
    const uint *globalElement(uint i) const {
      return element(i - eloff);
    }

    /// change element indices and type
    void swapElements(Mx::ElementType t, Indices & elix) {
      etype = t;
      inodes.swap(elix);
    }
    
    /// determine indices of points used in this section
    void usedNodes(Indices & ipts) const;

    /// drop all elements which contain duplicate nodes
    size_t dropDegenerateElements();

    /// triangle vertex indices, relative to element vertices
    int triangleVertices(int vi[]) const;
    
    /// quad vertex indices, relative to element vertices
    int quadVertices(int vi[]) const;
    
    /// line vertex indices, relative to element vertices
    int lineVertices(int vi[]) const;

    /// access mapping of local element vertex indices to triangle decomposition
    int triangleMap(const int *map[]) const {
      return MxMeshSection::triangleMap( elementType(), map );
    }

    /// access mapping of local element vertex indices to triangle decomposition
    static int triangleMap(Mx::ElementType etype, const int *map[]);

    /// convert entire section to triangles (e.g. for location queries)
    bool toTriangles(Indices &tri) const;

    /// true if section contains 1D (line) elements
    bool lineElements() const {
      return lineElement(etype);
    }

    /// true if section contains surface elements
    bool surfaceElements() const  {
      return surfaceElement(etype);
    }

    /// true if section contains volume elements
    bool volumeElements() const  {
      return volumeElement(etype);
    }

    /// true if element class (surface/volume/line) matches
    bool sameElementClass(const MxMeshSection &sec) const {
      if (lineElements() != sec.lineElements())
        return false;
      else if (surfaceElements() != sec.surfaceElements())
        return false;
      else if (volumeElements() != sec.volumeElements())
        return false;
      return true;
    }
    
    /// determine list of local elements that intersect p
    uint planeCut(const std::vector<bool> & nbelow, Indices & ise) const;
    
    /// compute element aspect ratio (longest/shortest edge)
    void aspectRatio(Vector & aspr) const;
    
    /// compute a typical one-dimensional element size
    void elementLength(Vector & elen) const;

    /// return a name for the element type
    std::string elementTypeName() const {return str(etype);}
    
    /// visualization utility : compute shell element normal data
    uint vizNormalPoints(PointList<3,float> & pts) const;

    /// utility : integrate a pressure field over this section
    Vct6 integratePressure(const MxMeshField &pfield, const Vct3 & pref) const;

    /// set the contents of the complete annotation object
    void note(const XmlElement & xe) {xnote = xe; xnote.rename("MxNote");}
    
    /// retrieve xml annotation object
    const XmlElement & note() const {return xnote;}
    
    /// append annotation element
    void annotate(const XmlElement & xe) {xnote.append(xe);}
    
    /// iterate over annotations
    XmlElement::const_iterator noteBegin() const {return xnote.begin();}
    
    /// iterate over annotations
    XmlElement::const_iterator noteEnd() const {return xnote.end();}
    
    /// return true if element set mapped by boco matches this section exactly
    bool maps(const MxMeshBoco & bc) const;

    /// return true if element set mapped by boco are all contained in *this
    bool contains(const MxMeshBoco & bc) const;

    /// estimate normal vector for surface elements, where supported
    bool estimateNormals(PointList<3> & nrm) const;

    /// access display color
    const Color & displayColor() const {return dispColor;}

    /// access display color
    void displayColor(const Color & c) {dispColor = c;}

    /// memory requirements for this section (w/o note)
    float megabytes() const {
      float bts = sizeof(MxMeshSection);
      bts += inodes.capacity()*sizeof(Indices::value_type);
      return 1e-6f*bts;
    }

    /// clear all elements
    void clear() {inodes.clear();}

    /// retrieve data from CGNS file section
    void readCgns(CgnsSection & cs);
    
    /// write section in CGNS file 
    void writeCgns(CgnsSection & cs, int isec=0) const;
    
    /// write in plain-text Abaqus format
    void writeAbaqus(const Indices &gid, const Indices &eid,
                     std::ostream &os) const;

    /// write to plain-text format for SU2
    void writeSU2(std::ostream &os) const;

    /// write section as part to binary Ensight format
    void writeEnsight(int partno, std::ostream &os) const;

    /// write field data for this section to binary Ensight format
    void writeEnsight(int partno, const MxMeshField &f, std::ostream &os) const;

    /// create mesh section from part block in Ensight geometry file
    static uint createFromEnsight(MxMesh *pmx, int flags, std::istream &in);

    /// write section to xml vtk 
    XmlElement toVTK() const;
    
    /// create a binary file node
    BinFileNodePtr gbfNode(bool share = true) const;
    
    /// retrieve data from gbf file node
    void fromGbf(const BinFileNodePtr & np, bool digestNode=false);

    /// convert to xml representation
    XmlElement toXml(bool share) const;

    /// retrieve section from xml representation
    void fromXml(const XmlElement & xe);
    
    /// write section in FFA format
    void toFFA(FFANode & node) const;
    
    /// recover section from FFA format
    bool fromFFA(const FFANode & node);

#ifdef HAVE_HDF5

    /// write section data to HDF5 file
    void writeHdf5(Hdf5Group &grp) const;

#endif

    /// return the number of node for element type t
    static uint nElementNodes(Mx::ElementType t) {
      return npelm[ int(t) ];
    }

    /// return if etype is a 1D (line) element
    static bool lineElement(Mx::ElementType etype);

    /// true if section contains surface elements
    static bool surfaceElement(Mx::ElementType etype);

    /// true if section contains volume elements
    static bool volumeElement(Mx::ElementType etype);
    
  private:
    
    /// element count offset (set by MxMesh)
    void indexOffset(uint off) {eloff = off;}
    
    /// change index ordering
    void ipreorder(const Indices & iperm);

    /// eliminate elements which collapse to one single node
    size_t dropCollapsedElements();
    
  private:
    
    /// pointer to parent mesh
    const MxMesh *parent;
    
    /// node indices 
    Indices inodes;
    
    /// element type 
    Mx::ElementType etype;

    /// optional name 
    std::string secid;
    
    /// annotation object
    XmlElement xnote;
    
    /// color to use for display
    Color dispColor;

    /// element count offset
    uint eloff;
    
    /// tag to identify fluid/structure domain
    DomainType domainType;

    /// integer tag
    int itag;

    /// number of nodes per element (fixed)
    static const uint npelm[Mx::NElmTypes];
    
    friend class MxMesh;
};

namespace Mx
{
  struct IndexOffsetCmp {
    bool operator() (const MxMeshSection & a, const MxMeshSection & b) const {
      // not strictly needed, but invoked by MSVC in debug mode
      return a.indexOffset() < b.indexOffset();
    }
    bool operator() (const MxMeshSection & a, uint b) const {
      return a.indexOffset() < b;
    }
    bool operator() (uint a, const MxMeshSection & b) const {
      return a < b.indexOffset();
    }
  };
}

#endif
