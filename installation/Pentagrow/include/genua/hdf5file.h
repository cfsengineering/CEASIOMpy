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

#ifndef GENUA_HDF5FILE_H
#define GENUA_HDF5FILE_H

#include "forward.h"
#include "typecode.h"
#include <hdf5.h>
#include <atomic>

/** Location in a HDF5 file.
 *
 * Hdf5Location wraps an object identifier which keeps track of objects inside
 * a Hdf5File (a hid_t). Furthermore, it provides access to object attributes
 * through the HDF5 high-level library.
 *
 * \ingroup mesh
 * \sa Hdf5File, MxMesh
 */
class Hdf5Location
{
public:

  /// create a location from id
  Hdf5Location(hid_t id = -1) : m_id(id) {}

  /// move construction, won't call destructor
  Hdf5Location(Hdf5Location &&a) : m_id(a.m_id) { a.m_id = -1; }

  /// move assignment
  Hdf5Location &operator= (Hdf5Location &&a) {
    m_id = a.m_id;
    a.m_id = -1;
    return *this;
  }

  /// access location id
  hid_t id() const {return m_id;}

  /// whether this location has been assigned
  bool valid() {return m_id >= 0;}

  /// attach a string attribute to object
  bool attach(const std::string &obj,
              const std::string &key, const std::string &val);

  /// attach a string attribute to this object itself
  bool attach(const std::string &key, const std::string &val) {
    return this->attach(".", key, val);
  }

  /// attach a integer attribute to object
  bool attach(const std::string &obj, const std::string &key, const int &val);

  /// attach a integer attribute to this object
  bool attach(const std::string &key, const int &val) {
    return this->attach(".", key, val);
  }

  /// return string attribute obj.key, or empty if not found
  std::string attribute(const std::string &obj, const std::string &key);

  /// retrieve attribute 'key'; returns false if not present
  template <typename ValueType>
  bool attribute(const std::string &obj, const std::string &key,
                 ValueType &val)
  {
    TypeCode memDataType = TypeCode::of<ValueType>();
    return this->getAttribute(obj, key, memDataType, (void *) &val);
  }

  /// return a simple unique object name
  static std::string uniqueName();

  /// return a simple unique object id
  static size_t uniqueId();

  /// print current error stack to stderr
  static void printErrorStack();

protected:

  /// low-level interface for attribute query
  bool getAttribute(const std::string &obj, const std::string &key,
                    TypeCode memDataType, void *buffer);

protected:

  /// identifier
  hid_t m_id = -1;

  /// used to generate identifiers
  static std::atomic<size_t> s_idcounter;
};

/** Dataset in HDF5 file.
 *
 * A thin wrapper around the HDF5 library calls for handling N-D arrays stored
 * in HDF5 files, Hdf5Dataset is meant to simplify the use of the library for
 * storing and loading large amount of multidimensional data.
 *
 * \note Important: HDF5 stores data in row-major order, i.e. the last
 *       dimensions changes fastest.
 *
 * \ingroup mesh
 * \sa Hdf5Location, Hdf5File, MxMeshField
 */
class Hdf5Dataset : public Hdf5Location
{
public:

  /// create dataset from id, or invalid stub
  Hdf5Dataset(hid_t id=-1) : Hdf5Location(id) {}

  /// move construction, won't call destructor
  Hdf5Dataset(Hdf5Dataset &&a) { m_id = a.m_id; a.m_id = -1; }

  /// move assignment
  Hdf5Dataset &operator= (Hdf5Dataset &&a) {
    m_id = a.m_id;
    a.m_id = -1;
    return *this;
  }

  /// closes dataset
  ~Hdf5Dataset();

  /// explicitly close dataset
  void close();

  /// query rank (number of dimensions)
  int rank();

  /// query dimensions of the dataset, assuming simple extents, return rank
  int dimensions(hsize_t *dim, hsize_t *maxdims = nullptr);

  /// number of elements in dataset
  size_t size();

  /// write complete dataset in one pass
  bool write(TypeCode dataType, const void *buf);

  /// write contents of array assumed to be in correct shape
  template <typename ScalarType>
  bool write(const ScalarType *p) {
    return this->write( TypeCode::of<ScalarType>(), (const void *) p );
  }

  /// write slice of the dataset
  bool writeSlab(TypeCode dataType,
                 const hsize_t offset[], const hsize_t count[],
                 const void *buf);

  /// special case: write a single row into a rank-2 dataset
  bool writeRow(TypeCode dataType, size_t irow, const void *buf);

  /// special case: write a single row into a rank-2 dataset
  template <typename ScalarType>
  bool writeRow(size_t irow, const ScalarType *p) {
    return this->writeRow( TypeCode::of<ScalarType>(), irow, (void *) p );
  }

  /// special case: write a single column into a rank-2 dataset
  bool writeColumn(TypeCode dataType, size_t jcol, const void *buf);

  /// special case: read a single row of a rank-2 dataset
  template <typename ScalarType>
  bool writeColumn(size_t jcol, const ScalarType *p) {
    return this->writeColumn( TypeCode::of<ScalarType>(), jcol, (void *) p );
  }

  /// write contents of array assumed to be in correct shape
  template <typename ScalarType>
  bool writeSlab(const hsize_t offset[], const hsize_t count[],
                 const ScalarType *p)
  {
    return this->writeSlab( TypeCode::of<ScalarType>(),
                            offset, count, (const void *) p );
  }

  /// read the entire dataset in one pass
  bool read(TypeCode dataType, void *buf);

