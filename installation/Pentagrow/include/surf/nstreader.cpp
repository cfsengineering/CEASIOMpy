
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
 
#include "nstreader.h"
#include <genua/xcept.h>
#include <genua/dbprint.h>
#include <genua/defines.h>
#include <genua/ioglue.h>
#include <genua/timing.h>
#include <boost/regex.hpp>
#include <sstream>

using std::string;

static const string nastran_wspace(" \n\t\r");

// ------------------------ NstReader ---------------------------------------

void NstReader::readLines(std::istream & in) 
{
  Wallclock clk;
  clk.start();

  lines.clear();
  std::string ln, left;

  // whether last line scanned was a wide field line
  bool widecard = false;
  bool endbulk = false;
  bool nopunch = (not ispunch);
  std::string::size_type pos, lpos, cpos;
  size_t lcount(0);
  while (std::getline(in, ln)) {

    ++lcount;

    // first non-blank character
    pos = ln.find_first_not_of(nastran_wspace);
    if (pos == string::npos)
      continue;
    else if (isf06Output)
      pos = std::min(pos, std::string::size_type(30));

    char c = ln[pos];

    // throw out invalid lines if it's not a punch file
    if (nopunch) {

      // skip full comment lines as soon as possible
      if (c == '$')
        continue;

      // chop off trailing comments
      cpos = ln.find_first_of('$');
      if (cpos != string::npos)
        ln = ln.substr(0, cpos);

      // bulk data echo contains lines like
      // .   1  ..   2  ..   3  ..   4  ..
      if ( (ln.size() > pos+1) and (c == '.') and (ln[pos+1] == ' '))
        continue;

      // skip lines which contain a 0 or 1 in first column
      if (pos == 0 and (c == '0' or c == '1')
          and (strstr(ln.c_str(), "SUBCASE ") == 0))
        continue;

      // skip page marker lines etc
      if ( (strstr(ln.c_str(), "   PAGE") != 0)
           or (strstr(ln.c_str(), " E C H O ") != 0) ) {
        // eat the two following lines
        std::getline(in, ln);
        // getline(in, ln);
        continue;
      } else if (strstr(ln.c_str(), "***") != 0) {
        continue;
      }

      if (not endbulk)
        endbulk = (strstr(ln.c_str(), "ENDDATA") != 0);
    }

    // extend short lines with blanks unless it's .f06 output
    if ((not isf06Output) and (ln.size() < 80+pos) ) {
      size_t nblank = 80 + pos - ln.size();
      ln.insert( ln.end(), nblank, ' ');
    }

    if (not widecard) {

      // most of the time, we do not read wide-format cards;
      // skip leading whitespace from .f06 output, but keep it
      // in plain bulk data files.
      if (isf06Output) {
        lines.push_back(ln.substr(pos, string::npos));
      } else {
        lines.push_back(ln);
      }

      // this line could be the left half of a wide-format card
      if ((not endbulk) and isalpha(c))
        widecard = ( strchr(ln.c_str(), '*') != 0 );

    } else if (c == '*') {

      // first non-blank character is '*'
      // meaning this is a long-format continuation
      // NX Nastran 5 QRG page 801
      left = lines.back();
      if (isf06Output) {

        lpos = left.find_first_not_of(' ');
        if (ln.size() > 7)
          lines.back() = left.substr(lpos, 72) + ln.substr(pos+8, 64);
        else
          lines.back() = left.substr(lpos, 72);

      } else {
        // cut of the final 8-wide field containing continuation mark
        // from the left half-line and the first 8-wide field from right
        lines.back() = left.substr(0, 72) + ln.substr(8, 72);
      }

      widecard = false;
    } else {
      // widecard == true and ln[0] != *
    }
  }

  dbprint("Kept",lines.size(),"of",lcount,"lines of input.");

  log("[t] NstReader::readLines: ", clk.stop());
}

