/* Copyright (c) 2015 Jeff Preshing

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgement in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution. */

#ifndef GENUA_SEMAPHORE_H
#define GENUA_SEMAPHORE_H

#include "defines.h"
#include <atomic>
#include <cassert>

#if defined(_WIN32)

#include <windows.h>
#undef min
#undef max

/** Platform-specific semaphore (Win32)
 * \internal
 */
class KernelSemaphore
{
public:
  KernelSemaphore(const KernelSemaphore& other) = delete;
  KernelSemaphore& operator=(const KernelSemaphore& other) = delete;
  KernelSemaphore(int initialCount = 0) {
    assert(initialCount >= 0);
    m_hSema = CreateKernelSemaphore(NULL, initialCount, MAXLONG, NULL);
  }
  ~KernelSemaphore() {CloseHandle(m_hSema);}
  void wait() {WaitForSingleObject(m_hSema, INFINITE);}
  void signal(int count = 1) {ReleaseKernelSemaphore(m_hSema, count, NULL);}
private:
  HANDLE m_hSema;
};

#elif defined(__MACH__)

#include <mach/mach.h>

/** Platform-specific semaphore (Darwin)
 * \internal
 */
class KernelSemaphore
{
public:
  KernelSemaphore(const KernelSemaphore& other) = delete;
  KernelSemaphore& operator=(const KernelSemaphore& other) = delete;
  KernelSemaphore(int initialCount = 0) {
    assert(initialCount >= 0);
    semaphore_create(mach_task_self(), &m_sema, SYNC_POLICY_FIFO, initialCount);
  }
  ~KernelSemaphore() {
    semaphore_destroy(mach_task_self(), m_sema);
  }
  void wait() {semaphore_wait(m_sema);}
  void signal() {semaphore_signal(m_sema);}
  void signal(int count) {
    while (count-- > 0)
      semaphore_signal(m_sema);
  }
private:
  semaphore_t m_sema;
};

#elif defined(__unix__)

#include <semaphore.h>

/** Platform-specific semaphore (posix)
 * \internal
 */
class KernelSemaphore
{
public:
  KernelSemaphore(const KernelSemaphore& other) = delete;
  KernelSemaphore& operator=(const KernelSemaphore& other) = delete;
  KernelSemaphore(int initialCount = 0) {
    assert(initialCount >= 0);
    sem_init(&m_sema, 0, initialCount);
  }
  ~KernelSemaphore() {sem_destroy(&m_sema);}
  void wait() {
    // http://stackoverflow.com/questions/2013181/gdb-causes-sem-wait-to-fail-with-eintr-error
    int rc;
    do {
      rc = sem_wait(&m_sema);
    } while (rc == -1 && errno == EINTR);
  }
  void signal() { sem_post(&m_sema); }
  void signal(int count) {
    while (count-- > 0)
      sem_post(&m_sema);
  }
private:
  sem_t m_sema;
};

#else

// TODO: Fallback implementation using std::condition_variable

#error Unsupported platform!

#endif

/** Two-level semaphore.
 *
 * \ingroup concurrency
 * \sa TaskScheduler, TaskCounter, parallel::enqueue()
 */
class Semaphore
{
public:

  /// create a sempahore with an initial state (0, i.e. closed, by default)
  Semaphore(int initialCount = 0) : m_count(initialCount) {
    assert(initialCount >= 0);
  }

  /// signal one more thread to pass through
  void signal(int count = 1) {
    int oldCount = m_count.fetch_add(count, std::memory_order_release);
    int toRelease = -oldCount < count ? -oldCount : count;
    if (toRelease > 0)
      m_sema.signal(toRelease);
  }

  /// check quickly whether we can pass without touching the kernel
  bool tryWait() {
    int oldCount = m_count.load(std::memory_order_relaxed);
    return (oldCount > 0 and
            m_count.compare_exchange_strong(oldCount, oldCount - 1,
                                            std::memory_order_acquire));
  }

  /// wait until signalled to pass
  void wait() {
    if (not tryWait())
      waitWithPartialSpinning();
  }

private:

  /// spin a while to see whether we might get through; block if not.
  void waitWithPartialSpinning()
  {
    int oldCount;
    int spin = 10000; // TODO: Choice?
    while (spin--) {
      oldCount = m_count.load(std::memory_order_relaxed);
      if ((oldCount > 0) and
          m_count.compare_exchange_strong(oldCount, oldCount - 1,
                                          std::memory_order_acquire))
        return;
      // Prevent the compiler from collapsing the loop.
      std::atomic_signal_fence(std::memory_order_acquire);
    }

    oldCount = m_count.fetch_sub(1, std::memory_order_acquire);
    if (oldCount <= 0)
      m_sema.wait();
  }

private:

  /// semaphore state
  std::atomic<int> m_count;

  /// heavy-weight, system-specific semaphore
  KernelSemaphore m_sema;
};

#endif // KernelSemaphore_H

