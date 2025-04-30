
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
#include "nstrecord.h"
#include "nstelementstress.h"
#include "nststressfield.h"

#include <genua/dbprint.h>
#include <boost/regex.hpp>
#include <cstring>

using namespace std;

// regular expression to extract deformation data
static const string rxint("([0-9]+)");
static const string rxfloat("([+-]?([0-9]*\\.?[0-9]+|[0-9]+\\.?[0-9]*)"
                            "([eE][+-]?[0-9]+)?)");

// const int InvalidInteger = INT_MIN;

// find first non-blank characters in each field of a bulk data line
// s is the first character of the line
// wmax the maximum number of words/fields to look for
// wds the output array (sized wmax) of first field characters
// returns the number of fields found.
// 
// wds must have space for wmax+1 pointers!
static inline int nst_tokenize(const char *s, int wmax, const char *wds[])
{
  //  // move to first non-blank character
  //  const char *pos = s;
  //  while (*pos == ' ' and *pos != 0)
  //    ++s;
  
  // check for comment line or field marker inserted in f06 files
  if (*s == 0 or *s == '$' or (s[0] == '.' and s[1] == ' '))
    return 0;
  
  // first field starts here
  wds[0] = s;
  
  // determine format : free or fixed?
  const char *pos = strchr(s, ',');
  
  // number of fields recognized
  int nf(1);
  
  // free format field, comma-separated
  if (pos != 0) {
    
    ++pos;
    wds[1] = pos;
    nf = 2;
    for (int i=2; i<wmax; ++i) {
      pos = strchr(pos, ',');
      if (pos == 0)
        break;
      ++pos;
      if (*pos == 0)
        break;
      wds[i] = pos;
      ++nf;
    }
  }
  
  // fixed format field
  else {

    // check for wide (16-char field) format here
    pos = s;
    while ((isalnum(*pos) or isspace(*pos)) and *pos != 0)
      ++pos;

    if (*pos != '*') {

      // short field
      pos = s;
      const char *end = pos + strlen(pos);
      const int nfmax = std::min(wmax, 10);
      for (int i=1; i<nfmax; ++i) {
        pos += 8;
        if (pos >= end)
          break;
        wds[i] = pos;
        ++nf;
      }

    } else {

      // wide format : first (keyword) and last (cont) field are 8 char,
      // 8 data fields are 16 char long
      static const int lflength[10] = {8, 16, 16, 16, 16, 16, 16, 16, 16, 8};
      int ip(8), nchar = strlen(s);
      while (ip < nchar) {
        wds[nf] = &s[ip];
        ip += lflength[nf];
        ++nf;
        if (nf >= wmax)
          break;
      }

      //      // how many 16-char data fields to process at most
      //      const int nfmax = min( 2+int((strlen(wds[0])-16)/16), min(wmax, 10));
      //      for (int i=1; i<nfmax; ++i) {
      //        wds[i] = wds[i-1] + lflength[i-1];
      //        ++nf;
      //      }
    }
  }

  // last string identified begins at wds[nf-1]
  // set the limits of the final one
  wds[nf] = wds[nf-1] + strlen(wds[nf-1]);
  
  return nf;
}

// turn an array of pointers into a vector of zero-terminated strings
// this is necessary to parse non-standard fields (such as 9.87-5) correctly
static inline void convert_words(int n, const char *wds[], StringArray & words)
{
  words.resize(n);
  if (n == 0)
    return;
  
  for (int i=0; i<n-1; ++i) {
    int m = wds[i+1] - wds[i];
    words[i].assign(wds[i], m);
  }
  words[n-1].assign(wds[n-1]);
}

static inline int nstSplitLine(const string & s, StringArray & wds)
{
  const char *wp[12];
  int nfields = nst_tokenize(s.c_str(), 10, wp);
  convert_words(nfields, wp, wds);
  return nfields;
}

static inline int w2int(const string & s)
{
  return atoi(s.c_str());
}

//static inline int w2int(const char *s)
//{
//  char *tail;
//  int v = strtol(s, &tail, 10);
//  return (tail != s) ? v : InvalidInteger;
//}

//static inline bool w2int(const char *s, int & v)
//{
//  char *tail;
//  v = strtol(s, &tail, 10);
//  return (tail != s);
//}

//static inline bool w2int(const string & str, int & v)
//{
//  return w2int(str.c_str(), v);
//}

static inline int words2ints(int nw, const char *wds[], int n, int v[])
{
  // must copy into temporary buffer because NASTRAN allows integers to
  // run into each other
  const size_t bufSize(64);
  char buf[bufSize];
  memset(buf, 0, bufSize);

  int nmax = std::min(nw, n);
  for (int i=0; i<nmax; ++i) {
    char *tail;
    size_t len = wds[i+1] - wds[i];
    memcpy(buf, wds[i], std::min(bufSize, len));
    v[i] = strtol(buf, &tail, 10);
    if (buf == tail)
      return i;
  }
  
  return nmax;
}

static inline NstDof w2dof(const string & s)
{
  static const NstDof a[] = { NstGrounded, NstTransX, NstTransY, NstTransZ,
                              NstRotX, NstRotY, NstRotZ};
  uint i = atoi(s.c_str());
  if (i < 7)
    return a[i];
  else
    return NstNoDof;
}

static inline double w2float(const string & str)
{
  // return atof(s.c_str());
  
  char *tail;
  const char *s = str.c_str();
  double v = strtod(s, &tail);
  if (s == tail)
    return NotDouble;
  
  // check for non-standard floating-point format
  // this only works if s is actually zero-terminated
  // so that we do not run into the next field
  if (tail != 0 and (*tail == '-' or *tail == '+')) {
    s = tail;
    double x = strtod(s, &tail);
    if (s == tail)
      return NotDouble;
    v *= pow(10.0, x);
  }
  
  return v;
}

