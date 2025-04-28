
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
 
#ifndef GENUA_IOBUFFER_H
#define GENUA_IOBUFFER_H

#include "ioglue.h"
#include <boost/iostreams/concepts.hpp>
#include <boost/iostreams/stream.hpp>
#include <vector>


/** Buffer for i/o operations.
 *
 * This is a primitive buffer object for use with the boost iostreams
 * library. It is useful in certain cases where the operating system's
 * internal buffering is insufficient or switched off.
 *
 * \ingroup io
 *
 */
class IoBuffer
{
public:

  /// create unattached buffer; default size is 64kB
  IoBuffer(uint64_t n = 64*1024) : m_bsize(n), m_rpos(0), m_wpos(0),
     m_ins(0), m_out(0) {}

  /// create read buffer
  IoBuffer(istream *pin, uint64_t n = 64*1024)
    : m_bsize(n), m_rpos(0), m_wpos(0), m_ins(pin), m_out(0) {}

  /// create write buffer
  IoBuffer(ostream *pout, uint64_t n = 64*1024)
    : m_bsize(n), m_rpos(0), m_wpos(0), m_ins(0), m_out(pout) {}

  /// delete buffer
  virtual ~IoBuffer();

  /// write bytes, flush when buffer full
  uint64_t write(const char *v, uint64_t n);

  /// read bytes, fetch new data when buffer empty
  uint64_t read(char *v, uint64_t n);

protected:

  /// flush buffer to output stream
  virtual bool flush();

  /// fetch new data from input stream
  virtual bool fetch();

private:

  /// storage
  std::vector<char> m_buffer;

  /// requested buffer size
  uint64_t m_bsize;

  /// pointers
  uint64_t m_rpos, m_wpos;

  /// input stream
  istream *m_ins;

  /// output stream
  ostream *m_out;
};

class IoBufferSource : protected IoBuffer, public boost::iostreams::source
{
public:

  /// create source with stream and buffer size
  IoBufferSource(istream *pin, uint64_t n) : IoBuffer(pin, n) {}

  /// read up to n bytes, return bytes read or -1 if end-of-sequence reached
  std::streamsize read(char* s, std::streamsize n) {
    if (n != 0) {
      uint64_t m = IoBuffer::read(s, n);
      return (m != 0) ? m : std::streamsize(-1);
    } else {
      return 0;
    }
  }
};

class IoBufferSink : protected IoBuffer, public boost::iostreams::sink
{
public:

  /// create sink with stream and buffer size
  IoBufferSink(ostream *pout, uint64_t n) : IoBuffer(pout, n) {}

  /// read up to n bytes, return bytes read or -1 if end-of-sequence reached
  std::streamsize write(const char* s, std::streamsize n) {
    if (n != 0) {
      uint64_t m = IoBuffer::write(s, n);
      return (m != 0) ? m : std::streamsize(-1);
    } else {
      return 0;
    }
  }
};

typedef boost::iostreams::stream<IoBufferSource>   BufferedIStream;
typedef boost::iostreams::stream<IoBufferSink>     BufferedOStream;

#endif // IOBUFFER_H
