
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
 
#ifndef GENUA_HAMMER_TRIAG_H
#define GENUA_HAMMER_TRIAG_H

/** \file hammertriag.h
 *  \brief Triangular Hammer integration rules.
 *
 * This file defines inline functions which implement Hammer integration rules
 * for triangles with 4-13 integration points. The integration domain is
 * \f[
 *  u \in (0, 1-v), \quad v \in (0,1)
 * \f]
 *
 * \ingroup numerics
 * \sa gausstriag.h
 */

#include "defines.h"

template <class Functor, class ResultType>
void hammer_triag4(const Functor & f, ResultType & sum)
{
  sum += 0.5 * -0.5625 * f(0.333333333333,0.333333333333);
  sum += 0.5 * 0.520833333333 * f(0.133333333333,0.133333333333);
  sum += 0.5 * 0.520833333333 * f(0.733333333333,0.133333333333);
  sum += 0.5 * 0.520833333333 * f(0.133333333333,0.733333333333);
}

template <class Functor, class ResultType>
void hammer_triag7(const Functor & f, ResultType & sum)
{
  const Real w[] = { 0.225 ,
                0.125939180545 ,
                0.125939180545 ,
                0.125939180545 ,
                0.132394152789 ,
                0.132394152789 ,
                0.132394152789 };
  const Real x[] = { 0.333333333333 ,
                0.101286507323 ,
                0.797426985353 ,
                0.101286507323 ,
                0.470142064105 ,
                0.0597158717898 ,
                0.470142064105 };
  const Real y[] = { 0.333333333333 ,
                0.101286507323 ,
                0.101286507323 ,
                0.797426985353 ,
                0.470142064105 ,
                0.470142064105 ,
                0.0597158717898 };
  for (uint i=0; i<7; ++i)
    sum += 0.5*w[i]*f(x[i],y[i]);
}

template <class Functor, class ResultType>
void hammer_triag13(const Functor & f, ResultType & sum)
{
  const Real w[] = { -0.149570044468 ,
                0.175615257433 ,
                0.175615257433 ,
                0.175615257433 ,
                0.0533472356088 ,
                0.0533472356088 ,
                0.0533472356088 ,
                0.0771137608903 ,
                0.0771137608903 ,
                0.0771137608903 ,
                0.0771137608903 ,
                0.0771137608903 ,
                0.0771137608903 };
  const Real x[] = { 0.333333333333 ,
                0.260345966079 ,
                0.479308067842 ,
                0.260345966079 ,
                0.0651301029022 ,
                0.869739794196 ,
                0.0651301029022 ,
                0.63844418857 ,
                0.0486903154253 ,
                0.312865496005 ,
                0.312865496005 ,
                0.0486903154253 ,
                0.63844418857 };
  const Real y[] = { 0.333333333333 ,
                0.260345966079 ,
                0.260345966079 ,
                0.479308067842 ,
                0.0651301029022 ,
                0.0651301029022 ,
                0.869739794196 ,
                0.312865496005 ,
                0.312865496005 ,
                0.0486903154253 ,
                0.63844418857 ,
                0.63844418857 ,
                0.0486903154253 };
  for (uint i=0; i<13; ++i)
    sum += 0.5*w[i]*f(x[i],y[i]);
}

#endif

