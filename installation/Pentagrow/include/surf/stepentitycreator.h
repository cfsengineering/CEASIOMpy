
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
 
#ifndef SURF_STEPENTITYCREATOR_H
#define SURF_STEPENTITYCREATOR_H

#include "step.h"
#include "stepentity.h"
#include "stepline.h"
#include <map>

// automatically created by surf/tools/fedex.py -- do not edit

class StepEntityCreator
{
public:
  StepEntityCreator();
  StepEntity *create(StepFileLine & line, const std::string & key) const;
private:
  typedef std::map<std::string, StepEntityCreatorFunction> FunctionMap;
  FunctionMap fmap;
};
#endif
