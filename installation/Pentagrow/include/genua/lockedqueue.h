
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

#ifndef GENUA_LOCKEDQUEUE_H
#define GENUA_LOCKEDQUEUE_H

#include <deque>
#include <mutex>

/** Mutex-protected queue.
 *
 *
 *
 * \ingroup concurrency
 * \sa ThreadGroup
 */
template <class Item>
class LockedQueue
{
  typedef std::lock_guard<std::mutex> LockGuard;

public:

  /// does nothing, present for API compatibility
  void reserve(size_t) {}

  /// wait for lock, then add an item to the end
  template <class Arg>
  bool push_back(Arg &&a) {
    LockGuard lock(m_guard);
    m_items.push_back(std::forward<Arg>(a));
    return true;
  }

  /// same as push_back(), for compatibility
  template <class Arg>
  bool push(Arg &&a) {
    return push_back(std::forward<Arg>(a));
  }

  /// wait for lock, then insert a range
  template <class Iterator>
  bool insert(Iterator first, Iterator last) {
    LockGuard lock(m_guard);
    m_items.insert(m_items.end(), first, last);
    return true;
  }

  /// if the lock is available, push back, return whether that succeeded
  template <class Arg>
  bool try_push_back(Arg &&a) {
    if ( m_guard.try_lock() ) {
      m_items.push_back(std::forward<Arg>(a));
      m_guard.unlock();
      return true;
    }
    return false;
  }

  /// same as try_push_back(), for compatibility
  template <class Arg>
  bool try_push(Arg &&a) {
    return try_push_back(std::forward<Arg>(a));
  }

  /// wait for lock, then add an item to the front
  template <class Arg>
  bool push_front(Arg &&a) {
    LockGuard lock(m_guard);
    m_items.push_front(std::forward<Arg>(a));
    return true;
  }

  /// if the lock is available, push to front, return whether that succeeded
  template <class Arg>
  bool try_push_front(Arg &&a) {
    if ( m_guard.try_lock() ) {
      m_items.push_front(std::forward<Arg>(a));
      m_guard.unlock();
      return true;
    }
    return false;
  }

  /// obtain lock and fetch the last item (if any)
  bool pop_back(Item &a) {
    LockGuard lock(m_guard);
    if (not m_items.empty()) {
      a = std::move( m_items.back() );
      m_items.pop_back();
      return true;
    }
    return false;
  }

  /// same as pop_back(), for compatibility
  bool pop(Item &a) {
    return pop_back(a);
  }

  /// try to obtain lock and fetch the last item (if any)
  bool try_pop_back(Item &a) {
    if (m_guard.try_lock()) {
      if (not m_items.empty()) {
        a = std::move( m_items.back() );
        m_items.pop_back();
        m_guard.unlock();
        return true;
      }
      m_guard.unlock();
      return false;
    }
    return false;
  }

  /// same as try_pop_back(), for compatibility
  bool try_pop(Item &a) {
    return try_pop_back(a);
  }

  /// access the current last element, if any, but do not pop
  bool back(Item &a) {
    LockGuard lock(m_guard);
    if (not m_items.empty()) {
      a = m_items.back();
      return true;
    }
    return false;
  }

  /// access element by index (unprotected)
  const Item &operator[] (size_t k) const {
    assert(k < m_items.size());
    return m_items[k];
  }

  /// access element by index (unprotected)
  Item &operator[] (size_t k) {
    assert(k < m_items.size());
    return m_items[k];
  }

  /// estimate the current number of items
  size_t loadfactor() const {return m_items.size();}

private:

  /// actual task objects
  std::deque<Item> m_items;

  /// protects access to items
  std::mutex m_guard;
};

#endif // LOCKEDQUEUE_H
