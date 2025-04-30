
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
 
#include "dftitransform.h"
#include "ssemalloc.h"
#include "xcept.h"
#include "dbprint.h"
#include <cstring>

DftiTransform::~DftiTransform()
{
  destroy();
}

void DftiTransform::plan(size_t n, bool forward, int flags)
{
  m_size = n;
  m_forward = forward;
  destroy();

  assert(sizeof(Complex) == sizeof(MKL_Complex16));
  m_work = (MKL_Complex16*) allocate_aligned(n*sizeof(MKL_Complex16));

  int status(0);
  status = DftiCreateDescriptor(&m_handle, DFTI_DOUBLE, DFTI_COMPLEX,
                                1, (MKL_LONG) n);
  check(status);
  if ((flags & Multithreaded) == 0) {
    status = DftiSetValue(m_handle, DFTI_THREAD_LIMIT, 1);
    check(status);
  }
  status = DftiCommitDescriptor(m_handle);
  check(status);
}

void DftiTransform::execute(const Complex in[], Complex out[])
{
  int status(0);
  memcpy(m_work, in, m_size*sizeof(Complex));
  if (m_forward)
    status = DftiComputeForward(m_handle, m_work);
  else
    status = DftiComputeBackward(m_handle, m_work);
  check(status);
  memcpy(out, m_work, m_size*sizeof(Complex));
}

void DftiTransform::destroy()
{
  DftiFreeDescriptor(&m_handle);
  if (m_work != 0)
    destroy_aligned(m_work);
  m_work = 0;
}

void DftiTransform::check(int status)
{
  if (status == 0)
    return;
  std::string msg( DftiErrorMessage(status) );
  if (not DftiErrorClass(status, DFTI_NO_ERROR))
    throw Error("MKL/DFTI library error: "+msg);
  else
    dbprint("MKL/DFTI library warning: ", msg);
}

