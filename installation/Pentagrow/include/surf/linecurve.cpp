
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
 

#include "igesdirentry.h"
#include "igesfile.h"
#include "iges110.h"
#include "linecurve.h"
#include <genua/dbprint.h>

void LineCurve::initGrid(Vector &t) const
{
  t.resize(2);
  t[0] = 0.0;
  t[1] = 1.0;
}

void LineCurve::apply()
{
  pStart = RFrame::forward(pStart);
  pEnd = RFrame::forward(pEnd);
  RFrame::clear();
}

XmlElement LineCurve::toXml(bool) const
{
  XmlElement xe("LineCurve");
  xe["name"] = name();
  xe["start"] = str(pStart);
  xe["end"] = str(pEnd);
  return xe;
}

void LineCurve::fromXml(const XmlElement &xe)
{
  rename(xe.attribute("name"));
  fromString(xe.attribute("start"), pStart);
  fromString(xe.attribute("end"), pEnd);
}

bool LineCurve::fromIges(const IgesFile &file, const IgesDirEntry &dir)
{
  assert(dir.etype == 110);

  IgesLineEntity e110;
  if (not file.createEntity(dir, e110))
    return false;

  const double *p1 = e110.point1();
  const double *p2 = e110.point2();
  for (int k=0; k<3; ++k) {
    pStart[k] = p1[k];
    pEnd[k] = p2[k];
  }

  setIgesName(file, e110);
  setIgesTransform(file, dir);

  return true;
}

int LineCurve::toIges(IgesFile &file, int tfi) const
{
  IgesLineEntity e110;
  e110.setup(pStart.pointer(), pEnd.pointer());
  e110.trafoMatrix(tfi);
  return e110.append(file);
}

