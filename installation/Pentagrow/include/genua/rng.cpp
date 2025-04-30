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

#include "rng.h"
#include <chrono>
#include <thread>
#include <functional>

static uint32_t time_seed_value()
{
  auto now = std::chrono::system_clock::now().time_since_epoch();
  auto sec = std::chrono::duration_cast<std::chrono::seconds>(now);
  return (sec.count() & 0xffffffff);
}

static uint32_t thread_seed_value()
{
  // std::hash generates a size_t, while mt19937 uses uint32_t
  const size_t vmax = std::numeric_limits<uint32_t>::max();
  std::hash<std::thread::id> hashfn;
  return hashfn(std::this_thread::get_id()) % vmax;
}

void IntRng::timeSeed()
{
  this->seed( time_seed_value()  );
}

void IntRng::threadSeed()
{
  this->seed( thread_seed_value() );
}

std::string IntRng::makeString(size_t n)
{
  std::string s;
  s.resize(n);
  this->sfill(n, &s[0]);
  return s;
}

void IntRng::sfill(size_t n, char *s)
{
  const char lexicon[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz";
  const size_t m = sizeof(lexicon);
  for (size_t i=0; i<n; ++i)
    s[i] = lexicon[ m_dist(m_rng) % m ];
}

void FloatRng::timeSeed()
{
  this->seed( time_seed_value()  );
}

void FloatRng::threadSeed()
{
  this->seed( thread_seed_value() );
}
