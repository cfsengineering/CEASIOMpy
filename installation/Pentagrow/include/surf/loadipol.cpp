
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
 
#include "loadipol.h"
#include <genua/xcept.h>

uint LoadIpol::cpimport(const MxMesh & mx, uint ifield)
{
  if (mx.nnodes() != nnodes())
    throw Error("LoadIpol::cpimport() - "
                "Import mesh has incompatible node count.");

  const MxMeshField & fcp( mx.field(ifield) );
  if ((not fcp.nodal()) or (not fcp.realField())
      or (fcp.ndimension() != 1))
    throw Error("LoadIpol::cpimport() -- "
                "Imported field is not a scalar nodal field.");

  // Vector cp( fcp.realPointer(), nnodes() );
  Vector cp;
  fcp.fetch(cp);
  return appendField("CoefPressure", cp);
}

void LoadIpol::markReference(uint k, const Vector & x)
{
  if (k == NotFound)
    throw Error("LoadIpol::markReference() - "
                "Cannot set undefined field as reference.");
  iReference = k;
  normState(x, xnref);
}

void LoadIpol::markDerivative(uint kf, uint kx)
{
  if (kf == NotFound)
    throw Error("LoadIpol::markDerivative() - "
                "Cannot set undefined field.");

  assert(kx < iDeriv.size());
  iDeriv[kx] = kf;

  // assume that field kf contains dcp/dx,
  // convert to dcp/dxn
  // Vector tmp( field(kf).realPointer(), nnodes() );
  // tmp /= xhi[kx] - xlo[kx];
  // field(kx).scalarField( field(kx).name(), tmp );
}

void LoadIpol::eval(const Vector & x, Vector & cp) const
{
  // normalized state
  const int ns = nstate();
  const int nn = nnodes();
  Vector xn(ns);
  normState(x, xn);

  // set reference solution or zero
  Vector tmp;
  if (iReference != NotFound)
    field(iReference).fetch(tmp);
    // tmp = Vector( field(iReference).realPointer(), nnodes() );
  else
    tmp.resize( nnodes() );

  // evaluate nonlinear load model

  // accumulate linear derivatives
  for (int j=0; j<ns; ++j) {

    // skip nonlinear states
    if (iDeriv[j] == NotFound)
      continue;

    Real dx;
    if (iReference != NotFound)
      dx = (xn[j] - xnref[j]) * (xhi[j] - xlo[j]);
    else
      dx = xn[j] * (xhi[j] - xlo[j]);

    // const Real *r = field(iDeriv[j]).realPointer();
    Vector r;
    field(iDeriv[j]).fetch(r);
    for (int i=0; i<nn; ++i)
      tmp[i] += dx*r[i];
  }

  cp.swap(tmp);
}

void LoadIpol::createNote()
{
  XmlElement xe("LoadInterpolator");
  const int nx = nstate();
  xe["nstate"] = str(nx);
  xe["reference"] = str(iReference);

  XmlElement xd("Derivatives");
  xd["count"] = str(iDeriv.size());
  xd.asBinary(iDeriv.size(), &iDeriv[0]);
  xe.append(std::move(xd));

  for (int i=0; i<nx; ++i) {
    XmlElement xs("State");
    xs["index"] = str(i);
    xs["low"] = str(xlo[i]);
    xs["high"] = str(xhi[i]);
    xs["xnref"] = str(xnref[i]);
    xs["name"] = stateNames[i];
    xe.append(std::move(xs));
  }

  if (xnote.name().empty()) {
    annotate(xe);
  } else {
    XmlElement::const_iterator ite;
    ite = xnote.findChild("LoadInterpolator");
    if (ite == xnote.end())
      xnote.append(xe);
    else
      xnote.replace( std::distance(xnote.begin(), ite), xe );
  }
}

bool LoadIpol::extractNote()
{
  XmlElement::const_iterator itn, nlast = noteEnd();
  for (itn = noteBegin(); itn != nlast; ++itn) {
    if (itn->name() == "LoadInterpolator") {
      uint nx = Int( itn->attribute("nstate") );
      iReference = itn->attr2int("reference", NotFound);

      stateNames.resize( nx );
      xlo.resize( nx );
      xhi.resize( nx );
      xnref.resize( nx );
      XmlElement::const_iterator ite, ilast = itn->end();
      for (ite = itn->begin(); ite != ilast; ++ite) {
        if (ite->name() == "State") {
          uint idx = Int(ite->attribute("index"));
          xlo[idx] = ite->attr2float("low", 0.0);
          xhi[idx] = ite->attr2float("high", 1.0);
          xnref[idx] = ite->attr2float("xnref", 0.0);
          stateNames[idx] = ite->attribute("name");
        } else if (ite->name() == "Derivatives") {
          iDeriv.resize( Int(ite->attribute("count")) );
          ite->fetch(iDeriv.size(), &iDeriv[0]);
        }
      }
      return true;
    }
  }
  return false;
}