static inline bool w2float(const char *s, double & v)
{
  char *tail;
  v = strtod(s, &tail);
  if (tail == s)
    return false;
  
  // check for non-standard floating-point format
  // this only works if s is actually zero-terminated
  // so that we do not run into the next field
  if (*tail == '-' or *tail == '+') {
    s = tail;
    double x = strtod(s, &tail);
    if (s == tail)
      return false;
    else
      v *= pow(10.0, x);
  }

  return true;
}

static inline bool w2float(const string & str, double & v)
{
  return w2float(str.c_str(), v);
}

static inline bool w2complex(const char *s, Complex &p)
{
  char *tail;
  Real pr = genua_strtod(s, &tail);
  if (tail == s)
    return false;
  s = tail + 1;
  Real pi = genua_strtod(s, &tail);
  if (tail == s)
    return false;

  p = Complex(pr, pi);
  return true;
}

static inline bool w2complex(const string &s, Complex &p)
{
  return w2complex(s.c_str(), p);
}

static inline uint evparse(const string & s, double dx[])
{
  const char *head(s.c_str()), *pos;
  char *tail;
  pos = head;
  
  uint gid = strtol(pos, &tail, 10);
  if (tail == pos)
    return NotFound;
  
  // proceed to letter 'G', if present
  pos = strchr(head, 'G');
  if (pos == 0)
    return NotFound;
  ++pos;
  
  // read six displacements, break if any one fails
  for (int j=0; j<6; ++j) {
    dx[j] = strtod(pos, &tail);
    if (tail == pos)
      return NotFound;
    pos = tail;
  }
  
  return gid;
}

// -------------------- NstRecord --------------------------------------------

NstRecordId NstRecord::toposcan(const char *s, bool ispunch)
{ 
  bool nopunch = not ispunch;
  if (strstr(s, "GRID") == s)
    return RidGRID;
  else if (strstr(s, "CTRIAR") == s)
    return RidCTRIAR;
  else if (strstr(s, "CQUADR") == s)
    return RidCQUADR;
  else if ((strstr(s, "CBEAM") == s) or (strstr(s, "CBAR") == s))
    return RidCBEAM;
  else if (strstr(s, "CTRIA3") == s)
    return RidCTRIA3;
  else if (strstr(s, "CTRIA6") == s)
    return RidCTRIA6;
  else if (strstr(s, "CQUAD4") == s)
    return RidCQUAD4;
  else if (strstr(s, "CQUAD8") == s)
    return RidCQUAD8;
  else if (strstr(s, "CHEXA") == s)
    return RidCHEXA;
  else if (strstr(s, "CTETRA") == s)
    return RidCTETRA;
  else if (strstr(s, "CONM2") == s)
    return RidCONM2;
  else if (strstr(s, "CMASS2") == s)
    return RidCMASS2;
  else if (strstr(s, "CELAS2") == s)
    return RidCELAS2;
  else if (strstr(s, "RBAR") == s)
    return RidRBAR;
  else if (strstr(s, "RBE2") == s)
    return RidRBE2;
  //  else if (strstr(s, "RBE3") == s)
  //    return RidRBE3;
  else if (strstr(s, "CORD2R") == s)
    return RidCORD2R;


  if (nopunch) {
    if (strstr(s, "ENDDATA") != 0)
      return RidEndBulk;
    else if (strstr(s, "R E A L   E I G E N V A L U E S") != 0)
      return RidEigMode;
    else if (strstr(s, "E I G E N V E C T O R   N O .") != 0)
      return RidEigMode;
    else if (strstr(s, "EIGENVECTOR FROM THE PK METHOD") != 0)
      return RidPkSubspaceMode;
    else if (strstr(s, "D I S P L A C E M E N T   V E C T O R") != 0)
      return RidDispl;
  } else {
    if (strstr(s, "$EIGENVECTOR") != 0)
      return RidEigMode;
    else if (strstr(s, "$DISPLACEMENTS") != 0)
      return RidDispl;
    else if (strstr(s, "$ELEMENT STRESS") != 0)
      return RidElmStress;
  }

  return RidUndefined;
}

void NstRecord::process(NstReader & rdr) const
{
  if (empty())
    return;
  
  switch (rid) {
  case RidGRID:
    readGrid(rdr);
    break;
  case RidCONM2:
    readConm2(rdr);
    break;
  case RidCMASS2:
    readCmass2(rdr);
    break;
  case RidCELAS2:
    readCelas2(rdr);
    break;
  case RidCBEAM:
    readBeam(rdr);
    break;
  case RidCTRIA3:
    readTria3(rdr);
    break;
  case RidCTRIAR:
    readTriaR(rdr);
    break;
  case RidCTRIA6:
    readTria6(rdr);
    break;
  case RidCQUAD4:
    readQuad4(rdr);
    break;
  case RidCQUADR:
    readQuadR(rdr);
    break;
  case RidCQUAD8:
    readQuad8(rdr);
    break;
  case RidCHEXA:
    readHexa(rdr);
    break;
  case RidCTETRA:
    readTetra(rdr);
    break;
  case RidRBAR:
    readRbar(rdr);
    break;
  case RidRBE2:
    readRbe2(rdr);
    break;
  case RidCORD2R:
    readCord2r(rdr);
    break;
  default:
    return;
  }
}

