
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
 
#include "lz4stream.h"
#include "lz4/lz4.h"
#include "lz4/xxhash.h"
#include "xcept.h"
#include "strutils.h"
#include "dbprint.h"
#include <iostream>

using namespace std;

size_t Lz4Stream::bufferSize(size_t nbytes)
{
  return LZ4_COMPRESSBOUND( nbytes );
}

size_t Lz4Stream::maxBlockSize() const
{
  return LZ4_COMPRESSBOUND( 4*1024*1024 );
}

bool Lz4Stream::openWrite(std::ostream &os)
{
  // initialize hash
  m_hashState = XXH32_init( 0 );

  // LZ4 stream header: first comes magic number
  const uint32_t magic = 0x184D2204;
  os.write( (const char*) &magic, 4 );
  if (not os)
    return false;

  m_header.stream_size = 0;

  // FLG
  m_header.flg = 0;
  m_header.flg |= 1 << 2; // stream checksum
  // m_header.flg |= 1 << 3; // stream size present
  m_header.flg |= 1 << 5; // block independence
  m_header.flg |= 1 << 6; // version

  // BD
  m_header.bd = 0;
  m_header.bd |= 7 << 4; // block size 4MB

  if ((m_header.flg & (1 << 3)) == 0) {
    char header[3];
    header[0] = m_header.flg;
    header[1] = m_header.bd;
    header[2] = (XXH32( &header, 2, 0 ) >> 8) & 0xff;
    os.write( header, 3 );
    if (not os)
      return false;

//    // debug
//    cout << "header flg: " << int(m_header.flg) << ", bd: "
//         << int(m_header.bd) << ", hc: " << int(header[2]) << endl;

  } else {
    m_header.hc = (XXH32( &m_header, 10, 0 ) >> 8) & 0xff;
    os.write( (const char *) &m_header, 11 );
    if (not os)
      return false;
  }

  return true;
}

bool Lz4Stream::openRead(istream &in)
{
  if (not in) {
    dbprint("Lz4Stream::openRead: bad bit.");
    return false;
  }

  // check for file format id
  int32_t magic(0);
  in.read((char *) &magic, 4);
  if ( (not in) or (magic != 0x184D2204) ) {
    dbprint("Lz4Stream::openRead: wrong magic.");
    return false;
  }

  // read header, which must have at least 3 bytes
  char header[2], hc;
  in.read(header, 2);

  m_header.flg = header[0];
  m_header.bd = header[1];

  // read stream size if present according to flg
  if (m_header.flg & (1 << 3)) {
    in.read( (char *) m_header.stream_size, 8 );
    m_header.hc = (XXH32( &m_header, 10, 0 ) >> 8) & 0xff;
  } else {
    m_header.hc = (XXH32( &m_header, 2, 0 ) >> 8) & 0xff;
  }

  // check checksum for header
  in.read(&hc, 1);
  bool ok = (hc == m_header.hc);
  if (ok and m_header.streamChecksum())
    m_hashState = XXH32_init(0);

  if (not ok)
    dbprint("Lz4Stream::openRead: header checksum mismatch.");
  return ok;
}

size_t Lz4Stream::write(std::ostream &os, const char *block, size_t nbytes)
{
  if (nbytes == 0)
    return 0;

  // always store small blocks in uncompressed form
  if (nbytes <= 64) {

    // update checksum of undecoded data
    XXH32_update(m_hashState, block, nbytes);

    uint32_t nb = nbytes;
    nb |= 0x80000000;
    os.write((const char *) &nb, 4);
    os.write((const char *) block, nbytes);

    m_header.stream_size += nbytes;
    return nbytes;
  }

  const size_t blockSize = 4*1024*1024;
  m_buffer.resize( LZ4_COMPRESSBOUND(blockSize)/4 + 4 );

  size_t compressed(0);
  size_t nblock = 1 + (nbytes / blockSize);
  for (size_t i=0; i<nblock; ++i) {

    // maximum amount of data to process
    int32_t slice = std::min( blockSize, nbytes );
    compressed += writeBlock( os, block, slice );

    nbytes -= slice;
    block += slice;

    if (nbytes == 0)
      break;
  }

  return compressed;
}

