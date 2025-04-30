
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
 
#ifndef SURF_IGESSUBFIGURE_H
#define SURF_IGESSUBFIGURE_H

#include <genua/defines.h>
#include "igesentity.h"

/** IGES 308 : Subfigure.

  Although named in a strange manner, this entity type is commonly employed
  to generate assemblies, that is, to group components and map hierarchical
  part-in-assembly relationships.

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesSubfigure : public IgesEntity
{
  public:

    /// create empty subfigure
    IgesSubfigure() : IgesEntity(308), depth(0) {}

    /// subfigure name
    const std::string & name() const {return id;}

    /// rename subfigure
    void rename(const std::string & s) {id = s;}

    /// assign nesting depth
    void nestingDepth(uint d) {depth = d;}

    /// number of DEs referenced
    uint size() const {return deps.size();}

    /// access DE index k
    uint operator[] (uint k) const {
      assert(k < deps.size());
      return deps[k];
    }

    /// access dependencies
    const Indices & subEntities() const {return deps;}

    /// copy entities
    void copy(const Indices & idx) {deps = idx;}

    /// append single entity
    void appendEntity(uint k) {deps.push_back(k);}

    /// assemble definition
    void definition(IgesFile & file);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  private:

    /// subfigure name
    std::string id;

    /// nesting depth
    uint depth;

    /// directory entries of sub-entities
    Indices deps;
};

#endif // IGESSUBFIGURE_H