bool NstRecord::mprocess(uint mi, NstReader & rdr, bool ispunch) const
{  
  if ((rid != RidEigMode) and (rid != RidEigTable))
    return false;

  NstMesh & m(rdr.mesh());
  if (rid == RidEigTable) {

    Vector kgen, mgen;
    for (uint i=0; i<size(); ++i) {

      const std::string & ln(rdr.line(lbegin+i));
      if (strstr(ln.c_str(), "RESULTANTS"))
        break;
      else if (strstr(ln.c_str(), "SUBCASE"))
        break;

      uint ModeNo, Order;
      Real Eigenvalue, Radians, Cycles, GenMass, GenStiffness;
      stringstream ss( rdr.line(lbegin+i) );
      if (ss >> ModeNo >> Order >> Eigenvalue >> Radians >>
          Cycles >> GenMass >> GenStiffness)
      {
        kgen.push_back(GenStiffness);
        mgen.push_back(GenMass);
        dbprint(mgen.size(),"k_gen = ",GenStiffness,"m_gen =",GenMass);
      }
    }

    dbprint("Identified ", mgen.size(), "modal properties.");
    m.generalized(kgen, mgen);
    return true;
  }

  if (ispunch)
    return readPunchMode(mi, rdr);
  else
    return readPrintMode(mi, rdr);
}

bool NstRecord::readPrintMode(uint mi, NstReader &rdr) const
{
  NstMesh & m(rdr.mesh());

  const uint nv(m.nvertices());
  const uint nl(size());
  if (nl < 2 or nv == 0)
    return false;

  // first line must contain frequency
  string::size_type p1;
  string s(rdr.line(lbegin));

  const char key[] = "CYCLES =";
  p1 = s.find(key);
  assert(p1 != string::npos);
  s = s.substr(p1 + sizeof(key));
  Real f = atof(s.c_str());

  dbprint("Processing EV",mi,"f =",f,"nlines=",nl);

  // storage for eigenmode
  Matrix z(nv,6);

  // try to parse a displacement line of the format
  // GID  G  tx ty tz rx ry rz
  double dx[6];
  uint nr(0);
  for (uint i=1; i<nl; ++i) {

    uint gid = evparse(rdr.line(lbegin+i), dx);
    if (gid == NotFound) {
      continue;
    }

    // in flutter solutions, displacements for aerodynamic collocation points
    // are also given, but there are no corresponding GRIDs; catch this case
    uint r = m.gid2index(gid);
    if (r != NotFound) {
      for (int j=0; j<6; ++j)
        z(r,j) = dx[j];
      ++nr;
    }

    if (nr >= nv)
      break;
  }

  // jump out if size of data read does not match mesh
  if (nr != nv) {
    cout << "Expected " << nv << " points, got " << nr << endl;
    return false;
  }

  appendMode(z, mi, rdr);
  return true;
}

bool NstRecord::readPunchMode(uint mi, NstReader &rdr) const
{
  // static const string epattern = R"(\$EIGENVALUE =\s*)" + rxfloat
  //               + R"(\s*MODE =\s*)" + rxint + ".*";
  static const string epattern = "\\$EIGENVALUE =\\s*" + rxfloat
      + "\\s*MODE =\\s*" + rxint + ".*";
  static const boost::regex evaline(epattern);

  // pattern for the first line
  // static const string pattern1 = R"(\s*)" + rxint + R"(\s*G\s*)"
  //    + rxfloat + R"(\s*)" + rxfloat + R"(\s*)" + rxfloat + R"(.*)";
  static const string pattern1 = "\\s*" + rxint + "\\s*G\\s*"
      + rxfloat + "\\s*" + rxfloat + "\\s*" + rxfloat + ".*";
  static const boost::regex defline1(pattern1);

  // pattern for the second line
  // static const string pattern2 = R"(\s*-CONT-\s*)"
  //    + rxfloat + R"(\s*)" + rxfloat + R"(\s*)" + rxfloat + R"(.*)";
  static const string pattern2 = "\\s*-CONT-\\s*"
      + rxfloat + "\\s*" + rxfloat + "\\s*" + rxfloat + ".*";
  static const boost::regex defline2(pattern2);

  NstMesh & m(rdr.mesh());

  // storage for eigenmode
  const size_t nv = m.nvertices();
  Matrix z(nv,6);

  Vct6 def;
  Real eigenvalue = 0;
  int gid(0), state = 0;
  boost::smatch what;
  size_t i = first();
  const size_t ilast = last();
  size_t nr(0);
  do {

    const string & s = rdr.line(i);
    if ( state == 0 and boost::regex_match(s, what, evaline) ) {
      eigenvalue = genua_strtod( what[1].str().c_str(), nullptr );
      state = 1;
    } else if ( state == 1 and boost::regex_match(s, what, defline1) ) {
      // matches 1 (gid) 2 5 8
      gid = genua_strtol( what[1].str().c_str(), nullptr, 10 );
      def[0] = genua_strtod( what[2].str().c_str(), nullptr );
      def[1] = genua_strtod( what[5].str().c_str(), nullptr );
      def[2] = genua_strtod( what[8].str().c_str(), nullptr );
      state = 2;
    } else if (state == 2 and boost::regex_match(s, what, defline2)) {
      // matches 1 4 7
      def[3] = genua_strtod( what[1].str().c_str(), nullptr );
      def[4] = genua_strtod( what[4].str().c_str(), nullptr );
      def[5] = genua_strtod( what[7].str().c_str(), nullptr );
      state = 1;

      // lookup coordinate
      uint r = m.gid2index(gid);
      if (r != NotFound) {
        for (int j=0; j<6; ++j)
          z(r,j) = def[j];
        ++nr;
      }

      def = 0.0;
    }

    if (nr == nv)
      break;

    ++i;

  } while (i <= ilast);

  // jump out if size of data read does not match mesh
  if (nr != nv) {
    cout << "Expected " << nv << " points, got " << nr << endl;
    return false;
  }

  appendMode(z, mi, rdr, eigenvalue);
  return true;
}

