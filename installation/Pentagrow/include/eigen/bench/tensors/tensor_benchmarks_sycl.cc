#define EIGEN_USE_SYCL

#include <SYCL/sycl.hpp>
#include <iostream>

#include "tensor_benchmarks.h"

using eeigen::array;
using eeigen::SyclDevice;
using eeigen::Tensor;
using eeigen::TensorMap;
// Simple functions
template <typename device_selector>
cl::sycl::queue sycl_queue() {
  return cl::sycl::queue(device_selector(), [=](cl::sycl::exception_list l) {
    for (const auto& e : l) {
      try {
        std::rethrow_exception(e);
      } catch (cl::sycl::exception e) {
        std::cout << e.what() << std::endl;
      }
    }
  });
}

#define BM_FuncGPU(FUNC)                                       \
  static void BM_##FUNC(int iters, int N) {                    \
    StopBenchmarkTiming();                                     \
    cl::sycl::queue q = sycl_queue<cl::sycl::gpu_selector>();  \
    eeigen::SyclDevice device(q);                               \
    BenchmarkSuite<eeigen::SyclDevice, float> suite(device, N); \
    suite.FUNC(iters);                                         \
  }                                                            \
  BENCHMARK_RANGE(BM_##FUNC, 10, 5000);

BM_FuncGPU(broadcasting);
BM_FuncGPU(coeffWiseOp);
