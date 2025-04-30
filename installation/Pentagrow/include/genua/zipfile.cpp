
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
 
#include "zipfile.h"
#include "algo.h"
#include "ioglue.h"
#include "xcept.h"
#include "zlib/unzip.h"
#include "zlib/zip.h"
#include <cstring>

using std::string;

ZipFile::~ZipFile()
{
  if (m_ufile != 0) {
    unzClose(m_ufile);
    m_ufile = 0;
  }
}

bool ZipFile::openArchive(const std::string &archive)
{
  m_rposition = m_wposition = 0;

  if (m_ufile != 0)
    unzClose(m_ufile);
  m_ufile = unzOpen(archive.c_str());
  if (m_ufile)
    unzGoToFirstFile(m_ufile);

  return m_ufile != 0;
}

bool ZipFile::nextFile()
{
  assert(m_ufile);
  m_rposition = m_wposition = 0;
  int stat = unzGoToNextFile(m_ufile);
  return (stat == UNZ_OK);
}

std::string ZipFile::currentFile()
{
  assert(m_ufile);
  const int nbytes(512);
  char fname[nbytes];
  memset(fname, 0, nbytes);
  int stat = unzGetCurrentFileInfo(m_ufile, 0, fname, nbytes, 0, 0, 0, 0);
  string s;
  if (stat == UNZ_OK)
    s = string(fname);

  return s;
}

/// move to file named fname
bool ZipFile::locateFile(const std::string &fname)
{
  assert(m_ufile);
  return (unzLocateFile(m_ufile, fname.c_str(), 0) == UNZ_OK);
}

bool ZipFile::openCurrentFile()
{
  assert(m_ufile);
  m_rposition = m_wposition = 0;
  return unzOpenCurrentFile(m_ufile) == UNZ_OK;
}

bool ZipFile::closeCurrentFile()
{
  assert(m_ufile);
  m_rposition = m_wposition = 0;
  return unzCloseCurrentFile(m_ufile) == UNZ_OK;
}

int ZipFile::read(uint nbytes, char *buf)
{
  assert(m_ufile);
  int stat = unzReadCurrentFile(m_ufile, buf, nbytes);
  if (stat > 0)
    m_rposition += stat;

  return stat;
}

uint ZipFile::skip(uint n)
{
  assert(m_ufile);
  if ( hint_unlikely(n == 0) )
    return 0;

  const uint bsize = 32*1024;
  char buffer[bsize];
  uint nskipped(0);
  do {
    uint chunk = std::min(bsize, n-nskipped);
    int stat = this->read(chunk, buffer);
    if (stat > 0)
      nskipped += stat;
    else if (stat == 0)  // EOF
      return nskipped;
    else
      throw Error("zlib reports error; corrupted zip file.");

  } while (nskipped < n);

  return nskipped;
}

size_t ZipFile::dumpFile(std::ostream &os)
{
  assert(m_ufile);
  const int nbytes(4096);
  char buf[nbytes];
  int stat, ncop(nbytes);

  stat = unzOpenCurrentFile(m_ufile);
  if (stat != UNZ_OK)
    return 0;

  size_t bytes(0);
  while (ncop == nbytes) {
    ncop = this->read(nbytes, buf);
    if (ncop > 0) {
      os.write(buf, ncop);
      bytes += ncop;
      m_rposition += ncop;
    } else if (ncop < 0) {
      unzCloseCurrentFile(m_ufile);
      return 0;
    }
  }
  os.flush();
  unzCloseCurrentFile(m_ufile);
  return bytes;
}

bool ZipFile::createArchive(const std::string &archive)
{
  m_rposition = m_wposition = 0;
  m_zfile = zipOpen(archive.c_str(), APPEND_STATUS_CREATE);
  return m_zfile != NULL;
}

bool ZipFile::newFile(const std::string &fname, int level)
{
  assert(m_zfile);
  m_rposition = m_wposition = 0;
  int stat = ZIP_OK;
  int method = Z_DEFLATED;
  stat = zipOpenNewFileInZip(m_zfile, fname.c_str(), 0, 0, 0, 0, 0, 0, method,
                             level);
  return stat == ZIP_OK;
}

bool ZipFile::write(uint nbytes, const char *buf)
{
  assert(m_zfile);
  int stat = ZIP_OK;
  stat = zipWriteInFileInZip(m_zfile, (const void *) buf, nbytes);
  if (stat == ZIP_OK)
    m_wposition += nbytes;
  return stat == ZIP_OK;
}

bool ZipFile::closeFile()
{
  assert(m_zfile);
  m_rposition = m_wposition = 0;
  int stat = ZIP_OK;
  stat = zipCloseFileInZip(m_zfile);
  return stat == ZIP_OK;
}

bool ZipFile::write(const std::string &fname, uint nbytes, const char *buf)
{
  assert(m_zfile);
  bool stat = newFile(fname);
  if (not stat)
    return false;
  stat = write(nbytes, buf);
  if (not stat)
    return false;
  return closeFile();
}

bool ZipFile::closeArchive()
{
  assert(m_zfile);
  m_rposition = m_wposition = 0;
  return zipClose(m_zfile, 0) == ZIP_OK;
}

bool ZipFile::isZip(const std::string &fname)
{
  ifstream in(asPath(fname).c_str(), std::ios::in | std::ios::binary);
  uint32_t head(0);
  in.read((char *) &head, 4);
  if (is_bigendian())
    swap_bytes<4>(4, (char *) &head);
  if (head == 0x04034b50)
    return true;
  else
    return false;
}