void NstRecord::appendMode(Matrix &z, uint mi, NstReader &rdr, Real kg) const
{
  NstMesh & m(rdr.mesh());

  // transform modeshape into global coordinate system
  rdr.transformMode(z);

  // copy modeshape into parent mesh
  if (kg != 0)
    m.swapMode(mi, z, kg, 1.0);
  else
    m.swapMode(mi, z);
}

void NstRecord::pkprocess(NstReader & rdr) const
{
  if (rid != RidPkSubspaceMode)
    return;

  NstMesh & m(rdr.mesh());
  const uint nm(m.nmodes());
  const uint nl(size());
  if (nl < 2 or nm == 0)
    return;

  // scan for line containing frequency
  const char key[] = "EIGENVALUE =";
  uint iline = 0;
  string s;
  string::size_type p1;
  do {
    s = rdr.line(lbegin+iline);
    p1 = s.find(key);
    ++iline;
  } while (p1 == string::npos and iline < nl);

  if (p1 == string::npos)
    return;

  Complex p;
  if (not w2complex(s.substr(p1 + sizeof(key)), p))
    return;

  // storage for eigenvector
  CpxVector z;
  z.reserve(nm);

  // collect eigenvector
  Complex zi;
  for (uint i=iline; i<nl; ++i) {
    if ( w2complex(rdr.line(lbegin+i), zi) )
      z.push_back(zi);
    if (z.size() == nm)
      break;
  }

  if (z.size() == nm)
    m.appendFlutterMode(p, z);
}

void NstRecord::sigprocess(NstReader &rdr) const
{
  if (rid != RidElmStress)
    return;

  NstMesh & m(rdr.mesh());
  const uint nv(m.nvertices());
  const uint nl(size());
  if (nl < 2 or nv == 0)
    return;

  dbprint("NstRecord::sigprocess(), lines ",first()," - ",last());

  /*
$TITLE   =                                                                 43713
$SUBTITLE=                                                                 43714
$LABEL   = MACH 0.70 ALPHA 5.0                                             43715
$ELEMENT STRESSES                                                          43716
$REAL OUTPUT                                                               43717
$SUBCASE ID =           1                                                  43718
$ELEMENT TYPE =          95                                                43719
*/

  // storage for results, one per ply index
  std::vector<NstStressField> fields;
  NstElementStressRecord record;

  uint itemCode(0), subcase(0);
  string label;
  bool isReal = false;
  const size_t ilast = last();
  size_t iline = first();
  while (iline <= ilast) {

    // process header
    const char *pos(nullptr);
    const string &ln( rdr.line(iline) );
    const char *s = ln.c_str();

    // extract label
    if ( (pos = strstr(s, "$LABEL   =")) != nullptr ) {
      const size_t keylen = strlen("$LABEL   =");
      label = strip(ln.substr(keylen, 72-keylen));
      ++iline;
      continue;
    }

    // accept only real stress
    if ( strstr(s, "$REAL OUTPUT") != nullptr ) {
      isReal = true;
      ++iline;
      continue;
    }

    if ( (pos = strstr(s, "$SUBCASE ID =")) != nullptr ) {
      pos += strlen("$SUBCASE ID =");
      subcase = genua_strtol(pos, nullptr, 0);
      ++iline;
      continue;
    }

    if ( (pos = strstr(s, "$ELEMENT TYPE =")) != nullptr ) {
      itemCode = genua_strtol(pos+15, nullptr, 10);
      dbprint("Found item code ", itemCode);

      // skip to next NstRecord if item code is not supported
      if (not record.setup(itemCode)) {
        dbprint("Item code not supported: ", itemCode);
        return;
      } else {
        // stress import for this element type is supported
        // prepare regular expressions for processing of this element type
        record.compile(itemCode);
      }

    } else {
      ++iline;
      continue;
    }

    dbprint("Start collecting items. Code = ", itemCode);

    // process records from here on
    uint status(NotFound);
    do {

      // we are still at the "ELEMENT TYPE" line when entering
      ++iline;
      status = record.process(rdr.line(iline));

      // status drops back to 0 when a record is completed
      if (status == 0) {
        assert(record.laminateIndex > 0);
        uint iply = record.laminateIndex - 1;
        if ( hint_unlikely(iply >= fields.size()) ) {
          uint npre = fields.size();
          fields.resize(iply+1);
          for (uint i=npre; i<=iply; ++i) {
            fields[i].setup(itemCode);
            fields[i].subcase(subcase);
            fields[i].label(label);
            fields[i].laminateIndex(i+1);
          }
        }
        fields[iply].append(record);
        record.setup(itemCode);
      }

    } while ((status != NotFound) and (iline+1 < lend));

    dbprint("Processing ends at line ", iline);

    // field is complete, store

    for (const NstStressField &f : fields) {
      if (f.nelements() > 0) {
        dbprint("sigprocess found stress field for ", f.nelements(),
                " elements, subcase ", f.subcase(),
                " type ", f.elementClass());
          size_t isig = m.appendStress(f);
          dbprint("Stress field index: ", isig);
      }
    }

    // reset for processing of the next header
    itemCode = 0;
    subcase = 0;
    label.clear();
    fields.clear();
    isReal = false;
  }
}

