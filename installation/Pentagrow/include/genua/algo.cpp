
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       algo.cpp
 * begin:      Sat Nov 3 2001
 * copyright:  (c) 2001 by david.eller@gmx.net
 * ------------------------------------------------------------------------
 * <description>
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include "defines.h"
#include "algo.h"

unsigned long binomial(unsigned long n, unsigned long k)
{
  // compute binomial coefficient (n,k)
  if (k == 0 or k == n)
    return 1;
  else if (k == 1)
    return n;

  if (n-k < k)
    return binomial(n,n-k);

  register unsigned long nm(n), dn(k);
  for (unsigned long i=1; i<k; i++)
    {
      nm *= n-i;
      dn *= k-i;
    }
  return nm/dn;
}




