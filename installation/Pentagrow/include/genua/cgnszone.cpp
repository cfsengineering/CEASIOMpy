
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
#include "cgnszone.h"
#include "cgnsfwd.h"

using namespace std;

void CgnsZone::rename(const std::string & s)
{
  if (s.length() > 32)
    clog << "Warning: Zone name '" << s << "' will be truncated." << endl;
  
  int n = min( size_t(33), s.length()+1);
  memcpy(zname, s.c_str(), n);
}

int CgnsZone::nsections() const
{
  int ierr, ns;
  ierr = cgns::cg_nsections(fileindex, baseindex, zoneindex, &ns);
  cgns_exception(ierr);
  return ns;
}
    
int CgnsZone::nbocos() const
{
  int ierr, nb;
  ierr = cgns::cg_nbocos(fileindex, baseindex, zoneindex, &nb);
  cgns_exception(ierr);
  return nb;
}

int CgnsZone::nsols() const
{
  int ierr, nb;
  ierr = cgns::cg_nsols(fileindex, baseindex, zoneindex, &nb);
  cgns_exception(ierr);
  return nb;
}

void CgnsZone::readNodes(PointList<3> & pts)
{
  int ierr;
  cgns::ZoneType_t zonetype;
  ierr = cgns::cg_zone_type(fileindex, baseindex, zoneindex, &zonetype);
  cgns_exception(ierr);

  if (zonetype != cgns::Unstructured)
    throw Error("CgnsZone: Not an unstructured zone: "+str(zoneindex));
    
  int np, isize[3];
  ierr = cgns::cg_zone_read(fileindex, baseindex, zoneindex, zname, isize);
  cgns_exception(ierr);
  
  np = isize[0];
  int rmin[3], rmax[3];
  for (int k=0; k<3; ++k) {
    rmin[k] = 1;
    rmax[k] = np;
  }
  
  Vector x(np), y(np), z(np);
  ierr = cgns::cg_coord_read(fileindex, baseindex, zoneindex, "CoordinateX", 
                       cgns::RealDouble, rmin, rmax, &x[0]);
  cgns_exception(ierr);
  ierr = cgns::cg_coord_read(fileindex, baseindex, zoneindex, "CoordinateY", 
                       cgns::RealDouble, rmin, rmax, &y[0]);
  cgns_exception(ierr);
  ierr = cgns::cg_coord_read(fileindex, baseindex, zoneindex, "CoordinateZ", 
                       cgns::RealDouble, rmin, rmax, &z[0]);
  cgns_exception(ierr);

  pts.resize(np);
  for (int i=0; i<np; ++i) {
    pts[i][0] = x[i];
    pts[i][1] = y[i];
    pts[i][2] = z[i];
  }
}

void CgnsZone::writeNodes(const PointList<3> & pts)
{
  // convert to separate arrays 
  const int np(pts.size());
  Vector x(np), y(np), z(np);
  for (int i=0; i<np; ++i) {
    x[i] = pts[i][0];
    y[i] = pts[i][1];
    z[i] = pts[i][2];
  }
  
  int ierr, icoord;
  ierr = cgns::cg_coord_write(fileindex, baseindex, zoneindex, cgns::RealDouble, 
                        "CoordinateX", x.pointer(), &icoord); 
  cgns_exception(ierr);
  ierr = cgns::cg_coord_write(fileindex, baseindex, zoneindex, cgns::RealDouble, 
                        "CoordinateY", y.pointer(), &icoord); 
  cgns_exception(ierr);
  ierr = cgns::cg_coord_write(fileindex, baseindex, zoneindex, cgns::RealDouble, 
                        "CoordinateZ", z.pointer(), &icoord); 
  cgns_exception(ierr);
}

CgnsSol CgnsZone::newSolution(const std::string & s, cgns::GridLocation_t loc)
{
  char sname[33];
  memset(sname, 0, sizeof(sname));
  if (s.length() > 32)
    clog << "Warning: Solution name '" << s << "' will be truncated." << endl;
  
  int n = min(size_t(32), s.length()+1);
  memcpy(sname, s.c_str(), n);
  
  int ierr, solindex(0);
  ierr = cgns::cg_sol_write(fileindex, baseindex, zoneindex, sname,
                            loc, &solindex);
  cgns_exception(ierr);
  
  return CgnsSol(fileindex, baseindex, zoneindex, solindex);
}

CgnsSection CgnsZone::readSection(int i)
{
  assert(i > 0);
  CgnsSection s(fileindex, baseindex, zoneindex, i);
  s.readInfo();
  return s;
}

CgnsBoco CgnsZone::readBoco(int i)
{
  assert(i > 0);
  CgnsBoco s(fileindex, baseindex, zoneindex, i);
  s.readInfo();
  return s;
}

CgnsSol CgnsZone::readSol(int i)
{
  assert(i > 0);
  CgnsSol s(fileindex, baseindex, zoneindex, i);
  s.readInfo();
  return s;
}
    
    
