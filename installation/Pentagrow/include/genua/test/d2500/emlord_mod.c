/* emlord_mod.f -- translated by f2c (version 20090411).
   You must link the resulting object file with libf2c:
	on Microsoft Windows system, link with libf2c.lib;
	on Linux or Unix systems, link with .../path/to/libf2c.a -lm
	or, if you install libf2c.a in a standard place, with -lf2c -lm
	-- in that order, at the end of the command line, as in
		cc *.o -lf2c -lm
	Source for libf2c is in /netlib/f2c/libf2c.zip, e.g.,

		http://www.netlib.org/f2c/libf2c.zip
*/

/*   Extracted from fortran code D2500.FOR from NASA PDAS

*     AUTHORS - Evelyn Eminton, Royal Aircraft Establishment
!               Armand Sigalla, Boeing Co.
!               Grant Erwin, Boeing Co.
!               Charlotte Craidon, NASA Langley
!               Roy Harris, NASA Langley
!               Arnie McCullers, NASA Langley
!               Bo Walkley, NASA Langley
!               Ralph Carmichael, Public Domain Aeronautical Software
!                  and maybe more
*
*     REVISION HISTORY
*   DATE  VERS PERSON  STATEMENT OF CHANGES
!   1956   xxx   EE    Publication of paper with the numerical algorithm
!   1959   xxx AS & GE Original coding for IBM 704. Known as TA-14
!   1963   xxx   RH    Publication of NASA TM X-947
!    ??    xxx   CC    Creation of d2500. Non-circular fuselage.
!    ??    xxx   ??    Loop to reshape body. With restraint points.
! 10Feb95  1.0   RLC   Adapted to PC(little needed). OPEN statements
!   May95  1.1   RLC   Added comments
! 14Jun95  1.2   RLC   Rearranged output to fit 80-column screen
! 19Jun95  1.21  RLC   Put character data in common /TEXT/
! 28Jun95  1.3   RLC   Output file for gnuplot
! 25Aug95  1.4   RLC   Added MODIFIER
!  1Nov95  1.5   RLC   Ask for input file name
! 25Nov95  1.6   RLC   Lots of additional comments; print R on next areas
! 29Nov96  1.7   RLC   Print error if unable to open output
!                      Numerous nnHxxxxxxx strings changed to 'xxxxxxx'
! 29Dec96  1.8   RLC   Changed unit numbers of input&output to 1 & 2
!                      Some compilers make 5 & 6 equivalent to *

  */

#include <math.h>
#define integer int
#define real double
#define 	abs(x)   ((x) >= 0 ? (x) : -(x))
#define 	dabs(x)   (double)abs(x)

/* Table of constant values */

static integer c__400 = 400;
static integer c__0 = 0;
static integer c__1 = 1;

