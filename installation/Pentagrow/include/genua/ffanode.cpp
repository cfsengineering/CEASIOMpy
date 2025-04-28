
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
 
#include "ffanode.h"
#include "algo.h"
#include "xcept.h"
#include "strutils.h"
#include "ioglue.h"
#include "timing.h"
#include "iobuffer.h"
#include <sstream>

using std::string;
using std::stringstream;
using std::vector;

float FFANode::s_tsys(0.0f);
float FFANode::s_tself(0.0f);

// macros for i/o timing
#define CLOCK_SYS(x)  \
  clk.start(); \
#x ; \
  clk.stop(); \
  s_tsys += clk.elapsed();

template <class Element>
static void scanRows(istream & is, int n, vector<char> & rb)
{
  is >> std::skipws;
  
  size_t bpos(0);
  int count(0);
  Element tmp;
  Element *base;
  while (count < n and is >> tmp) {
    base = (Element *) &rb[bpos];
    *base = tmp;
    bpos += sizeof(Element);
    ++count;
  }
}

template <int N>
static void scanStringRows(istream & is, int n, vector<char> & rb)
{
  is >> std::noskipws;
  
  char c;
  size_t bpos(0);
  memset(&rb[0], ' ', rb.size());
  for (int i=0; i<n; ++i) {
    // scan for start (single quote)
    c = 0;
    while (c != 0x27)
      is >> c;
    
    // read string block
    for (int k=0; k<N; ++k) {
      is >> c;
      if (c != 0x27)
        rb[bpos+k] = c;
      else
        break;
    }
    bpos += N;
    
    // scan for last single quote
    while (c != 0x27)
      is >> c;
  }
}

template <class Element>
static void writeRows(ostream & os, int n, const vector<char> & rb)
{
  const int nr = n/5;
  size_t bpos(0);
  for (int ir=0; ir<nr; ++ir) {
    for (int k=0; k<5; ++k) {
      os << " " << *((const Element*) &rb[bpos]);
      bpos += sizeof(Element);
    }
    os << endl;
  }
  for (int i=5*nr; i<n; ++i) {
    os << " " << *((const Element*) &rb[bpos]);
    bpos += sizeof(Element);
  }
  if (n-5*nr != 0)
    os << endl;
}

template <int N>
static void writeStringRows(ostream & os, int n, const vector<char> & rb)
{
  size_t bpos(0);
  const int spr = std::max(1, 72/N);
  const int nr = n/spr;
  for (int ir=0; ir<nr; ++ir) {
    for (int w=0; w<spr; ++w) {
      os << " '";
      for (int k=0; k<N; ++k) {
        os << rb[bpos];
        ++bpos;
      }
      os << "'";
    }
    os << endl;
  }
  for (int i=spr*nr; i<n; ++i) {
    os << " '";
    for (int k=0; k<N; ++k) {
      os << rb[bpos];
      ++bpos;
    }
    os << "'";
  }
  if (n-spr*nr != 0)
    os << endl;
}

// -------------------- FFANode -----------------------------------------------

uint FFANode::findChild(const std::string & s) const
{
  const int nc = children.size();
  for (int i=0; i<nc; ++i)
    if (children[i]->name() == s)
      return i;
  return NotFound;
}

FFANodePtr FFANode::findPath(const std::string &path) const
{
  string::size_type p1 = path.find_first_of('/');
  string key = path.substr(0,p1);
  uint ichild = findChild(key);
  if (ichild == NotFound) {
    return FFANodePtr();
  } else {
    FFANodePtr cnp = child(ichild);
    if (p1 == string::npos)
      return cnp;
     else
      return cnp->findPath(path.substr(p1+1, path.length()));
  }
}

void FFANode::copy(FFADataType t, int nr, int nc, const void *ptr)
{
  type = t;
  nrow = nr;
  ncol = nc;
  size_t esize = elementSize(t);
  size_t nbyt = esize*nrow*ncol;
  rblock.resize(nbyt);
  memcpy(&rblock[0], ptr, nbyt);
}

