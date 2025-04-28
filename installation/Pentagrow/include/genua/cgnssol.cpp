
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
#include "cgnsfwd.h"
#include "cgnssol.h"

using namespace std;

void CgnsSol::readInfo()
{
  int ierr;
  ierr = cgns::cg_sol_info(fileindex, baseindex, zoneindex, solindex,
                           name, &loc);
  cgns_exception(ierr);
}

int CgnsSol::nfields()
{
  int ierr, nf(0);
  ierr = cgns::cg_nfields(fileindex, baseindex, zoneindex, solindex, &nf);
  cgns_exception(ierr);
  return nf;
}

void CgnsSol::fieldInfo(int i, std::string & fname, cgns::DataType_t & dtype)
{
  assert(i > 0);
  assert(i <= nfields());
  char fieldname[33];
  int ierr;
  memset(fieldname, 0, sizeof(fieldname));
  ierr = cgns::cg_field_info(fileindex, baseindex, zoneindex, solindex, i,
                             &dtype, fieldname);
  cgns_exception(ierr);

  fname = fieldname;
}

void CgnsSol::readField(const char *field, int & imin, int & imax, double a[])
{
  int ierr;
  char fieldname[33];
  memset(fieldname, 0, sizeof(fieldname));
  memcpy(fieldname, field, std::min(size_t(32), strlen(field)));
  ierr = cgns::cg_field_read(fileindex, baseindex, zoneindex, solindex, fieldname,
                             cgns::RealDouble, &imin, &imax, (void *) a);
  cgns_exception(ierr);
}

void CgnsSol::readField(const char *field, int & imin, int & imax, int a[])
{
  int ierr;
  char fieldname[33];
  memset(fieldname, 0, sizeof(fieldname));
  memcpy(fieldname, field, std::min(size_t(32), strlen(field)));
  ierr = cgns::cg_field_read(fileindex, baseindex, zoneindex, solindex, fieldname,
                             cgns::Integer, &imin, &imax, (void *) a);
  cgns_exception(ierr);
}

int CgnsSol::writeField(const std::string & fname, const double a[],
                        cgns::DataType_t dtype)
{
  // setup name field 
  char fieldname[33];
  memset(fieldname, 0, sizeof(fieldname));
  if (fname.length() > 32)
    clog << "CGNS Warning: Field name '" << fname << "' will be truncated." << endl;
  
  int n = min(size_t(32), fname.length()+1);
  memcpy(fieldname, fname.c_str(), n);
  
  // write field 
  int ierr, field(0);
  ierr = cgns::cg_field_write(fileindex, baseindex, zoneindex, solindex,
                              dtype, fieldname, (void *) a, &field);
  cgns_exception(ierr);
  
  return field;
}

int CgnsSol::writeField(const std::string & fname, const float a[],
                        cgns::DataType_t dtype)
{
  // setup name field 
  char fieldname[33];
  memset(fieldname, 0, sizeof(fieldname));
  if (fname.length() > 32)
    clog << "CGNS Warning: Field name '" << fname << "' will be truncated." << endl;
  
  int n = min(size_t(32), fname.length()+1);
  memcpy(fieldname, fname.c_str(), n);
  
  // write field 
  int ierr, field(0);
  ierr = cgns::cg_field_write(fileindex, baseindex, zoneindex, solindex,
                              dtype, fieldname, (void *) a, &field);
  cgns_exception(ierr);
  
  return field;
}

int CgnsSol::writeField(const std::string & fname, const int a[])
{
  // setup name field 
  char fieldname[33];
  memset(fieldname, 0, sizeof(fieldname));
  if (fname.length() > 32)
    clog << "CGNS Warning: Field name '" << fname << "' will be truncated." << endl;
  
  int n = min(size_t(32), fname.length()+1);
  memcpy(fieldname, fname.c_str(), n);
  
  // write field 
  int ierr, field(0);
  ierr = cgns::cg_field_write(fileindex, baseindex, zoneindex, solindex,
                              cgns::Integer, fieldname, (void *) a, &field);
  cgns_exception(ierr);
  
  return field;
}
