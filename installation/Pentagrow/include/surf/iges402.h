
/* Copyright (C) 2017 David Eller <david@larosterna.com>
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

#ifndef SURF_IGES402_H
#define SURF_IGES402_H

#include <genua/defines.h>
#include "igesentity.h"

/** IGES 402: Associativity Instance

  Expresses associativity of a set of other entities that may contain back
  pointers to the associativity instance.

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesAssociativity : public IgesEntity
{
  public:

    /// create empty subfigure
    IgesAssociativity() : IgesEntity(402) {}

    /// ordered or not?
    bool ordered() const;

    /// back-pointers or not?
    bool backpointers() const;

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

    /// directory entries of sub-entities
    Indices deps;
};

#endif // IGES402_H

