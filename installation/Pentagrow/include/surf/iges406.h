
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
 
#ifndef SURF_IGES406_H
#define SURF_IGES406_H

#include "igesentity.h"

/** IGES 406 : Name property entity.

  Creates an entity type 406, form 15 to define a long name
  for a given entity, to which this entity's DE is linked by
  means of addPropRef().

  \b Spec : IGES 5.3, page 444

  The Property Entity contains numerical or textual data. Its Form Number
  specifies its meaning. Form Numbers in the range 5001–9999 are reserved for
  implementors. Note that properties may also reference other properties,
  participate in associativities, reference related general notes, or display
  text by referencing a Text Display Template Entity (Type 312). Properties
  usually are referenced by a pointer in the second group of additional pointers
  as described in Section 2.2.4.5.2; however, as stated in Section 1.6.1, when a
  property is independent, it applies to all entities on the same level as its
  Directory Entry Level attribute.

  \b Spec : IGES 5.3, page 477 about Form 15

  This property attaches a string which specifies a user-defined name. It can be
  used for any entity ECO630 that does not have a name explicitly specified in
  the parameter data for the entity.

  \ingroup interop
  \sa IgesEntity, IgesFile
  */
class IgesNameProperty : public IgesEntity
{
  public:

    /// create empty entity
    IgesNameProperty(const std::string & s="") : IgesEntity(406), name(s) {}

    /// access name
    const std::string & str() const {return name;}

    /// assemble definition (enforces form 15)
    void definition(IgesFile & file);

    /// fetch data from string, return number of parameter values used
    uint parse(const std::string & pds, const Indices & vpos);

  private:

    /// the name to store
    std::string name;
};

#endif // IGES406_H
