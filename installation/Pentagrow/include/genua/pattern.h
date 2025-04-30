
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
 
#ifndef GENUA_PATTERN_H
#define GENUA_PATTERN_H

#include "defines.h"
#include "dvector.h"

Vector polynomial_pattern(uint n, Real xp);
Vector equi_pattern(uint n, Real from = 0.0, Real to = 1.0);
Vector cosine_pattern(uint n, Real omega = 2*PI, Real phi = 0, Real dmp = 1.0);
Vector resize_pattern(const Vector & a, uint n);
Vector relax(const Vector & v, uint iter = 1);
Vector expand_pattern(uint n, Real f);
void expand_pattern(uint n, Real f, Vector & v);
void airfoil_pattern(uint n, Real tle, Real fle, Real fte, Vector & t);
Vector interpolate_pattern(const Vector & a, uint n);
void interpolate_pattern(const Vector & a, uint n, Vector & b);
Indices linspace(uint first, uint last, uint stride);



#endif

