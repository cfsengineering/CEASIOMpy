
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
#include "cgnsboco.h"

using namespace std;

void CgnsBoco::rename(const std::string & s)
{
  if (s.length() > 32)
    clog << "CGNS Warning: Boco name '" << s << "' will be truncated." << endl;
  
  int n = min( size_t(33), s.length()+1);
  memcpy(bname, s.c_str(), n);
}

void CgnsBoco::readInfo()
{
  int ierr, ndataset, NormalListFlag;
  cgns::DataType_t NormalDataType;
  ierr = cgns::cg_boco_info(fileindex, baseindex, zoneindex, bcindex, bname,
                            &bctype, &pstype, &npnts, 0, &NormalListFlag,
                            &NormalDataType, &ndataset);
  cgns_exception(ierr);
}

void CgnsBoco::readPoints(CgnsIntVector & elix)
{
  int ierr;
  elix.resize(npnts);
  ierr = cgns::cg_boco_read(fileindex, baseindex, zoneindex, bcindex, 
                            &elix[0], 0);
  cgns_exception(ierr);
}
    
void CgnsBoco::writePoints(CgnsIntVector & elix)
{
  int ierr;
  ierr = cgns::cg_boco_write(fileindex, baseindex, zoneindex, bname,
                             bctype, pstype, elix.size(), 
                             elix.pointer(), &bcindex );
  cgns_exception(ierr);
}





