/* Interface to f2c converted NACA 6-series coordinate generation program
 * originally written by
 * 
 * Charles L. Ladson and Cuyler W. Brooks, Jr. NASA Langley Research Center 
 * Liam Hardy, NASA Ames Research Center 
 * Ralph L. Carmichael, Public Domain Aeronautical Software 
 *
 * REFERENCES - NASA Technical Memorandum TM X-3069 (September, 1974) 
 *              by Charles L. Ladson and Cuyler W. Brooks, Jr.
 * 
 * This file is in the public domain.
 * ------------------------------------------------------------------------ */

#ifndef SURF_NACA_H
#define SURF_NACA_H

#ifdef __cplusplus
extern "C" {
#endif

/* Error codes */

#define NACA6_SUCCESS           0
#define NACA6_INVALID_FAMILY   -1
#define NACA6_INVALID_CAMBER   -2
#define NACA6_INVALID_TOC      -3
#define NACA6_TOOMANYLINES     -4
#define NACA6_ZERO_POINTER     -5
#define NACA6_A_OUTOFRANGE     -6
#define NACA6_NOTCONVERGED     -7
#define NACA6_LIBFAILED        -8

/** Generate NACA 6- and 6A-series airfoil coordinates.

  @param iprofile Profile family code, 63-67 or 163-165 for 63A-65A family
  @param icamber  Camber code, 0: uncambered, 1: standard camber line,
                  2: modified camber line (A-profiles)
  @param toc      Thickness-to-chord ratio
  @param ncmbl    Number of mean lines to superimpose (max 10)
  @param cli      Design lift coefficients for camber lines (size 10)
  @param a        Mean-line chordwise loading factor (0.8 for A-series)
                  (size 10)
  @param nout     Number of chordwise stations for coordinates
  @param xyout    Coordinate output, size at least 800
  @return Error code (<0) or 0 on success.

  \ingroup geometry
  \sa Airfoil
  */
int naca6(int iprofile, int icamber, double toc, 
          int ncmbl, double *cli, double *a, 
          int *nout, double *xyout);
          
#ifdef __cplusplus
}
#endif		
		
#endif

