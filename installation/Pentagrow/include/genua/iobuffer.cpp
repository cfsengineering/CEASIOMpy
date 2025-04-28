
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
 
#include "iobuffer.h"

IoBuffer::~IoBuffer()
{
  flush();
}

uint64_t IoBuffer::write(const char *v, uint64_t n)
{
  if (m_buffer.size() != m_bsize)
    m_buffer.resize( m_bsize );

  uint64_t written = 0;
  while ( n > 0 ) {
    uint64_t m = std::min( m_buffer.size() - m_wpos, n );
    if (m > 0) {
      memcpy( &m_buffer[m_wpos], v, m );
      v += m;
      m_wpos += m;
      n -= m;
      written += m;
    } else {
      if (not flush())
        return written;
    }
  }

  return written;
}

bool IoBuffer::flush()
{
  if (m_out == 0)
    return false;
  if (m_wpos == 0)
    return false;

  m_out->write( &m_buffer[0], m_wpos );
  m_wpos = 0;
  return true;
}

uint64_t IoBuffer::read(char *v, uint64_t n)
{
  uint64_t nread = 0;
  while ( n > 0 ) {
    uint64_t m = std::min( m_buffer.size() - m_rpos, n );
    if (m > 0) {
      memcpy( v, &m_buffer[m_rpos], m );
      v += m;
      m_rpos += m;
      n -= m;
      nread += m;
    } else {
      if (not fetch())
        return nread;
    }
  }
  return nread;
}

bool IoBuffer::fetch()
{
  if (m_ins == 0)
    return false;

  if (m_buffer.size() != m_bsize)
    m_buffer.resize(m_bsize);

  m_ins->read( &m_buffer[0], m_bsize );
  uint64_t nread = m_ins->gcount();
  if (nread < m_bsize)
    m_buffer.resize( nread );

  // read pointer to start of buffer
  m_rpos = 0;

  return (nread > 0);
}