  /// read contents into array assumed to be in correct shape
  template <typename ScalarType>
  bool read(ScalarType *p) {
    return this->read( TypeCode::of<ScalarType>(), (void *) p );
  }

  /// read a slice of the dataset into buf
  bool readSlab(TypeCode dataType,
                const hsize_t offset[], const hsize_t count[], void *buf);

  /// read contents into array assumed to be in correct shape
  template <typename ScalarType>
  bool readSlab(const hsize_t offset[], const hsize_t count[], ScalarType *p)
  {
    return this->readSlab( TypeCode::of<ScalarType>(),
                           offset, count, (void *) p );
  }

  /// special case: read a single row of a rank-2 dataset
  bool readRow(TypeCode dataType, size_t irow, void *buf);

  /// special case: read a single row of a rank-2 dataset
  template <typename ScalarType>
  bool readRow(size_t irow, ScalarType *p) {
    return this->readRow( TypeCode::of<ScalarType>(), irow, (void *) p );
  }

  /// special case: read a single column of a rank-2 dataset
  bool readColumn(TypeCode dataType, size_t jcol, void *buf);

  /// special case: read a single row of a rank-2 dataset
  template <typename ScalarType>
  bool readColumn(size_t jcol, ScalarType *p) {
    return this->readColumn( TypeCode::of<ScalarType>(), jcol, (void *) p );
  }

  /// extend size, will fail unless dataset was created as extensible
  bool extend(const hsize_t *dim);

  /// extend size for dataset with rank 1 or 2
  bool extend(size_t nrows, size_t ncols = 1);
};

/** Group in HDF5 file.
 *
 * Since the HDF5 file format is hierarchical, it can store objects in a
 * tree-like structure. A Hdf5Group is a node in that tree (and a file itself
 * is a node as well). Nodes in a tree are referenced using the name which is
 * passed on construction (to createGroup()), which means that no node can
 * have more than one child of the same name. In order to map other hierarchical
 * data that may not have the same restriction, use Hdf5Location::uniqueName()
 * to generate node names and store the real name in a property.
 *
 * \ingroup mesh
 * \sa Hdf5File
 */
class Hdf5Group : public Hdf5Location
{
public:

  /// create group from id or an invalid stub
  Hdf5Group(hid_t id = -1) : Hdf5Location(id) {}

  /// move construction, won't call destructor
  Hdf5Group(Hdf5Group &&a) { m_id = a.m_id; a.m_id = -1; }

  /// move assignment
  Hdf5Group &operator= (Hdf5Group &&a) {
    m_id = a.m_id;
    a.m_id = -1;
    return *this;
  }

  /// closes group
  virtual ~Hdf5Group();

  /// close this group
  virtual void close();

  /// create a new ND dataset attached to location id (may be group or file)
  static Hdf5Dataset createDataset(hid_t locid, const std::string &name,
                                   TypeCode dataType,
                                   int rank,
                                   const hsize_t *dimensions,
                                   const hsize_t *maxDimensions,
                                   int gzip = 0);

  /// create a new ND dataset attached to location id (may be group or file)
  static Hdf5Dataset createDataset(hid_t locid, const std::string &name,
                                   TypeCode dataType,
                                   int rank, const hsize_t *dimensions,
                                   int gzip = 0);

  /// create a dataset attached to this group
  Hdf5Dataset createDataset(const std::string &name, TypeCode dataType,
                            int rank, const hsize_t *dimensions, int gzip = 0);

  /// create a new 1D or 2D dataset attached to this group
  Hdf5Dataset createDataset(const std::string &name, TypeCode dataType,
                            size_t nrows, size_t ncols = 1, int gzip = 0);

  /// create a new extensible 1D or 2D dataset attached to this group
  Hdf5Dataset createExtensibleDataset(const std::string &name,
                                      TypeCode dataType,
                                      size_t nrows, size_t ncols = 1, int gzip = 0);

  /// write dataset directly in one pass, then close it
  template <typename ScalarType>
  bool writeDataset(const std::string &name, const ScalarType *p,
                    size_t nrows, size_t ncols = 1)
  {
    bool stat = false;
    Hdf5Dataset dset = this->createDataset( name, TypeCode::of<ScalarType>(),
                                            nrows, ncols );
    if (dset.valid())
      stat = dset.write(p);
    else
      return false;

    dset.close();
    return stat;
  }

  /// open an already existing dataset
  Hdf5Dataset openDataset(const std::string &name);

  /// open an existing group
  Hdf5Group openGroup(const std::string &name);

  /// create a group
  Hdf5Group createGroup(const std::string &name);

  /// return child groups, if any
  Hdf5GroupArray childGroups();

};

/** Interface to HDF5 files.
 *
 * Most of the functionality needed is in the base class Hdf5Group; Hdf5File
 * only gathers purely file-related interfaces. Normally, a Hdf5File would
 * created or opened and then treated as an instance of Hdf5Group.
 *
 * \ingroup mesh
 * \sa Hdf5Group, MxMesh
 */
class Hdf5File : public Hdf5Group
{
public:

  /// create invalid stub
  Hdf5File() : Hdf5Group() {}

  /// close and release
  ~Hdf5File();

  /// tests whether a file is HDF5
  static bool isHdf5(const std::string &fname);

  /// open existing file
  bool open(const std::string &fname, bool readOnly = true);

  /// create a new file, erase if it already exists
  bool create(const std::string &fname);

  /// close file (if open)
  void close();
};

#endif // HDF5FILE_H
