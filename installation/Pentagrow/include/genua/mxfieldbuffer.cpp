
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
 
#include "mxfieldbuffer.h"
#include "strutils.h"
#include "quantbuffer.h"
#include "binfilenode.h"
#include <sstream>

using namespace std;

XmlElement MxFieldBuffer::toXml(bool share) const
{
  XmlElement xe("MxFieldBuffer");
  xe["dimension"] = str(m_lda);
  xe["count"] = str(m_blob.size());
  if (isSparse()) {
    xe["sparse"] = "true";
    XmlElement xi("SparseIndex");
    xi["count"] = str(m_idx.size());
    xi.asBinary(m_idx.size(), &m_idx[0], share);
    xe.append(std::move(xi));
  }

  if ( quantized() ) {
    xe["quantized_type_code"] = m_quantType.toString();
    {
      stringstream ss;
      ss.precision(15);
      ss << m_qoffset;
      xe["quant_offset"] = ss.str();
    }
    {
      stringstream ss;
      ss.precision(15);
      ss << m_qscale;
      xe["quant_scale"] = ss.str();
    }
  }

  XmlElement xb("Blob");
  m_blob.toXmlBlock( xb, share );
  xe.append(std::move(xb));

  return xe;
}

bool MxFieldBuffer::fromXml(const XmlElement &xe)
{
  bool ok = false;
  m_idx = IndexArray();
  m_lda = xe.attr2int("dimension",1);
  XmlElement::const_iterator itr, ilast = xe.end();
  for (itr = xe.begin(); itr != ilast; ++itr) {
    const string & s = itr->name();
    if (s == "SparseIndex") {
      size_t nsi = 0;
      fromString(itr->attribute("count"), nsi);
      m_idx.resize(nsi);
      itr->fetch(nsi, &m_idx[0]);
    } else if (s == "Blob") {
      ok = m_blob.fromXmlBlock(*itr);
    }
  }

  m_quantized = false;
  m_quantType = TypeCode(TypeCode::None);
  XmlElement::attr_iterator ita;
  for (ita = xe.attrBegin(); ita != xe.attrEnd(); ++ita) {
    if (ita->first == "quantized_type_code")
      m_quantType = TypeCode::fromString(ita->second);
    else if (ita->first == "quant_offset")
      m_qoffset = genua_strtod(ita->second.c_str(), 0);
    else if (ita->first == "quant_scale")
      m_qscale = genua_strtod(ita->second.c_str(), 0);
  }

  if ( m_quantType.isReal() ) {
    m_quantized = true;
  } else {
    m_quantType = TypeCode(TypeCode::None);
  }

  return ok;
}

