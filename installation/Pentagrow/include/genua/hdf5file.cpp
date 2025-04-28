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

#include "hdf5file.h"
#include <hdf5_hl.h>
#include <fstream>

using namespace std;

// table which maps TypeCode to HDF5 data types

const static hid_t s_typeMap[15] = {
  -1,
  H5T_NATIVE_INT8,
  H5T_NATIVE_UINT8,
  H5T_NATIVE_INT16,
  H5T_NATIVE_UINT16,
  H5T_NATIVE_INT32,
  H5T_NATIVE_UINT32,
  H5T_NATIVE_INT64,
  H5T_NATIVE_UINT64,
  -1,
  H5T_NATIVE_FLOAT,
  H5T_NATIVE_DOUBLE,
  -1,
  -1,
  H5T_C_S1
};

// ---------------------- Location --------------------------------------------

std::atomic<size_t> Hdf5Location::s_idcounter(0);

bool Hdf5Location::attach(const string &obj, const string &key, const string &val)
{
  herr_t stat = H5LTset_attribute_string(m_id, obj.c_str(),
                                         key.c_str(), val.c_str());
  return (stat >= 0);
}

bool Hdf5Location::attach(const string &obj, const string &key, const int &val)
{
  herr_t stat = H5LTset_attribute_int(m_id, obj.c_str(), key.c_str(), &val, 1);
  return (stat >= 0);
}

string Hdf5Location::attribute(const string &obj, const string &key)
{
  size_t typesize(0);
  hsize_t dims[32];
  std::fill(std::begin(dims), std::end(dims), 0);
  H5T_class_t cls;
  herr_t stat = H5LTget_attribute_info(m_id, obj.c_str(), key.c_str(),
                                       dims, &cls, &typesize);
  if (stat < 0 or dims[0] < 1)
    return string();

  std::string val;
  val.resize(dims[0]);
  stat = H5LTget_attribute_string(m_id, obj.c_str(), key.c_str(),
                                  (char *) &val[0]);
  return (stat < 0) ? string() : val;
}

size_t Hdf5Location::uniqueId()
{
  s_idcounter++;
  return s_idcounter;
}

string Hdf5Location::uniqueName()
{
  size_t id = uniqueId();
  return "id" + std::to_string(id);
}

void Hdf5Location::printErrorStack()
{
  hid_t estack = H5Eget_current_stack();
  H5Eprint2(estack, NULL);
}

bool Hdf5Location::getAttribute(const string &obj, const string &key,
                                TypeCode memDataType, void *buffer)
{
  if (buffer == nullptr)
    return false;

  hid_t dtype = s_typeMap[ memDataType.value() ];
  if (dtype < 0)
    return false;

  herr_t stat = H5LTget_attribute(m_id, obj.c_str(), key.c_str(),
                                  dtype, buffer);
  return (stat >= 0);
}

// ---------------------- Dataset ---------------------------------------------

Hdf5Dataset::~Hdf5Dataset()
{
  close();
}

void Hdf5Dataset::close()
{
  if (valid())
    H5Dclose(m_id);
  m_id = -1;
}

int Hdf5Dataset::rank()
{
  if (valid()) {
    hid_t space_id = H5Dget_space(m_id);
    return H5Sget_simple_extent_ndims(space_id);
  }
  return 0;
}

int Hdf5Dataset::dimensions(hsize_t *dim, hsize_t *maxdims)
{
  if (valid()) {
    hid_t space = H5Dget_space(m_id);
    int r = H5Sget_simple_extent_dims(space, dim, maxdims);
    return r;
  } else {
    return -1;
  }
}

size_t Hdf5Dataset::size()
{
  hsize_t dim[32];
  std::fill(dim, dim+32, 1);
  int r = dimensions(dim);
  size_t n = 1;
  for (int k=0; k<r; ++k)
    n *= dim[k];
  return n;
}

bool Hdf5Dataset::write(TypeCode dataType, const void *buf)
{
  hid_t dtype = s_typeMap[ dataType.value() ];
  if (dtype == -1)
    return false;

  herr_t stat = H5Dwrite( m_id, dtype, H5S_ALL, H5S_ALL, H5P_DEFAULT, buf );
  return (stat >= 0);
}

