
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
 
#ifndef GENUA_MXMESHFIELD_H
#define GENUA_MXMESHFIELD_H

#include "forward.h"
#include "mxmeshtypes.h"
#include "mxannotated.h"
#include "svector.h"
#include "dvector.h"
#include "xmlelement.h"
#include "binfilenode.h"
#include "enumobject.h"
#include "typecode.h"
#include <initializer_list>

/** Data fields on mixed-element meshes.

  This class represents a single data field defined on a mixed-element mesh.
  Data can have arbitrary dimensions (scalar, n-dimensional vector, etc),
  but must either be defined for all elements of the mesh, or for all vertices.

  \ingroup mesh
  \sa MxMesh
 */
class MxMeshField : public MxAnnotated
{
public:

  /// class represented by this field
  class ValueClass : public EnumObject<11> {
  public:
    enum Code { Field, Eigenmode, Displacement, Rotation,
                Force, Moment, ForceAndMoment, CoefPressure,
                DeltaCp, ReDCp, ImDCp };
    ValueClass() : m_code(Field) {}
    ValueClass(int c) : m_code(c) {}
    int code() const {return m_code;}
    bool parse(const std::string &s) {
      int c = EnumObject<11>::parse(s_keylist, s);
      if (c != -1) {
        m_code = c;
        return true;
      }
      return false;
    }
    const char *str() const {return s_keylist[m_code];}
    bool operator== (int c) const {return m_code == c;}
    bool operator!= (int c) const {return m_code != c;}
    bool operator== (ValueClass c) const {return m_code == c.m_code;}
    bool operator!= (ValueClass c) const {return m_code != c.m_code;}
  private:
    int m_code;
    static const char *s_keylist[11];
  };

  /// create named field
  MxMeshField(const MxMesh *pmesh, bool nodalf = true, size_t dim = 1) :
    MxAnnotated(), parent(pmesh), ndim(dim),
    solindex(0), bNodal(nodalf) {}

  /// default copy
  MxMeshField(const MxMeshField &) = default;

  /// move construction
  MxMeshField(MxMeshField &&a) { *this = std::move(a); }

  /// copy assignment
  MxMeshField & operator= (const MxMeshField &) = default;

  /// move assignment
  MxMeshField & operator= (MxMeshField &&a) {
    if (this != &a) {
      parent = a.parent;
      fid = std::move(a.fid);
      rval = std::move(a.rval);
      ival = std::move(a.ival);
      ndim = a.ndim;
      vclass = a.vclass;
      solindex = a.solindex;
      bNodal = a.bNodal;
    }
    return *this;
  }

  /// field name
  const std::string & name() const {return fid;}

  /// change name
  void rename(const std::string & s) {fid = s;}

  /// bind to another mesh (dangerous)
  void bind(const MxMesh *pmesh) {parent = pmesh;}

  /// access value class tag
  ValueClass valueClass() const {return vclass;}

  /// access value class tag
  void valueClass(ValueClass c) {vclass = c;}

  /// field belongs to this solution
  size_t solutionIndex() const {return solindex;}

  /// change solution index
  void solutionIndex(size_t si) {solindex = si;}

  /// nodal or cell data?
  bool nodal() const {return bNodal;}

  /// real-valued or integer-valued ?
  bool realField() const {return ival.empty();}

  /// number of components per node/cell value
  size_t ndimension() const {return ndim;}

  /// field length : number of scalar values
  size_t size() const {return ival.empty() ? rval.size() : ival.size();}

  /// number of N-dimensional elements
  size_t nelements() const {return size() / ndimension();}

  /// check if dimension and type are compatible
  bool compatible(const MxMeshField & a) const;

  /// append data in a if possible
  bool merge(const MxMeshField & a);

  /// transform 3D field data
  void transform(const Trafo3d & trafo);

  /// retrieve vector value
  template <typename Type, uint N>
  void value(size_t node, SVector<N,Type> & x) const {
    assert(N <= ndimension());
    const size_t noffset = ndim*node;
    for (size_t k=0; k<N; ++k)
      x[k] = rval[noffset + k];
  }

  /// change vector value
  template <typename Type, uint N>
  void setValue(size_t k, const SVector<N,Type> & x) {
    assert(N <= ndimension());
    for (size_t i=0; i<N; ++i)
      rval[ndim*k+i] = x[i];
  }

