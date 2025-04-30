
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
 
#ifndef GENUA_MXMESHBOCO_H
#define GENUA_MXMESHBOCO_H

#include "mxmeshtypes.h"
#include "mxannotated.h"
#include "defines.h"
#include "svector.h"
#include "xmlelement.h"
#include "binfilenode.h"
#include "color.h"

class MxMesh;
class CgnsBoco;
class FFANode;

/** Boundary conditions in mixed-element mesh.

  MxMeshBoco contains a list (or range) of global element indices to 
  which a certain boundary condition should be applied. In all cases,
  boundary conditions must concern elements, not vertices.

  \ingroup mesh
  \sa MxMesh
 */
class MxMeshBoco : public MxAnnotated
{
  public:
    
    /// construct unconnected boco 
    MxMeshBoco(Mx::BocoType t = Mx::BcUndefined)
      : MxAnnotated(), bRange(false), bctype(t),
        dispColor(0.5f,0.5f,0.5f), itag(0) {}

    /// construct boco from element list
    MxMeshBoco(Mx::BocoType t, const Indices &idx)
      : MxAnnotated(), bcelm(idx), bRange(false), bctype(t),
        dispColor(0.5f,0.5f,0.5f), itag(0) {}

    /// construct boco from element range
    MxMeshBoco(Mx::BocoType t, uint a, uint b);
    
    /// default copy constructor
    MxMeshBoco(const MxMeshBoco &) = default;

    /// move constructor
    MxMeshBoco(MxMeshBoco &&a) {
      *this = std::move(a);
    }

    /// default copy assignment
    MxMeshBoco &operator= (const MxMeshBoco &) = default;

    /// move constructor
    MxMeshBoco &operator= (MxMeshBoco &&a) {
      if (this != &a) {
        bcelm = std::move(a.bcelm);
        bcid = std::move(a.bcid);
        bRange = a.bRange;
        dispColor = a.dispColor;
        itag = a.itag;
      }
      return *this;
    }

    /// boundary condition type flag
    Mx::BocoType bocoType() const {return bctype;}
    
    /// change boundary condition type flag
    void bocoType(Mx::BocoType t) {bctype = t;}
    
    /// access section name 
    const std::string & name() const {return bcid;}
    
    /// change section name 
    void rename(const std::string & s) {bcid = s;}
    
    /// access integer tag
    int tag() const {return itag;}

    /// set integer tag
    void tag(int t) {itag = t;}

    /// append single element
    void appendElement(uint idx) {
      bRange = false;
      bcelm.push_back( idx );
    }

    /// sort elements
    void sort() {
      sort_unique(bcelm);
    }

    /// append elements for which to apply this BC
    void appendElements(const Indices & idx) {
      bRange = false;
      bcelm.insert(bcelm.end(), idx.begin(), idx.end());
      sort_unique(bcelm);
    } 

    /// append elements for which to apply this BC
    template <class Iterator>
    void appendElements(Iterator begin, Iterator end) {
      bRange = false;
      bcelm.insert(bcelm.end(), begin, end);
      sort_unique(bcelm);
    } 

    /// erase range of elements
    void eraseElements(uint a, uint b);
    
    /// set element range (STL style, first and one-beyond last)
    void setRange(uint begin, uint end) {
      bRange = true;
      bcelm.resize(2);
      bcelm[0] = begin;
      bcelm[1] = end;
    }
    
    /// return true if element set is a continuous range
    bool isRange() const {return bRange;}

    /// first element of range, or NotFound if not a range-set
    uint rangeBegin() const {
      return (bRange ? bcelm[0] : NotFound);
    }

    /// one-past-last element of range, or NotFound if not a range-set
    uint rangeEnd() const {
      return (bRange ? bcelm[1] : NotFound);
    }

    /// empty region?
    bool empty() const {return bcelm.empty();}
    
    /// number of elements in this group
    uint nelements() const;

    /// remove all elements in set
    void clearElements();
    
    /// retrieve set of element indices
    size_t elements(Indices & idx) const;
    
    /// return the first element only
    uint firstElement() const {
      return isRange() ? rangeBegin() : (bcelm.empty() ? NotFound : bcelm[0]);
    }

    /// shift all element indices above threshold by shift
    void shiftElementIndices(int shift, uint threshold=0);

    /// define a total massflow inlet for EDGE
    void edgeMassflowInlet(Real mdot, Real Ttot, const Vct3 & dir);
    
    /// define a total massflow outlet for EDGE
    void edgeMassflowOutlet(Real mdot);
    
    /// create a binary file node
    BinFileNodePtr gbfNode(bool share = true) const;
    
    /// retrieve data from gbf file node
    void fromGbf(const BinFileNodePtr & np, bool digestNode=false);

    /// convert to xml representation
    XmlElement toXml(bool share) const;

    /// retrieve section from xml representation
    void fromXml(const XmlElement & xe);
    
    /// export boundary condition data to FFA format
    void toFFA(FFANode & node) const;

    /// read from CGNS
    void readCgns(CgnsBoco & cb);
    
    /// write to CGNS file 
    void writeCgns(CgnsBoco & cb) const;

#ifdef HAVE_HDF5

    /// write to HDF5 group
    void writeHdf5(Hdf5Group &grp) const;

#endif

    /// write element or node set in Abaqus plain text format
    void writeAbaqus(const Indices &gid, const Indices &eid, std::ostream &os) const;
    
    /// memory requirements (w/o notes)
    float megabytes() const {
      float bts = sizeof(MxMeshBoco);
      bts += bcelm.capacity()*sizeof(Indices::value_type);
      return 1e-6f*bts;
    }

    /// access display color
    const Color & displayColor() const {return dispColor;}

    /// access display color
    void displayColor(const Color & c) {dispColor = c;}

  private:

    /// element indices affected 
    Indices bcelm;
    
    /// interprete as element range or list?
    bool bRange;

    /// boundary condition type 
    Mx::BocoType bctype;
    
    /// boco identification 
    std::string bcid;
    
    /// color to use for graphical display
    Color dispColor;

    /// tag used to track bc across call to tetgen
    int itag;
    
    friend class MxMesh;
};

#endif