void NstRecord::dprocess(NstReader & rdr, bool ispunch) const
{
  NstMesh & m(rdr.mesh());
  const uint nv(m.nvertices());
  const uint nl(size());
  if (nl < 2 or nv == 0)
    return;

  dbprint("NstRecord::dprocess(), lines ",first()," - ",last());

  // storage for displacements
  Matrix z(nv,6);
  size_t nr(0);

  if (ispunch) {

    // displacements in punch format:
    //      1001       G      6.937150E-03      5.348116E-05      9.216487E-02       7
    //-CONT-                  0.000000E+00      0.000000E+00      0.000000E+00       8

    // pattern for the first line
    static const string pattern1 = "\\s*" + rxint + "\\s*G\\s*"
        + rxfloat + "\\s*" + rxfloat + "\\s*" + rxfloat + ".*";
    static const boost::regex defline1(pattern1);

    // pattern for the second line
    static const string pattern2 = "\\s*-CONT-\\s*"
        + rxfloat + "\\s*" + rxfloat + "\\s*" + rxfloat + ".*";
    static const boost::regex defline2(pattern2);

    Vct6 def;
    int gid(0), state = 0;
    boost::smatch what;
    size_t ngarbage(0);
    const size_t ilast = last();
    for (size_t i=first(); i<=ilast; ++i) {

      // NOTE:
      // We can use strtod() directly in this case (instead of w2float)
      // because the displacement output in punch format always uses a
      // sensible floating-point format for encoding.

      const string & s = rdr.line(i);
      if ( state < 2 and boost::regex_match(s, what, defline1) ) {
        // matches 1 (gid) 2 5 8
        gid = genua_strtol( what[1].str().c_str(), nullptr, 10 );
        def[0] = genua_strtod( what[2].str().c_str(), nullptr );
        def[1] = genua_strtod( what[5].str().c_str(), nullptr );
        def[2] = genua_strtod( what[8].str().c_str(), nullptr );
        state = 2;
      } else if (state == 2 and boost::regex_match(s, what, defline2)) {
        // matches 1 4 7
        def[3] = genua_strtod( what[1].str().c_str(), nullptr );
        def[4] = genua_strtod( what[4].str().c_str(), nullptr );
        def[5] = genua_strtod( what[7].str().c_str(), nullptr );
        state = 1;

        // lookup coordinate
        uint r = m.gid2index(gid);
        if (r != NotFound) {
          for (int j=0; j<6; ++j)
            z(r,j) = def[j];
          ++nr;
        } else {
          dbprint("GID not found: ", gid);
        }

        def = 0.0;
      } else {
        ++ngarbage;
      }

      // jump out if all disps found
      if (nr == nv)
        break;
    }

    dbprint(ngarbage,"/",nl,"lines not recognized.");

  } else { // not punch format

    // try to parse a displacement line of the format
    // GID  G  tx ty tz rx ry rz
    double dx[6];
    for (uint i=1; i<nl; ++i) {

      uint gid = evparse(rdr.line(lbegin+i), dx);
      if (gid == NotFound)
        continue;

      // all displacements successfully read - store
      uint r = m.gid2index(gid);
      assert(r != NotFound);
      for (int j=0; j<6; ++j)
        z(r,j) = dx[j];
      ++nr;
      if (nr == nv)
        break;
    }

  }
  assert(nr == nv);
  
  // transform displacement into global coordinate system
  rdr.transformMode(z);
  
  // copy displacement into parent mesh
  m.appendDisp(z);

  cout << "Recovered " << nr << " displacemnt values. (" << nv << ") nodes" << endl;
}

void NstRecord::readGrid(NstReader & rdr) const
{
  Vct3 p;
  uint gid, cid(0), cd(0);
  StringArray wds;
  nstSplitLine( rdr.line(lbegin), wds );

  if (wds.size() < 6)
    return;
  gid = w2int(wds[1]);
  if (gid == 0)
    return;

  bool ok = true;
  ok &= w2float(wds[3], p[0]);
  ok &= w2float(wds[4], p[1]);
  ok &= w2float(wds[5], p[2]);
  if (not ok)
    return;

  // see if there is a coordinate system to read
  // strol() returns 0 if conversion is not possible or
  // the string consists of whitespace only -- 0 is default cid
  cid = strtol(wds[2].c_str(), 0, 10);
  
  if (wds.size() > 6)
    cd = strtol(wds[6].c_str(), 0, 10);

  rdr.addNode(p, gid, cid, cd);
}

void NstRecord::readBeam(NstReader & rdr) const
{
  uint a, b, eid, pid;
  StringArray words;
  nstSplitLine(rdr.line(lbegin), words);

  assert(words.size() > 7);
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(words[1]);
  pid = w2int(words[2]);
  a = m.gid2index(w2int(words[3]));
  b = m.gid2index(w2int(words[4]));
  
  Vct3 orn;
  orn[0] = w2float(words[5]);
  orn[1] = w2float(words[6]);
  orn[2] = w2float(words[7]);
  
  NstBeam *ep = new NstBeam(&m, a, b);
  ep->pid(pid);
  ep->id(eid);
  ep->orientation(orn);
  
  rdr.addElement(ep);
}

