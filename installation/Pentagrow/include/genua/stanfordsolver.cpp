
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

#include "stanfordsolver.h"

const char *SolIterativeSolver::s_error_msg[] = {
  "The exact solution is  x = 0",
  "Ax - b is small enough, given atol, btol",
  "The least-squares solution is good enough, given atol",
  "The estimate of cond(Abar) has exceeded conlim",
  "Ax - b is small enough for this machine",
  "The least-squares solution is good enough for this machine",
  "Cond(Abar) seems to be too large for this machine",
  "The iteration limit has been reached",
  "The system Ax = b seems to be incompatible"
  "Maximum permitted length of x is exceeded."
};

const char *SolIterativeSolver::statusMessage(int code)
{
  if (code < 10)
    return s_error_msg[code];
  else
    return "Unknown error code.";
}

