
#include <genua/color.h>
#include <genua/timing.h>
#include <boost/compute.hpp>
#include <boost/compute/algorithm/detail/copy_on_device.hpp>

#include <iostream>
#include <exception>
#include <fstream>
#include <vector>
#include <algorithm>
#include <cstdlib>

using namespace std;
namespace gpu = boost::compute;
typedef  gpu::uchar4_ clChar4;

float frandom()
{
  return float(rand()) / RAND_MAX;
}

Color fmap_cpu(float x)
{
  Color c;
  c.map(0.0f, 1.0f, x);
  return c;
}

template <class InputIterator, class OutputIterator>
string ckernel_src(InputIterator first, InputIterator last, OutputIterator result)
{
  gpu::detail::copy_kernel<InputIterator, OutputIterator> kernel;
  kernel.set_range(first, last, result);
  return kernel.source();
}

int main(int argc, char *argv[])
{
  gpu::device dev = gpu::system::default_device();

  if (argc > 1) {
    std::vector<gpu::device> devices = gpu::system::devices();
    size_t idev = atoi( argv[1] );
    if (idev >= devices.size()) {
      cout << "Device index " << idev << " out of range." << endl;
      for (size_t i=0; i<devices.size(); ++i)
        cout << "Device [" << i << "]: " << devices[i].name() << endl;
      return EXIT_FAILURE;
    } else {
      dev = devices[idev];
    }
  }

  // create context for default device
  // gpu::context context(dev);
  // gpu::command_queue queue(context, dev);

  cout << "Present device name: " << dev.name() << endl;
  cout << " Global memory: " << dev.global_memory_size() / 1024 << "kB" << endl;
  cout << " Local memory: " << dev.local_memory_size() / 1024 << "kB" << endl;
  cout << " Compute units: " << dev.compute_units() << endl;

  try {

    Wallclock clk;

    // generate random numbers
    size_t n = 20000000;
    std::vector<float> x(n);
    std::generate( x.begin(), x.end(), frandom );

    // map to colors
    cout << "Color conversion OpenCL test:" << endl;
    clk.start();
    std::vector<Color> c(n);
    std::transform( x.begin(), x.end(), c.begin(), fmap_cpu );
    clk.stop();
    cout << "CPU operation: " << clk.elapsed()*1000 << "ms." << endl;

    clk.start();
    gpu::vector<float> gx(n);
    gpu::copy(x.begin(), x.end(), gx.begin());
    clk.stop();
    cout << "Copy to GPU: " << clk.elapsed()*1000 << "ms." << endl;

    boost::compute::function<gpu::uchar4_ (float)> fmap_gpu =
        boost::compute::make_function_from_source<gpu::uchar4_ (float)>(
          "fmap_gpu",
          "uchar4 fmap_gpu(float x);"
          "uchar4 fmap_gpu(float x) {"
          "  uchar4 c0 = (uchar4) 255;"
          "  c0.s0 = 0; "
          "  c0.s1 = (uchar) 4*255*x;"
          "  uchar4 c1 = (uchar4) 255;"
          "  c1.s0 = 0; "
          "  c1.s2 = (uchar) 255*(4.0f - 4.0f*x);"
          "  uchar4 c2 = (uchar4) 255;"
          "  c2.s0 = (uchar) 255*(4.0f*x - 2.0f);"
          "  c2.s2 = 0;"
          "  uchar4 c3 = (uchar4) 255;"
          "  c3.s1 = (uchar) 255*(4.0f - 4.0f*x);"
          "  c3.s2 = 0;"
          "  uchar4 b0 = (uchar4) (x <= 0.25f ? 255 : 0);"
          "  uchar4 b1 = (uchar4) (x <= 0.50f ? 255 : 0);"
          "  uchar4 b2 = (uchar4) (x <= 0.75f ? 255 : 0);"
          "  uchar4 c = select(c3, c2, b2);"
          "  c = select(c, c1, b1);"
          "  c = select(c, c0, b0);"
          "return c; }"
          );

    clk.start();
    gpu::vector<gpu::uchar4_> gc(n);
    gpu::transform(gx.begin(), gx.end(), gc.begin(), fmap_gpu);
    clk.stop();
    cout << "GPU transform: " << clk.elapsed()*1000 << "ms." << endl;

    clk.start();
    std::vector<gpu::uchar4_> hc(n);
    gpu::copy(gc.begin(), gc.end(), hc.begin());
    clk.stop();
    cout << "back to CPU: " << clk.elapsed()*1000 << "ms." << endl;

    for (size_t k=0; k<8; ++k) {
      cout << "Value: " << x[k] << " gpu color: "
           << (int) hc[k][0] << ',' << (int) hc[k][1] << ','
           << (int) hc[k][2];
      cout << " cpu color: "
           << c[k].red() << ',' << c[k].green() << ',' << c[k].blue() << endl;
    }

    string src = ckernel_src( gpu::make_transform_iterator(gx.begin(), fmap_gpu),
                              gpu::make_transform_iterator(gx.end(), fmap_gpu),
                              gc.begin() );
    cout << "Copy kernel source: " << endl << src << endl;




  } catch (exception & xcp) {
    cout << "Problem: " << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  return 0;
}