void NstReader::parseTopo()
{
  Wallclock clk;
  clk.start();

  toprec.clear();
  const uint nl(lines.size());
  
  NstRecordId id;
  NstRecord rcd;
  for (uint i=0; i<nl; ++i) {
    
    const string & ln(lines[i]);
    id = NstRecord::toposcan(ln.c_str(), ispunch);
    if (id == RidDispl or id == RidElmStress or
        id == RidEigMode or id == RidEndBulk) {

      dbprint("Exit parseTopo() at line ",i);

      if (rcd.id() == RidGRID)
        rcd.readGrid(*this);
      else
        toprec.push_back(rcd);
      return;

    } else if (id != RidUndefined) {
      
      if (rcd.id() == RidGRID)
        rcd.readGrid(*this);
      else
        toprec.push_back(rcd);
      
      // create next record
      rcd.clear();
      rcd.firstLine(i);
      rcd.id(id);

    } else {
      rcd.lastLine(i);
    }
  }
  
  // store last element
  if (rcd.id() == RidGRID)
    rcd.readGrid(*this);
  else
    toprec.push_back(rcd);

  dbprint("parseTopo() found nodes:", msh.nvertices());

  log("[t] NstReader::parseTopo: ", clk.stop());
}

uint NstReader::parseEvec()
{
  Wallclock clk;
  clk.start();

  evrec.clear();

  NstRecord rcd;
  // string::size_type p1,p2;
  uint imode(0), mi(0), maxmode(0);
  const uint istart(toprec.back().last()+1);
  const uint nlines(lines.size());

  dbprint("Parsing",nlines-istart,"lines of eigenvector results.");

  // there's no eigenvalue table in punch files
  bool nopunch = (not ispunch);
  bool searchTable = nopunch;

  // regex for eigenmode and frequency recognition in punch files
  const string rxint("([0-9]+)");
  const string rxfloat("([+-]?([0-9]*\\.?[0-9]+|[0-9]+\\.?[0-9]*)([eE][+-]?[0-9]+)?)");
  const string pattern = R"(\$EIGENVALUE =\s*)" + rxfloat
      + R"(\s*MODE =\s*)" + rxint + ".*";
  const boost::regex evline(pattern);
  boost::smatch what;

  Real eigenvalue;
  for (uint i=istart; i<nlines; ++i) {

    const string & ln(lines[i]);
    if (searchTable and NstRecord::eigtablescan(ln.c_str())) {
      rcd.clear();
      rcd.id(RidEigTable);
      rcd.firstLine(i);
      searchTable = false;
    }

    if (nopunch) {
      mi = NstRecord::evscan(ln.c_str());
    } else if (boost::regex_match(ln, what, evline)) {
      eigenvalue = Float(what[1].str());
      mi = Int(what[4].str());
      msh.appendGeneralized( eigenvalue, 1.0 );
    } else {
      mi = 0;
    }

    if (mi != 0) {

      dbprint("Found EV indicator:",mi);
      if (rcd.id() == RidEigTable) {
        rcd.lastLine(i);
        evrec.push_back(rcd);
      }

      if (mi != imode) {
        if (imode > maxmode) {
          maxmode = imode;
          evrec.push_back(rcd);
        }

        imode = mi;
        rcd.clear();
        rcd.id(RidEigMode);
        rcd.firstLine(i);
      }
    }
    rcd.lastLine(i);
  }
  
  if (imode > maxmode)
    evrec.push_back(rcd);

  dbprint(evrec.size(), "records for eigenvector output.");

  uint nmode = evrec.size() - 1;
  if (searchTable or ispunch)
    nmode++;

  log("[t] NstReader::parseEvec: ", clk.stop());
  return nmode;
}

uint NstReader::parsePkz()
{
  Wallclock clk;
  clk.start();

  pkzrec.clear();

  NstRecord rcd;
  string::size_type p1,p2;
  uint imode(0);
  const uint istart(toprec.back().last()+1);
  const uint nlines(lines.size());
  for (uint i=istart; i<nlines; ++i) {

    // skip empty lines and comments
    string ln(lines[i]);
    p1 = ln.find_first_not_of(nastran_wspace);
    p2 = ln.find_last_not_of(nastran_wspace);
    if (p2 <= p1)
      continue;

    ln = ln.substr(p1, p2-p1+1);
    if (ln[0] == '$')
      continue;

    if ( NstRecord::pkzscan(ln.c_str()) ) {
      if (imode > 0)
        pkzrec.push_back(rcd);
      ++imode;
      rcd.clear();
      rcd.id(RidPkSubspaceMode);
      rcd.firstLine(i);
    }
    rcd.lastLine(i);
  }

  if (imode != 0)
    pkzrec.push_back(rcd);

  log("[t] NstReader::parsePkz: ", clk.stop());
  return pkzrec.size();
}

