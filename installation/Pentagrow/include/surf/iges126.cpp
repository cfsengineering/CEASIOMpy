
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
 
#include "iges126.h"
#include "igesfile.h"

void IgesSplineCurve::setup(int ncp, int degree, const double kts[],
                            const double cp[])
{
  polynomial = 1;
  k = ncp - 1;
  m = degree;
  nknots = ncp + m + 1;

  weights.clear();
  knots = Vector(kts, nknots);
  cpoints.resize(ncp);
  memcpy(cpoints.pointer(), cp, 3*ncp*sizeof(double));
}

void IgesSplineCurve::setup(int ncp, int degree, const double kts[],
                            const double wgt[], const double cp[])
{
  setup(ncp, degree, kts, cp);
  polynomial = 0;
  weights = Vector(wgt, ncp);
}

void IgesSplineCurve::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  // set curve parameters
  par.addIntParameter( k );
  par.addIntParameter( m );
  par.addIntParameter( planar );
  par.addIntParameter( closed );
  par.addIntParameter( polynomial );
  par.addIntParameter( periodic );

  // knot vector, unit weights and control points
  par.addParameter( k+2+m, knots.pointer() );

  if (weights.empty()) {
    for (int i=0; i<=k; ++i)
      par.addFloatParameter( 1.0 );
  } else {
    par.addParameter( k+1, weights.pointer() );
  }
  par.addParameter( 3*(k+1), cpoints.pointer() );

  // first and last parameter
  par.addFloatParameter( 0.0 );
  par.addFloatParameter( 1.0 );

  // normal vector for planar curve
  par.addFloatParameter( 0.0 );
  par.addFloatParameter( 0.0 );
  par.addFloatParameter( 0.0 );
}

uint IgesSplineCurve::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 6)
    return 0;

  const char *s = pds.c_str();
  k = asInt(s, vpos[0]);
  m = asInt(s, vpos[1]);
  planar = asInt(s, vpos[2]);
  closed = asInt(s, vpos[3]);
  polynomial = asInt(s, vpos[4]);
  periodic = asInt(s, vpos[5]);

  uint nused = 6;
  int ncp = k + 1;
  int nknots = ncp + m + 1;

  if (vpos.size() < uint(11+nknots+4*ncp))
    return 0;

  knots.allocate(nknots);
  for (int i=0; i<nknots; ++i)
    knots[i] = asDouble(s, vpos[nused+i]);
  nused += nknots;

  weights.allocate(ncp);
  for (int i=0; i<ncp; ++i)
    weights[i] = asDouble(s, vpos[nused+i]);
  nused += ncp;

  cpoints.resize(ncp);
  for (int i=0; i<ncp; ++i)
    for (int ki=0; ki<3; ++ki)
      cpoints[i][ki] = asDouble(s, vpos[nused+3*i+ki]);
  nused += 3*ncp;

  ustart = asDouble(s, vpos[nused+0]);
  uend = asDouble(s, vpos[nused+1]);
  nused += 2;

  for (int i=0; i<3; ++i)
    nrm[i] = asDouble(s, vpos[nused+i]);
  nused += 3;

  return nused;
}