void NstRecord::readTria3(NstReader & rdr) const
{
  uint a, b, c, eid, pid;
  StringArray words;
  nstSplitLine(rdr.line(lbegin), words);
  assert(words.size() > 5);
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(words[1]);
  pid = w2int(words[2]);
  a = m.gid2index(w2int(words[3]));
  b = m.gid2index(w2int(words[4]));
  c = m.gid2index(w2int(words[5]));

  uint mcid(0);
  if (words.size() > 6)
    mcid = w2int(words[6]);
  
  NstTria3 *ep = new NstTria3(&m, a, b, c);
  ep->pid(pid);
  ep->id(eid);
  ep->mcid(mcid);
  
  rdr.addElement(ep);
}

void NstRecord::readTriaR(NstReader & rdr) const
{
  uint a, b, c, eid, pid;
  StringArray words;
  nstSplitLine(rdr.line(lbegin), words);
  assert(words.size() > 5);
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(words[1]);
  pid = w2int(words[2]);
  a = m.gid2index(w2int(words[3]));
  b = m.gid2index(w2int(words[4]));
  c = m.gid2index(w2int(words[5]));

  uint mcid(0);
  if (words.size() > 6)
    mcid = w2int(words[6]);
  
  NstTriaR *ep = new NstTriaR(&m, a, b, c);
  ep->pid(pid);
  ep->id(eid);
  ep->mcid(mcid);
  
  rdr.addElement(ep);
}

void NstRecord::readTria6(NstReader & rdr) const
{
  uint eid, pid, v[6];
  StringArray words;
  nstSplitLine(rdr.line(lbegin), words);
  assert(words.size() > 8);
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(words[1]);
  pid = w2int(words[2]);
  v[0] = m.gid2index(w2int(words[3]));
  v[1] = m.gid2index(w2int(words[4]));
  v[2] = m.gid2index(w2int(words[5]));
  v[3] = m.gid2index(w2int(words[6]));
  v[4] = m.gid2index(w2int(words[7]));
  v[5] = m.gid2index(w2int(words[8]));

  uint mcid(0);
  if (size() > 1) {
    nstSplitLine(rdr.line(lbegin+1), words);
    if (words.size() > 0)
      mcid = w2int(words[0]);
  }
  
  NstTria6 *ep = new NstTria6(&m, v);
  ep->pid(pid);
  ep->id(eid);
  ep->mcid(mcid);
  
  rdr.addElement(ep);
}

void NstRecord::readQuad4(NstReader & rdr) const
{
  uint a, b, c, d, eid, pid;
  StringArray words;
  nstSplitLine(rdr.line(lbegin), words);
  if (words.size() < 7) {
    dbprint("Invalid record: ",rdr.line(lbegin));
    for (size_t k=0; k<words.size(); ++k)
      dbprint("Word:",words[k]);
    return;
  }
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(words[1]);
  pid = w2int(words[2]);
  a = m.gid2index(w2int(words[3]));
  b = m.gid2index(w2int(words[4]));
  c = m.gid2index(w2int(words[5]));
  d = m.gid2index(w2int(words[6]));

  uint mcid(0);
  if (words.size() > 7)
    mcid = w2int(words[7]);
  
  NstQuad4 *ep = new NstQuad4(&m, a, b, c, d);
  ep->pid(pid);
  ep->id(eid);
  ep->mcid(mcid);
  
  rdr.addElement(ep);
}

void NstRecord::readQuadR(NstReader & rdr) const
{
  uint a, b, c, d, eid, pid;
  StringArray words;
  nstSplitLine(rdr.line(lbegin), words);
  assert(words.size() > 6);
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(words[1]);
  pid = w2int(words[2]);
  a = m.gid2index(w2int(words[3]));
  b = m.gid2index(w2int(words[4]));
  c = m.gid2index(w2int(words[5]));
  d = m.gid2index(w2int(words[6]));

  uint mcid(0);
  if (words.size() > 7)
    mcid = w2int(words[7]);
  
  NstQuadR *ep = new NstQuadR(&m, a, b, c, d);
  ep->pid(pid);
  ep->id(eid);
  ep->mcid(mcid);
  
  rdr.addElement(ep);
}

void NstRecord::readQuad8(NstReader & rdr) const
{
  uint eid, pid, v[8];
  StringArray words1, words2;
  
  assert(size() >= 2);
  // nstSplitLine(rdr.line(iln[0]), words1);
  // nstSplitLine(rdr.line(iln[1]), words2);
  nstSplitLine(rdr.line(lbegin), words1);
  nstSplitLine(rdr.line(lbegin+1), words2);
  assert(words1.size() > 8);
  assert(words2.size() > 2);
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(words1[1]);
  pid = w2int(words1[2]);
  v[0] = m.gid2index(w2int(words1[3]));
  v[1] = m.gid2index(w2int(words1[4]));
  v[2] = m.gid2index(w2int(words1[5]));
  v[3] = m.gid2index(w2int(words1[6]));
  v[4] = m.gid2index(w2int(words1[7]));
  v[5] = m.gid2index(w2int(words1[8]));
  v[6] = m.gid2index(w2int(words2[1]));
  v[7] = m.gid2index(w2int(words2[2]));
  
  uint mcid(0);
  if (words2.size() > 6)
    mcid = w2int(words2[6]);

  NstQuad8 *ep = new NstQuad8(&m, v);
  ep->pid(pid);
  ep->id(eid);
  ep->mcid(mcid);
  
  rdr.addElement(ep);
}

