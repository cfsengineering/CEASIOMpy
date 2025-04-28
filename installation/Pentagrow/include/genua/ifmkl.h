
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
 
#ifndef GENUA_IFMKL_H
#define GENUA_IFMKL_H

/** \file ifmkl.h
 *  \brief Optional features to support MKL interfaces
 *
 * This file defines empty (no-op) function stubs with the same signatures
 * as the MKL service and control functions when MKL is not present; otherwise,
 * includes the appropriate header.
 */

#if defined(HAVE_MKL) || defined(HAVE_MKL_PARDISO)

#include <mkl_service.h>

#else

#include <thread>

#define MKL_DOMAIN_ALL      0
#define MKL_DOMAIN_BLAS     1
#define MKL_DOMAIN_FFT      2
#define MKL_DOMAIN_VML      3
#define MKL_DOMAIN_PARDISO  4

inline void mkl_set_dynamic(int) {}
inline int mkl_get_dynamic() {return 0;}
inline int mkl_get_max_threads() {
  return std::thread::hardware_concurrency();
}
inline void mkl_set_num_threads(int) {}
inline void mkl_domain_set_num_threads(int, int) {}
inline int mkl_domain_get_max_threads(int) {
  return std::thread::hardware_concurrency();
}

#endif

#endif // IFMKL_H

