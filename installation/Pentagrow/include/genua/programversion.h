
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
 
#ifndef GENUA_PROGRAMVERSION_H
#define GENUA_PROGRAMVERSION_H

#include <string>
#include <sstream> 

#define _UINT_VERSION(major, minor, patch) ((major<<16)|(minor<<8)|(patch))
#define _MAJOR_VERSION(v) ((v & 0x00ff0000)>>16)
#define _MINOR_VERSION(v) ((v & 0x0000ff00)>>8)
#define _PATCH_VERSION(v) ((v & 0x000000ff))

inline std::string version_string(int v)
{
  std::stringstream s;
  s << _MAJOR_VERSION(v) << "." << _MINOR_VERSION(v) << "." << _PATCH_VERSION(v);
  return s.str();
}

#endif


