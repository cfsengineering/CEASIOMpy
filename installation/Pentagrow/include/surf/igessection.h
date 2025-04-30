
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

#ifndef SURF_IGESSECTION_H
#define SURF_IGESSECTION_H

#include <iostream>
#include <vector>
#include <sstream>

#include <genua/strutils.h>
#include "igesline.h"

struct IgesDirEntry;

/** Section of IGES file.

  Base class which contains the actual data and handles writing to file.

  \ingroup interop
  \sa IgesFile
*/
class IgesSection
{
public:

  typedef enum {IgesStart, IgesGlobal, IgesDirectory,
                IgesParameter, IgesTerminate} SecType;

  /// create an undefined section
  IgesSection() : sectionChar('U') {}

  /// create a defined section
  IgesSection(SecType t) : parDelim(','), recDelim(';') {changeType(t);}

  /// virtual destructor
  virtual ~IgesSection() {}

  /// number of lines in this section
  uint nlines() const {return lines.size();}

  /// access parameter delimiter
  char parameterDelimiter() const {return parDelim;}

  /// access record delimiter
  char recordDelimiter() const {return recDelim;}

  /// set/change section type
  void changeType(SecType t);

  /// add a line to section and set its number
  int addLine(const IgesLine & il) {
    assert(sectionChar != 'U');
    lines.push_back(il);
    lines.back().number(lines.size());
    lines.back().section(sectionChar);
    return lines.size() - 1;
  }

  /// access line at i
  const IgesLine & content(uint i) const {
    assert(i < nlines());
    return lines[i];
  }

  /// access line at i
  IgesLine & content(uint i) {
    assert(i < nlines());
    return lines[i];
  }

  /// add a single character parameter
  void addCharParameter(char c) {
    sbuf << "1H" << c << parDelim;
  }

  /// a string parameter
  void addParameter(const std::string & s) {
    sbuf << s.size() << 'H' << s << parDelim;
  }

  /// an integer parameter
  void addIntParameter(int v) {
    sbuf << v << parDelim;
  }

  /// a floating-point parameter
  void addFloatParameter(double v) {
    sbuf << std::scientific;
    sbuf << v << parDelim;
  }

  /// add a vector of floating-point values
  void addParameter(int n, const double v[], int prec=13) {
    sbuf.precision(prec);
    sbuf << std::scientific;
    for (int i=0; i<n; ++i)
      sbuf << v[i] << parDelim;
  }

  /// end a record and flush to lines
  void endRecord() {
    sbuf.seekp(-1, std::ios::cur);
    sbuf << recDelim;
  }

  /// flush the current string buffer into lines
  void flush(int nuse = 72);

  /// write lines
  void write(std::ostream & os) const;

  /// fetch lines for this section from global line set, return next index
  virtual uint parse(const IgesLineArray & file, uint first);

  /// clear content lines
  void clear() {lines.clear();}

protected:

  /// lines to write (actual content)
  IgesLineArray lines;

  /// section type
  SecType type;

  /// section identification character
  char sectionChar, parDelim, recDelim;

  /// buffer used to assemble free-format lines
  std::stringstream sbuf;
};

/** Start section of an IGES file.

  The start section contains nothing but a human-readable comment.

  */
class IgesStartSection : public IgesSection
{ 
public:

  /// creates mandatory minimal start section (single blank line)
  IgesStartSection();

  /// add readable string content to start section
  void setContent(const std::string & s);
};

/** Global section of an IGES file.
  
  The global sections contains data such as the product name, the name
  of the geometry system/IGES preprocessor, scale and tolerance values and
  line drawing specifications.

*/
class IgesGlobalSection : public IgesSection
{
public:

  /// create global section with default values
  IgesGlobalSection();

  /// set product name
  void productName(const std::string & s) {
    sndrproduct = recvproduct = s;
  }

  /// set file name stored in global section
  void fileName(const std::string & s) {
    filename = s;
  }

  /// access current model tolerance
  double modelTolerance() const {return modeltol;}

  /// change model tolerance setting
  void modelTolerance(double tol) {modeltol = tol;}

  /// set preprocessor name and version
  void preprocessorVersion(const std::string & s) {ppversion = s;}

  /// set native system name
  void nativeSystem(const std::string & s) {natsys = s;}

  /// assemble parameters into lines
  void assemble();

  /// read content, as far as understood
  uint parse(const IgesLineArray & file, uint first);

public:

  /// string parameter
  std::string sndrproduct, filename, natsys, ppversion;
  std::string recvproduct, unitnames, author, organiz;

  /// float parameters
  double scale, maxlinewidth, modeltol, maxcoord;

  /// integer parameters
  int unitflag, nlwgrad;
};

/** Directory section of the IGES file 
  */
class IgesDirectorySection : public IgesSection
{
public:

  /// create empty directory section
  IgesDirectorySection() : IgesSection( IgesDirectory ) {}

  /// add a directory entry, return index
  uint addEntry(const IgesDirEntry & e);

  /// fill directory entry strating from line k
  void fillEntry(uint iline, IgesDirEntry & e) const;

  /// change existing directory entry, return false if that doesn't exist
  bool changeEntry(uint idx, const IgesDirEntry & e);
};

/** Parameter section of an IGES file

  
*/
class IgesParameterSection : public IgesSection
{
public:

  /// create an empty parameter section
  IgesParameterSection() : IgesSection( IgesParameter ) {}

};

inline void toHollerith(const std::string & s, std::string & hs)
{
  std::string st = strip(s);
  std::stringstream ss;
  ss << st.length() << "H" << st;
  hs = ss.str();
}

inline void fromHollerith(const std::string & hs, std::string & s)
{
  const char *cstr = hs.c_str();
  const char *hpos = strchr(cstr, 'H');
  if (hpos == 0)
    return;

  std::string::size_type p1 = hpos-cstr+1;
  s = hs.substr(p1, strtol(cstr, 0, 10));
}

#endif
