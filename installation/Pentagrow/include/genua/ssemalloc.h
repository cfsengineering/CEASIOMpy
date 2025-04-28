
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
 
#ifndef GENUA_SSEMALLOC_H
#define GENUA_SSEMALLOC_H

#include "sse.h"

#if defined(ARCH_SSE2) || defined(__INTEL_COMPILER)

// where available, use _mm_malloc from the SSE header file

#include <xmmintrin.h>

/** Return aligned heap memory.
 *
 *  This is a wrapper around system functions which returns a pointer to an
 *  aligned chunk of memory. Deallocate using the destroy_aligned() function.
 *
 *  When available, _mm_malloc() is used; otherwise, a portable reference
 *  implementation of the same is used.
 */
inline void *allocate_aligned(size_t n, size_t algn = 64)
{
  return _mm_malloc(n, algn);
}

inline void destroy_aligned(void *p)
{
  _mm_free(p);
}

#elif defined(__GNUC__)

#include <mm_malloc.h>

inline void *allocate_aligned(size_t n, size_t algn = 64)
{
  return _mm_malloc(n, algn);
}

inline void destroy_aligned(void *p)
{
  _mm_free(p);
}

#else // no SSE header, neither is this GCC

/* Generic fallback.

  This is based on the implementation of _mm_malloc() shipping with the GCC
  compiler in the header file include/mm_malloc.h since version 4.0.

*/

#include <cstddef>
#include <cstdlib>

inline void *allocate_aligned(size_t size, size_t align = 64)
{
  assert( !(align & (align - 1)) );
  void *malloc_ptr;
  void *aligned_ptr;

  if (size == 0)
    return ((void *) 0);

  align = std::max(align, 2*sizeof(void*));
  malloc_ptr = malloc(size + align);
  if (!malloc_ptr)
    return ((void *) 0);

  aligned_ptr = (void *)(((size_t)malloc_ptr + align) & ~((size_t)(align) - 1));
  ((void **) aligned_ptr) [-1] = malloc_ptr;

  return aligned_ptr;
}

inline void destroy_aligned( void *aligned_ptr )
{
  if (aligned_ptr)
    free (((void **) aligned_ptr) [-1]);
}

#endif // no sse

#endif // SSEMALLOC_H
