
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
 
#ifndef GENUA_PACKETSTREAM_H
#define GENUA_PACKETSTREAM_H

#include "defines.h"
#include "ioglue.h"
#include "xcept.h"
#include "dbprint.h"
#include "allocator.h"
#include <deque>

/** Binary data packet for streaming.
 *
 * StreamPacket is the block by which streaming data is passed to the i/o
 * buffer PacketBuffer which ships off data to disk once full. The total size
 * of one packet (in bytes) is set by the template argument; it includes the
 * 16-byte header.
 *
 *  \ingroup experimental
 *  \sa PacketBuffer
 */
template <int tBlockSize>
class StreamPacket
{
public:

  static const uint64_t InvalidFlag = std::numeric_limits<uint64_t>::max();

  /// make empty, invalid packet
  StreamPacket() : m_type(InvalidFlag), m_size(0)
  {
#ifndef NDEBUG
    memset(m_block, 0xfa, sizeof(m_block));
#endif
  }

  /// make packet from content
  StreamPacket(uint64_t type, uint64_t bytes, const char *contents)
    : m_type(type), m_size(bytes)
  {
    assert(m_size < capacity());
    if (bytes > 0)
      memcpy(m_block, contents, m_size);
  }

  /// whether packet is valid
  bool valid() { return m_type != InvalidFlag; }

  /// mark as invalid
  void invalidate() {
    m_type = InvalidFlag;
    m_size = 0;
#ifndef NDEBUG
    memset(m_block, 0xfa, sizeof(m_block));
#endif
  }

  /// type indicator
  uint64_t type() const {return m_type;}

  /// number of bytes in the entire packet, including header
  size_t size() const {return m_size + 16;}

  /// capacity of the payload block
  static size_t capacity() {return tBlockSize - 16;}

  /// start adress for writing
  const char *begin() const {return m_block - 16;}

  /// end adress for writing
  const char *end() const {return m_block + m_size;}

  /// number of bytes in payload
  size_t payload() const {return m_size;}

  /// address of the payload block
  const char *pointer() const {return &m_block[0];}

  /// fetch packet from raw buffer
  const char *fetch(const char *pos) {
    memcpy((char *) this, pos, 16);
    assert(m_size < capacity());
    memcpy(m_block, pos+16, m_size);
    return pos + size();
  }

  /// append one more float to existing packet
  void append(float x) {
    memcpy(m_block[m_size], &x, 4);
    m_size += 4;
  }

  /// append one more int to existing packet
  void append(int32_t x) {
    memcpy(m_block[m_size], &x, 4);
    m_size += 4;
  }

protected:

  /// packet type identifier for dispatcher
  uint64_t m_type;

  /// number of bytes in payload
  uint64_t m_size;

  /// payload
  char m_block[tBlockSize - 16];
};

/** Binary data stream.
 *
 * Classes StreamPacket and PacketBuffer are meant to be used for applications
 * which cannot hold generated data in memory. A precondition for use of
 * PacketBuffer is that data is produced by small or fixed-size chunks
 * (StreamPacket) which do not need to be touched again after generation.
 *
 *  \ingroup experimental
 *  \sa StreamPacket
 */
template <int tBlockSize>
class PacketBuffer
{
public:

  /// create unassociated stream buffer
  PacketBuffer() : m_pos(0), m_pin(0) {}

  /// create output buffer, reserve space for n messages
  PacketBuffer(ostream *pos, size_t n = 1024) : m_pos(pos), m_pin(0)
  {
    assert(n > 1);
    m_buffer.reserve(n);
    uint64_t blockSize(tBlockSize);
    char header[32] = "PACKET_STREAM_V1";
    memcpy(header+16, (const char *) &blockSize, 8);
    m_pos->write( header, 32 );
  }

  /// create input buffer for n messages
  PacketBuffer(istream *pin, size_t n = 1024)
    : m_pos(0), m_pin(pin), m_cursor(0)
  {
    assert(n > 1);
    m_buffer.reserve(n);
    if (not isPacketStream(*m_pin))
      throw Error("Not a packet stream.");
  }

  /// sync on destruction
  ~PacketBuffer()
  {
    if (m_pos)
      sync();
  }

  /// check whether stream is writeable
  bool isWritable() const {return m_pos != 0;}

  /// check whether stream is writeable
  bool isReadable() const {return m_pin != 0;}

  /// check if stream is a compatible packet source
  static bool isPacketStream(istream &in)
  {
    char header[32];
    in.read(header, 32);
    if (strstr(header, "PACKET_STREAM_V1") != header) {
      in.seekg(0);
      return false;
    }
    uint64_t blockSize(0);
    memcpy((char *) &blockSize, header+16, 8);
    if (blockSize <= tBlockSize) {
      return true;
    } else {
      in.seekg(0);
      return false;
    }
  }

  /// copy packet and append at the end of the buffer; sync when buffer full
  PacketBuffer & operator<< (const StreamPacket<tBlockSize> &packet) {
    if (m_buffer.size() >= m_buffer.capacity())
      sync();
    m_buffer.push_back(packet);
    return *this;
  }

  /// fetch next packet from buffer; refill buffer if necessary
  PacketBuffer &operator>> (StreamPacket<tBlockSize> &packet) {
    packet.invalidate();
    if (m_cursor >= m_buffer.size())
      refill();
    if (m_cursor < m_buffer.size()) {
      packet = m_buffer[m_cursor];
      ++m_cursor;
    }
    return *this;
  }

  /// write current buffer to output stream
  void sync()
  {
    if (m_buffer.empty() or m_pos == nullptr)
      return;

    // first, dump all fixed-size packets into a memory buffer
    std::vector<char> tmp;
    tmp.reserve( m_buffer.size() * PacketType::capacity() );

    // 8 bytes for the chunk size
    tmp.insert(tmp.begin(), 8, '0');
    const size_t npack = m_buffer.size();
    for (size_t i=0; i<npack; ++i) {
      if (m_buffer[i].valid()) {
        const PacketType &packet( m_buffer[i] );
        tmp.insert(tmp.end(), packet.begin(), packet.end());
      }
    }

    // insert chunk size into stream
    uint64_t chunkSize = tmp.size() - 8;
    memcpy( &tmp[0], &chunkSize, 8 );

    // only then, dump buffer into stream (one system call)
    m_pos->write( (const char *) &tmp[0], tmp.size() );
    m_buffer.clear();
  }

  /// refill buffer from input stream
  bool refill()
  {
    assert(m_pin != nullptr);

    m_buffer.clear();
    m_cursor = 0;

    uint64_t chunkSize(0);
    m_pin->read((char *) &chunkSize, 8);
    if (m_pin->fail() or chunkSize == 0)
      return false;

    std::vector<char> tmp(chunkSize);
    m_pin->read(&tmp[0], chunkSize);

    StreamPacket<tBlockSize> packet;
    const char *pos = &tmp[0];
    const char *end = pos + tmp.size();
    while (pos != end) {
      const char *tail = packet.fetch(pos);
      m_buffer.push_back(packet);
      pos = tail;
    };
    m_cursor = 0;
    return true;
  }

private:

  typedef StreamPacket<tBlockSize> PacketType;
  typedef std::vector<PacketType> Storage;

  /// buffer which is synched to stream once filled
  Storage m_buffer;

  /// reference to stream into which buffer is dumped when full
  ostream *m_pos;

  /// reference to stream from where buffer contents are fetched when empty
  istream *m_pin;

  /// cursor for input streams
  size_t m_cursor;
};

#endif // PACKETSTREAM_H
