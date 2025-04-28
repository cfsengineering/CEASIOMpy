
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
 
#include "instance.h"
#include "iges308.h"
#include "iges408.h"
#include "iges406.h"
#include "iges124.h"
#include "igesfile.h"

// ------------------- Instance -------------------------------------------------

XmlElement Instance::toXml(bool) const
{
  XmlElement xe("Instance");
  xe["name"] = m_name;
  xe["id"] = str(m_iid);
  xe.append(m_placement.toXml());
  return xe;
}

void Instance::fromXml(const XmlElement & xe)
{
  m_name = xe.attribute("name");
  xe.fromAttribute("id", m_iid);
  XmlElement::const_iterator ite, elast;
  elast = xe.end();
  for (ite = xe.begin(); ite != elast; ++ite) {
    if (ite->name() == "Trafo3") {
      m_placement.fromXml(*ite);
    }
  }
}

// ------------------- IndexInstance --------------------------------------------

uint IndexInstance::toIges(IgesFile & file) const
{
  if (size() == 0)
    return NotFound;

//  // transformation matrix
//  Mtx44 tfm;
//  m_placement.matrix(tfm);

//  IgesTrafoMatrix ig124;
//  for (int j=0; j<3; ++j) {
//    ig124.translation(j) = tfm(j,3);
//    for (int i=0; i<3; ++i)
//      ig124.rotation(i,j) = tfm(i,j);
//  }
//  int itf = ig124.append( file );

  // subfigure entity
  IgesSubfigure ig308;
  ig308.rename( name() );
  ig308.copy( m_objects );
  // ig308.trafoMatrix(itf);
  int isub = ig308.append( file );

  return isub;
}

bool IndexInstance::fromIges(const IgesFile & file,
                             const IgesDirEntry & entry)
{
  if (entry.etype != 308)
    return false;

  IgesEntityPtr ep = file.createEntity(entry);
  {
    IgesSubfigure ig308;
    if (not IgesEntity::as(ep, ig308))
      return false;

    const int nobj = ig308.size();
    m_objects.resize( nobj );
    for (int i=0; i<nobj; ++i)
      m_objects[i] = ig308[i];

    rename( ig308.name() );
  }

//  // transformation
//  m_placement.identity();
//  int itf = entry.trafm;
//  if (itf != 0) {
//    ep = file.createEntity(itf);
//    IgesTrafoMatrix ig124;
//    if (not IgesEntity::as(ep, ig124))
//      return false;

//    Mtx44 m;
//    for (int j=0; j<3; ++j) {
//      m(j,3) = ig124.translation(j);
//      for (int i=0; i<3; ++i)
//        m(i,j) = ig124.rotation(i,j);
//    }
//    m_placement.reconstruct(m);
//  }

  return true;
}

XmlElement IndexInstance::toXml(bool share) const
{
  XmlElement xe( Instance::toXml(share) );
  xe.rename("IndexInstance");
  xe["count"] = m_objects.size();
  xe.asBinary(m_objects.size(), &m_objects[0], share);
  return xe;
}

void IndexInstance::fromXml(const XmlElement & xe)
{
  Instance::fromXml(xe);
  uint nobj = Int( xe.attribute("count") );
  xe.fetch(nobj, &m_objects[0]);
}
