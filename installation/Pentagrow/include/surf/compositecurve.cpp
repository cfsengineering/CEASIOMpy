
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

#include "compositecurve.h"
#include "mappedcurve.h"
#include "iges102.h"
#include "iges402.h"
#include "igesfile.h"
#include <genua/dbprint.h>
#include <sstream>

using namespace std;

const Vector & CompositeCurve::init(const AbstractCurveArray &ca)
{
  m_curves = ca;
  breakPoints();
  return m_tbreak;
}

CompositeCurve *CompositeCurve::clone() const
{
  return ( new CompositeCurve(*this) );
}

Vct3 CompositeCurve::eval(Real t) const
{
  assert(not m_curves.empty());
  Real ti;
  uint s = segment(t, ti);
  return m_curves[s-1]->eval(ti);
}

Vct3 CompositeCurve::derive(Real t, uint k) const
{
  assert(not m_curves.empty());
  Real ti;
  uint s = segment(t, ti);
  return m_curves[s-1]->derive(ti, k);
}

void CompositeCurve::apply()
{
  const int nc = m_curves.size();
  for (int i=0; i<nc; ++i) {
    m_curves[i]->setTrafoMatrix( this->trafoMatrix() );
    m_curves[i]->apply();
  }
  RFrame::clear();
}

void CompositeCurve::tgline(Real t, Vct3 & c, Vct3 & dc) const
{
  assert(not m_curves.empty());
  Real ti;
  uint s = segment(t, ti);
  m_curves[s-1]->tgline(ti, c, dc);
}

void CompositeCurve::initGrid(Vector &t) const
{
  t.clear();
  Vector tc;
  const int nc = m_curves.size();
  for (int i=0; i<nc; ++i) {
    Real t1 = m_tbreak[i];
    Real t2 = m_tbreak[i+1];
    m_curves[i]->initGrid(tc);
    tc = (t2 - t1)*tc + t1;
    t.insert(t.end(), tc.begin(), tc.end());
  }

  // eliminate duplicate values
  almost_equal<Real> pred(1e-4);
  t.erase(std::unique(t.begin(), t.end(), pred), t.end());
}

void CompositeCurve::breakPoints()
{
  // arc length parametrization
  const int nc = m_curves.size();
  m_tbreak.clear();
  m_tbreak.resize(nc + 1);
  Vector t;
  for (int i=0; i<nc; ++i) {
    t.clear();
    m_curves[i]->initGrid(t);
    Vct3 p1, p2;
    Real clen = 0.0;
    p1 = m_curves[i]->eval(t[0]);
    for (uint j=1; j<t.size(); ++j) {
      p2 = m_curves[i]->eval(t[j]);
      clen += norm(p2 - p1);
      p1 = p2;
    }
    m_tbreak[i+1] = m_tbreak[i] + clen;
  }
  m_tbreak /= m_tbreak.back();
}

XmlElement CompositeCurve::toXml(bool share) const
{
  XmlElement xe("CompositeCurve");
  xe["name"] = name();
  const int nc = m_curves.size();
  xe["count"] = str(m_curves.size());
  for (int i=0; i<nc; ++i)
    xe.append( m_curves[i]->toXml(share) );

  XmlElement xb("BreakPoints");
  xb["count"] = str(m_tbreak.size());
  xb.asBinary(m_tbreak.size(), m_tbreak.pointer(), share);
  xe.append(std::move(xb));

  return xe;
}

void CompositeCurve::fromXml(const XmlElement & xe)
{
  clearSurface();
  assert(xe.name() == "CompositeCurve");
  rename(xe.attribute("name"));
  const uint nc = Int( xe.attribute("count") );
  XmlElement::const_iterator itr, ilast = xe.end();
  for (itr = xe.begin(); itr != ilast; ++itr) {
    if (itr->name() == "BreakPoints") {
      m_tbreak.resize( Int(itr->attribute("count")) );
      itr->fetch(m_tbreak.size(), m_tbreak.pointer());
    } else {
      AbstractCurvePtr acp = AbstractCurve::createFromXml(*itr);
      if (acp)
        m_curves.push_back(acp);
    }
  }
  if (m_curves.size() != nc) {
    stringstream ss;
    ss << "Reading CompositeCurve from XML: Expected " << nc;
    ss << " constituent curves, found " << m_curves.size() << endl;
    throw Error(ss.str());
  }
}

