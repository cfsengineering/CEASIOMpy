
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
 #ifndef GENUA_LZ4FILTER_H
#define GENUA_LZ4FILTER_H

#include "lz4/lz4frame.h"
#include <boost/iostreams/concepts.hpp>
#include <boost/iostreams/stream.hpp>
#include <vector>
#include <iosfwd>

class Lz4Source : public boost::iostreams::source
{
public:

  /// initialize with destination stream
  Lz4Source(std::istream &in);

  /// free context
  ~Lz4Source();

  /// fetch from stream and decompress until n bytes reached
  std::streamsize read(char* s, std::streamsize n);

private:

  /// decompress the next frame
  void nextFrame();

  /// move decompressed data into s
  size_t dump(char* s, std::streamsize n);

private:

  /// source of compressed data
  std::istream &m_inp;

  /// context for the decompressor
  LZ4F_decompressionContext_t m_ctx;

  /// temporary buffer for decompressed data
  std::vector<char> m_buf;

  /// buffer range containing left-over decompressed data
  size_t m_rbegin, m_rend;

  /// temporary buffer for stream input
  std::vector<char> m_chunk;

  /// buffer range containing left-over compressed data
  size_t m_cbegin, m_cend;
};

class Lz4Sink : public boost::iostreams::sink
{
public:

  /// initialize with destination stream
  Lz4Sink(std::ostream &os, int compressionLevel=1);

  /// compress n bytes from s and write to stored stream
  std::streamsize write(const char* s, std::streamsize n);

private:

  /// destination of compressed data
  std::ostream &m_out;

  /// compression settings
  LZ4F_preferences_t m_pref;

  /// temporary buffer for compression library
  std::vector<char> m_buf;
};

typedef boost::iostreams::stream<Lz4Source> Lz4DecprStream;
typedef boost::iostreams::stream<Lz4Sink>   Lz4ComprStream;

#endif // LZ4FILTER_H
