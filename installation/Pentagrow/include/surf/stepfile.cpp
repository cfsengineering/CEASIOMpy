
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
 

#include "stepfile.h"
#include "stepentitycreator.h"
#include "stepline.h"
#include <genua/sysinfo.h>
#include <genua/dbprint.h>
#include <genua/ioglue.h>

using std::string;

static bool nextLine(std::istream & is, std::string & line)
{
  line.clear();
  string s;
  while (getline(is,s)) {
    line.append(s);
    if (line.rfind(';') != string::npos)
      return true;
  }
  return false;
}

void StepFile::read(const std::string & fname)
{
  StepEntityCreator creator;

  ifstream in(asPath(fname).c_str(), std::ios::binary);
  string line, etype;

  // header
  do {
    getline(in, line);
  } while (strstr(line.c_str(), "DATA;") == 0);

  entities.clear();
  while (nextLine(in, line)) {

    if (strstr(line.c_str(), "ENDSEC") != 0)
      break;

    StepFileLine sl(line.c_str());
    StepID eid = sl.entityType(etype);
    if (etype.empty()) {
      dbprint("Not recognized: ", line);
      continue;
    }

    StepEntity *ptr = creator.create(sl, etype);
    if (ptr != 0) {
      ptr->eid = eid;
      entities.insert( StepEntityPtr(ptr) );
    } else {
      dbprint("Entity ", eid, "not created: ", etype);
    }
  }

  dbprint(entities.size(), " entities created.");
}

void StepFile::write(std::ostream & os) const
{
  // stream settings
  os << std::showpoint;
  os.precision(14);

  // fetch time
  int year, month, day, hour, minu, sec;
  SysInfo::localTime(year, month, day, hour, minu, sec);

  // write P21 file header
  os << "ISO-10303-21;" << endl << "HEADER;" << endl;
  os << "FILE_DESCRIPTION(('" << hdDescription << "'),'2;1');" << endl;
  os << "FILE_NAME('" << hdFileName << "','";
  os << year << '-' << month << '-' << day << 'T'
      << hour << ':' << minu << ":" << sec << "+00:00',";
  os << '\'' << hdAuthor << "',";
  os << '\'' << hdOrg << "',";
  os << '\'' << hdPpVersion << "',";
  os << '\'' << hdOrigSystem << "',";
  os << '\'' << hdAuth << "');" << endl;
  os << "FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));" << endl;
  os << "ENDSEC;" << endl;
  os << "/* File written by libsurf. http://www.larosterna.com */" << endl;
  os << "DATA;" << endl;

  const_iterator itr, last = end();
  for (itr = begin(); itr != last; ++itr) {
    const StepEntityPtr & e( *itr );
    os << '#' << e->eid << '=' << e->keyString() << '(';
    e->write(os);
    os << ");\n";
  }

  os << "ENDSEC;" << endl;
  os << "END-ISO-10303-21;" << endl;
}

bool StepFile::isStepFile(const std::string &fname)
{
  ifstream in(asPath(fname).c_str(), std::ios::binary);
  string line;

  // find first non-empty line of header
  while (line.empty()) {
    getline(in, line);
    line = strip(line);
  }

  return (line.find("ISO-10303-21;") != string::npos);
}
