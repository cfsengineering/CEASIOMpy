
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

#include "parallelfilter.h"
#include "algo.h"
#include "parallel_algo.h"
#include <boost/thread/locks.hpp>
#include <boost/thread.hpp>
#include <atomic>

using Chunk = ParallelFilter::Chunk;

template <class SrcType, class DstType>
void pipeline(ParallelFilter &filter, SrcType &&src, DstType &&dst)
{
  std::vector<Chunk> rqueue, wqueue;
  boost::mutex rguard;
  boost::mutex wguard;
  size_t nextToWrite = 0;
  bool stillReading = true;
  bool stillProcessing = true;

  // reader task (only one will be started)
  auto rtask = [&]() {
    Chunk c;
    do {
      c = filter.nextChunk(src);
      rguard.lock();
      rqueue.push_back(c);
      rguard.unlock();
    } while (c.payloadIn() > 0);
    stillReading = false;
  };

  auto pred = [&](const Chunk &c) {return c.index() == nextToWrite;};

  // writer task (only one will be started)
  auto wtask = [&]() {
    std::vector<Chunk>::iterator pos;
    while (stillProcessing) {
      Chunk c;
      c.index( std::numeric_limits<size_t>::max() );
      wguard.lock();
      pos = std::find_if(wqueue.begin(), wqueue.end(), pred);
      if (pos != wqueue.end()) {
        c = *pos;
        wqueue.erase(pos);
      }
      wguard.unlock();
      if (c.index() == nextToWrite) {
        filter.consumeChunk(std::move(c), dst);
        ++nextToWrite;
      }
      boost::this_thread::yield();
    }
  };

  // processing task
  auto work = [&]() {
    while (stillReading or (not rqueue.empty())) {
      Chunk c;
      rguard.lock();
      if (not rqueue.empty()) {
        c = rqueue.back();
        rqueue.pop_back();
      }
      rguard.unlock();
      filter.process(c);
      wguard.lock();
      wqueue.push_back(std::move(c));
      wguard.unlock();
    }
    stillProcessing = false;
  };

  const size_t nworker = boost::thread::hardware_concurrency();
  std::vector< boost::thread > threads;
  threads.push_back( boost::thread(rtask) );
  for (size_t i=0; i<nworker; ++i)
    threads.push_back( boost::thread(work) );
  threads.push_back( boost::thread(wtask) );

  // wait until the writer task has finished
  threads.back().join();
}

// ------------------- ParallelFilter ----------------------------------------

void ParallelFilter::read(std::istream &in,
                          std::vector<char> &blob)
{
  pipeline(*this, in, blob);
}

void ParallelFilter::write(size_t n, const char *ptr, std::ostream &os)
{
  ConstBlob b(ptr, n);
  pipeline(*this, b, os);
}

void ParallelFilter::pipe(const std::vector<char> &src, std::vector<char> &dst)
{
  ConstBlob b(&src[0], src.size());
  pipeline(*this, b, dst);
}

void ParallelFilter::pipe(std::istream &in, std::ostream &os)
{
  pipeline(*this, in, os);
}

void ParallelFilter::process(ParallelFilter::Chunk &c)
{
  memcpy( c.pointer() + c.payloadIn(),
          c.pointer(), c.payloadIn() );
  c.payloadOut( c.payloadIn() );
}

ParallelFilter::Chunk ParallelFilter::nextChunk(std::istream &in)
{
  Chunk c = emptyChunk();
  c.index( m_nextChunk++ );
  in.read( c.pointer(), m_ibytes );
  c.payloadIn( in.gcount() );
  return c;
}

ParallelFilter::Chunk ParallelFilter::nextChunk(ParallelFilter::ConstBlob &b)
{
  Chunk c = emptyChunk();
  c.index( m_nextChunk++ );
  size_t bp = std::min(b.size - b.pos, m_ibytes);
  memcpy(c.pointer(), b.current(), bp);
  c.payloadIn( bp );

  return c;
}

void ParallelFilter::consumeChunk(ParallelFilter::Chunk &&c,
                                  std::vector<char> &blob)
{
  const char *src = c.pointer() + c.payloadIn();
  blob.insert(blob.end(), src, src + c.payloadOut());
  disposeChunk(std::move(c));
}

void ParallelFilter::consumeChunk(ParallelFilter::Chunk &&c, std::ostream &os)
{
  const char *src = c.pointer() + c.payloadIn();
  os.write(src, c.payloadOut());
  disposeChunk(std::move(c));
}

ParallelFilter::Chunk ParallelFilter::emptyChunk()
{
  boost::unique_lock<boost::mutex> lock(m_hguard);
  if (hint_unlikely(m_heap.empty())) {
    const size_t bytes = m_ibytes + m_obytes;
    const size_t blk = 64;
    m_heap.clear();
    m_heap.reserve(blk);
    for (size_t i=0; i<blk; ++i)
      m_heap.emplace_back(bytes);
  }

  Chunk c = m_heap.back();
  m_heap.pop_back();
  return c;
}

void ParallelFilter::disposeChunk(ParallelFilter::Chunk &&c)
{
  boost::unique_lock<boost::mutex> lock(m_hguard);
  m_heap.push_back( std::move(c) );
}