  /// retrieve scalar value (conversion)
  template <typename Type>
  void scalar(size_t k, Type & x) const {
    if (realField())
      x = static_cast<Type>( rval[k] );
    else
      x = static_cast<Type>( ival[k] );
  }

  /// retrieve scalar value (conversion)
  template <typename Type>
  void scalar(size_t i, size_t k, Type & x) const {
    assert(k < ndim);
    if (realField())
      x = static_cast<Type>( rval[i*ndim+k] );
    else
      x = static_cast<Type>( ival[i*ndim+k] );
  }

  /// change scalar value
  template <typename Type>
  void setScalar(size_t k, const Type &x) {
    assert(ndim == 1);
    if (realField())
      rval[k] = x;
    else
      ival[k] = x;
  }

  /// retrieve scalar values (conversion)
  template <typename Type>
  void fetch(const Indices &idx, Type x[]) const {
    const size_t n = idx.size();
    if (realField()) {
      for (size_t i=0; i<n; ++i)
        x[i] = static_cast<Type>( rval[idx[i]] );
    } else {
      for (size_t i=0; i<n; ++i)
        x[i] = static_cast<Type>( ival[idx[i]] );
    }
  }

  /// retrieve values to container
  template <typename Container>
  void fetch(Container & c) const {
    c.resize( size() );
    if (realField())
      std::copy(rval.begin(), rval.end(), c.begin());
    else
      std::copy(ival.begin(), ival.end(), c.begin());
  }

  /// retrieve values to container
  template <typename ElementType>
  void fetch(DVector<ElementType> & c) const {
    c.allocate( size() );
    if (realField())
      std::copy(rval.begin(), rval.end(), c.begin());
    else
      std::copy(ival.begin(), ival.end(), c.begin());
  }

  /// retrieve values to container
  template <typename Type, uint N>
  void fetch(PointList<N,Type> & vf) const {
    if (realField()) {
      assert(N <= ndim);
      const size_t nv = nelements();
      vf.resize(nv);
      for (size_t i=0; i<nv; ++i)
        value(i, vf[i]);
    }
  }

  // debug
  template <typename Type, uint N>
  void vfetch(PointList<N,Type> & vf) const {
    if (realField()) {
      assert(N <= ndim);
      const size_t nv = nelements();
      vf.resize(nv);
      for (size_t i=0; i<nv; ++i)
        value(i, vf[i]);
    }
  }

  /// retrieve subset of vector values to container
  template <typename Type, uint N>
  void fetch(const Indices &idx, PointList<N,Type> & vf) const {
    if (realField()) {
      assert(N <= ndim);
      const size_t n = idx.size();
      vf.resize(n);
      for (size_t i=0; i<n; ++i)
        value(idx[i], vf[i]);
    }
  }

  /// strided copy
  template <typename Container>
  void fetch(size_t stride, Container & c) const {
    assert(stride >= ndim);
    assert(c.size() >= stride*nelements());
    const int n = nelements();
    if (realField()) {
      for (int i=0; i<n; ++i)
        for (size_t k=0; k<ndim; ++k)
          c[i*stride+k] = rval[i*ndim+k];
    } else {
      for (int i=0; i<n; ++i)
        for (size_t k=0; k<ndim; ++k)
          c[i*stride+k] = ival[i*ndim+k];
    }
  }

  /// scale real values
  void scale(Real f);

  /// construct field from raw data
  template<class FloatType>
  void copyReal(const std::string & s, size_t nd, const FloatType a[]) {
    ndim = nd;
    rename(s);
    rval.allocate(ndim*nalloc());
    std::copy(a, a+nd*nalloc(), rval.begin());
  }

  /// construct field from raw data
  template<class IntType>
  void copyInt(const std::string & s, size_t nd, const IntType a[]) {
    ndim = nd;
    rename(s);
    ival.allocate(ndim*nalloc());
    std::copy(a, a+nd*nalloc(), ival.begin());
  }

  /// set scalar field
  void scalarField(const std::string & s, const DVector<double> & v);

  /// set scalar field
  void scalarField(const std::string & s, const DVector<float> & v);

  /// set scalar field
  void scalarField(const std::string & s, const DVector<int> & vi);

  /// set 3-component vector field (displacements, velocities...)
  void vectorField(const std::string & s, const PointList<3> & v);