void FFANode::copy(const std::string & s)
{
  nrow = ncol = 1;
  type = FFAString72;
  rblock.resize(72);
  memset(&rblock[0], ' ', 72);
  memcpy(&rblock[0], &s[0], std::min(rblock.size(), s.size()));
}

FFANodePtr FFANode::append(const string &tag, const string &content)
{
  FFANodePtr childNode(new FFANode(tag));
  childNode->copy(content);
  append(childNode);
  return childNode;
}

std::string FFANode::summary() const
{
  int nchi = children.size();
  stringstream ss;
  ss << "[" << tag << "] ";
  ss << nrow << " rows, " << ncol << " cols, ";
  ss << nchi << " children, type: " << elementCode(type) << endl;
  for (int i=0; i<nchi; ++i)
    ss << "  " << children[i]->summary();
  return ss.str();
}

void FFANode::swapBytes() const
{
  if (is_bigendian())
    return;
  
  switch (type) {
  case FFAInt4:
  case FFAFloat4:
  case FFAComplex8:
    swap_bytes<4>(rblock.size(), &rblock[0]);
    break;
  case FFAInt8:
  case FFAFloat8:
  case FFAComplex16:
    swap_bytes<8>(rblock.size(), &rblock[0]);
    break;
  case FFAChar:
  case FFAString16:
  case FFAString72:
  case FFAParent:
    break;
  }
}

void FFANode::write(const std::string & s) const
{
  string::size_type pos = s.find_last_of('.');
  if (pos == string::npos or pos+1 >= s.size() or s[pos+1] == 'b') {
    ofstream os( asPath(s).c_str(), std::ios::out | std::ios::binary);
    if (not os)
      throw Error("FFANode: Could not open file "+s);

    // put a one-megabyte buffer between us and the OS.
    BufferedOStream bos(&os, 1024*1024);
    bwrite(bos);
  } else {
    ofstream os( asPath(s).c_str() );
    if (not os)
      throw Error("FFANode: Could not open file "+s);
    awrite(os);
  }
}

void FFANode::read(const std::string & s)
{
  string::size_type pos = s.find_last_of('.');
  if (pos == string::npos or pos+1 >= s.size() or s[pos+1] == 'b') {
    ifstream is( asPath(s).c_str(), std::ios::binary);
    if (not is)
      throw Error("FFANode: Could not open file "+s);

    // put a one-megabyte buffer between us and the OS.
    BufferedIStream bis(&is, 1024*1024);
    bread(bis);
  } else {
    ifstream is( asPath(s).c_str());
    if (not is)
      throw Error("FFANode: Could not open file "+s);
    aread(is);
  }
}

void FFANode::awrite(std::ostream & os) const
{
  const int nch = children.size();
  string ftag = (type < FFAChar and (nrow*ncol) > 1) ? "F   " : "   ";
  string stag = (tag.size() <= 16) ? tag : tag.substr(0,16);
  os << stag << ", " << elementCode(type) << ftag << ", "
     << ncol << ", " << nrow << ", " << nch << endl;

  switch (type) {

  case FFAInt4:
    writeRows<int32_t>(os, nrow*ncol, rblock);
    break;

  case FFAInt8:
    writeRows<int64_t>(os, nrow*ncol, rblock);
    break;

  case FFAFloat4:
    os << std::scientific;
    writeRows<float>(os, nrow*ncol, rblock);
    break;
    
  case FFAFloat8:
    os << std::scientific;
    writeRows<double>(os, nrow*ncol, rblock);
    break;

  case FFAComplex8:
  case FFAComplex16:
    throw Error("FFANode: ASCII format for complex data not known yet.");
    break;

  case FFAChar:
    writeStringRows<1>(os, nrow*ncol, rblock);
    break;

  case FFAString16:
    writeStringRows<16>(os, nrow*ncol, rblock);
    break;

  case FFAString72:
    writeStringRows<72>(os, nrow*ncol, rblock);
    break;

  case FFAParent:
    break;

  }
  
  for (int i=0; i<nch; ++i)
    children[i]->awrite(os);
}

