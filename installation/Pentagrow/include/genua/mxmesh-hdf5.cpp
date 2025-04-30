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

#include "mxmesh.h"
#include "mxmeshsection.h"
#include "mxmeshboco.h"
#include "mxmeshfield.h"
#include "mxsolutiontree.h"
#include "hdf5file.h"
#include "xcept.h"

void MxMesh::writeHdf5(const std::string &fname)
{
  Hdf5File h5f;
  bool stat = h5f.create(fname);
  if (not stat)
    throw Error("HDF5: Could not create new file: "+fname);

  this->writeHdf5(h5f);
  h5f.close();
}

void MxMesh::writeHdf5(Hdf5Group &parent)
{
  parent.attach("scheme", "MxMesh1");

  Hdf5Group gmesh = parent.createGroup("/mesh");
  if (not gmesh.valid())
    throw Error("HDF5: Could not create group /mesh");

  Hdf5Dataset dset = gmesh.createDataset("/mesh/vertices",
                                         s_fileFloatPrecision, vtx.size(), 3);
  if (not dset.valid())
    throw Error("HDF5: Could not create dataset /mesh/vertices");
  bool stat = dset.write(vtx.pointer());
  if (not stat)
    throw Error("HDF5: Could not write dataset /mesh/vertices");
  dset.close();

  Hdf5Group gsections = gmesh.createGroup("/mesh/sections");
  if (not gsections.valid())
    throw Error("HDF5: Could not create group /mesh/sections");

  for (const MxMeshSection &sec : sections)
    sec.writeHdf5(gsections);
  gsections.close();

  Hdf5Group gbocos = gmesh.createGroup("/mesh/bocos");
  if (not gbocos.valid())
    throw Error("HDF5: Could not create group /mesh/bocos");
  for (const MxMeshBoco &bc : bocos)
    bc.writeHdf5(gbocos);

  gbocos.close();
  gmesh.close();

  Hdf5Group gfields = parent.createGroup("/fields");
  const size_t nf = nfields();
  for (size_t i=0; i<nf; ++i)
    field(i).writeHdf5(gfields, i);

  if (soltree != nullptr)
    soltree->writeHdf5(gfields);
  gfields.close();
}

void MxMesh::readHdf5(Hdf5Group &parent)
{
  // scheme : MxMesh1

  Hdf5Group gmesh = parent.openGroup("/mesh");
  if (not gmesh.valid())
    throw Error("HDF5: Could not open group /mesh");

  Hdf5Dataset dset = gmesh.openDataset("/mesh/vertices");
  if (not dset.valid())
    throw Error("HDF5: Could not open dataset /mesh/vertices");

  hsize_t dims[32];
  std::fill(dims, dims+32, 0);
  int rank = dset.dimensions(dims);
  if ((rank != 2) or (dims[1] != 3))
    throw Error("MxMesh::readHdf5 - Expected 3D nodes.");

  vtx.resize(dims[0]);
  dset.read(vtx.pointer());

  Hdf5Group gsections = gmesh.openGroup("/mesh/sections");
  if (not gsections.valid())
    throw Error("HDF5: Could not open group /mesh/sections");
}

void MxMeshSection::writeHdf5(Hdf5Group &grp) const
{
  // mesh topology datasets profit very much from shuffling and compression
  // so these are always stored gzipped to save space.
  TypeCode tc = TypeCode::of<Indices::value_type>();
  Hdf5Dataset dset = grp.createDataset( Hdf5Location::uniqueName(),
                                        tc, inodes.size(), 1, 1 );
  if (not dset.valid())
    throw Error("HDF5: Unable to create dataset for section: "+name());
  bool stat = dset.write(&inodes[0]);
  if (not stat)
    throw Error("HDF5: Unable to write data for section: "+name());
  dset.attach("etype", str(etype));
  dset.attach("name", name());
  dset.attach("itag", itag);
  dset.attach("domainType", domainType);
  dset.attach("dispColor", dispColor.str());
  dset.close();
}

void MxMeshBoco::writeHdf5(Hdf5Group &grp) const
{
  TypeCode tc = TypeCode::of<Indices::value_type>();
  Hdf5Dataset dset = grp.createDataset( Hdf5Location::uniqueName(),
                                        tc, bcelm.size() );
  if (not dset.valid())
    throw Error("HDF5: Unable to create dataset for boco: "+name());
  bool stat = dset.write(&bcelm[0]);
  if (not stat)
    throw Error("HDF5: Unable to write data for boco: "+name());

  dset.attach("bRange", (int) bRange);
  dset.attach("name", name());
  dset.attach("itag", itag);
  dset.attach("bctype", bctype);
  dset.attach("dispColor", dispColor.str());
  dset.close();
}

void MxMeshField::writeHdf5(Hdf5Group &grp, size_t idx)
{
  TypeCode tc;
  Hdf5Dataset dset;
  bool stat;
  if (realField()) {
    dset = grp.createDataset( Hdf5Location::uniqueName(),
                              s_fileFloatPrecision, rval.size() );
    if (not dset.valid()) {
      Hdf5Location::printErrorStack();
      throw Error("HDF5: Unable to create dataset for field: "+name());
    }
    stat = dset.write(rval.pointer());
  } else {
    tc = TypeCode::of<int>();
    dset = grp.createDataset(Hdf5Location::uniqueName(),
                             tc, ival.size(), 1, 1 );
    if (not dset.valid())
      throw Error("HDF5: Unable to create dataset for field: "+name());
    stat = dset.write(ival.pointer());
  }
  if (not stat)
    throw Error("HDF5: Unable to write data for field: "+name());

  dset.attach("name", name());
  dset.attach("bnodal", (int) bNodal);
  dset.attach("solindex", (int) solindex);
  dset.attach("fieldidx", (int) idx);
  dset.close();
}

void MxSolutionTree::writeHdf5(Hdf5Group &parent)
{
  std::string uid = "node" + std::to_string(Hdf5Location::uniqueId());
  Hdf5Group gnode = parent.createGroup(uid);
  if (not gnode.valid())
    throw Error("HDF5: Cannot generate node for solution tree.");

  gnode.attach("name", name());
  if (not m_fields.empty())
    gnode.writeDataset("fields", &m_fields[0], m_fields.size());

  for (const MxSolutionTreePtr &child : m_siblings)
    child->writeHdf5(gnode);
  gnode.close();
}
