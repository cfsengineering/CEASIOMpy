
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
 
#ifndef SURF_NSTELEMENTSTRESS_H
#define SURF_NSTELEMENTSTRESS_H

#include "forward.h"
#include <boost/regex.hpp>
#include <cstring>

/** Nastran element stress record.
 *
 * This class is used by NstReader to extract stress data from PUNCH files. It
 * contains data for a single record, i.e. one lamina of a single element.
 *
 * \ingroup structures
 * \sa NstStressField, NstReader, NstRecord, NstMesh
 */
class NstElementStressRecord
{
private:

  enum { MaxComp = 32 };

public:

  /// element class
  enum Class { Unknown, LinearShell, CompositeShell, Solid };

  /// setup to process stress items of a certain code
  void compile(uint icode);

  /// reset to starting condition, return whether reading item code is supported
  bool setup(uint icode) {
    const uint supported[] = {33, 67, 68, 74, 95, 96, 97,
                              227, 228, 232, 233, 255};
    const uint ncodes = sizeof(supported) / sizeof(supported[0]);
    itemCode = icode;
    eid = 0;
    laminateIndex = 1;
    gid = 0;
    stage = 0;
    ipoint = 0;
    npoints = 0;
    memset(sigma, 0, sizeof(sigma));
    return std::binary_search(supported, supported+ncodes, icode);
  }

  /// fetch data from next line, return state 0 if set complete
  uint process(const std::string &ln);

  /// return element class identifier
  static int elementClass(uint ic) {
    if (isLinearShell(ic))
      return LinearShell;
    else if (isCompositeShell(ic))
      return CompositeShell;
    else if (isSolid(ic))
      return Solid;
    return Unknown;
  }

  /// type characterization
  static bool isLinearShell(uint ic) {
    const uint codes[] = {33,74,227,228};
    const uint *end = codes + sizeof(codes)/sizeof(codes[0]);
    return std::find(codes, end, ic) != end;
  }

  /// type characterization
  static bool isCompositeShell(uint ic) {
    const uint codes[] = {95,96,97,232,233};
    const uint *end = codes + sizeof(codes)/sizeof(codes[0]);
    return std::find(codes, end, ic) != end;
  }

  /// type characterization
  static bool isShell(uint ic) {
    return isLinearShell(ic) or isCompositeShell(ic);
  }

  /// type characterization
  static bool isSolid(uint ic) {
    const uint codes[] = {39,67,68,255};
    const uint *end = codes + sizeof(codes)/sizeof(codes[0]);
    return std::find(codes, end, ic) != end;
  }

  /// stress components
  float sigma[MaxComp];

  /// item code identifies type of stress data recovered
  uint itemCode;

  /// element id
  uint eid;

  /// ply identifier for composite elements
  uint laminateIndex;

  /// node gid for solid elements
  uint gid;

private:

  /// fetch data from next line, return state 0 if set complete
  uint process33(const std::string &ln);

  /// fetch data from next line, return state 0 if set complete
  uint process95(const std::string &ln);

  /// fetch data from next line, return state 0 if set complete
  uint process67(const std::string &ln);

private:

  /// internal state counter
  uint stage;

  /// number of points to expect (CHEXA)
  uint npoints, ipoint;

  /// regular expressions to use
  boost::regex pattern[8];

  /// regex matches
  boost::smatch matches;
};

#endif // NSTELEMENTSTRESS_H
