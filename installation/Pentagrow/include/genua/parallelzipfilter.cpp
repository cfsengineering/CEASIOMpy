
/* Copyright (C) 2017 David Eller <david@larosterna.com>
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

#include "defines.h"
#include "parallelzipfilter.h"
#include "zlib/zlib.h"

#define BLK_SIZE 64*1024

using Chunk = ParallelFilter::Chunk;
using ConstBlob = ParallelFilter::ConstBlob;

ParallelDeflateFilter::ParallelDeflateFilter()
  : ParallelFilter(BLK_SIZE, 8+compressBound(BLK_SIZE)) {}

void ParallelDeflateFilter::process(ParallelFilter::Chunk &c)
{
  const Bytef *src = (const Bytef*) c.pointer();
  Bytef *dst = (Bytef *) c.pointer() + c.payloadIn();

  // write uncompressed block size
  uint32_t uncompSize = c.payloadIn();
  memcpy(dst, &uncompSize, 4);

  uLongf dstlen = c.capacity() - 8;
  int stat = compress2(dst+8, &dstlen, src, c.payloadIn(), m_level);
  c.payloadOut(dstlen+8);

  uint32_t compSize = dstlen;
  memcpy(dst+4, &compSize, 4);
}

ParallelInflateFilter::ParallelInflateFilter()
  : ParallelFilter(8+compressBound(BLK_SIZE), BLK_SIZE) {}

Chunk ParallelInflateFilter::nextChunk(std::istream &in)
{
  Chunk c;
  if (!in)
    return c;

  uint32_t uncompSize, compSize;
  in.read((char *) &uncompSize, 4);
  in.read((char *) &compSize, 4);

  assert(compSize <= m_ibytes);
  assert(uncompSize <= m_obytes);

  c = emptyChunk();
  c.index( m_nextChunk++ );
  in.read(c.pointer(), compSize);
  c.payloadIn(compSize);
  assert(in.gcount() == compSize);
  c.payloadOut(uncompSize);
  return c;
}

Chunk ParallelInflateFilter::nextChunk(ConstBlob &b)
{
  Chunk c;

  uint32_t uncompSize, compSize;
  b.read((char *) &uncompSize, 4);
  b.read((char *) &compSize, 4);

  assert(compSize <= m_ibytes);
  assert(uncompSize <= m_obytes);

  c = emptyChunk();
  c.index( m_nextChunk++ );
  b.read(c.pointer(), compSize);
  c.payloadIn(compSize);
  c.payloadOut(uncompSize);
  return c;
}

void ParallelInflateFilter::process(ParallelFilter::Chunk &c)
{
  const Bytef *src = (const Bytef*) c.pointer() + 8;  // compressed block
  Bytef *dst = (Bytef *) c.pointer() + c.payloadIn() + 8;  // uncompressed data

  uLongf dstlen = c.payloadOut();
  int stat = uncompress(dst, &dstlen, src, c.payloadIn());
}