int CompositeCurve::toIges(IgesFile & file, int tfi) const
{
  IgesDirEntry entry;

  // write all subcurves and keep their DE entries
  Indices cde(m_curves.size());
  for (uint i=0; i<m_curves.size(); ++i) {
    cde[i] = m_curves[i]->toIges(file);
    if (cde[i] == 0)
      return 0;

    file.directory().fillEntry(cde[i], entry);
    entry.subswitch = 1;
    file.directory().changeEntry(cde[i], entry);
  }

  // write CompositeCurve entity
  IgesCompositeCurve e102;
  e102.curves = cde;
  e102.trafoMatrix(tfi);
  return e102.append(file);
}

bool CompositeCurve::fromIges(const IgesFile &file, const IgesDirEntry &entry)
{
  clearSurface();
  if (entry.etype != 102 and entry.etype != 402)
    return false;

  // fetch parent entry
  IgesEntityPtr eptr = file.createEntity(entry);
  if (entry.etype == 102) {
    IgesCompositeCurve cce;
    if (not IgesEntity::as(eptr, cce))
      return false;

    // retrieve child curves
    IgesDirEntry echild;
    const int ncc = cce.curves.size();
    for (int i=0; i<ncc; ++i) {
      file.dirEntry(cce.curves[i], echild);
      AbstractCurvePtr acp = AbstractCurve::createFromIges(file, echild);
      if (acp)
        m_curves.push_back(acp);
      else
        return false;
    }
    setIgesName(file, cce);
  } else if (entry.etype == 402) {
    IgesAssociativity assoc;
    if (IgesEntity::as(eptr, assoc)) {
      uint nsub = assoc.size();
      IgesDirEntry echild;
      for (uint j=0; j<nsub; ++j) {
        file.dirEntry(assoc[j], echild);
        AbstractCurvePtr acp = AbstractCurve::createFromIges(file, echild);
        if (acp)
          m_curves.push_back(acp);
        else
          return false;
      }
    }
    setIgesName(file, assoc);

    // may need to sort segments, not only flip
  }

  setIgesTransform(file, entry);
  flipSegments();
  // breakPoints();

  return true;
}

typedef std::pair<Vct3, Vct3> PointPair;
typedef std::vector<PointPair> PairArray;

enum Joining { HT=0, TH=1, HH=2, TT=3 };

static int ppdistance(const PairArray &p, uint a, uint b, Real d[])
{
  int imin = HT;
  d[HT] = sq(p[a].first - p[b].second);
  d[TH] = sq(p[a].second - p[b].first);
  if (d[TH] < d[imin])
    imin = TH;
  d[HH] = sq(p[a].first - p[b].first);
  if (d[HH] < d[imin])
    imin = HH;
  d[TT] = sq(p[a].second - p[b].second);
  if (d[TT] < d[imin])
    imin = TT;
  return imin;
}

static AbstractCurvePtr reverse_curve(AbstractCurvePtr acp)
{
  return boost::make_shared<MappedCurve>(acp, -1.0, 1.0);
}

void CompositeCurve::flipSegments()
{
  const size_t nc = m_curves.size();
  if (nc < 2)
    return;

  PairArray pts(nc);
  for (size_t i=0; i<nc; ++i)
    pts[i] = std::make_pair( m_curves[i]->eval(0.0),
                             m_curves[i]->eval(1.0) );

  // even the first curve segment may need to be flipped
  AbstractCurveArray cv(nc);

  Real dst[4];
  int tag = ppdistance(pts, 0, 1, dst);
  if (tag == TH) {
    cv[0] = m_curves[0];
    cv[1] = m_curves[1];
  } else if (tag == HH) {
    cv[0] = reverse_curve(m_curves[0]);
    cv[1] = m_curves[1];

  } else if (tag == HT) {
    cv[0] = reverse_curve(m_curves[0]);
    cv[1] = reverse_curve(m_curves[1]);

  } else { // TT
    cv[0] = m_curves[0];
    cv[1] = reverse_curve(m_curves[1]);

  }

  for (size_t i=2; i<nc; ++i) {
    tag = ppdistance(pts, i-1, i, dst);
    if (tag == TH or tag == HH) {
      cv[i] = m_curves[i];
    } else {
      cv[i] = reverse_curve(m_curves[i]);
    }
  }

  m_curves.swap(cv);
  breakPoints();
}