  /// set 3-component vector field (displacements, velocities...)
  void vectorField(const std::string & s, const PointList<3,float> & v);

  /// set 6-component vector field
  void vectorField(const std::string & s, const PointList<6> & v);

  /// set 6-component vector field
  void vectorField(const std::string & s, const PointList<6,float> & v);

  /// pad field with t to match changed node/element count
  void fitField(Real t = 0.0);

  /// create a condensed field for visualization
  void condensed(int vfm, DVector<float> & vf) const;

  /// field statistics for real-valued scalar fields
  void stats(Real & minval, Real & maxval, Real & meanval) const;

  /// field statistics for real-valued vector fields
  void stats(int condensation, Real & minval, Real & maxval, Real & meanval) const;

  /// update a extremal value array from *this field
  template <class BinaryOp>
  void updateExtremes(Vector &xvalues, BinaryOp op) const {
    const size_t n = std::min( rval.size(), xvalues.size() );
    for (size_t i=0; i<n; ++i)
      xvalues[i] = op(xvalues[i], rval[i]);
  }

  /// erase range of values
  void erase(size_t begin, size_t end);

  /// extend with copies of values belonging to nodes/elements in idx
  void extend(const Indices &idx);

  /// extend with mirror copies of values belonging to nodes/elements in idx
  void extend(const Indices &idx, const Plane &pln);

  /// insert values (changes field size!)
  template <typename Iterator>
  void insert(size_t pos, Iterator begin, Iterator end) {
    if (realField())
      rval.insert( rval.begin()+pos, begin, end );
    else
      ival.insert( ival.begin()+pos, begin, end );
  }

  /// reorder nodal field
  void reorder(const Indices & perm);

  /// access name of component k
  std::string componentName(uint k) const;

  /// set all component names
  void componentNames(const std::initializer_list<const char *> &namelist);

  /// read from FFA node returns status
  bool fromFFA(const FFANode & node);

  /// read displacement field from .bdis file
  bool readBdis(const std::string &fname);

  /// write field as bdis; will only create correct output if annotations present
  bool writeBdis(const std::string &fname) const;

  /// read field i from CGNS solution
  bool readCgns(CgnsSol & sol, int i);

  /// write to cgns solution entry
  void writeCgns(CgnsSol & sol) const;

  /// write to VTK xml format
  XmlElement toVTK(const Indices & ipts) const;

  /// create a binary file node
  BinFileNodePtr gbfNode(bool share = true) const;

  /// retrieve data from gbf file node
  void fromGbf(const BinFileNodePtr & np, bool digestNode=false);

  /// convert to xml representation
  XmlElement toXml(bool share) const;

  /// retrieve section from xml representation
  void fromXml(const XmlElement & xe);

#ifdef HAVE_HDF5

  /// append to group in HDF5 file
  void writeHdf5(Hdf5Group &grp, size_t idx);

#endif

  /// memory requirements (w/o notes)
  float megabytes() const {
    float bts = sizeof(MxMeshField);
    bts += rval.capacity()*sizeof(Vector::value_type);
    bts += ival.capacity()*sizeof(int);
    return 1e-6f*bts;
  }

  /// swap contents
  void swap(MxMeshField & a) {
    std::swap(parent, a.parent);
    fid.swap(a.fid);
    rval.swap(a.rval);
    ival.swap(a.ival);
    std::swap(xnote, a.xnote);
    std::swap(ndim, a.ndim);
    std::swap(vclass, a.vclass);
    std::swap(solindex, a.solindex);
    std::swap(bNodal, a.bNodal);
  }

  /// globally change the precision stored in files that support conversion
  static void fileFloatPrecision(TypeCode tc) {
    s_fileFloatPrecision = tc;
  }

private:

  /// allocated size
  size_t nalloc() const;

private:

  /// parent mesh
  const MxMesh *parent;

  /// name of the field stored
  std::string fid;

  /// floating-point field values
  Vector rval;

  /// integer field values
  DVector<int> ival;

  /// (optional) names for the components of a multi-dimensional field
  StringArray compNames;

  /// components per point
  size_t ndim;

  /// value class, default is field
  ValueClass vclass;

  /// assign a solution index
  size_t solindex;

  /// nodal or cell data?
  bool bNodal;

  /// global setting - store real data in single precision?
  static TypeCode s_fileFloatPrecision;

  friend class MxMesh;
};

#endif