uint NstReader::parseDisp()
{
  Wallclock clk;
  clk.start();

  dsprec.clear();

  NstRecord rcd;
  string::size_type p1,p2;
  const uint istart(toprec.back().last()+1);
  const uint nlines(lines.size());
  dbprint("Displacement parser starts at line ", istart);

  bool firstfound = false;
  int subcase(0), lastcase(0);
  double thistime, lasttime;
  thistime = lasttime = NotDouble;
  for (uint i=istart; i<nlines; ++i) {
    
    // skip empty lines and comments
    string ln(lines[i]);
    p1 = ln.find_first_not_of(nastran_wspace);
    p2 = ln.find_last_not_of(nastran_wspace);
    if (p2 <= p1)
      continue;
    ln = ln.substr(p1, p2-p1+1);
    if ((not ispunch) and (ln[0] == '$'))
      continue;

    // interrupt parsing if a stress header was found
    if ( NstRecord::sigscan(ln.c_str(), ispunch) )
      break;

    bool newcase = false;
    if (solSequence == 101) {
      int linecase = NstRecord::subcasescan( ln.c_str() );
      if (linecase > 0 and linecase != subcase) {
        subcase = linecase;
        dbprint(i, "Identified SUBCASE ", linecase);
      }
      // newcase = ( (lastcase == 0) or (subcase != lastcase) );
      newcase = (subcase != lastcase);
    } else if (solSequence == 109) {
      double linetime = NstRecord::timescan( ln.c_str() );
      if (linetime != NotDouble)
        cout << "TIME: " << linetime << endl;
      if ((linetime != NotDouble) and (linetime != thistime))
        thistime = linetime;
      newcase = ( (lasttime == NotDouble) or (thistime != lasttime) );
    }

    bool dspHeader = NstRecord::dspscan(ln.c_str(), ispunch);
    firstfound |= dspHeader;

    if ( newcase and dspHeader ) {          // displacement begins

      if (rcd.size() > 1) {
        if (solSequence == 101)
          dbprint("Stored subcase ", lastcase, rcd.size(), "records");
        else if (solSequence == 109)
          dbprint("Stored time slice ", lasttime, rcd.size(), "records");
        dsprec.push_back(rcd);
      }

      if (solSequence == 101)
        dbprint("Beginning new subcase = ", subcase, "at", i);
      else if (solSequence == 109)
        dbprint("Beginning new timeslice ", thistime);

      lastcase = subcase;
      lasttime = thistime;
      rcd.clear();
      rcd.id(RidDispl);
      rcd.firstLine(i);
      firstfound = true;

    } else if ((subcase != 0) and firstfound) {

      // not (newcase and dspHeader) but subcase != 0
      // means we're in the middle of the displacement block
      rcd.lastLine(i);
    }

  } // loop over lines

  if (firstfound and rcd.size() > 1) {
    cout << "Stored subcase " << lastcase << " size: " << rcd.size() << endl;
    dsprec.push_back(rcd);
  }

  log("[t] NstReader::parseDisp: ", clk.stop());
  return dsprec.size();
}

uint NstReader::parseElmStress()
{
  Wallclock clk;
  clk.start();

  estressrec.clear();

  // can only handle PUNCH files
  if (not ispunch)
    return 0;
  if (solSequence != 101) {
    dbprint("Stress parsing only for SOL 101");
    return 0;
  }

  uint istart(0);
  if (not dsprec.empty())
    istart = dsprec.back().last()-1;
  else if (not evrec.empty())
    istart = evrec.back().last()-1;
  else if (not toprec.empty())
    istart = toprec.back().last()-1;
  dbprint("Stress parser starts at line ", istart);

  NstRecord rcd;
  const uint nlines(lines.size());
  bool firstfound = false;
  for (uint i=istart; i<nlines; ++i) {

    const string &ln(lines[i]);

    if ( not NstRecord::sigscan(ln.c_str(), true) ) {
      rcd.lastLine(i);
    } else {

      // new stress record found : "ELEMENT STRESSES" detected

      // store the previously gathered record, if any
      if ( firstfound and rcd.size() > 1 ) {
        estressrec.push_back(rcd);
      }
      firstfound = true;

      // see if we can include the label in the line before
      uint blockStart = i;
      if ((i > 0) and
          (strstr(lines[i-1].c_str(), "LABEL") != 0))
        --blockStart;

      // and start a new one
      rcd.clear();
      rcd.id(RidElmStress);
      rcd.firstLine(blockStart);
    }

  } // loop over lines

  // store the last record
  if (firstfound and rcd.size() > 1) {
    estressrec.push_back(rcd);
  }

  log("[t] NstReader::parseElmStress: ", clk.stop());
  return estressrec.size();
}

