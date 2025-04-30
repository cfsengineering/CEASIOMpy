
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
 
#ifndef GENUA_MXSTREAMER_H
#define GENUA_MXSTREAMER_H

#include "lz4stream.h"
#include "mxmesh.h"
#include "point.h"
#include <fstream>

/** Interface for streaming result fields to file immediately.
 *
 *  MxStreamer allows to open a LZ4-compressed file stream and successively
 *  append data fields. This allows to reduce the amount of data which needs
 *  to be kept in memory at any one time, since the written field can be either
 *  recycled with different content or destroyed.
 *
 * \ingroup mesh
 *  \sa MxMesh, Lz4Stream
 */
class MxStreamer
{
public:

  /// undefined streamer
  MxStreamer() : m_pmx(0) {}

  /// open a stream for given mesh, write mesh geometry
  void open(const std::string &fname, const MxMesh *pmx);

  /// append any XML node
  void append(const XmlElement &xe);

  /// write a mesh field to file (may be destroyed after this call)
  size_t append(const MxMeshField &field);

  /// construct a temporary mesh field, write to file
  template <typename ElementType>
  size_t append(const std::string &fieldName, const DVector<ElementType> &c) {
    MxMeshField field(m_pmx, c.size() == m_pmx->nnodes(), 1);
    field.scalarField(fieldName, c);
    return this->append(field);
  }

  /// construct a temporary mesh field, write to file
  template <typename ElementType, uint N>
  size_t append(const std::string &fieldName,
                const PointList<N,ElementType> &c) {
    MxMeshField field(m_pmx, c.size() == m_pmx->nnodes(), N);
    field.vectorField(fieldName, c);
    return this->append(field);
  }

  /// finally, append a solution tree (call this only once!)
  void append(const MxSolutionTree &tree);

  /// close stream
  void close();

private:

  /// pointer to parent mesh
  const MxMesh *m_pmx;

  /// file stream to use
  std::ofstream m_file;

  /// compressed stream
  Lz4Stream m_stream;

  /// field index counter
  size_t m_ifield;
};

#endif // MXSTREAMER_H
