#include "../eeigen/Core"

#ifdef EIGEN_SHOULD_FAIL_TO_BUILD
#define CV_QUALIFIER const
#else
#define CV_QUALIFIER
#endif

using namespace eeigen;

void foo(CV_QUALIFIER float *ptr, DenseIndex size)
{
    Map<ArrayXf> m(ptr, size);
}

int main() {}
