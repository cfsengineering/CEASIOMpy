
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
 
#ifndef GENUA_ZIPFILE
#define GENUA_ZIPFILE

#include "forward.h"
#include <iosfwd>
#include <string>

typedef void *unzFile;
typedef void *zipFile;

/** Minimal frontend to zlib.

  ZipFile provides a simple interface for the reading and
  writing of standard .zip archive files. This class is available
  only if the 'zip' option is added to the genua.pro project
  file.

  \ingroup io
  */
class ZipFile
{
public:

  /// undefined zipfile
  ZipFile() : m_ufile(0), m_rposition(0), m_wposition(0) {}

  /// close file if any
  ~ZipFile();

  /// open existing zip file, move to first file in archive
  bool openArchive(const std::string &archive);

  /// move to next file
  bool nextFile();

  /// retrieve name of current file in archive
  std::string currentFile();

  /// move to file named fname
  bool locateFile(const std::string &fname);

  /// open current file
  bool openCurrentFile();

  /// read data from current file
  int read(uint nbytes, char *buf);

  /// current uncompressed byte offset (reading)
  size_t readOffset() const {return m_rposition;}

  /// read n bytes (decompressed) from current file and discard
  uint skip(uint n);

  /// close current file
  bool closeCurrentFile();

  /// dump content of current file into stream
  size_t dumpFile(std::ostream &os);

  /// create new zip archive
  bool createArchive(const std::string &archive);

  /// begin a new file in currently created archive
  bool newFile(const std::string &fname, int level = -1);

  /// write data to file
  bool write(uint nbytes, const char *buf);

  /// current uncompressed byte offset (writing)
  size_t writeOffset() const {return m_wposition;}

  /// close current archive file
  bool closeFile();

  /// shortcut for the above three
  bool write(const std::string &fname, uint nbytes, const char *buf);

  /// close archive file
  bool closeArchive();

  /// test file header
  static bool isZip(const std::string &fname);

private:

  /// zlib file handle for unzipping
  unzFile m_ufile;

  /// zlib file handle for zipping
  zipFile m_zfile;

  /// uncompressed byte position pointer for reading
  size_t m_rposition;

  /// uncompressed byte position pointer for writing
  size_t m_wposition;
};

#endif
