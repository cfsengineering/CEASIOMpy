
/* Copyright (C) 2017 David Eller <david@larosterna.com>
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

#ifndef GENUA_SPINBARRIER_H
#define GENUA_SPINBARRIER_H

#include "forward.h"
#include <atomic>
#include <thread>
#include <chrono>

/**
 *
 *
 *
 * \ingroup concurrency
 * \sa ThreadGroup, ForkJoinQueue, boost::lockfree::stack
 */
class SpinBarrier
{
public:

  /// initialize barrier with thread count
  SpinBarrier(int v = 0) : m_value(v) {}

  /// called by a thread on startup (if barrier not initialized with count)
  void enter() {
    ++m_value;
  }

  /// decrease the value by one and return if that makes it zero
  void wait() {
    int before = m_value.fetch_sub(1);
    if (before > 1)
      spinuntil(0);
  }

  /// check if value is v; if not, wait gradually longer until it is
  void spinuntil(int v) const {
    int spincount = 0;
    const int fast_attempts = 8;
    while (m_value.load(std::memory_order_acquire) != v) {
      ++spincount;
      if (spincount <= fast_attempts) {
        std::this_thread::yield();
      } else {
        const int max_sleep_ms = 16;
        int ms = std::min(max_sleep_ms, spincount-fast_attempts);
        std::this_thread::sleep_for( std::chrono::milliseconds(ms) );
      }
    }
  }

  // ---

  /// increase value
  SpinBarrier &operator += (int v) {
    m_value += v;
    return *this;
  }

  /// decrease value
  SpinBarrier &operator -= (int v) {
    m_value -= v;
    return *this;
  }

private:

  /// value
  std::atomic<int> m_value = 0;
};

#endif // SPINBARRIER_H
