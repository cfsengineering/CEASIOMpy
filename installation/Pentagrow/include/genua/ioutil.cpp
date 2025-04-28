
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

#include "ioutil.h"
#include <string>
#include <iostream>

using namespace std;

namespace detail {

size_t filesize(const std::string &fname)
{
  std::ifstream in(fname, std::ifstream::ate | std::ifstream::binary);
  return (in) ? size_t(in.tellg()) : size_t(0);
}

size_t file_as_string(const std::string &fname, std::string &contents)
{
  std::ifstream in(fname, std::ios::in | std::ios::binary);
  if (in) {
    contents.clear();
    in.seekg(0, std::ios::end);
    contents.resize(in.tellg());
    in.seekg(0, std::ios::beg);
    in.read(&contents[0], contents.size());
    in.close();
    return contents.size();
  } else {
    return 0;
  }
}

std::string file_as_string(const std::string &fname)
{
  std::string contents;
  file_as_string(fname, contents);
  return contents;
}

} // detail

LogRedirector::LogRedirector(const std::string &fname)
{
  m_logf.open(fname);
  m_rdbuf = clog.rdbuf();
  clog.rdbuf( m_logf.rdbuf() );
}

LogRedirector::~LogRedirector()
{
  m_logf.flush();
  clog.rdbuf( m_rdbuf );
  m_logf.close();
}