real emlord_mod(const real *ell, const real *sn, const real *sb, const integer *nn,
                const real *xx, const real *ss)
{
    /* System generated locals */
    integer i__1, i__2;
    real r__1, r__2;

    /* Builtin functions 
    double sqrt(doublereal), acos(doublereal), log(doublereal);
    */

    /* Local variables */
    static real b, c__[400], e;
    static integer m, n;
    static real q[400], r__[400], x, y, e1, e2;
    static integer nk;
    static real pq[160000]	/* was [400][400] */;
    static integer ind[800]	/* was [400][2] */;
    static real det;
    static integer ikk, ipi[400];
    static real sum;
    extern /* Subroutine */ int matinv_(const integer *, const integer *, real *, integer 
	    *, real *, integer *, real *, integer *, integer *, integer *);

/*   -------------------------------------------------------------------- */
/*     PURPOSE - Compute drag of a slender body of revolution */

/*     NOTES- */

/*      IMPLICIT NONE */

/*      EXTERNAL */
/* *********************************************************************** */
/*     A R G U M E N T S                                                * */
/* *********************************************************************** */
/* length of the body                               IN */
/* nose area                                        IN */
/* base area                                        IN */
/* number of INTERIOR points where area is defined  IN */
/* interior points (non-dimensional)                IN */
/* corresponding areas                              IN */
/*      REAL R(*)    ! used for something ??                           OUT */
/*      INTEGER K    ! K=1, normal mode, compute matrix                 IN */
/*                    K=2, read matrix from unit 10 */
/* *********************************************************************** */
/*     L O C A L   C O N S T A N T S                                    * */
/* *********************************************************************** */
/* drag/q                                          OUT */
/* *********************************************************************** */
/*     L O C A L   V A R I A B L E S                                    * */
/* *********************************************************************** */
/* *********************************************************************** */
/*     L O C A L   A R R A Y S                                          * */
/* *********************************************************************** */
/* ----------------------------------------------------------------------- */
    /* Parameter adjustments */
    --ss;
    --xx;

    if (*nn > 400)
      return 0.0;

    /* Function Body */
    /*      IF (K.GT.1) GO TO 50 */
    i__1 = *nn;
    for (n = 1; n <= i__1; ++n) {
	x = xx[n];
/* Computing 2nd power */
	r__1 = x;
	q[n - 1] = (acos(1.f - x * 2.f) - (2.f - x * 4.f) * sqrt(x - r__1 * 
		r__1)) / 3.14159265f;
	i__2 = *nn;
	for (m = n; m <= i__2; ++m) {
	    y = xx[m];
/* Computing 2nd power */
	    r__1 = x - y;
	    e = r__1 * r__1;
	    e1 = x + y - x * 2.f * y;
	    e2 = sqrt(x * y * (1.f - x) * (1.f - y)) * 2.f;
	    if (e != 0.f) {
		goto L5;
	    } else {
		goto L10;
	    }
L5:
	    pq[m + n * 400 - 401] = e * .5f * log((e1 - e2) / (e1 + e2)) + e1 
		    * e2;
	    goto L15;
L10:
	    pq[m + n * 400 - 401] = e1 * e2;
L15:
	    ;
	}
	nk = n - 1;
	if (nk <= 0) {
	    goto L30;
	} else {
	    goto L20;
	}
L20:
	i__2 = nk;
	for (m = 1; m <= i__2; ++m) {
	    e = pq[n + m * 400 - 401];
/* L25: */
	    pq[m + n * 400 - 401] = e;
	}
L30:
	;
    }
    matinv_(&c__400, nn, pq, &c__0, &b, &c__1, &det, &ikk, ipi, ind);
    i__1 = *nn;
    for (n = 1; n <= i__1; ++n) {
/* L35: */
	c__[n - 1] = ss[n] - *sn - (*sb - *sn) * q[n - 1];
    }
    i__1 = *nn;
    for (m = 1; m <= i__1; ++m) {
	sum = 0.f;
	i__2 = *nn;
	for (n = 1; n <= i__2; ++n) {
/* L40: */
	    sum += pq[m + n * 400 - 401] * c__[n - 1];
	}
/* L45: */
	r__[m - 1] = sum;
    }
    goto L70;
/* 50    REWIND 10 */
/*      READ(10) (Q(I),I=1,NN) */
/*      DO 55 N=1,NN */
/* 55    C(N)=SS(N)-SN-(SB-SN)*Q(N) */
/*      DO 65 M=1,NN */
/*      READ(10) (PQQ(I),I=1,NN) */
/*      SUM=0.0 */
/*      DO 60 N=1,NN */
/* 60    SUM=SUM+PQQ(N)*C(N) */
/* 65    R(M)=SUM */
L70:
    sum = 0.f;
    i__1 = *nn;
    for (m = 1; m <= i__1; ++m) {
/* L75: */
	sum += r__[m - 1] * c__[m - 1];
    }
/* Computing 2nd power */
    r__1 = *sb - *sn;
/* Computing 2nd power */
    r__2 = *ell;
    return (r__1 * r__1 * 4.f / 3.14159265f + sum * 3.14159265f) / (r__2 * 
	    r__2);
} /* emlord_ */

