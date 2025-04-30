
#include <genua/atomicop.h>
#include <atomic>

//      node<T>* old_head = head.load(std::memory_order_relaxed);
//      do {
//          new_node->next = old_head;
//       } while(!head.compare_exchange_weak(old_head, new_node,
//                                           std::memory_order_release,
//                                           std::memory_order_relaxed));

void by_pointer(std::atomic<float> *p, float dx)
{
  float xnew, xold = p->load(std::memory_order_acquire);
  do {
    xnew = xold + dx;
  } while (not p->compare_exchange_weak(xold, xnew,
                                        std::memory_order_release,
                                        std::memory_order_relaxed));
} 

void by_ref(float &a, float dx)
{
  std::atomic<float> *p = reinterpret_cast<std::atomic<float>*>(&a);
  float xnew, xold = p->load(std::memory_order_acquire);
  do {
    xnew = xold + dx;
  } while (not p->compare_exchange_weak(xold, xnew,
                                        std::memory_order_release,
                                        std::memory_order_relaxed));
}


void late_load(float &a, float dx)
{
  std::atomic<float> *p = reinterpret_cast<std::atomic<float>*>(&a);
  float xnew, xold;
  do {
    xold = p->load(std::memory_order_acquire);
    xnew = xold + dx;
  } while (not p->compare_exchange_weak(xold, xnew,
                                        std::memory_order_release,
                                        std::memory_order_relaxed));
}


void fcheck(float &x, float dx)
{
  atomic_add(x, dx);
}

void icheck(int &x, int dx)
{
  atomic_add(x, dx);
}

void dcheck(std::complex<double> &x, std::complex<double> dx)
{
  atomic_add(x, dx);
}