bool Hdf5Dataset::writeSlab(TypeCode dataType,
                            const hsize_t offset[], const hsize_t count[],
                            const void *buf)
{
  hid_t dtype = s_typeMap[ dataType.value() ];
  if (dtype == -1)
    return false;

  herr_t stat;
  hid_t space = H5Dget_space(m_id);
  stat = H5Sselect_hyperslab(space, H5S_SELECT_SET,
                             offset, NULL, count, NULL);
  if (stat < 0)
    return false;

  stat = H5Dwrite(m_id, dtype, H5S_ALL, space, H5P_DEFAULT, buf);
  return (stat >= 0);
}

bool Hdf5Dataset::writeRow(TypeCode dataType, size_t irow, const void *buf)
{
  hsize_t dim[32];
  int r = dimensions(dim);
  if (r > 2)
    return false;
  hsize_t offset[2] = {irow, 0};
  hsize_t count[2] = {1, dim[1]};
  return writeSlab(dataType, offset, count, buf);
}

bool Hdf5Dataset::writeColumn(TypeCode dataType, size_t jcol, const void *buf)
{
  hsize_t dim[32];
  int r = dimensions(dim);
  if (r > 2)
    return false;
  hsize_t offset[2] = {0, jcol};
  hsize_t count[2] = {dim[0], 1};
  return writeSlab(dataType, offset, count, buf);
}

bool Hdf5Dataset::read(TypeCode dataType, void *buf)
{
  hid_t dtype = s_typeMap[ dataType.value() ];
  if (dtype == -1)
    return false;

  herr_t stat = H5Dread( m_id, dtype, H5S_ALL, H5S_ALL, H5P_DEFAULT, buf );
  return (stat >= 0);
}

bool Hdf5Dataset::readSlab(TypeCode dataType,
                           const hsize_t offset[], const hsize_t count[],
                           void *buf)
{
  hid_t dtype = s_typeMap[ dataType.value() ];
  if (dtype == -1)
    return false;

  herr_t stat;
  hid_t space = H5Dget_space(m_id);
  stat = H5Sselect_hyperslab(space, H5S_SELECT_SET,
                             offset, NULL, count, NULL);
  if (stat < 0)
    return false;

  // assumes that the memory pointed to by buf has the same layout
  // as the slab defined by count
  hid_t memspace = H5Screate_simple(2, count, NULL);

  stat = H5Dread(m_id, dtype, memspace, space, H5P_DEFAULT, buf);
  return (stat >= 0);
}

bool Hdf5Dataset::readRow(TypeCode dataType, size_t irow, void *buf)
{
  hsize_t dim[32];
  int r = dimensions(dim);
  if (r > 2)
    return false;
  hsize_t offset[2] = {irow, 0};
  hsize_t count[2] = {1, dim[1]};
  return readSlab(dataType, offset, count, buf);
}

bool Hdf5Dataset::readColumn(TypeCode dataType, size_t jcol, void *buf)
{
  hsize_t dim[32];
  int r = dimensions(dim);
  if (r > 2)
    return false;
  hsize_t offset[2] = {0, jcol};
  hsize_t count[2] = {dim[0], 1};
  return readSlab(dataType, offset, count, buf);
}

bool Hdf5Dataset::extend(const hsize_t *dim)
{
  if (m_id == -1)
    return false;
  herr_t stat = H5Dextend(m_id, dim);
  return (stat >= 0);
}

bool Hdf5Dataset::extend(size_t nrows, size_t ncols)
{
#ifndef NDEBUG
  int r = rank();
  assert((r == 1 and ncols == 1) or (r == 2));
#endif
  hsize_t dims[32];
  std::fill(dims, dims+32, 1);
  dims[0] = nrows;
  dims[1] = ncols;
  return extend(dims);
}

// ------------------------------ Group ---------------------------------------

Hdf5Group::~Hdf5Group()
{
  close();
}

void Hdf5Group::close()
{
  if (valid())
    H5Gclose(m_id);
}

