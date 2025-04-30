
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
 
#include "topovertex.h"
#include "topology.h"
#include <iostream>

using namespace std;

TopoVertex::TopoVertex(const Topology &topo, uint iface, const Vct2 &uvp)
{
  m_faces.push_back(iface);
  m_uvp.push_back(uvp);
  m_position = topo.face(iface).eval(uvp[0], uvp[1]);
}

TopoVertex::TopoVertex(const Topology &topo, uint ifa, const Vct2 &uva,
                       uint ifb, const Vct2 &uvb)
{
  m_faces.push_back(ifa);
  m_faces.push_back(ifb);
  m_uvp.push_back(uva);
  m_uvp.push_back(uvb);
  m_position = 0.5* ( topo.face(ifa).eval(uva[0], uva[1])
      + topo.face(ifb).eval(uvb[0], uvb[1]) );
}

uint TopoVertex::append(uint iface, const Vct2 &uvp)
{
  uint idx = m_faces.size();
  m_faces.push_back(iface);
  m_uvp.push_back(uvp);
  return idx;
}

void TopoVertex::merge(const TopoVertex &v)
{
  const Indices & fv( v.faces() );
  const int nf = fv.size();
  for (int i=0; i<nf; ++i) {
    m_faces.insert(m_faces.end(), fv[i]);
    m_uvp.insert(m_uvp.end(), v.m_uvp[i]);
  }
}

void TopoVertex::print(uint k, std::ostream &os) const
{
  os << "TopoVertex " << k << " at " << m_position << endl;
  for (uint i=0; i<m_uvp.size(); ++i)
    os << " - Face " << m_faces[i] << " (u,v) = " << m_uvp[i] << endl;
}