void FFANode::aread(std::istream & is)
{
  // scan for header line
  StringArray words;
  string line, typestr;
  while ( getline(is, line) ) {
    
    // skip comments
    line = strip(line);
    if (line.empty() or line[0] == '*')
      continue;

    // try to split line by commas
    words = split(line, ",");
    if (words.size() == 5)
      break;
    
    // didn't work. split at spaces perhaps?
    words = split(line, " ");
    if (words.size() == 5)
      break;
  }
  
  if (not is)
    return;
  
  // parse header line
  int nchi(0);
  tag = strip(words[0]);
  typestr = strip(words[1]);
  ncol = Int(words[2]);
  nrow = Int(words[3]);
  nchi = Int(words[4]);
  
  switch (typestr[0]) {
  case 'I':
    type = FFAInt4;
    rblock.resize(nrow*ncol*elementSize(type));
    scanRows<int32_t>(is, nrow*ncol, rblock);
    break;
  case 'J':
    type = FFAInt8;
    rblock.resize(nrow*ncol*elementSize(type));
    scanRows<int64_t>(is, nrow*ncol, rblock);
    break;
  case 'R':
    type = FFAFloat4;
    rblock.resize(nrow*ncol*elementSize(type));
    scanRows<float>(is, nrow*ncol, rblock);
    break;
  case 'D':
    type = FFAFloat8;
    rblock.resize(nrow*ncol*elementSize(type));
    scanRows<double>(is, nrow*ncol, rblock);
    break;
  case 'C':
  case 'Z':
    throw Error("Don't know how to read complex values yet.");
    break;
  case 'A':
    type = FFAChar;
    rblock.resize(nrow*ncol*elementSize(type));
    scanStringRows<1>(is, nrow*ncol, rblock);
    break;
  case 'S':
    type = FFAString16;
    rblock.resize(nrow*ncol*elementSize(type));
    scanStringRows<16>(is, nrow*ncol, rblock);
    break;
  case 'L':
    type = FFAString72;
    rblock.resize(nrow*ncol*elementSize(type));
    scanStringRows<72>(is, nrow*ncol, rblock);
    break;
  case 'N':
    type = FFAParent;
    break;
  default:
    throw Error("Cannot handle type string "+typestr);
  }
  
  children.resize(nchi);
  for (int i=0; i<nchi; ++i) {
    children[i] = FFANodePtr(new FFANode);
    children[i]->aread(is);
  }
}

struct ffa_hdr
{
  uint32_t iRecordBegin;  // 4B (marker)
  char caName[16];
  char caType[4];
  uint32_t iDim[3];        // 12B
  uint32_t iRecordEnd;    // 4B (marker)
};

void FFANode::bwrite(std::ostream & os) const
{
  // construct and write header
  char tbuf[4], hbuf[16];
  memset(tbuf, ' ', sizeof(tbuf));
  tbuf[0] = elementCode(type);
  if (type < FFAChar and (ncol*nrow) > 1)
    tbuf[1] = 'F';
  memset(hbuf, ' ', sizeof(hbuf));
  memcpy(hbuf, &tag[0], std::min(tag.size(), sizeof(hbuf)));
  uint32_t hsize = host2network(32u);
  uint32_t nsze = host2network(uint32_t(nrow));
  uint32_t ndim = host2network(uint32_t(ncol));
  uint32_t nchi = host2network(uint32_t(children.size()));
  os.write((const char *) &hsize, 4);
  os.write(hbuf, 16);
  os.write(tbuf, 4);
  os.write((const char *) &ndim, 4);
  os.write((const char *) &nsze, 4);
  os.write((const char *) &nchi, 4);
  os.write((const char *) &hsize, 4);

  // write record for data, byteswap if necessary
  if ( not rblock.empty() ) {
    swapBytes();
    hsize = host2network(uint32_t(rblock.size()));
    os.write((const char *) &hsize, 4);
    os.write(&rblock[0], rblock.size());
    os.write((const char *) &hsize, 4);
    swapBytes();
  }
  
  // write child nodes
  nchi = children.size();
  for (uint32_t i=0; i<nchi; ++i)
    children[i]->bwrite(os);
}

