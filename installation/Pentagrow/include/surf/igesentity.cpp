
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
 
#include "igesentity.h"
#include "igesfile.h"
#include "iges100.h"
#include "iges102.h"
#include "iges108.h"
#include "iges110.h"
#include "iges116.h"
#include "iges118.h"
#include "iges120.h"
#include "iges124.h"
#include "iges126.h"
#include "iges128.h"
#include "iges142.h"
#include "iges144.h"
#include "iges308.h"
#include "iges314.h"
#include "iges402.h"
#include "iges406.h"
#include "iges408.h"
#include <genua/xcept.h>

using namespace std;

void IgesEntity::label(const char *s)
{
  size_t nc = std::min(size_t(8), strlen(s));
  memcpy(entry.elabel, s, nc);
}

int IgesEntity::append(IgesFile & igfile)
{
  IgesDirectorySection & dir(igfile.directory());
  IgesParameterSection & par(igfile.parameters());
  
  // store current line count and add mandatory type parameter 
  plcpre = par.nlines();
  par.addIntParameter( entry.etype );
  
  // add type-specific parameters 
  definition(igfile);
  
  // additional properties 
  const int np1 = addprop1.size();
  const int np2 = addprop2.size();
  if (np1 != 0 or np2 != 0) {
    par.addIntParameter( np1 );
    for (int i=0; i<np1; ++i)
      par.addIntParameter( addprop1[i] );
    par.addIntParameter( np2 );
    for (int i=0; i<np2; ++i)
      par.addIntParameter( addprop2[i] );
  }
  
  // conclude parameter data 
  par.endRecord();
  par.flush(64);
  plcpost = par.nlines();

  // connect parameter datasets to directory entry
  int dirno = dir.nlines() + 1;
  for (int i=plcpre; i<plcpost; ++i) 
    par.content( i ).fixedNumber( 8, dirno );
  
  entry.pdata = plcpre + 1;
  entry.plines = plcpost - plcpre;
  return dir.addEntry( entry ) + 1;
}

bool IgesEntity::retrieve(const IgesFile & igfile)
{
  if (not entry.valid())
    return false;

  const IgesParameterSection & par(igfile.parameters());
  uint lbegin = entry.pdata - 1;
  uint lend = lbegin + entry.plines;
  if (lend > par.nlines())
    return false;

  string pds;
  for (uint i=lbegin; i<lend; ++i) {
    const char *ln = par.content(i).content();
    pds.insert(pds.end(), ln, ln+64);
  }

  // mark parameter value locations
  Indices vpos;
  vpos.push_back(0);
  const char *s = pds.c_str();
  const char *next;
  do {
    next = strchr(s+vpos.back(), par.parameterDelimiter());
    if (next != 0)
      vpos.push_back(next-s+1);
  } while (next != 0);

  // drop first index : entity id
  vpos.erase(vpos.begin());

  uint nused = parse(pds, vpos);
  if (nused == 0)
    return false;

  uint off = nused;
  addprop1.clear();
  addprop2.clear();
  if (vpos.size() > nused+1) {
    int n1 = asInt(s, vpos[off]);
    addprop1.resize(n1);
    ++off;
    for (int i=0; i<n1; ++i)
      addprop1[i] = asInt(s, vpos[off+i]);
    off += n1;
    if (off+1 < vpos.size()) {
      int n2 = asInt(s, vpos[off]);
      ++off;
      addprop2.resize(n2);
      for (int i=0; i<n2; ++i)
        addprop2[i] = asInt(s, vpos[off+i]);
    }
  }

  return true;
}

uint IgesEntity::parse(const std::string &, const Indices &)
{
  // some entities do not define parse() yet, these simply return false
  return 0;
}

IgesEntity *IgesEntity::create(const IgesDirEntry & e)
{
  IgesEntity *ep = 0;
  switch (e.etype) {
  case 100:
    ep = new IgesCircularArc();
    ep->entry = e;
    break;
  case 102:
    ep = new IgesCompositeCurve();
    ep->entry = e;
    break;
  case 108:
    ep = new IgesPlane();
    ep->entry = e;
    break;
  case 110:
    ep = new IgesLineEntity();
    ep->entry = e;
    break;
  case 116:
    ep = new IgesPoint();
    ep->entry = e;
    break;
  case 118:
    ep = new IgesRuledSurface();
    ep->entry = e;
    break;
  case 120:
    ep = new IgesRevolutionSurface();
    ep->entry = e;
    break;
  case 124:
    ep = new IgesTrafoMatrix();
    ep->entry = e;
    break;
  case 126:
    ep = new IgesSplineCurve();
    ep->entry = e;
    break;
  case 128:
    ep = new IgesSplineSurface();
    ep->entry = e;
    break;
  case 142:
    ep = new IgesCurveOnSurface();
    ep->entry = e;
    break;
  case 144:
    ep = new IgesTrimmedSurface();
    ep->entry = e;
    break;
  case 308:
    ep = new IgesSubfigure();
    ep->entry = e;
    break;
  case 314:
    ep = new IgesColorDefinition();
    ep->entry = e;
    break;
  case 402:
    ep = new IgesAssociativity();
    ep->entry = e;
    break;
  case 406:
    ep = new IgesNameProperty();
    ep->entry = e;
    break;
  case 408:
    ep = new IgesSingularSubfigure();
    ep->entry = e;
    break;
  }
  return ep;
}

//// -------------- IGES entity 402  : associativity --------------------------

//void IgesGroupAssoc::definition(IgesFile & igfile)
//{
//  IgesParameterSection & par(igfile.parameters());
  
//  const int n = mptr.size();
//  par.addIntParameter(n);
//  for (int i=0; i<n; ++i)
//    par.addIntParameter( mptr[i] );
//}