int Lz4Stream::writeBlock(ostream &os, const char *block, size_t nbytes)
{
  assert(nbytes <= 4*1024*1024);

  // update checksum of undecoded data
  XXH32_update(m_hashState, block, nbytes);

  // try to compress to internal buffer
  assert( 4*m_buffer.size() >= size_t(LZ4_compressBound(nbytes)+1) );
  int32_t stat = LZ4_compress_limitedOutput(block, (char *) &m_buffer[1],
                                            nbytes, 4*(m_buffer.size() - 1));

  if (stat != 0 and size_t(stat) < nbytes) {
    m_buffer[0] = stat;
    os.write((const char *) &m_buffer[0], stat + 4);
  } else {
    // store uncompressed block, set highest bit of block size
    uint32_t bmark(nbytes);
    bmark |= 0x80000000;
    os.write((const char *) &bmark, 4);
    os.write((const char *) block, nbytes);
    stat = nbytes;
  }

  m_header.stream_size += nbytes;
  return stat;
}

size_t Lz4Stream::read(istream &in, char *block, size_t nbytes)
{
  if (nbytes == 0)
    return 0;

  size_t retrieved(0);
  do {

    int decoded = readBlock(in, block, nbytes);
    if (decoded == 0)
      return retrieved;

#ifndef NDEBUG
    if (decoded < 0)
      throw Error("LZ4: Corrupt stream detected.");
    else if (size_t(decoded) > nbytes)
      throw Error("LZ4: Unexpected block boundary position; "
                  "decoded "+str(decoded)+", expected "+str(nbytes));
#endif

    block += decoded;
    nbytes -= decoded;
    retrieved += decoded;

  } while (nbytes > 0);

  return retrieved;
}

int Lz4Stream::readBlock(std::istream &in, char *block, size_t bufSpace)
{
  // read block size
  int32_t inpBlockSize(0), decoded(0);
  in.read((char *) &inpBlockSize, 4);
  if (inpBlockSize == 0) {
    return 0;
  } else if ( (inpBlockSize & 0x80000000) == 0 ) {
    m_buffer.resize(4 + inpBlockSize/4);  // m_buffer is int32_t
    in.read((char *) &m_buffer[0], inpBlockSize);
    decoded = LZ4_decompress_safe( (const char *) &m_buffer[0], block,
                                   inpBlockSize, bufSpace );
  } else { // uncompressed block
    inpBlockSize &= 0x7fffffff;
    in.read(block, inpBlockSize);
    decoded = inpBlockSize;
  }

  if ( (decoded > 0) and m_header.streamChecksum() )
    XXH32_update(m_hashState, block, decoded);
  return decoded;
}

bool Lz4Stream::closeWrite(std::ostream &os)
{
  // write stream checksum
  uint32_t footer[2];
  footer[0] = 0;
  footer[1] = XXH32_digest(m_hashState);
  m_hashState = 0;
  os.write((const char *) footer, 8);
  if (not os)
    return false;

  // jump to the header again and update stream size
  // and header checksum
  if ( m_header.flg & (1 << 3) ) {
    m_header.hc = (XXH32( &m_header, 10, 0 ) >> 8) & 0xff;
    os.seekp( 4 );
    os.write( (const char *) &m_header, 11 );
  }

  return true;
}

bool Lz4Stream::closeRead(istream &in)
{
  bool stat = true;
  if (m_header.streamChecksum()) {
    uint32_t streamHash(1);
    if (not in.read( (char *) &streamHash, 4 )) {
      dbprint("LZ4 closeRead: Unexpected EOF.");
      return false;
    }

    // at this point, the last (empty) block may not have been touched,
    // in which case we would read a zero blocksize here
    if (streamHash == 0)
      in.read( (char *) &streamHash, 4 ); // stream hash is the next int

    uint32_t checksum = XXH32_digest(m_hashState);
    stat = (streamHash == checksum);
    m_hashState = 0;
  }
  return stat;
}
