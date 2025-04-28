
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
 
#include "cgstrip.h"
#include "strutils.h"

using namespace std;

void CgStrip::append(const std::string & s, uint voff)
{
  const char *pos = s.c_str();
  char *tail;
  Indices ts;
  uint v;
  do {

    ts.clear();
    do {
      v = genua_strtol(pos, &tail, 10);
      if (pos == tail)
        break;
      ts.push_back(v + voff);
      pos = tail;
    } while (*pos != ',');

    // import single triangle strip
    append(ts.begin(), ts.end());

    // move forward to next digit
    while (not isdigit(*pos) and *pos != 0)
      ++pos;

  } while (*tail != 0 and *pos != 0);
}

uint CgStrip::strips2triangles(Indices & t) const
{
  uint ntotal(0);
  uint v[3];
  for (uint j=0; j<nstrip(); ++j) {
    const int nts = size(j) - 2;
    const uint *ts = first(j);
    for (int i=0; i<nts; ++i) {
      if (i%2 == 0) {
        v[0] = ts[i];
        v[1] = ts[i+1];
        v[2] = ts[i+2];
      } else {
        v[0] = ts[i+1];
        v[1] = ts[i];
        v[2] = ts[i+2];
      }
      t.insert(t.end(), v, v+3);
    }
    ntotal += nts;
  }
  return ntotal;
}

uint CgStrip::fans2triangles(Indices & t) const
{
  uint ntotal(0);
  uint v[3];
  for (uint j=0; j<nstrip(); ++j) {
    const int nts = size(j) - 2;
    const uint *ts = first(j);
    v[0] = ts[0];
    v[1] = ts[1];
    v[2] = ts[2];
    t.insert(t.end(), v, v+3);
    for (int i=1; i<nts; ++i) {
      v[1] = v[2];
      v[2] = ts[i+2];
      t.insert(t.end(), v, v+3);
    }
    ntotal += nts;
  }
  return ntotal;
}

uint CgStrip::poly2lines(Indices & lns, int voffset) const
{
  uint ntotal(0);
  const int ns = nstrip();
  for (int j=0; j<ns; ++j) {
    const int fst = offset(j);
    const int np = size(j);
    for (int i=0; i<np-1; ++i) {
      int k = fst + i + voffset;
      lns.push_back(k);
      lns.push_back(k+1);
    }
    ntotal += np;
  }
  return ntotal;
}

void CgStrip::pointerOffsets(BufferOffset & boff) const
{
  const uint ns = nstrip();
  if (useStrips) {
    boff.resizeOffset(ns);
    for (uint i=0; i<ns; ++i) {
      boff.poff[i] = ((const char *) 0) + offset(i)*sizeof(Indices::value_type);
      boff.pcount[i] = size(i);
    }
  } else {
    boff.resizeFirstp(ns);
    for (uint i=0; i<ns; ++i) {
      boff.pcount[i] = size(i);
      boff.pfirst[i] = offset(i);
    }
  }
}

void CgStrip::merge(const CgStrip & s, uint voff)
{
  assert(useStrips == s.useStrips);

  if (useStrips) {

  // append vertex indices to end of array
  const uint soff = istrip.size();
  const int nv = s.istrip.size();
  istrip.resize(soff + nv);
  for (int i=0; i<nv; ++i)
    istrip[soff+i] = s.istrip[i] + voff;

  // append strip offsets
  const int ns = s.nstrip();
  const int foff = ifirst.size();
  ifirst.resize(foff + ns);
  for (int i=0; i<ns; ++i)
    ifirst[foff+i] = s.ifirst[i+1] + soff;

  } else {

    // append shifted offsets
    const uint foff = ifirst.size();
    const int nss = s.nstrip();
    ifirst.resize(foff+nss);
    for (int i=0; i<nss; ++i)
      ifirst[foff+i] = s.ifirst[i+1] + voff;
  }
}

float CgStrip::megabytes() const
{
  float bytes = sizeof(CgStrip);
  bytes += istrip.capacity() * sizeof(Indices::value_type);
  bytes += ifirst.capacity() * sizeof(Indices::value_type);
  return 1e-6f * bytes;
}

XmlElement CgStrip::toXml(bool share) const
{
  XmlElement xe("CgStrip");
  xe["strips"] = str(strips());

  XmlElement xo("Offsets");
  xo["count"] = str(ifirst.size());
  xo.asBinary(ifirst.size(), &ifirst[0], share);
  xe.append(xo);

  if (strips()) {
    XmlElement xs("Strips");
    xs["count"] = str(istrip.size());
    xs.asBinary(istrip.size(), &istrip[0], share);
    xe.append(xs);
  }

  return xe;
}

void CgStrip::fromXml(const XmlElement & xe)
{
  clear();

  assert(xe.name() == "CgStrip");
  XmlElement::const_iterator itr, last;
  last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "Strips") {
      const uint n = Int( itr->attribute("count") );
      istrip.resize(n);
      if (n > 0)
        itr->fetch(n, &istrip[0]);
    } else if (itr->name() == "Offsets") {
      const uint n = Int( itr->attribute("count") );
      ifirst.resize(n);
      if (n > 0)
        itr->fetch(n, &ifirst[0]);
    }
  }

  if (xe.hasAttribute("strips"))
    fromString(xe.attribute("strips"), useStrips);
}
