#include "../eeigen/SVD"

#ifdef EIGEN_SHOULD_FAIL_TO_BUILD
#define SCALAR int
#else
#define SCALAR float
#endif

using namespace eeigen;

int main()
{
  BDCSVD<Matrix<SCALAR,Dynamic,Dynamic> > qr(Matrix<SCALAR,Dynamic,Dynamic>::Random(10,10));
}
