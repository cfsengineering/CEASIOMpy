
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
 
#ifndef GENUA_LZ4STREAM_H
#define GENUA_LZ4STREAM_H

#include "forward.h"
#include <iosfwd>

/** LZ4 compressed binary stream.
 *
 * Interface to LZ4 compression by Yann Collet (http://code.google.com/p/lz4/).
 *
 * When using on Windows, make sure that the streams passed to the interface
 * are opened with the std::ios::binary flag set.
 *
 * \sa BinFileNode
 */
class Lz4Stream
{
public:

  /// initialize empty stream
  Lz4Stream() : m_hashState(0) {}

  /// memory block size needed to decompress nbytes
  static size_t bufferSize(size_t nbytes);

  /// maximum size of a block of uncompressed data
  size_t maxBlockSize() const;

  /// write header to stream
  bool openWrite(std::ostream &os);

  /// open stream for reading, return true if LZ4 format recognized
  bool openRead(std::istream &in);

  /// compress and append to stream, return number of compressed bytes written
  size_t write(std::ostream &os, const char *block, size_t nbytes);

  /// decompress and append to buffer
  size_t read(std::istream &in, char *block, size_t nbytes);

  /// close stream used for writing
  bool closeWrite(std::ostream &os);

  /// close stream used for reading (stream checksum)
  bool closeRead(std::istream &in);

  /// write one block to stream, return number of compressed bytes or <0
  int writeBlock(std::ostream &os, const char *block, size_t nbytes);

  /// fetch entire next block from stream, block must have maxBlockSize() bytes
  int readBlock(std::istream &in, char *block, size_t bufSpace);

private:

  /// stream descriptor
  struct Descriptor {
    char flg;
    char bd;
    uint64_t stream_size;
    char hc;

    bool streamChecksum() const { return (flg & (1 << 2)); }
  };

  /// state of the XXH32 hash
  void *m_hashState;

  /// header
  Descriptor m_header;

  /// temporary block storage
  std::vector<int32_t> m_buffer, m_dcb;
};

#endif // LZ4STREAM_H
