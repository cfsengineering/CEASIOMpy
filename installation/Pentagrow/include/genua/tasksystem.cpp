
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
 
#include "tasksystem.h"

// --------------- NotificationQueue --------------------------------------

void FunctionQueue::done()
{
  {
    UniqueLock lock(m_mutex);
    m_done = true;
  }
  m_ready.notify_all();
}

bool FunctionQueue::pop(std::function<void ()> &x)
{
  UniqueLock lock(m_mutex);
  while (m_queue.empty() and (not m_done))
    m_ready.wait(lock);
  if (m_queue.empty())
    return false;
  x = move(m_queue.front());
  m_queue.pop_front();
  return true;
}

void FunctionQueue::clear()
{
  UniqueLock lock(m_mutex);
  m_queue.clear();
}

// --------------- TaskSystem --------------------------------------

TaskScheduler TaskScheduler::s_pool;

TaskScheduler::TaskScheduler() : m_qindex(0)
{
  for (uint i = 0; i < m_ncores; ++i) {
    m_threads.emplace_back([&, i]{ run(i); });
  }
}

TaskScheduler::~TaskScheduler()
{
  for (auto& e : m_queues)
    e.done();
  for (auto& e : m_threads) {
    if (e.joinable())
      e.join();
  }
}

void TaskScheduler::sweep()
{
  for (uint n = 0; n < m_ncores; ++n)
    m_queues[n].clear();
}

void TaskScheduler::run(unsigned i)
{
  while (true) {
    std::function<void()> f;
    for (uint n = 0; n < m_ncores * 128; ++n) {
      if (m_queues[(i + n) % m_ncores].try_pop(f))
        break;
    }
    if ((not f) and (not m_queues[i].pop(f)))
      break;
    f();
  }
}

// --------------- TaskSystem --------------------------------------

void TaskContext::wait()
{
  UniqueLock lock(m_mutex);
  while ( 0 < m_enqeued.load(std::memory_order_acquire) )
    m_completed.wait(lock);
}
