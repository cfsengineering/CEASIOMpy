
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
 
#include "iges128.h"
#include "igesfile.h"

void IgesSplineSurface::setup(int ncpu, int ncpv, int udegree, int vdegree,
                              const double ukts[],
                              const double vkts[],
                              const double cp[])
{
  polynomial = 1;
  ku = ncpu - 1;
  kv = ncpv - 1;
  mu = udegree;
  mv = vdegree;
  const uint nuk = ncpu + mu + 1;
  const uint nvk = ncpv + mv + 1;
  uknots = Vector(ukts, nuk);
  vknots = Vector(vkts, nvk);
  weights.clear();
  cpoints.resize(ncpu, ncpv);
  memcpy(cpoints.pointer(), cp, ncpu*ncpv*3*sizeof(double));
}

void IgesSplineSurface::setup(int ncpu, int ncpv, int udegree, int vdegree,
                              const double ukts[], const double vkts[],
                              const double wgt[], const double cp[])
{
  setup(ncpu, ncpv, udegree, vdegree, ukts, vkts, cp);
  polynomial = 0;
  weights.allocate(ncpu, ncpv);
  memcpy(weights.pointer(), wgt, ncpu*ncpv*sizeof(double));
}

void IgesSplineSurface::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  // set curve parameters
  par.addIntParameter( ku );
  par.addIntParameter( kv );
  par.addIntParameter( mu );
  par.addIntParameter( mv );
  par.addIntParameter( uclosed );
  par.addIntParameter( vclosed );
  par.addIntParameter( polynomial );
  par.addIntParameter( uperiodic );
  par.addIntParameter( vperiodic );

  // knot vector, unit weights and control points
  par.addParameter( ku+2+mu, uknots.pointer() );
  par.addParameter( kv+2+mv, vknots.pointer() );

  int ncp = (ku+1)*(kv+1);
  if (weights.size() == 0) {
    for (int i=0; i<ncp; ++i)
      par.addFloatParameter( 1.0 );
  } else {
    par.addParameter( ncp, weights.pointer() );
  }
  par.addParameter( 3*ncp, cpoints.pointer() );

  // first and last parameter
  par.addFloatParameter( 0.0 );
  par.addFloatParameter( 1.0 );
  par.addFloatParameter( 0.0 );
  par.addFloatParameter( 1.0 );
}

uint IgesSplineSurface::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 9)
    return 0;

  const char *s = pds.c_str();
  ku = asInt(s, vpos[0]);
  kv = asInt(s, vpos[1]);
  mu = asInt(s, vpos[2]);
  mv = asInt(s, vpos[3]);
  uclosed = asInt(s, vpos[4]);
  vclosed = asInt(s, vpos[5]);
  polynomial = asInt(s, vpos[6]);
  uperiodic = asInt(s, vpos[7]);
  vperiodic = asInt(s, vpos[8]);

  uint nused = 9;
  int ncpu = ku + 1;
  int ncpv = kv + 1;
  int ncp = ncpu*ncpv;
  int nuk = ncpu + mu + 1;
  int nvk = ncpv + mv + 1;

  if (vpos.size() < uint(13+nuk+nvk+4*ncp))
    return 0;

  uknots.allocate(nuk);
  for (int i=0; i<nuk; ++i)
    uknots[i] = asDouble(s, vpos[nused+i]);
  nused += nuk;

  vknots.allocate(nvk);
  for (int i=0; i<nvk; ++i)
    vknots[i] = asDouble(s, vpos[nused+i]);
  nused += nvk;

  weights.allocate(ncpu,ncpv);
  for (int j=0; j<ncpv; ++j)
    for (int i=0; i<ncpu; ++i)
      weights(i,j) = asDouble(s, vpos[nused+j*ncpu+i]);
  nused += ncp;

  cpoints.resize(ncpu, ncpv);
  for (int j=0; j<ncpv; ++j)
    for (int i=0; i<ncpu; ++i)
      for (int k=0; k<3; ++k)
        cpoints(i,j)[k] = asDouble(s, vpos[nused+3*(j*ncpu + i)+k]);
  nused += 3*ncp;

  ustart = asDouble(s, vpos[nused+0]);
  uend = asDouble(s, vpos[nused+1]);
  vstart = asDouble(s, vpos[nused+2]);
  vend = asDouble(s, vpos[nused+3]);
  nused += 4;

  return nused;
}
