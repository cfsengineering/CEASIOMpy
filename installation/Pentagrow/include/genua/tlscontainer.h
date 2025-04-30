
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

#ifndef GENUA_TLSCONTAINER_H
#define GENUA_TLSCONTAINER_H

#include <atomic>
#include <algorithm>

/** Helper class for managing thread-local containers.
 *
 * A common pattern in parallel algorithms is the use of a local container that
 * is allocated thread-local or specific to a large task and only used by a
 * single thread, the localContainer below. Then, there is a globalContainer
 * that must hold combined results, but not in any particular order.
 *
 * The aim of TlsCounter is to avoid unnecessary multiple allocations and
 * data movement by first counting up the required global container size by
 * atomically adding contributions from each thread, where an offset value is
 * saved for each local container. Then, the global container must be resized
 * (by the master thread) after which each thread can independently copy or
 * move the local data into the global container.
 *
 * \ingroup concurrency
 *
 */
class TlsCounter
{
public:

  /// reset counter to zero
  void reset(size_t n=0) { m_size = n; }

  /// return current size (insert position) and increment atomically
  size_t increment(size_t n=1) {
    return m_size.fetch_add(n);
  }

  /// current counter value
  size_t size() const {return m_size;}

  /// move data from local to global container (called in parallel)
  template <class Container>
  void moveToGlobal(size_t insertPos,
                    Container &localContainer, Container &globalContainer) const
  {
    assert(globalContainer.size() >= m_size);
    assert(globalContainer.size() >= insertPos+localContainer.size());
    std::move(localContainer.begin(), localContainer.end(),
              globalContainer.begin() + insertPos);
    localContainer.clear();
  }

  /// copy data from local to global container (called in parallel)
  template <class Container>
  void copyToGlobal(size_t insertPos,
                    const Container &localContainer,
                    Container &globalContainer) const
  {
    assert(globalContainer.size() >= m_size);
    assert(globalContainer.size() >= insertPos+localContainer.size());
    std::copy(localContainer.begin(), localContainer.end(),
              globalContainer.begin() + insertPos);
  }

private:

  /// size counter
  std::atomic<size_t> m_size = 0;
};

#endif // TLSCONTAINER_H
