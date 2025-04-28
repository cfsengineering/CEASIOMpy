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

#include "xmlelement.h"
#include "hdf5file.h"

// this cpp file is only compiled if hdf5 support is configured

void XmlElement::toHdf5(Hdf5Group &parent) const
{
  Hdf5Group self = parent.createGroup( Hdf5Location::uniqueName() );

  // attributes
  self.attach("__xml_tag", name());
  for (const auto &itr : m_attributes)
    self.attach(itr.first, itr.second);

  // dataset, if any
  if (m_nbytes > 0) {
    TypeCode tc(m_typecode);
    Hdf5Dataset dset = self.createDataset("BinaryData",
                                          tc, m_nbytes/tc.width());
    if (not dset.valid())
      throw Error("HDF5: Cannot create binary dataset in XmlElement::toHdf5()");
    dset.write(tc, blobPointer());
    dset.close();
  }

  if (not m_txt.empty()) {
    TypeCode strType( TypeCode::Str8 );
    Hdf5Dataset dset = self.createDataset("StringData",
                                          strType, m_txt.length());
    if (not dset.valid())
      throw Error("HDF5: Cannot create string dataset in XmlElement::toHdf5()");
    dset.write(strType, m_txt.data());
    dset.close();
  }

  for (const XmlElement &child : m_siblings)
    child.toHdf5(self);
  self.close();
}
