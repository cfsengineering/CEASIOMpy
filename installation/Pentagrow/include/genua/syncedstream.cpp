#include "syncedstream.h"
#include "bitfiddle.h"
#include <iostream>
#include <fstream>

using namespace std;

SyncedStreamDevice::SyncedStreamDevice(const SyncedStreamDevice &a)
{
  std::lock_guard<std::mutex> lock(a.m_guard);
  m_contents = a.m_contents;
  m_rpos = a.m_rpos;
  m_wpos = a.m_wpos;
}

std::streamsize SyncedStreamDevice::read(char *s, std::streamsize n)
{
  std::lock_guard<std::mutex> lock(m_guard);
  if (m_rpos < m_contents.size()) {
    size_t m = std::min(n, std::streamsize(m_contents.size() - m_rpos));
    if (m > 0)
      memcpy(s, &m_contents[m_rpos], m);
    m_rpos += m;
    return m;
  } else
    return -1;
}

std::streamsize SyncedStreamDevice::write(const char *s, std::streamsize n)
{
  std::lock_guard<std::mutex> lock(m_guard);
  if (m_wpos == m_contents.size()) {
    m_contents.insert(m_contents.end(), s, s+n); 
  } else {
    m_contents.resize(m_wpos + n);
    if (n > 0)
      memcpy(&m_contents[m_wpos], s, n);
  }
  m_wpos += n;
  return n;
}

SyncedStreamDevice::stream_offset
SyncedStreamDevice::seek(SyncedStreamDevice::stream_offset off,
                         std::ios_base::seekdir way,
                         std::ios_base::openmode which)
{
  std::lock_guard<std::mutex> lock(m_guard);
  stream_offset next(0);
  if ( bit_is_set(which, std::ios_base::in) ) {
    next = movePos(off, way, m_rpos);
    if (next < 0)
      return next;
  }

  if ( bit_is_set(which, std::ios_base::out) ) {
    next = movePos(off, way, m_wpos);
    if (next < 0)
      return next;
  }

  return next;
}

void SyncedStreamDevice::dump(const string &fname) const
{
  std::lock_guard<std::mutex> lock(m_guard);
  ofstream os(fname);
  if (m_contents.size() > 0)
    os.write(&m_contents[0], m_contents.size());
  os.close();
}

string SyncedStreamDevice::str() const
{
  std::lock_guard<std::mutex> lock(m_guard);
  return std::string(m_contents.begin(), m_contents.end());
}

void SyncedStreamDevice::reset()
{
  std::lock_guard<std::mutex> lock(m_guard);
  m_contents.clear();
  m_rpos = m_wpos = 0;
}

SyncedStreamDevice::stream_offset
SyncedStreamDevice::movePos(SyncedStreamDevice::stream_offset off,
                            ios_base::seekdir way, size_t &pos) const
{
  stream_offset next;
  if (way == ios_base::beg) {
    next = off;
  } else if (way == ios_base::cur) {
    next = pos + off;
  } else if (way == ios_base::end) {
    next = m_contents.size() + off - 1;
  } else {
    throw ios_base::failure("bad seek direction");
  }

  if (next < 0 or next >= stream_offset(m_contents.size()))
    throw ios_base::failure("bad seek offset");

  pos = next;
  return next;
}

