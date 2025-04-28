/* Point-in polygon query.

Copyright (c) 1970-2003, Wm. Randolph Franklin

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimers.
Redistributions in binary form must reproduce the above copyright notice in the
documentation and/or other materials provided with the distribution.
The name of W. Randolph Franklin may not be used to endorse or promote products
derived from this Software without specific prior written permission.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE. */

#ifndef GENUA_PTINPOLY_H
#define GENUA_PTINPOLY_H

/** Determine whether a point is inside a polygon.
 *
 * This is the low-level implementation; the version acting on a PointList
 * is likely more useful in practice.
 *
 * \ingroup geometry
 * \sa PointList
 */
template <class FloatType>
bool point_in_polygon(int nv, const FloatType poly[], const FloatType p[])
{
  // david@larosterna.com :
  // Converted to C++ template

  /* original C code:
 int i, j, c = 0;
  for (i = 0, j = nvert-1; i < nvert; j = i++) {
    if ( ((verty[i]>testy) != (verty[j]>testy)) &&
   (testx < (vertx[j]-vertx[i]) * (testy-verty[i]) / (verty[j]-verty[i]) + vertx[i]) )
       c = !c;
  }
  return c;
  */

  int i, j;
  bool c = false;
  for (i=0, j=nv-1; i<nv; j = i++) {
    if ( ( (poly[1+2*i]>p[1]) != (poly[1+2*j]>p[1]) ) &&
         (p[0] < (poly[2*j]-poly[2*i]) * (p[1]-poly[1+2*i]) / (poly[1+2*j]-poly[1+2*i]) + poly[2*i]) )
      c = !c;
  }
  return c;
}

#endif // PTINPOLY_H
