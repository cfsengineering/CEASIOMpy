
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
 
#include <iostream>
#include "cgnsfile.h"
#include "cgnsdescriptor.h"
#include "cgnsfwd.h"

using cgns::cg_ndescriptors;
using cgns::cg_descriptor_read;
using cgns::cg_descriptor_write;
using cgns::cg_gopath;
using cgns::cg_free;

using namespace std;

uint CgnsDescriptor::nnodes(int fn, const std::string & path) const
{
  int ierr, ndescriptors(0);
  string p(path); // cgns API does not 'const' correctly
  ierr = cg_gopath(fn, p.c_str());
  if (ierr != 0)
    return 0;
  ierr = cg_ndescriptors(&ndescriptors);
  cgns_exception(ierr);
  return ndescriptors;
}

void CgnsDescriptor::read(int d)
{
  int ierr;
  char *ptr;
  ierr = cg_descriptor_read(d, dname, &ptr);
  cgns_exception(ierr);
  if (ptr != 0) {
    txt = ptr;
    cg_free(ptr);
  }
}

void CgnsDescriptor::write(int fn, const std::string & path)
{
  int ierr;
  string p(path); // cgns API does not 'const' correctly
  ierr = cg_gopath(fn, p.c_str());
  cgns_exception(ierr);
  ierr = cg_descriptor_write(dname, txt.c_str());
  cgns_exception(ierr);
}

void CgnsDescriptor::rename(const std::string & s)
{
  if (s.length() > 32)
    clog << "Warning: UserDate name '" << s << "' will be truncated." << endl;
  
  int n = min( size_t(33), s.length()+1);
  memcpy(dname, s.c_str(), n);
}

