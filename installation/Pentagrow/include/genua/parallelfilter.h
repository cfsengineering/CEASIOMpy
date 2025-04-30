
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

#ifndef GENUA_PARALLELFILTER_H
#define GENUA_PARALLELFILTER_H

#include "forward.h"
#include "propmacro.h"
#include <boost/shared_ptr.hpp>
#include <boost/thread/mutex.hpp>
#include <atomic>

/** Parallel filter.
 *
 * Machinery which supports the parallelization of complex stream transformation
 * such as compression or encryption on large chunks of data or files. One
 * thread will be created to retrieve chunks of data from a source (buffer or
 * stream), one thread per logical core is spawn in a group that performs
 * the compression and another thread handles writing of processed blocks in the
 * correct order.
 *
 * \ingroup experimental, concurrency
 */
class ParallelFilter
{
public:

  /// create filter setup for input/output block sizes
  ParallelFilter(size_t ibytes, size_t obytes)
    : m_ibytes(ibytes), m_obytes(obytes) {}

  /// helper class, holds pointer to read-only data
  struct ConstBlob {
    ConstBlob(const char *p, size_t n) : begin(p), size(n) {}
    const char *current() const {return begin+pos;}
    size_t read(char *dst, size_t n) {
      size_t bytes = std::min(n, size-pos);
      memcpy(dst, current(), bytes);
      pos += bytes;
      return bytes;
    }
    const char *begin = nullptr;
    size_t size = 0;
    size_t pos = 0;
  };

  class Chunk
  {
  public:
    Chunk() = default;
    Chunk(const Chunk &a) = default;
    Chunk(Chunk &&a)
      : m_ptr(std::move(a.m_ptr)), m_bytes(a.m_bytes),
        m_payloadIn(a.m_payloadIn), m_payloadOut(a.m_payloadOut),
        m_index(a.m_index) {}
    Chunk(size_t bytes) : m_bytes(bytes) {
      m_ptr = boost::make_shared<char[]>(m_bytes);
    }
    ~Chunk() = default;
    Chunk &operator= (const Chunk &a) = default;
    Chunk &operator= (Chunk &&a) {
      if (this != &a) {
        m_bytes = a.m_bytes;
        m_payloadIn = a.m_payloadIn;
        m_payloadOut = a.m_payloadOut;
        m_index = a.m_index;
        m_ptr = std::move(a.m_ptr);
      }
      return *this;
    }
    const char *pointer() const {return m_ptr.get();}
    char *pointer() {return m_ptr.get();}
    size_t capacity() {return m_bytes - payloadIn();}
  private:

    /// pointer to actual buffer
    boost::shared_ptr<char[]> m_ptr;

    /// allocated on construction
    size_t m_bytes;

    /// actual input content size
    GENUA_PROP_INI(size_t, payloadIn, 0)

    /// actual output content size
    GENUA_PROP_INI(size_t, payloadOut, 0)

    /// sequence index which determines ordering
    GENUA_PROP_INI(size_t, index, 0)
  };

  /// read from stream, process, write to binary blob (call reserve on blob!)
  void read(std::istream &in, std::vector<char> &blob);

  /// read from buffer, process, write to stream
  void write(size_t n, const char *ptr, std::ostream &os);

  /// pipe from buffer to buffer (call reserve on dst first!)
  void pipe(const std::vector<char> &src, std::vector<char> &dst);

  /// pipe from stream to stream
  void pipe(std::istream &in, std::ostream &os);

  /// overload this (default just copies)
  virtual void process(Chunk &c);

  /// fetch a new chunk and fill from stream
  virtual Chunk nextChunk(std::istream &in);

  /// fetch a new chunk and fill from buffer
  virtual Chunk nextChunk(ConstBlob &b);

  /// write chunk to ostream and dispose
  virtual void consumeChunk(Chunk &&c, std::ostream &os);

  /// write chunk to ostream and dispose
  virtual void consumeChunk(Chunk &&c, std::vector<char> &blob);

protected:

  /// obtain a new allocated container, w/o contents
  Chunk emptyChunk();

  /// put chunk back on the heap for recycling
  void disposeChunk(Chunk &&c);

protected:

  /// allocated, but unused chunks
  std::vector<Chunk> m_heap;

  /// mutex to protect access to the heap
  boost::mutex m_hguard;

  /// block sizes for allocation
  size_t m_ibytes, m_obytes;

  /// index of next chunk to issue
    size_t m_nextChunk = 0;
};

#endif // PARALLELFILTER_H
