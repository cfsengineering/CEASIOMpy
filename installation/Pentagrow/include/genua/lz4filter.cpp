
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
 
#include "lz4filter.h"
#include <iostream>
#include <cassert>

Lz4Sink::Lz4Sink(std::ostream &os, int compressionLevel) : m_out(os)
{
  memset( &m_pref, 0, sizeof(m_pref) );
  m_pref.frameInfo.blockSizeID = LZ4F_max4MB;
  m_pref.compressionLevel = compressionLevel;
  m_pref.autoFlush = 1;
}

std::streamsize Lz4Sink::write(const char *s, std::streamsize n)
{
  size_t nc, nbound;
  nbound = LZ4F_compressFrameBound(n, &m_pref);
  if (m_buf.size() < nbound)
    m_buf.resize(nbound);

  nc = LZ4F_compressFrame(&m_buf[0], m_buf.size(),
                          (const void*) s, n, &m_pref);
  m_out.write(&m_buf[0], nc);

  return n;
}

// -------------------------------- source -------------------------------------

Lz4Source::Lz4Source(std::istream &in)
  : m_inp(in), m_rbegin(0), m_rend(0), m_cbegin(0), m_cend(0)
{
  LZ4F_errorCode_t stat;
  stat = LZ4F_createDecompressionContext(&m_ctx, LZ4F_VERSION);
}

Lz4Source::~Lz4Source()
{
  LZ4F_errorCode_t stat;
  stat = LZ4F_freeDecompressionContext(m_ctx);
}

std::streamsize Lz4Source::read(char* s, std::streamsize n)
{
  if (n <= 0)
    return 0;

  const size_t bufSize = 4*1024*1024;
  if (m_buf.size() < bufSize)
    m_buf.resize(bufSize);

  // cannot handle more than bufSize in one call, chop off
  // bufSize at a time and write into s, adjust parameters and drop out
  assert(s != nullptr);
  std::streamsize nacc(0);
  if (size_t(n) > bufSize) {
    size_t npre = n / bufSize;
    for (size_t i=0; i<npre; ++i) {
      nacc += this->read(s, bufSize);
      s += bufSize;
      n -= bufSize;
    }
  }

  assert(size_t(n) <= bufSize);

  do {

    // copy decompressed data from the last frame processed
    size_t nc = dump(s, n);
    s += nc;
    n -= nc;
    nacc += nc;

    if (n == 0)
      break;

    // fetch the next frame if necessary
    nextFrame();

  } while (n > 0);

  return nacc;
}

void Lz4Source::nextFrame()
{
  // the size of the first chunk of data read from stream, before anthing
  // is known about the block size
  const size_t chunkSize = 64*1024;

  size_t srcSize, dstSize(m_buf.size() - m_rend);
  size_t hint(chunkSize);
  do {

    // fetch new compressed data from stream if necessary
    if (m_cend <= m_cbegin) {
      m_cbegin = 0;
      if (hint > m_chunk.size())
        m_chunk.resize(hint);
      m_inp.read((char *) &m_chunk[0], hint);
      m_cend = m_inp.gcount();
    }

    srcSize = m_cend - m_cbegin;
    hint = LZ4F_decompress(m_ctx, (void *) &m_buf[m_rend], &dstSize,
                           (const void*) &m_chunk[m_cbegin], &srcSize,
                           nullptr);

    // dstSize bytes of decompressed data were written to m_buf
    m_rend += dstSize;
    dstSize = m_buf.size() - m_rend;


    // srcSize bytes of compressed data were read from m_chunk, and that
    // could be less than the amount expected, so there might be data left
    // in m_chunk for the next pass
    m_cbegin += srcSize;

    // destination buffer full?
    if (dstSize == 0)
      break;

  } while (hint != 0);
}

size_t Lz4Source::dump(char *s, std::streamsize n)
{
  size_t nmove(0);
  if (m_rend > m_rbegin) {
    nmove = std::min( size_t(n), m_rend-m_rbegin );
    memcpy( s, &m_buf[m_rbegin], nmove );
    m_rbegin += nmove;
  } else {
    m_rbegin = m_rend = 0;
  }

  return nmove;
}
