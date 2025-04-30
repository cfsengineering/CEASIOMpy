
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
 
#include "meshgenerator.h"
#include "assembly.h"

using namespace std;

uint CmpAssembly::find(const std::string & s) const
{
  const int nc = ncomponents();
  for (int i=0; i<nc; ++i) {
    if (components[i]->surface()->name() == s)
      return i;
  }
  return NotFound;
}

uint CmpAssembly::append(const AsyComponentPtr & c)
{
  components.push_back(c);
  return components.size()-1;
}
    
void CmpAssembly::erase(uint k)
{
  if (k >= components.size())
    return;
  components.erase(components.begin()+k);
}

XmlElement CmpAssembly::toXml() const
{
  XmlElement xe("CmpAssembly");
  xe["name"] = id;
  
  for (uint i=0; i<ncomponents(); ++i)
    xe.append(components[i]->toXml());
  return xe;
}
    
void CmpAssembly::fromXml(const XmlElement & xe)
{
  if (xe.name() != "CmpAssembly")
    throw Error("Incompatible XML representation for 'CmpAssembly': "+xe.name());
    
  components.clear();
  id = xe.attribute("name");
  XmlElement::const_iterator ite;
  for (ite = xe.begin(); ite != xe.end(); ++ite) {
    AsyComponentPtr acp = createFromXml(*ite);
    if (acp)
      append(acp);
  }
}

AsyComponentPtr CmpAssembly::createFromXml(const XmlElement & xe) const
{
  AsyComponentPtr acp;
  if (xe.name() == "AsyComponent") {
    acp->fromXml(xe);
  }
  return acp;
}

uint CmpAssembly::generateMesh(const MgProgressPtr & prog, ThreadPool *pool)
{
  MeshGenerator mgen;
  mgen.progressController(prog);
  mgen.postprocess(ppIter, ppMaxStretch, ppMaxPhi, ppMergeTol);
  mgen.process(*this, true, pool);

  // store mesh tags
  uint stag;
  const int nc = components.size();
  for (int i=0; i<nc; ++i) {
    string sn = component(i)->name();
    stag = mgen.findTag(sn);
    component(i)->mainTag(stag);
    for (int j=0; j<4; ++j) {
      stag = mgen.findTag(sn + "Cap" + str(j+1));
      component(i)->capTag(j, stag);
    }
  }  
  
  if (prog->interrupt()) {
    msh.clear();
    return 0;
  } else {
    mgen.swap(msh);
    return mgen.ncomponents();
  }
}



