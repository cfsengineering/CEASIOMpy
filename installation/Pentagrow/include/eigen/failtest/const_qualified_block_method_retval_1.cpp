#include "../eeigen/Core"

#ifdef EIGEN_SHOULD_FAIL_TO_BUILD
#define CV_QUALIFIER const
#else
#define CV_QUALIFIER
#endif

using namespace eeigen;

void foo(CV_QUALIFIER Matrix3d &m)
{
    Block<Matrix3d> b(m.block(0, 0, 3, 3));
}

int main() {}