void NstRecord::readHexa(NstReader & rdr) const
{
  // maximum number of fields used : 3 lines of 10 fields
  const char *wds[12];
  int stage(0), nw, nread, tv[8], nv(8);
  
  uint eid(0), pid(0), v[20];
  const int maxlines = size();
  for (int i=0; i<maxlines; ++i) {

    const char *sbegin = rdr.line(lbegin+i).c_str();
    nw = nst_tokenize(sbegin, 10, wds);
    
    // cout << "CHEXA, line: [" << sbegin << "]" << endl;

    if (stage == 0) {

      // look for first line : at least 9 words
      if (nw < 9)
        continue;
      
      nread = words2ints(nw-1, &wds[1], 8, tv);
      if (nread != 8)
        continue;

      //      // debug
      //      for (int i=0; i<nread; ++i) {
      //        cout << "0 word: [" << string(wds[i+1], wds[i+2])
      //             << "], v = " << tv[i] << endl;
      //      }
      
      eid = tv[0];
      pid = tv[1];
      for (int j=0; j<6; ++j)
        v[j] = tv[2+j];
      
      stage = 1;
    }
    
    
    else if (stage == 1) {

      nread = words2ints(nw-1, &wds[1], 8, tv);

      //      // debug
      //      for (int i=0; i<nread; ++i) {
      //        cout << "1 word: [" << string(wds[i+1], wds[i+2])
      //             << "], v = " << tv[i] << endl;
      //      }

      // look for vertices 7,8 at least
      if (nw < 3)
        continue;

      if (nread == 2) {
        v[6] = tv[0];
        v[7] = tv[1];
        nv = 8;
        stage = 3;
      } else if (nread == 8) {
        for (int j=0; j<8; ++j)
          v[6+j] = tv[j];
        nv = 20;
        stage = 2;
      }
    }

    else if (stage == 2) {

      if (nw < 7)
        continue;

      nread = words2ints(nw-1, &wds[1], 6, tv);

      //      // debug
      //      for (int i=0; i<nread; ++i) {
      //        cout << "2 word: [" << string(wds[i+1], wds[i+2])
      //             << "], v = " << tv[i] << endl;
      //      }

      if (nread == 6) {
        for (int j=0; j<6; ++j)
          v[14+j] = tv[j];
        stage = 3;
      }
    }
    
    if (stage == 3)
      break;
  }
  
  // translate to index
  const NstMesh & m(rdr.mesh());
  uint vix[20];
  for (int i=0; i<nv; ++i)
    vix[i] = m.gid2index(v[i]);
  
  NstHexa *ep = new NstHexa(&m, vix, nv);
  ep->pid(pid);
  ep->id(eid);
  rdr.addElement(ep);
}

void NstRecord::readTetra(NstReader & rdr) const
{
  // maximum number of fields used : 2 lines of max 10 fields
  const char *wds[12];
  int stage(0), nw, nread, tv[8], nv(4);

  uint eid(0), pid(0), v[10];
  const int maxlines = size();
  for (int i=0; i<maxlines; ++i) {

    const char *sbegin = rdr.line(lbegin+i).c_str();
    nw = nst_tokenize(sbegin, 10, wds);

    if (stage == 0) {

      // look for first line : at least 7 words
      if (nw < 7)
        continue;

      nread = words2ints(nw-1, &wds[1], 8, tv);
      if (nread != 6 and nread != 8)
        continue;

      nv = (nread == 6) ? 4 : 10;

      eid = tv[0];
      pid = tv[1];
      for (int j=0; j<nread-2; ++j)
        v[j] = tv[2+j];

      stage = (nv == 4) ? 2 : 1;

    } else if (stage == 1) {

      // look for vertices 7-10
      if (nw < 4)
        continue;

      nread = words2ints(nw-1, &wds[1], 8, tv);
      if (nread == 4) {
        for (int k=0; k<4; ++k)
          v[6+k] = tv[k];
        stage = 2;
      }
    }

    if (stage == 2)
      break;
  }

  // translate to index
  const NstMesh & m(rdr.mesh());
  for (int i=0; i<nv; ++i)
    v[i] = m.gid2index(v[i]);

  NstTetra *ep = new NstTetra(&m, v, nv);
  ep->pid(pid);
  ep->id(eid);
  rdr.addElement(ep);
}

void NstRecord::readConm2(NstReader & rdr) const
{
  StringArray wds;
  nstSplitLine( rdr.line(lbegin), wds );
  
  Vct3 poff;
  double ms;
  int gid, cid, eid;
  
  const NstMesh & m(rdr.mesh());
  assert(wds.size() > 4);
  eid = w2int(wds[1]);
  gid = m.gid2index(w2int(wds[2]));
  cid = w2int(wds[3]);
  if (not w2float(wds[4], ms))
    return;
  
  // check if we need to read offset
  if (cid == -1) {
    assert(wds.size() > 7);
    for (int k=0; k<3; ++k)
      poff[k] = w2float(wds[5+k]);
  }
  
  // read inertia terms if present
  Mtx33 J;
  if (size() > 1) {
    nstSplitLine(rdr.line(lbegin+1), wds);
    if (wds.size() == 6) {
      J(0,0) = w2float(wds[0]);
      J(0,1) = J(1,0) = w2float(wds[1]);
      J(1,1) = w2float(wds[2]);
      J(0,2) = J(2,0) = w2float(wds[3]);
      J(1,2) = J(2,1) = w2float(wds[4]);
      J(2,2) = w2float(wds[5]);
    }
  }
  
  NstConMass *ep = new NstConMass(&m, gid);
  ep->id(eid);
  ep->mass(ms);
  ep->setJ(J);
  ep->offset(poff);
  
  rdr.addElement(ep);
}

