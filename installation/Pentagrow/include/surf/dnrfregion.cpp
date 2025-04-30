
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
 
#include <genua/strutils.h>
#include "dnrfregion.h"

using namespace std;

XmlElement DnRefineRegion::toXml() const 
{
  XmlElement xe("RefinementRegion");
  if (rtype == DnRectRegion) {
    xe["lower"] = str(rfd[0]) + " " + str(rfd[1]);
    xe["upper"] = str(rfd[2]) + " " + str(rfd[3]);
  } else {
    xe["center"] = str(rfd[0]) + " " + str(rfd[1]);
    xe["ru"] = str(rfd[2]);
    xe["rv"] = str(rfd[3]);
  }
  xe["factor"] = str(1.0 / rfd[4]);
  return xe;
}

void DnRefineRegion::fromXml(const XmlElement & xe)
{
  if (xe.hasAttribute("center")) {
    rtype = DnRadialRegion;
    Vct2 ctr;
    fromString(xe.attribute("center"), ctr);
    rfd[0] = ctr[0];
    rfd[1] = ctr[1];
    rfd[2] = Float(xe.attribute("ru"));
    rfd[3] = Float(xe.attribute("rv"));
  } else {
    rtype = DnRectRegion;
    Vct2 plo, phi;
    fromString(xe.attribute("lower"), plo);
    fromString(xe.attribute("upper"), phi);
    rfd[0] = plo[0];
    rfd[1] = plo[1];
    rfd[2] = phi[0];
    rfd[3] = phi[1];
  }
  rfd[4] = 1.0 / Float(xe.attribute("factor"));
}
