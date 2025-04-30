
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
 
#include "blob.h"
#include "xmlelement.h"
#include "strutils.h"

bool Blob::toXmlBlock(XmlElement &xe, bool share) const
{
  xe["blob_nval"] = str(m_nval);
  xe["blob_type"] = typeString();
  return m_code.toXmlBlock(xe, m_nval, pointer(), share);
}

bool Blob::fromXmlBlock(const XmlElement &xe)
{
  fromString( xe.attribute("blob_nval"), m_nval );
  m_code = TypeCode::fromString( xe.attribute("blob_type") );
  allocate(m_code, m_nval);
  return m_code.fromXmlBlock(xe, m_nval, m_block.get());
}
