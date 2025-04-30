
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
 
#include "xcept.h"
#include "cgnsfile.h"
#include "cgnsfwd.h"

using namespace std;
using cgns::cg_is_cgns;
using cgns::cg_open;
using cgns::cg_close;
using cgns::cg_get_error;
using cgns::cg_base_write;
using cgns::cg_nbases;
using cgns::cg_base_read;
using cgns::cg_zone_write;
using cgns::cg_nzones;
using cgns::cg_zone_read;
using cgns::cg_ncoords;
using cgns::cg_coord_write;
using cgns::cg_coord_read;
using cgns::cg_section_read;
using cgns::cg_section_write;
using cgns::cg_elements_read;
using cgns::cg_nsections;
using cgns::cg_boco_info;
using cgns::cg_boco_read;
using cgns::cg_boco_write;

CgnsFile::CgnsFile() : fileindex(CG_NO_INDEX), baseindex(CG_NO_INDEX), eloff(0)
{
  basename = "Base1";
}

CgnsFile::~CgnsFile()
{
  if (fileindex != CG_NO_INDEX)
    cg_close(fileindex);
}

bool CgnsFile::isCgns(const std::string & s)
{
  return (cg_is_cgns(s.c_str()) == 0);
}

void CgnsFile::wopen(const std::string & fname)
{
  int ierr;
  ierr = cg_open(fname.c_str(), CG_MODE_WRITE, &fileindex);
  cgns_exception(ierr);
  
  ierr = cg_base_write(fileindex, basename.c_str(), 3, 3, &baseindex);
  cgns_exception(ierr);
}

void CgnsFile::ropen(const std::string & fname, int ibase)
{
  int ierr;
  ierr = cg_open(fname.c_str(), CG_MODE_READ, &fileindex);
  cgns_exception(ierr);

  int nbase(0);
  ierr = cg_nbases(fileindex, &nbase);
  cgns_exception(ierr);
  if (ibase > nbase)
    throw Error("CgnsFile: No such base index.");

  baseindex = ibase;
  char bname[33];
  int cell_dim(0), phys_dim(0);
  ierr = cg_base_read(fileindex, baseindex, bname, &cell_dim, &phys_dim);
  basename = bname;
  cgns_exception(ierr);
}

int CgnsFile::nzones() const
{
  int ierr, nzone;
  ierr = cg_nzones(fileindex, baseindex, &nzone);
  cgns_exception(ierr);
  return nzone;
}

std::string CgnsFile::readZone(int izone, int & nvertex, int & ncell, int & nbndv)
{
  int ierr;
  char zname[33];
  cgns::ZoneType_t zonetype;
  ierr = cg_zone_type(fileindex, baseindex, izone, &zonetype);
  cgns_exception(ierr);

  if (zonetype != cgns::Unstructured)
    throw Error("CgnsFile: Not an unstructured zone: "+str(izone));
    
  int isize[3];
  ierr = cg_zone_read(fileindex, baseindex, izone, zname, isize);
  cgns_exception(ierr);
  nvertex = isize[0];
  ncell = isize[1];
  nbndv = isize[2];
  return string(zname);
}

CgnsZone CgnsFile::newZone(const std::string & name, int nvertex, int ncell)
{
  int size[3];
  size[0] = nvertex;
  size[1] = ncell;
  size[2] = 0;
  
  string zname;
  if (name.size() > 32)
    zname = name.substr(0, 32);
  else
    zname = name;
  
  int ierr, zoneindex;
  ierr = cg_zone_write(fileindex, baseindex, zname.c_str(), 
                       size, cgns::Unstructured, &zoneindex);
  cgns_exception(ierr);
  
  eloff = 0;
 
  return CgnsZone(fileindex, baseindex, zoneindex);
}

int CgnsFile::uzone(const std::string & name, int nvertex, int ncell)
{
  int size[3];
  size[0] = nvertex;
  size[1] = ncell;
  size[2] = 0;
  
  string zname;
  if (name.size() > 32)
    zname = name.substr(0, 32);
  else
    zname = name;
  
  int ierr, zoneindex;
  ierr = cg_zone_write(fileindex, baseindex, zname.c_str(), 
                       size, cgns::Unstructured, &zoneindex);
  cgns_exception(ierr);
  
  eloff = 0;
  return zoneindex;
}

void CgnsFile::readNodes(int zix, int np, PointList<3> & pts)
{
  int ierr, rmin[3], rmax[3];
  for (int k=0; k<3; ++k) {
    rmin[k] = 1;
    rmax[k] = np;
  }
  
  Vector x(np), y(np), z(np);
  ierr = cg_coord_read(fileindex, baseindex, zix, "CoordinateX", 
                       cgns::RealDouble, rmin, rmax, &x[0]);
  cgns_exception(ierr);
  ierr = cg_coord_read(fileindex, baseindex, zix, "CoordinateY", 
                       cgns::RealDouble, rmin, rmax, &y[0]);
  cgns_exception(ierr);
  ierr = cg_coord_read(fileindex, baseindex, zix, "CoordinateZ", 
                       cgns::RealDouble, rmin, rmax, &z[0]);
  cgns_exception(ierr);

  pts.resize(np);
  for (int i=0; i<np; ++i) {
    pts[i][0] = x[i];
    pts[i][1] = y[i];
    pts[i][2] = z[i];
  }
}

