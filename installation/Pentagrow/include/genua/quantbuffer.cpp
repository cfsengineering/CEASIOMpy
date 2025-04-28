
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
 
#include "quantbuffer.h"
#include <sstream>

using namespace std;

XmlElement QuantBuffer::toXml(bool share) const
{
  XmlElement xe("QuantBuffer");
  xe["code_type"] = "UInt16";
  xe["count"] = str(m_qv.size());

  {
    stringstream ss;
    ss.precision(16);
    ss << m_offset;
    xe["offset"] = ss.str();
  }

  {
    stringstream ss;
    ss.precision(16);
    ss << m_scale;
    xe["scale"] = ss.str();
  }

  xe.asBinary(m_qv.size(), m_qv.pointer(), share);
  return xe;
}

void QuantBuffer::fromXml(const XmlElement &xe)
{
  m_offset = Float( xe.attribute("offset") );
  m_scale = Float( xe.attribute("scale") );
  m_qv.allocate( Int(xe.attribute("count")) );
  xe.fetch(m_qv.size(), m_qv.pointer());
}