Hdf5Dataset Hdf5Group::createDataset(hid_t locid, const std::string &name,
                                     TypeCode dataType,
                                     int rank,
                                     const hsize_t *dimensions,
                                     const hsize_t *maxDimensions,
                                     int gzip)
{
  hid_t dtype = s_typeMap[ dataType.value() ];
  if (dtype == -1)
    return Hdf5Dataset(-1);

  hid_t spaceid = H5Screate_simple(rank, dimensions, maxDimensions);
  hid_t dcpl = H5P_DEFAULT;

  // use only GZIP and SHUF filters which are always available.
  if ((gzip > 0) or (maxDimensions != NULL)) {
    dcpl = H5Pcreate( H5P_DATASET_CREATE );

    hsize_t cdims[32];
    std::fill(cdims, cdims+32, 1);
    cdims[0] = dimensions[0];
    H5Pset_chunk(dcpl, rank, cdims);

    if (gzip > 0) {
      H5Pset_shuffle(dcpl);
      H5Pset_deflate(dcpl, gzip);
    }
  }

  hid_t id = H5Dcreate2(locid, name.c_str(), dtype, spaceid,
                        H5P_DEFAULT, dcpl, H5P_DEFAULT);
  return Hdf5Dataset(id);
}

Hdf5Dataset Hdf5Group::createDataset(hid_t locid, const std::string &name,
                                     TypeCode dataType,
                                     int rank,
                                     const hsize_t *dimensions,
                                     int gzip)
{
  return Hdf5Group::createDataset(locid, name, dataType, rank,
                                  dimensions, NULL, gzip);
}

Hdf5Dataset Hdf5Group::createDataset(const string &name, TypeCode dataType,
                                     int rank, const hsize_t *dimensions, int gzip)
{
  return this->createDataset(m_id, name, dataType, rank, dimensions, gzip);
}

Hdf5Dataset Hdf5Group::createDataset(const std::string &name, TypeCode dataType,
                                     size_t nrows, size_t ncols, int gzip)
{
  hsize_t dim[2] = {nrows, ncols};
  int rank = (ncols > 1) ? 2 : 1;
  return this->createDataset(name, dataType, rank, dim, gzip);
}

Hdf5Dataset Hdf5Group::createExtensibleDataset(const string &name,
                                               TypeCode dataType,
                                               size_t nrows, size_t ncols, int gzip)
{
  hsize_t dim[2] = {nrows, ncols};
  hsize_t maxdim[2] = {H5S_UNLIMITED, H5S_UNLIMITED};

  // always created with rank 2 because later extension could increase column
  // count beyond 1
  return this->createDataset(m_id, name, dataType, 2, dim, maxdim, gzip);
}

Hdf5Dataset Hdf5Group::openDataset(const string &name)
{
  hid_t id = H5Dopen2( m_id, name.c_str(), H5P_DATASET_ACCESS_DEFAULT );
  return Hdf5Dataset(id);
}

Hdf5Group Hdf5Group::openGroup(const string &name)
{
  hid_t id = H5Gopen2(m_id, name.c_str(), H5P_DEFAULT);
  return Hdf5Group(id);
}

Hdf5Group Hdf5Group::createGroup(const string &name)
{
  hid_t id = H5Gcreate2(m_id, name.c_str(),
                        H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
  return Hdf5Group(id);
}

static herr_t collect_groups(hid_t root, const char *childName,
                             const H5L_info_t *, void *ptr)
{
  Hdf5GroupArray *parray = (Hdf5GroupArray *) ptr;
  hid_t id = H5Gopen2(root, childName, H5P_DEFAULT);
  if ((parray != nullptr) and (id >= 0))
    parray->emplace_back( id );
  return 0;
}

Hdf5GroupArray Hdf5Group::childGroups()
{
  Hdf5GroupArray children;
  hsize_t idx = 0;
  H5Literate(m_id, H5_INDEX_NAME, H5_ITER_NATIVE, &idx,
             collect_groups, &children);
  return children;
}

// ------------------------------ File ---------------------------------------

Hdf5File::~Hdf5File()
{
  this->close();
}

bool Hdf5File::isHdf5(const string &fname)
{
  return (H5Fis_hdf5(fname.c_str()) > 0);
}

bool Hdf5File::open(const std::string &fname, bool readOnly)
{
  m_id = H5Fopen(fname.c_str(),
                 readOnly ? H5F_ACC_RDONLY : H5F_ACC_RDWR, H5P_DEFAULT);

  return valid();
}

bool Hdf5File::create(const string &fname)
{
  m_id = H5Fcreate(fname.c_str(), H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
  return valid();
}

void Hdf5File::close()
{
  if (valid())
    H5Fclose(m_id);
  m_id = -1;
}







