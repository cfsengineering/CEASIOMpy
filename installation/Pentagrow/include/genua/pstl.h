
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

#ifndef GENUA_PSTL_H
#define GENUA_PSTL_H

#include "defines.h"

// Use PSTL implementation aligned with the Intel Compiler version,
// if that is active; otherwise, include the Open-Source version
// forked in
// https://svn.larosterna.com/oss/thirdparty/parallelstl

#if defined(__INTEL_COMPILER) && (__INTEL_COMPILER >= 1800)

#include <pstl/execution>
#include <pstl/algorithm>
#include <pstl/numeric>
#include <pstl/memory>

#else

#include <parallelstl/include/pstl/execution>
#include <parallelstl/include/pstl/algorithm>
#include <parallelstl/include/pstl/numeric>
#include <parallelstl/include/pstl/memory>

#endif

#endif // PSTL_H