void NstReader::transformPoints()
{
  Cid2GidsMap::const_iterator itg, glast;
  CidMap::const_iterator ics;
  glast = cid2gid.end();
  for (itg = cid2gid.begin(); itg != glast; ++itg) {
    ics = crdsys.find( itg->first );
    if (ics == crdsys.end()) {
      std::stringstream ss;
      ss << "Cannot find definition of coordinate system " << itg->first;
      throw Error(ss.str());
    }
    const NstCoordSys & cs(ics->second);
    const Indices & gids( itg->second );
    const int ng(gids.size());
    for (int i=0; i<ng; ++i) {
      uint k = msh.gid2index(gids[i]);
      msh.vertex(k) = cs.toGlobal(msh.vertex(k));
    }
  }
}

void NstReader::transformMode(Matrix & z) const
{
  Cid2GidsMap::const_iterator itg, glast;
  CidMap::const_iterator ics;
  glast = cid2def.end();
  for (itg = cid2def.begin(); itg != glast; ++itg) {
    ics = crdsys.find( itg->first );
    if (ics == crdsys.end()) {
      std::stringstream ss;
      ss << "Cannot find definition of coordinate system " << itg->first;
      throw Error(ss.str());
    }
    const NstCoordSys & cs(ics->second);
    const Indices & gids( itg->second );
    const int ng(gids.size());
    for (int i=0; i<ng; ++i) {
      uint k = msh.gid2index(gids[i]);
      cs.toGlobal(k, z);
    }
  }
}

void NstReader::read(const std::string & fname)
{
  Wallclock clk;

  ifstream in(asPath(fname).c_str(), std::ios::in | std::ios::binary);
  if (not in)
    throw Error("Could not open file "+fname);
  
  isf06Output = false;
  ispunch = (fname.find(".pch") != string::npos) or
      (fname.find(".f07") != string::npos);
  if (not ispunch)
    isf06Output = (fname.find(".f06") != string::npos);

  // skip until "BEGIN BULK" reached, but only if this is
  // an output file (f06) since bulk data input files often
  // do not contain BEGIN BULK
  if (isf06Output) {
    string ln;
    const char *pos;
    while ( std::getline(in, ln) ) {
      if (strstr(ln.c_str(), "BEGIN BULK")) {
        break;
      } else if ( (pos = strstr(ln.c_str(), "SOL ")) ) {
        const char *head = pos + 3;
        if (head != 0)
          solSequence = strtol(head, 0, 10);
      }
    }
  } else if (ispunch) {
    dbprint("NstReader assuming file is punch file: ", fname);

    // .pch does not contain case control, so we need to figure out whether
    // to look for eigenvector data later on
    string ln;
    bool foundEv = false;
    bool foundDisp = false;
    while ( std::getline(in, ln) ) {
      if (strstr(ln.c_str(), "$EIGENVECTOR")) {
        foundEv = true;
        solSequence = 103;
        break;
      } else if (strstr(ln.c_str(), "$DISPLACEMENTS")) {
        foundDisp = true;
        break;
      }
    }
    if (foundDisp and (not foundEv))
      solSequence = 101;

    // go back to the start of the stream
    in.seekg(0);

  } else {
    dbprint("NstReader assuming file is raw bulk data file: ", fname);
  }

  cout << "Solution sequence: " << solSequence << endl;
  readLines(in);
  parseTopo();
  uint nmoderec(0);
  if (solSequence == 103 or solSequence == 145)
    nmoderec = parseEvec();
  if (solSequence == 101 or solSequence == 109)
    parseDisp();
  if (ispunch and solSequence == 101)
    parseElmStress();
  if (solSequence == 145)
    parsePkz();

  clk.start();
  uint nr = toprec.size();
  for (uint i=0; i<nr; ++i)
    toprec[i].process(*this);
  log("[t] NstReader process topology: ", clk.stop());

  // detect the case of a file without mesh echo
  if (msh.nvertices() == 0) {
    string msg("Nastran modal analysis result file does not contain mesh\n");
    msg += " echo. Please specify ECHO = UNSORT or ECHO = PUNCH "
           "in the case control section.";
    throw Error(msg);
  }
  
  // process modal/flutter results
  clk.start();
  if (solSequence == 103 or solSequence == 145) {

    // mode index
    int mi(0);
    msh.resizeModes(nmoderec);
    for (uint i=0; i<evrec.size(); ++i) {
      const NstRecord & rcd(evrec[i]);
      bool okmode = rcd.mprocess(mi, *this, ispunch);
      if (not okmode) {
        dbprint("Failed to read mode index",i,", abandoning import.");
        msh.resizeModes(0);
        break;
      }
      if (rcd.id() == RidEigMode)
        ++mi;
    }

    nr = pkzrec.size();
    for (uint i=0; i<nr; ++i)
      pkzrec[i].pkprocess(*this);
  }
  log("[t] NstReader process modal data: ", clk.stop());

  clk.start();
  nr = dsprec.size();
  for (uint i=0; i<nr; ++i) {
    const NstRecord & rcd(dsprec[i]);
    rcd.dprocess(*this, ispunch);
  }
  log("[t] NstReader process displacements: ", clk.stop());

  // process stress results
  clk.start();
  if (solSequence == 101 and ispunch) {
    nr = estressrec.size();
    for (int i=0; i<int(nr); ++i)
      estressrec[i].sigprocess(*this);
  }
  log("[t] NstReader process stress: ", clk.stop());
  
  transformPoints();

  clk.start();
  msh.mergeStressFields();
  log("[t] NstReadr merging stress fields: ", clk.stop());
}

