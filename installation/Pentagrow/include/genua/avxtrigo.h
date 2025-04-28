
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
 #ifndef GENUA_AVXTRIGO_H
#define GENUA_AVXTRIGO_H

// this header exists for code which does not want to distinguish between
// the AVX and AVX2 versions of the trig functions. if you want separate
// versions of these functions, include "avxtrigo_inc.h" instead.

#if defined(HAVE_AVX2) || defined(__AVX2__)

#define TRIGO_USE_AVX2
#include "avxtrigo_inc.h"

#define _mm256_log_ps  log256_ps_fma
#define _mm256_exp_ps  exp256_ps_fma
#define _mm256_cos_ps  cos256_ps_fma
#define _mm256_sin_ps  sin256_ps_fma
#define sincos256_ps   sincos256_ps_fma

#elif defined(HAVE_AVX) || defined(__AVX__)

#undef TRIGO_USE_AVX2
#include "avxtrigo_inc.h"

#define _mm256_log_ps  log256_ps_avx
#define _mm256_exp_ps  exp256_ps_avx
#define _mm256_cos_ps  cos256_ps_avx
#define _mm256_sin_ps  sin256_ps_avx
#define sincos256_ps   sincos256_ps_avx

#endif // HAVE_AVX



#endif // AVXTRIGO_H
