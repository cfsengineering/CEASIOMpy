
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
 
#include "mxstreamer.h"
#include "mxsolutiontree.h"
#include "xmlelement.h"
#include "binfilenode.h"
#include "xcept.h"
#include <ios>

void MxStreamer::open(const std::string &fname, const MxMesh *pmx)
{
  assert(pmx != 0);
  m_pmx = pmx;
  MxSolutionTreePtr soltree = pmx->solutionTree();
  if (soltree)
    throw Error("Cannot stream field which already contains solution tree.");

  m_file.open( fname.c_str(), std::ios::out | std::ios::binary );
  if (not m_file)
    throw Error("MxStreamer cannot open file: "+fname);
  m_stream.openWrite(m_file);

  XmlElement xe( pmx->toXml(true) );
  BinFileNodePtr bfp = xe.toGbf(true);
  bfp->writeNodeLZ4(m_file, m_stream, false);  // write, but do not terminate
  m_ifield = pmx->nfields();
}

void MxStreamer::append(const XmlElement &xe)
{
  BinFileNodePtr bfp = xe.toGbf(true);
  bfp->writeNodeLZ4(m_file, m_stream);
}

size_t MxStreamer::append(const MxMeshField &field)
{
  this->append( field.toXml(true) );
  ++m_ifield;
  return m_ifield-1;
}

void MxStreamer::append(const MxSolutionTree &tree)
{
  this->append(tree.toXml(true));
}

void MxStreamer::close()
{
  m_stream.closeWrite(m_file);
  m_file.close();
}
