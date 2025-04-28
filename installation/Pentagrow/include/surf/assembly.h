
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

#ifndef SURF_CMPASSEMBLY_H
#define SURF_CMPASSEMBLY_H

#include "forward.h"
#include "asycomponent.h"

/** Container for components.

  A plain array of pointers to AsyComponent objects grouped with global
  mesh generation parameters.

  \todo Move to sumo

  \ingroup meshgen
  \sa AsyComponent
  */
class CmpAssembly
{
public:

  /// empty assembly
  CmpAssembly() : ppMaxPhi(PI/12.), ppMaxStretch(9.),
    ppMergeTol(0.0), ppIter(0) {}

  /// meant as a base class
  virtual ~CmpAssembly() {}

  /// access name
  const std::string & name() const {return id;}

  /// change name
  void rename(const std::string & s) {id = s;}

  /// number of components
  uint ncomponents() const {return components.size();}

  /// access component
  AsyComponentPtr & component(uint k) {
    assert(k < components.size());
    return components[k];
  }

  /// access component
  const AsyComponentPtr & component(uint k) const {
    assert(k < components.size());
    return components[k];
  }

  /// return the index of a component name, or NotFound
  uint find(const std::string & s) const;

  /// add a component, return index
  virtual uint append(const AsyComponentPtr & c);

  /// erase a component by index
  virtual void erase(uint k);

  /// generate surface mesh
  uint generateMesh(const MgProgressPtr & prog, ThreadPool *pool = 0);

  /// access mesh later
  const TriMesh & mesh() const {return msh;}

  /// convert to XML
  virtual XmlElement toXml() const;

  /// convert from XML
  virtual void fromXml(const XmlElement & xe);

protected:

  virtual AsyComponentPtr createFromXml(const XmlElement & xe) const;

protected:

  /// assembly name
  std::string id;

  /// components
  AsyComponentArray components;

  /// last surface mesh
  TriMesh msh;

  /// global mesh postprocessing options
  Real ppMaxPhi, ppMaxStretch, ppMergeTol;

  /// number of postprocessing iterations
  uint ppIter;
};    

#endif
