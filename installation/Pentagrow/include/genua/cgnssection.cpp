
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
#include "xcept.h"
#include "cgnssection.h"

using namespace std;

void CgnsSection::rename(const std::string & s)
{
  if (s.length() > 32)
    clog << "CGNS Warning: Section name '" << s << "' will be truncated." << endl;
  
  int n = min( size_t(33), s.length()+1);
  memcpy(sname, s.c_str(), n);
}

void CgnsSection::readInfo()
{
  int ierr, start, end, nbndry;
  ierr = cgns::cg_section_read(fileindex, baseindex, zoneindex, sindex,
                         sname, &elmtype, &start, &end, &nbndry, &parentflag);
  cgns_exception(ierr);
  nelm = end - start + 1;
}

void CgnsSection::readElements(CgnsIntMatrix & ielm)
{
  int ierr, npe = nodesPerElement(elmtype);
  if (npe == 0) {
    string ename = cgns::cg_ElementTypeName(elmtype);
    throw Error("CgnsSection: Cannot handle element type ");
  }
  
  ielm.resize(npe, nelm);
  ierr = cgns::cg_elements_read(fileindex, baseindex, zoneindex, sindex, 
                                ielm.pointer(), &parentflag);
  cgns_exception(ierr);
}
    
void CgnsSection::writeElements(CgnsIntMatrix & ielm)
{
  int ierr, ne = ielm.ncols();
  ierr = cgns::cg_section_write(fileindex, baseindex, zoneindex, sname,
                                elmtype, eloff+1, eloff+ne, 0, 
                                ielm.pointer(), 
                                &sindex);
  cgns_exception(ierr);
  eloff += ne;
}

int CgnsSection::nodesPerElement(cgns::ElementType_t t)
{
  // typedef enum {
// 	ElementTypeNull, ElementTypeUserDefined,	/* 0, 1,	*/
// 	NODE, BAR_2, BAR_3, 				/* 2, 3, 4, 	*/
// 	TRI_3, TRI_6,					/* 5, 6,	*/
// 	QUAD_4, QUAD_8, QUAD_9,				/* 7, 8, 9,	*/
// 	TETRA_4, TETRA_10, 				/* 10, 11,	*/
// 	PYRA_5, PYRA_14, 				/* 12, 13,	*/
// 	PENTA_6, PENTA_15, PENTA_18,			/* 14, 15, 16,	*/
// 	HEXA_8, HEXA_20, HEXA_27, 			/* 17, 18, 19,	*/
// 	MIXED, NGON_n					/* 20, 21+	*/
// } ElementType_t;
  
  using namespace cgns;
  switch (t) {
    case NODE:
      return 1;
    case BAR_2:
      return 2;
    case BAR_3:
      return 3;
    case TRI_3:
      return 3;
    case TRI_6:
      return 6;
    case QUAD_4:
      return 4;
    case QUAD_8:
      return 8;
    case QUAD_9:
      return 9;
    case TETRA_4:
      return 4;
    case TETRA_10:
      return 10;
    case PYRA_5:
      return 5;
    case PYRA_14:
      return 14;
    case PENTA_6:
      return 6;
    case PENTA_15:
      return 15;
    case PENTA_18:
      return 18;
    case HEXA_8:
      return 8;
    case HEXA_20:
      return 20;
    case HEXA_27:
      return 27;
    default:
      return 0;
  }
}