void FFANode::bread(std::istream & is)
{
  Wallclock clk;

  // read header with one system call
  ffa_hdr hdr;
  memset( &hdr, 0, sizeof(ffa_hdr) ); // zero'd out to detect i/o problems

  // CLOCK_SYS( is.read( (char *) &hdr, sizeof(ffa_hdr) ) );
  is.read( (char *) &hdr, sizeof(ffa_hdr) );

  hdr.iRecordBegin = network2host( hdr.iRecordBegin );
  hdr.iRecordEnd = network2host( hdr.iRecordEnd );

  if ( hdr.iRecordBegin != 32 )
    throw Error("FFA header record must be 32 bytes long: "
                +str(hdr.iRecordBegin));
  else if ( hdr.iRecordEnd != 32 )
    throw Error("FFA header record must be 32 bytes long: "
                +str(hdr.iRecordEnd));

  // set name
  tag.resize(16);
  memcpy(&tag[0], hdr.caName, 16);
  std::string::size_type pos;
  pos = tag.find_last_not_of(' ');
  tag.erase(pos+1, std::string::npos);

  uint32_t nchi;
  ncol = network2host( hdr.iDim[0] );
  nrow = network2host( hdr.iDim[1] );
  nchi = network2host( hdr.iDim[2] );
  const char *tbuf = hdr.caType;

  // determine data type
  switch (tbuf[0]) {
  case 'I':
    type = FFAInt4;
    break;
  case 'J':
    type = FFAInt8;
    break;
  case 'R':
    type = FFAFloat4;
    break;
  case 'D':
    type = FFAFloat8;
    break;
  case 'C':
    type = FFAComplex8;
    break;
  case 'Z':
    type = FFAComplex16;
    break;
  case 'A':
    type = FFAChar;
    break;
  case 'S':
    type = FFAString16;
    break;
  case 'L':
    type = FFAString72;
    break;
  case 'N':
    type = FFAParent;
    break;
  default:
    throw Error("Could not determine data type of FFA record.");
  }

  // read raw data
  size_t blockSize = nrow*ncol*elementSize(type);
  if ((nrow*ncol) > 0) {

    uint32_t nbyt;
    // CLOCK_SYS( is.read((char *) &nbyt, 4) );
    is.read((char *) &nbyt, 4);
    nbyt = network2host( (int) nbyt );

#ifndef NDEBUG
    if ( size_t(nbyt) != blockSize) {
      stringstream ss;
      ss << "Inconsistent opening FFA record length: " << nbyt;
      ss << " expected " << nrow*ncol*elementSize(type) << endl;
      ss << "Type: " << tbuf[0] << " nrows: " << nrow << " ncols: " << ncol;
      ss << " Node name: " << tag << endl;
      throw Error(ss.str());
    }
#endif
    
    clk.start();
    rblock.resize(blockSize);
    // CLOCK_SYS( is.read(&rblock[0], blockSize) );;
    is.read(&rblock[0], blockSize);
    swapBytes();
    // CLOCK_SYS( is.read((char *) &nbyt, 4) );
    is.read((char *) &nbyt, 4);
    nbyt = network2host( (int) nbyt );

#ifndef NDEBUG
    if (size_t(nbyt) != rblock.size()) {
      stringstream ss;
      ss << "Inconsistent closing FFA record length: " << nbyt;
      ss << " expected " << nrow*ncol*elementSize(type) << endl;
      ss << "Type: " << tbuf[0] << " nrows: " << nrow << " ncols: " << ncol;
      ss << " Node name: " << tag << endl;
      throw Error(ss.str());
    }
#endif
  }
  
  children.resize(nchi);
  for (uint32_t i=0; i<nchi; ++i) {
    children[i] = FFANodePtr(new FFANode);
    children[i]->bread(is);
  }
}



