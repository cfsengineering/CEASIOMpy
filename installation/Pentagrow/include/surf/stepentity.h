
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
 

#ifndef SURF_STEPENTITY_H
#define SURF_STEPENTITY_H

#include "step.h"
#include <boost/shared_ptr.hpp>
#include <set>

class StepFileLine;

/** Common base class for all STEP entities.

  Classes which inherit from StepEntity are automatically generated.

  \ingroup interop
*/
class StepEntity
{
public:

  /// construct with entity id
  StepEntity(StepID id=0) : eid(id) {}

  /// virtual destructor
  virtual ~StepEntity();

  /// read entity data from line
  virtual bool read(StepFileLine & s);

  /// write to text stream
  virtual void write(std::ostream & os) const;

  /// return key string for class
  virtual const char *keyString() const;

public:

  /// entity id
  StepID eid;
};

typedef StepEntity *(*StepEntityCreatorFunction)(StepFileLine &);
typedef boost::shared_ptr<StepEntity> StepEntityPtr;

/// Comparison functor for STEP entities.
struct StepEntityCmp
{
  bool operator() (const StepEntityPtr & a, const StepEntityPtr & b) const
  {
    return a->eid < b->eid;
  }
};

typedef std::set<StepEntityPtr, StepEntityCmp> StepEntitySet;

#endif // STEPENTITY_H