/* --------------------------------- End of Subroutine EMLORD */
int matinv_(const integer *max__, const integer *n, real *a, integer *m,
	real *b, integer *iop, real *determ, integer *iscale, integer *ipivot,
	 integer *iwk)
{
    /* System generated locals */
    integer a_dim1, a_offset, b_dim1, b_offset, iwk_dim1, iwk_offset, i__1, 
	    i__2, i__3, i__4;
    real r__1;
    static integer equiv_0[1], equiv_1[1];
    static real equiv_2[1];

    /* Local variables */
    static integer i__, j, k, l;
#define t (equiv_2)
    static integer l1;
    static real r1, r2;
#define amax (equiv_2)
    static real tmax;
#define swap (equiv_2)
#define irow (equiv_0)
#define jrow (equiv_0)
    static real pivot;
#define icolum (equiv_1)
#define jcolum (equiv_1)
    static real pivoti;

/*   -------------------------------------------------------------------- */
/*     PURPOSE - INVERT A REAL SQUARE MATRIX A. IN ADDITION THE ROUTINE */
/*        SOLVES THE MATRIX EQUATION AX=B,WHERE B IS A MATRIX OF CONSTANT */
/*        VECTORS. THERE IS ALSO AN OPTION TO HAVE THE DETERMINANT */
/*        EVALUATED. IF THE INVERSE IS NOT NEEDED, USE GELIM TO SOLVE A */
/*        SYSTEM OF SIMULTANEOUS EQUATIONS AND DETFAC TO EVALUATE A */
/*        DETERMINANT FOR SAVING TIME AND STORAGE. */

/*     AUTHORS - COMPUTER SCIECES CORPORATION, HAMPTON, VA */
/*               Ralph L. Carmichael, Public Domain Aeronautical Software */

/*     REVISION HISTORY */
/*   DATE  VERS PERSON  STATEMENT OF CHANGES */
/*  July73  0.1   CSC   Original release */
/* 29Jul81  1.0?  CSC   Latest release (in release of D2500) */
/*  9Nov94  1.1   RLC   IMPLICIT NONE; declared variables */

/*     REFERENCE: FOX,L, AN INTRODUCTION TO NUMERICAL LINEAR ALGEBRA */


/*      EXTERNAL */
/* *********************************************************************** */
/*     A R G U M E N T S                                                * */
/* *********************************************************************** */
/*                       DIMENSION STATEMENT OF THE CALLING PROGRAM. */

/*  THE MAXIMUM ORDER OF A AS STATED IN THE */

/* - THE ORDER OF A, 1.LE.N.LE.MAX. */
/*                       ON RETURN TO THE CALLING PROGRAM, A INVERSE */
/*                       IS STORED IN A. */
/*                       A MUST BE DIMENSIONED IN THE CALLING PROGRAM */
/*                       WITH FIRST DIMENSION MAX AND SECOND DIMENSION */
/*                       AT LEAST N. */

/*    - A TWO-DIMENSIONAL ARRAY OF THE COEFFICIENTS. */
/*                       M=0 SIGNALS THAT THE SUBROUTINE IS */
/*                       USED SOLELY FOR INVERSION,HOWEVER, */
/*                       IN THE CALL STATEMENT AN ENTRY CORRE- */
/*                       SPONDING TO B MUST BE PRESENT. */

/* - THE NUMBER OF COLUMN VECTORS IN B. */
/*                       VECTOR B. ON RETURN TO CALLING PROGRAM, */
/*                       X IS STORED IN B. B SHOULD HAVE ITS FIRST */
/*                       DIMENSION MAX AND ITS SECOND AT LEAST M. */

/*   - A TWO-DIMENSIONAL ARRAY OF THE CONSTANT */
/*                        IOP=0 COMPUTES THE MATRIX INVERSE AND */
/*                              DETERMINANT. */
/*                        IOP=1 COMPUTES THE MATRIX INVERSE ONLY. */

/* - COMPUTE DETERMINANT OPTION. */
/*                       REPRESENTS THE VALUE OF THE DETERMINANT */
/*                       OF A, DET(A),AS FOLLOWS. */
/*                        DET(A)=(DETERM)(10**100(ISCALE)) */
/*                       THE COMPUTATION DET(A) SHOULD NOT BE */
/*                       ATTEMPTED IN THE USER PROGRAM SINCE IF */
/*                       THE ORDER OF A IS LARGER AND/OR THE */
/*                       MAGNITUDE OF ITS ELEMENTS ARE LARGE(SMALL), */
/*                       THE DET(A) CALCULATION MAY CAUSE OVERFLOW */
/*                     (UNDERFLOW). DETERM SET TO ZERO FOR */
/*                     SINGULAR MATRIX CONDITION, FOR EITHER */
/*                     I0P=1,OR 0. SHOULD BE CHECKED BY PROGRAMER */
/*                     ON RETURN TO MAIN PROGRAM. */

/* - FOR IOP=0-IN CONJUNCTION WITH ISCALE */
/*                       SUBROUTINE TO AVOID OVERFLOW OR */
/*                       UNDERFLOW IN THE COMPUTATION OF */
/*                       THE QUANTITY,DETERM. */

/* - A SCALE FACTOR COMPUTED BY THE */
/*                       USED BY THE SUBPROGRAM TO STORE */
/*                       PIVOTOL INFORMATION. IT SHOULD BE */
/*                       DIMENSIONED AT LEAST N. IN GENERAL */
/*                       THE USER DOES NOT NEED TO MAKE USE */
/*                       OF THIS ARRAY. */

/*  - A ONE DIMENSIONAL INTEGER ARRAY */
/*                       TEMPORARY STORAGE USED BY THE ROUTINE. */
/*                       IWK SHOULD HAVE ITS FIRST DIMENSION */
/*                       MAX, AND ITS SECOND 2. */

/*     REQUIRED ROUTINES- */

/*     STORAGE          - 542 OCTAL LOCATIONS */

/*     LANGUAGE         -FORTRAN */
/*     LIBRARY FUNCTIONS -ABS */

/* *********************************************************************** */
/*     L O C A L   C O N S T A N T S                                    * */
/* *********************************************************************** */
/* *********************************************************************** */
/*     L O C A L   V A R I A B L E S                                    * */
/* *********************************************************************** */
/*  - A TWO-DIMENSIONAL INTEGER ARRAY OF */
/* *********************************************************************** */
/*     L O C A L   A R R A Y S                                          * */
/* *********************************************************************** */
/* ----------------------------------------------------------------------- */

/*     INITIALIZATION */

    /* Parameter adjustments */
    iwk_dim1 = *max__;
    iwk_offset = 1 + iwk_dim1;
    iwk -= iwk_offset;
    b_dim1 = *max__;
    b_offset = 1 + b_dim1;
    b -= b_offset;
    a_dim1 = *max__;
    a_offset = 1 + a_dim1;
    a -= a_offset;
    --ipivot;

    /* Function Body */
    *iscale = 0;
    r1 = 1e37f;
/* changed by RLC from 100 */
    r2 = 1.f / r1;
    *determ = 1.f;
    i__1 = *n;
    for (j = 1; j <= i__1; ++j) {
	ipivot[j] = 0;
/* L20: */
    }
    i__1 = *n;
    for (i__ = 1; i__ <= i__1; ++i__) {

/*       SEARCH FOR PIVOT ELEMENT */

	*amax = 0.f;
	i__2 = *n;
	for (j = 1; j <= i__2; ++j) {
	    if (ipivot[j] - 1 != 0) {
		goto L60;
	    } else {
		goto L105;
	    }
L60:
	    i__3 = *n;
	    for (k = 1; k <= i__3; ++k) {
		if ((i__4 = ipivot[k] - 1) < 0) {
		    goto L80;
		} else if (i__4 == 0) {
		    goto L100;
		} else {
		    goto L740;
		}
L80:
		tmax = (r__1 = a[j + k * a_dim1], dabs(r__1));
		if (*amax - tmax >= 0.f) {
		    goto L100;
		} else {
		    goto L85;
		}
L85:
		*irow = j;
		*icolum = k;
		*amax = tmax;
L100:
		;
	    }
L105:
	    ;
	}
	if (*amax < 0.f) {
	    goto L740;
	} else if (*amax == 0) {
	    goto L106;
	} else {
	    goto L110;
	}
L106:
	*determ = 0.f;
	*iscale = 0;
	goto L740;
L110:
	ipivot[*icolum] = 1;

/*       INTERCHANGE ROWS TO PUT PIVOT ELEMENT ON DIAGONAL */

	if (*irow - *icolum != 0) {
	    goto L140;
	} else {
	    goto L260;
	}
L140:
	*determ = -(*determ);
	i__2 = *n;
	for (l = 1; l <= i__2; ++l) {
	    *swap = a[*irow + l * a_dim1];
	    a[*irow + l * a_dim1] = a[*icolum + l * a_dim1];
	    a[*icolum + l * a_dim1] = *swap;
/* L200: */
	}
	if (*m <= 0) {
	    goto L260;
	} else {
	    goto L210;
	}
L210:
	i__2 = *m;
	for (l = 1; l <= i__2; ++l) {
	    *swap = b[*irow + l * b_dim1];
	    b[*irow + l * b_dim1] = b[*icolum + l * b_dim1];
	    b[*icolum + l * b_dim1] = *swap;
/* L250: */
	}
L260:
	iwk[i__ + iwk_dim1] = *irow;
	iwk[i__ + (iwk_dim1 << 1)] = *icolum;
	pivot = a[*icolum + *icolum * a_dim1];
	if (*iop < 0) {
	    goto L740;
	} else if (*iop == 0) {
	    goto L1000;
	} else {
	    goto L321;
	}

/*       SCALE THE DETERMINANT */

L1000:
	pivoti = pivot;
	if (dabs(*determ) - r1 >= 0.f) {
	    goto L1010;
	} else {
	    goto L1030;
	}
L1010:
	*determ /= r1;
	++(*iscale);
	if (dabs(*determ) - r1 >= 0.f) {
	    goto L1020;
	} else {
	    goto L1060;
	}
L1020:
	*determ /= r1;
	++(*iscale);
	goto L1060;
L1030:
	if (dabs(*determ) - r2 <= 0.f) {
	    goto L1040;
	} else {
	    goto L1060;
	}
L1040:
	*determ *= r1;
	--(*iscale);
	if (dabs(*determ) - r2 <= 0.f) {
	    goto L1050;
	} else {
	    goto L1060;
	}
L1050:
	*determ *= r1;
	--(*iscale);
L1060:
	if (dabs(pivoti) - r1 >= 0.f) {
	    goto L1070;
	} else {
	    goto L1090;
	}
L1070:
	pivoti /= r1;
	++(*iscale);
	if (dabs(pivoti) - r1 >= 0.f) {
	    goto L1080;
	} else {
	    goto L320;
	}
L1080:
	pivoti /= r1;
	++(*iscale);
	goto L320;
L1090:
	if (dabs(pivoti) - r2 <= 0.f) {
	    goto L2000;
	} else {
	    goto L320;
	}
L2000:
	pivoti *= r1;
	--(*iscale);
	if (dabs(pivoti) - r2 <= 0.f) {
	    goto L2010;
	} else {
	    goto L320;
	}
L2010:
	pivoti *= r1;
	--(*iscale);
L320:
	*determ *= pivoti;

/*       DIVIDE PIVOT ROW BY PIVOT ELEMENT */

L321:
	a[*icolum + *icolum * a_dim1] = 1.f;
	i__2 = *n;
	for (l = 1; l <= i__2; ++l) {
/* L350: */
	    a[*icolum + l * a_dim1] /= pivot;
	}
	if (*m <= 0) {
	    goto L380;
	} else {
	    goto L360;
	}
L360:
	i__2 = *m;
	for (l = 1; l <= i__2; ++l) {
/* L370: */
	    b[*icolum + l * b_dim1] /= pivot;
	}

/*       REDUCE NON-PIVOT ROWS */

L380:
	i__2 = *n;
	for (l1 = 1; l1 <= i__2; ++l1) {
	    if (l1 - *icolum != 0) {
		goto L400;
	    } else {
		goto L550;
	    }
L400:
	    *t = a[l1 + *icolum * a_dim1];
	    a[l1 + *icolum * a_dim1] = 0.f;
	    i__3 = *n;
	    for (l = 1; l <= i__3; ++l) {
/* L450: */
		a[l1 + l * a_dim1] -= a[*icolum + l * a_dim1] * *t;
	    }
	    if (*m <= 0) {
		goto L550;
	    } else {
		goto L460;
	    }
L460:
	    i__3 = *m;
	    for (l = 1; l <= i__3; ++l) {
/* L500: */
		b[l1 + l * b_dim1] -= b[*icolum + l * b_dim1] * *t;
	    }
L550:
	    ;
	}
    }

/*     INTERCHANGE COLUMNS */

    i__2 = *n;
    for (i__ = 1; i__ <= i__2; ++i__) {
	l = *n + 1 - i__;
	if (iwk[l + iwk_dim1] - iwk[l + (iwk_dim1 << 1)] != 0) {
	    goto L630;
	} else {
	    goto L710;
	}
L630:
	*jrow = iwk[l + iwk_dim1];
	*jcolum = iwk[l + (iwk_dim1 << 1)];
	i__1 = *n;
	for (k = 1; k <= i__1; ++k) {
	    *swap = a[k + *jrow * a_dim1];
	    a[k + *jrow * a_dim1] = a[k + *jcolum * a_dim1];
	    a[k + *jcolum * a_dim1] = *swap;
/* L705: */
	}
L710:
	;
    }
L740:
    return 0;
} /* matinv_ */

#undef jcolum
#undef icolum
#undef jrow
#undef irow
#undef swap
#undef amax
#undef t


