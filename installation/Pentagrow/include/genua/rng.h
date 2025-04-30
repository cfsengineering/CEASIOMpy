
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
 
#ifndef GENUA_RNG_H
#define GENUA_RNG_H

#include "forward.h"
#include <random>
#include <string>

/** Generator for random integer values.
 *
 *  Thin wrapper around C++ 2011 pseudo random generators and distributions
 *  which provide a generating (functor) interface with less verbosity than
 *  the std interface.
 *
 * \ingroup utility
 * \sa FloatRng
 */
class IntRng
{
public:

  typedef std::mt19937 RngType;
  typedef RngType::result_type SeedType;
  typedef std::uniform_int_distribution<int> DistType;

  /// int-valued RNG with default range (0, INT_MAX)
  IntRng() {}

  /// construct with custom range
  IntRng(int imin, int imax) : m_dist(imin, imax) {}

  /// seed the RNG
  void seed(SeedType value) { m_rng.seed(value); }

  /// seed the RNG with current time
  void timeSeed();

  /// seed RNG such that each thread generates a differnt sequence
  void threadSeed();

  /// generate new random value
  int operator() () { return m_dist(m_rng); }

  /// fill a string with alphanumeric characters
  void sfill(size_t n, char *s);

  /// return a string of alphanumeric characters
  std::string makeString(size_t n);

private:

  /// pseudo-random number generator
  RngType m_rng;

  /// distribution function
  DistType m_dist;
};

/** Generator for random double-precision values.
 *
 *  Thin wrapper around C++ 2011 pseudo random generators and distributions
 *  which provide a generating (functor) interface with less verbosity than
 *  the std interface.
 *
 *  \ingroup utility
 *  \sa IntRng
 */
class FloatRng
{
public:

  typedef std::mt19937 RngType;
  typedef RngType::result_type SeedType;
  typedef std::uniform_real_distribution<double> DistType;

  /// int-valued RNG with default range (0.0, 1.0)
  FloatRng() : m_dist(0.0, 1.0) {}

  /// construct with custom range
  FloatRng(double imin, double imax) : m_dist(imin, imax) {}

  /// seed the RNG
  void seed(SeedType value) { m_rng.seed(value); }

  /// seed the RNG with current time
  void timeSeed();

  /// seed RNG such that each thread generates a differnt sequence
  void threadSeed();

  /// generate new random value
  double operator() () { return m_dist(m_rng); }

private:

  /// pseudo-random number generator
  RngType m_rng;

  /// distribution function
  DistType m_dist;
};

#endif // RNG_H