void CgnsFile::writeNodes(int zix, const PointList<3> & pts)
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
  ierr = cg_coord_write(fileindex, baseindex, zix, cgns::RealDouble, 
                        "CoordinateX", x.pointer(), &icoord); 
  cgns_exception(ierr);
  ierr = cg_coord_write(fileindex, baseindex, zix, cgns::RealDouble, 
                        "CoordinateY", y.pointer(), &icoord); 
  cgns_exception(ierr);
  ierr = cg_coord_write(fileindex, baseindex, zix, cgns::RealDouble, 
                        "CoordinateZ", z.pointer(), &icoord); 
  cgns_exception(ierr);
}

int CgnsFile::nsections(int zix) const
{
  int ierr, ns;
  ierr = cg_nsections(fileindex, baseindex, zix, &ns);
  cgns_exception(ierr);
  return ns;
}

int CgnsFile::nbocos(int zix) const
{
  int ierr, nb;
  ierr = cgns::cg_nbocos(fileindex, baseindex, zix, &nb);
  cgns_exception(ierr);
  return nb;
}

std::string CgnsFile::readSection(int zix, int isec, int & elmType, 
                                  IndexMatrix & ielm)
{
  char sname[33];
  int ierr, parentflag, start, end, nbndry;
  cgns::ElementType_t etype;
  
  ierr = cg_section_read(fileindex, baseindex, zix, isec,
                         sname, &etype, &start, &end, &nbndry, &parentflag);
  cgns_exception(ierr);
  
  elmType = (int) etype;
  int ne = end - start + 1;
  switch (etype) {
    case cgns::TETRA_4:
      ielm.resize(4,ne);
      break;
    case cgns::TRI_3:
      ielm.resize(3,ne);
      break;
    default:
      throw Error("CgnsFile::readSection Unsupported element type.");
  }
  
  ierr = cg_elements_read(fileindex, baseindex, zix, isec, 
                          ielm.pointer(), &parentflag);
  cgns_exception(ierr);
  
  return string(sname);
}

int CgnsFile::writeTets(int zix, const std::string & name, 
                        const IndexMatrix & ielem)
{
  const int ne = ielem.ncols();
  int ierr, elmindex;
  
  string zname;
  if (name.size() > 32)
    zname = name.substr(0, 32);
  else
    zname = name;
  
  ierr = cg_section_write(fileindex, baseindex, zix, zname.c_str(),
                          cgns::TETRA_4, eloff+1, eloff+ne, 0, ielem.pointer(), 
                          &elmindex);
  cgns_exception(ierr);
  eloff += ne;
  return elmindex;
}

int CgnsFile::writeTriBoundary(int zix, const std::string & name, 
                            const IndexMatrix & ielem)
{
  const int ne = ielem.ncols();
  int ierr, elmindex;
  
  string zname;
  if (name.size() > 32)
    zname = name.substr(0, 32);
  else
    zname = name;
  
  ierr = cg_section_write(fileindex, baseindex, zix, zname.c_str(),
                          cgns::TRI_3, eloff+1, eloff+ne, 0, ielem.pointer(), 
                          &elmindex);
  cgns_exception(ierr);
  eloff += ne;
  return elmindex;
}

std::string CgnsFile::readBoundaryCondition(int zix, int ibc, IndexVector & elix,
                                            int & boco)
{
  char bcname[33];
  int ierr, npnts, ndataset, NormalListFlag;
  cgns::BCType_t bocotype;
  cgns::PointSetType_t ptsettype;
  cgns::DataType_t NormalDataType;
  
  ierr = cg_boco_info(fileindex, baseindex, zix, ibc, bcname,
                      &bocotype, &ptsettype, 
                      &npnts, 0, &NormalListFlag,
                      &NormalDataType, &ndataset);
  cgns_exception(ierr);
  
  boco = (int) bocotype;
  elix.resize(npnts);
  ierr = cg_boco_read(fileindex, baseindex, zix, ibc, &elix[0], 0);
  cgns_exception(ierr);
  
  return string(bcname);
}

int CgnsFile::writeBoundaryCondition(int zix, const std::string & name, 
                                     const IndexVector & elix, int boco)
{
  int ierr, bcindex;
  if (boco == -1)
    boco = cgns::BCGeneral;
  
  if (boco < 0 or boco >= NofValidBCTypes)
    throw Error("Invalid CGNS boundary condition specification.");
  
  string zname;
  if (name.size() > 32)
    zname = name.substr(0, 32);
  else
    zname = name;
  
  ierr = cg_boco_write(fileindex, baseindex, zix, zname.c_str(),
                       (cgns::BCType_t) boco, cgns::ElementList, 
                       elix.size(), elix.pointer(), &bcindex );
  cgns_exception(ierr);
  return bcindex;
}

// ---------------------------------------------------------------------------

void cgns_exception(int ierr)
{
  if (ierr != 0) {
    const char *msg = cg_get_error();
#ifndef NDEBUG
    cerr << msg;
    abort();
#else
    throw Error(msg);
#endif
  }
}
