
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
 
#include <genua/ioglue.h>
#include <genua/xcept.h>
#include "igesentity.h"
#include "igesdirentry.h"
#include "igesfile.h"

using std::string;

bool IgesFile::isIges(const string &fname)
{
  ifstream in(asPath(fname).c_str(), std::ios::binary);
  if (not in)
    return false;

  IgesLine line;
  uint ns(0), ng(0), nd(0);
  do {
    line.erase();
    line.read(in);
    switch (line.section()) {
    case 'S':
      ++ns;
      break;
    case 'G':
      ++ng;
      break;
    case 'D':
      ++nd;
      break;
    default:
      return false;
    }

    if (ns > 0 and ng > 1 and nd >= 2)
      return true;

  } while (in);

  return false;
}

void IgesFile::dirEntry(uint de, IgesDirEntry & entry) const
{
  entry.invalidate();
  if (de < 1)
    return;

  dirSec.fillEntry(de-1, entry);
}

IgesEntityPtr IgesFile::createEntity(const IgesDirEntry & entry) const
{
  IgesEntityPtr ep;

  if (entry.valid()) {
    IgesEntity *entp = IgesEntity::create(entry);
    if (entp != 0 and entp->retrieve(*this))
      ep.reset(entp);
  }

  return ep;
}

IgesEntityPtr IgesFile::createEntity(uint de) const
{
  IgesDirEntry entry;
  dirEntry(de, entry);
  return createEntity(entry);
}

void IgesFile::write(const std::string & fname)
{
  ofstream os(fname, std::ios::binary);
  
  startSec.write(os);
  globalSec.assemble();
  globalSec.write(os);
  dirSec.write(os);
  parSec.write(os);
  
  // terminate section 
  IgesLine tline;
  tline.section('T');
  tline.number(1);
  tline.fixedNumber(0, startSec.nlines());
  tline.fixedNumber(1, globalSec.nlines());
  tline.fixedNumber(2, dirSec.nlines());
  tline.fixedNumber(3, parSec.nlines());
 
  char *s = tline.content();
  s[0] = 'S';
  s[8] = 'G';
  s[16] = 'D';
  s[24] = 'P';
  tline.write(os);
  
  os.close();
}

void IgesFile::read(const std::string & fname)
{
  ifstream in(asPath(fname).c_str(), std::ios::binary);
  if (not in)
    throw Error("Cannot open file: "+fname);

  // read all lines first
  IgesLine line;
  std::vector<IgesLine> lines;
  while (in) {
    line.read(in);
    lines.push_back(line);
  }

  // assign lines to sections
  uint next(0);
  next = startSec.parse(lines, next);
  next = globalSec.parse(lines, next);
  next = dirSec.parse(lines, next);
  next = parSec.parse(lines, next);
}




