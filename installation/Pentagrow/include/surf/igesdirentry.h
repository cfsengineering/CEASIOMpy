
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

#ifndef SURF_IGESDIRENTRY_H
#define SURF_IGESDIRENTRY_H

#include <cstring>
#include <string>

/** Data in each directory entry of an IGES file. 
 *
 * Each geometry object creates one or more IGES entities, each of which owns
 * a directory entry (an object of this class) and a block of parameter data
 * (IgesEntity). The directory entry is in some sense a fixed-size entry in the
 * table of contents at the top of an IGES file.
 *
 * \ingroup interop
 * \sa IgesFile, IgesEntity
  */
struct IgesDirEntry
{
public:

  /// create entry with defaulted values where possible
  IgesDirEntry() : strct(0), lpattern(0), level(1), view(0), trafm(0),
    lbdisp(0), blank(0), subswitch(0), useflag(0),
    hierarchy(1), lweight(0), color(0), plines(0), form(0),
    esubscript(0) { memset(elabel, ' ', sizeof(elabel)); }

  /// check if entry is defined at all
  bool valid() const {return (plines != 0);}

  /// make invalid
  void invalidate() {plines = 0;}

  /// return label as std::string
  std::string label() const {
    std::string s;
    s.assign(elabel, elabel+8);
    return s;
  }

  /// entity label
  char elabel[8];

  /// integer directory entries
  int etype, pdata, strct, lpattern, level, view, trafm, lbdisp;
  int blank, subswitch, useflag, hierarchy, lweight, color, plines;
  int form, esubscript;
};

#endif
