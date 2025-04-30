
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

#include "defines.h"
#include "strutils.h"
#include <fstream>
#include <sstream>

#ifdef _WIN32
#include <Windows.h>  // for multi-byte string conversion
#endif

using namespace std;

vector<string> split(const string & sin, const string & sep)
{
  // split string into tokens
  vector<string> words;

  string s = strip(sin, sep);
  
  if (s.empty())
    return words;
  
  string::size_type pos;
  string sub;

  pos = s.find_first_of(sep);
  while (pos != string::npos)
  {
    sub = s.substr(0, pos);
    sub = strip(sub, sep);
    if (!sub.empty())
      words.push_back(sub);
    s = s.substr(pos, string::npos);
    s = strip(s,sep);
    pos = s.find_first_of(sep);
  }

  if (!s.empty())
    words.push_back(s);

  return words;
}

string strip(const string & s, const string & wsp)
{
  // strip whitespace
  if (s.empty())
    return s;

  string::size_type first, last;
  first = s.find_first_not_of(wsp);
  last = s.find_last_not_of(wsp);

  if (first == string::npos and last == string::npos)
    return string();
  else if (first > last)
    return string();
  else
    return s.substr(first, last-first+1);
}

string strip_comments(const string & s, const string & cmtid)
{
  // return line with comments removed
  string cleared;
  string::size_type cmt_pos;

  cmt_pos = s.find_first_of(cmtid);
  cleared = s.substr(0, cmt_pos);

  return cleared;
}

vector<double> lineToDouble(const string & lin)
{
  string line = strip(lin);
  vector<string> nums = split(line);

  vector<double> v;
  double x;
  for (uint i=0; i<nums.size(); i++)
  {
    if (!nums[i].empty())
    {
      x = atof( nums[i].c_str() );
      //  cerr << x << "  ";
      v.push_back(x);
    }
  }
  //cerr << endl;

  return v;
}

vector<int> lineToInt(const string & lin)
{
  string line = strip(lin);
  vector<string> nums = split(line);
  vector<int> v;
  for (uint i=0; i<nums.size(); i++)
    v.push_back( atoi( nums[i].c_str() ) );

  return v;
}

void fromString(const string & s, bool & obj)
{
  // read boolean variable
  if (s == "1" or s == "true" or s == "TRUE" or s == "True"
      or s == "YES" or s == "yes" or s == "Yes")
    obj = true;
  else
    obj = false;
}

string nstr(Real x)
{
  string s;
  if (fabs(x) < 1e-99) {
    return string("0.");
  } else if (  (x > 0.001 and x < 1e7) or      // one char needed for '-'
               (x < -0.01 and x > -1e6) ) {
    int xp, prc(6);
    xp = int(log10(fabs(x)));
    stringstream ss;
    ss << fixed << showpoint;
    if (xp > 0)
      prc -= xp;
    if (x < 0)
      --prc;
    ss.precision( max(prc,0) );
    ss << x;
    s = ss.str();
  } else {
    int prc, xp;
    Real dxp = round( log10(fabs(x)) );
    xp = int(dxp);
    if (pow(10.0, double(xp)) != fabs(x)) {
      Real m = x * pow(0.1, xp);
      prc = 4;
      if (xp < 0)
        --prc;
      if (x < 0)
        --prc;
      if (abs(xp) > 9)
        --prc;
      if (abs(xp) > 99)
        --prc;
      
      stringstream ss;
      ss << fixed << showpoint;
      ss.precision( max(prc,0) );
      ss << m << 'E' << xp;
      s = ss.str();
    } else {

      // special case : x is a power of 10
      stringstream ss;
      ss << "1.E" << xp;
      s = ss.str();
    }
  }

  if (s.find('E') == string::npos) {
    uint lnz, n;
    lnz = n = s.size();
    for (uint i=0; i<n; ++i) {
      if ( s[n-1-i] == '0' )
        lnz--;
      else
        break;
    }
    return s.substr(0, lnz);
  }

  return s;
}

std::string append_suffix(const std::string & fname, const std::string & sfx)
{
  string::size_type pos;
  pos = fname.rfind('.');
  if (pos == string::npos)
    return fname + sfx;
  else
    return fname.substr(0, pos) + sfx;
}

std::string filename_suffix(const std::string & fname)
{
  string::size_type pos;
  pos = fname.rfind('.');
  if (pos != string::npos)
    return fname.substr(pos, fname.size() - pos);
  else
    return std::string();
}

std::string strip_suffix(const std::string &fname)
{
  string::size_type pos;
  pos = fname.rfind('.');
  if (pos != string::npos)
    return fname.substr(0, pos);
  else
    return fname;
}

std::string format_time(double sec, int secprec)
{
  stringstream ss;
  ss.precision(secprec);
  ss << fixed;

  int nh(0), nm(0);
  if (sec >= 3600) {
    nh = int (sec/3600.0);
    ss << nh << ':';
    sec -= nh * 3600.0;
  }

  if (sec >= 60) {
    nm = int(sec/60.0);
    if (nm < 10)
      ss << '0';
    ss << nm << ':';
    sec -= nm * 60.0;
  } else if (nh > 0) {
    ss << "00:";
  }

  ss << sec;
  return ss.str();
}

#ifdef _WIN32

std::wstring utf8ToWide(const string &u8s)
{
  const char *filename = u8s.c_str();
  size_t fnlen = MultiByteToWideChar(CP_UTF8, 0, filename, -1, 0, 0);
  std::wstring w;
  w.resize(fnlen);
  int stat = MultiByteToWideChar(CP_UTF8, 0, filename, -1, &w[0], fnlen );
  if (stat == 0)
    w.clear();
  return w;
}

#endif

bool file_exists(const string &fname)
{
  ifstream in(fname.c_str());
  return in.good();
}

std::string file_contents(const string &fname)
{
  //  ifstream in(fname);
  //  stringstream ss;
  //  ss << in.rdbuf();
  //  return ss.str();

  string contents;
  ifstream in(fname, std::ios::in | std::ios::binary);
  if (in) {
    in.seekg(0, std::ios::end);
    contents.resize(in.tellg());
    in.seekg(0, std::ios::beg);
    in.read(&contents[0], contents.size());
  }
  return contents;
}

std::string path2filename(const std::string &s)
{
  string::size_type p1 = s.find_last_of('/');
  if (p1 == string::npos)
    p1 = s.find_last_of('\\');
  if (p1 != string::npos)
    return s.substr(p1+1);
  else
    return s;
}