void NstReader::readOp4Ascii(const std::string & fname,
                             CsrMatrix<Real> & mtx)
{
  ifstream in(asPath(fname).c_str(), std::ios::binary);

  // low-level string processing
  char *tail;
  const char *head;

  // parse header line
  string ln, name, numformat;
  int ncol, nrow, nform, ntype;
  // bool bigmat = false;

  getline(in, ln);
  head = ln.c_str();
  ncol = strtol(head, &tail, 10);
  if (head == tail)
    throw Error("OUTPUT4 matrix parser: Invalid entry in header - NCOL");
  head = tail;
  nrow = strtol(head, &tail, 10);
  if (head == tail)
    throw Error("OUTPUT4 matrix parser: Invalid entry in header - NR");
  head = tail;
  // bigmat = (nrow < 0);
  nrow = std::abs(nrow);
  nform = strtol(head, &tail, 10);
  if (head == tail)
    throw Error("OUTPUT4 matrix parser: Invalid entry in header - NFORM");
  head = tail;
  ntype = strtol(head, &tail, 10);
  if (head == tail)
    throw Error("OUTPUT4 matrix parser: Invalid entry in header - NTYPE");
  head = tail;
  name.assign(head, head+8);
  numformat.assign(head+8, head+16);

  // debug
  cout << "NCOL = " << ncol << " NR = " << nrow
       << " NF = " << nform << " NTYPE = " << ntype << endl;
  cout << "Matrix: " << name << " Number format: " << numformat << endl;

  //  // read sparse bigmat format only
  //  if (not bigmat)
  //    throw Error("Nastran matrix format not supported: "
  //                "Use IUNIT < 0 (sparse format) and BIGMAT = TRUE");

  // coordinate storage
  Indices rc;
  Vector val;
  rc.reserve(16*ncol);
  val.reserve(16*ncol);

  // process columns
  int icol(0);
  while (icol < ncol) {

    // column header
    int nw, dummy;
    in >> icol >> dummy >> nw;
    if (icol > ncol)
      break;

    assert(icol > 0);
    assert(dummy == 0);

    // read 'string' (as in string of values) blocks
    // until number of words nw exhausted. real values
    // count as two words, integer header values as one.
    while (nw > 0) {

      int len, rfirst;
      in >> len >> rfirst;
      assert(len > 1);
      assert(rfirst > 0);
      nw -= 2;

      // number of real values to expect
      len = (len - 1) / 2;
      Real vij;
      for (int i=0; i<len; ++i) {
        in >> vij;
        if ( vij != 0.0 ) {
          rc.push_back( rfirst-1+i );
          rc.push_back( icol-1 );
          val.push_back(vij);
        }
        nw -= 2;
      }

    }
  }

  // create CSR matrix connectivity
  {
    ConnectMap spty;
    spty.assign(nrow, rc);
    spty.compress();
    mtx.swap(spty);
  }

  // fill values
  const int nnz = val.size();
  for (int i=0; i<nnz; ++i) {
    uint lix = mtx.lindex( rc[2*i], rc[2*i+1] );
    assert(lix != NotFound);
    mtx.value(lix, 0) = val[i];
  }
}