void NstRecord::readCmass2(NstReader & rdr) const
{
  StringArray wds;
  nstSplitLine( rdr.line(lbegin), wds );
  assert(wds.size() > 6);
  
  double ms;
  int g[2], eid;
  NstDof dof[2];
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(wds[1]);
  ms = w2float(wds[2]);
  g[0] = m.gid2index(w2int(wds[3]));
  dof[0] =  w2dof(wds[4]);
  g[1] = m.gid2index(w2int(wds[5]));
  dof[1] = w2dof(wds[6]);
  
  NstScalarMass *ep = new NstScalarMass(&m, g[0], g[1]);
  ep->dof(dof[0], dof[1]);
  ep->id(eid);
  ep->mass(ms);
  
  rdr.addElement(ep);
}

void NstRecord::readCelas2(NstReader & rdr) const
{
  StringArray wds;
  nstSplitLine( rdr.line(lbegin), wds );

  double k;
  uint eid, g[2] = {NotFound, NotFound};
  NstDof dof[2] = {NstGrounded, NstGrounded};
  
  const NstMesh & m(rdr.mesh());
  eid = w2int(wds[1]);
  k = w2float(wds[2]);

  // don't throw exception on 'NotFound' because
  // CELAS can be a grounded element (GID == 0)
  g[0] = m.gid2index(w2int(wds[3]), false);
  dof[0] =  w2dof(wds[4]);

  if (wds.size() > 6) {
    g[1] = m.gid2index(w2int(wds[5]), false);
    dof[1] = w2dof(wds[6]);
  }
  
  if (g[0] == NotFound or g[1] == NotFound or
      dof[0] == 0 or dof[1] == 0)
    return;
  
  NstSpring *ep = new NstSpring(&m, g[0], g[1]);
  ep->dof(dof[0], dof[1]);
  ep->id(eid);
  ep->stiffness(k);
  
  rdr.addElement(ep);
}

void NstRecord::readRbar(NstReader & rdr) const
{
  StringArray wds;
  nstSplitLine( rdr.line(lbegin), wds );
  assert(wds.size() > 4);
  
  const NstMesh & m(rdr.mesh());
  uint a, b, eid, cna(0), cnb(0), cma(0), cmb(0);
  eid = w2int(wds[1]);
  a = m.gid2index(w2int(wds[2]));
  b = m.gid2index(w2int(wds[3]));
  
  if (not wds[4].empty())
    cna = w2int(wds[4]);
  if (wds.size() > 5 and (not wds[5].empty()))
    cnb = w2int(wds[5]);
  if (wds.size() > 6 and (not wds[6].empty()))
    cma = w2int(wds[6]);
  if (wds.size() > 7 and (not wds[7].empty()))
    cmb = w2int(wds[7]);
  
  NstRigidBar *ep = new NstRigidBar(&m, a, b);
  ep->id(eid);
  ep->components(cna, cnb, cma, cmb);
  
  rdr.addElement(ep);
}

void NstRecord::readRbe2(NstReader & rdr) const
{
  StringArray wds;
  
  
  Indices v(3);
  const NstMesh & m(rdr.mesh());
  
  // process first line
  nstSplitLine( rdr.line(lbegin), wds );
  assert(wds.size() > 4);
  
  uint eid, cm, gm, nw;
  eid = w2int(wds[1]);
  v[1] = m.gid2index(w2int(wds[2]));
  cm = w2int(wds[3]);
  v[2] = m.gid2index(w2int(wds[4]));
  
  nw = min(wds.size(), size_t(9));
  for (uint i=5; i<nw; ++i) {
    if (wds[i].empty())
      break;
    long c = strtol(wds[i].c_str(), 0, 0);
    if (c != 0) {
      gm = m.gid2index(c);
      if (gm != NotFound)
        v.push_back(gm);
      else
        break;
    } else {
      break;
    }
  }
  
  // FIXME: process remaining lines if present
  
  v[0] = v.size()-1;
  NstRigidBody2 *ep = new NstRigidBody2(&m, cm, v);
  ep->id(eid);
  rdr.addElement(ep);
}

void NstRecord::readCord2r(NstReader & rdr) const
{
  uint cid, rid;
  Vct3 a, b, c;
  StringArray words1, words2;
  
  assert(size() >= 2);
  nstSplitLine(rdr.line(lbegin), words1);
  nstSplitLine(rdr.line(lbegin+1), words2);

  //    // debug
  //    cout << "CORD2R count: " << words1.size() << ", " << words2.size() << endl;
  //    cout << "first line: [" << rdr.line(lbegin) << "]" << endl;
  //    for (uint i=0; i<words1.size(); ++i)
  //      cout << i << ": [" << words1[i] << "]" << endl;
  //    cout << "second line: [" << rdr.line(lbegin+1) << "]" << endl;
  //    for (uint i=0; i<words2.size(); ++i)
  //      cout << i << ": [" << words2[i] << "]" << endl;

  assert(words1.size() > 8);
  assert(words2.size() > 2);

  cid = w2int(words1[1]);
  rid = w2int(words1[2]);
  for (int k=0; k<3; ++k)
    a[k] = w2float(words1[3+k]);
  for (int k=0; k<3; ++k)
    b[k] = w2float(words1[6+k]);

  // first word is '*  ' only for long format entries
  int offs = (words2.size() > 3) ? 1 : 0;
  for (int k=0; k<3; ++k)
    c[k] = w2float(words2[offs+k]);
  
  NstCoordSys cs;
  cs.fromCord2r(a, b, c);
  rdr.addCoordSys(cid, cs);
}

void NstRecord::dump(const NstReader & rdr, std::ostream & os) const
{
  for (uint i=lbegin; i<lend; ++i)
    os << rdr.line(i) << endl;
}

