
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
 
#ifndef GENUA_CGNSFWD_H
#define GENUA_CGNSFWD_H

// FIXME
// This header defines something which apparently conflicts somehow
// with the Microsoft source annotation language (SAL). Whenever this 
// header is not the last one included, there will be hundreds of compile
// errors pointing to assert.h(28) or such.

#include "dmatrix.h"

// must put cgns header inside its own namespace because it defines 
// PointList as an enum which collides with libgenua
namespace cgns {
  #include "cgns/cgnslib.h"
}

#define CG_NO_INDEX  -1

void cgns_exception(int ierr);

typedef DMatrix<int> CgnsIntMatrix;
typedef DVector<int> CgnsIntVector;

#endif
