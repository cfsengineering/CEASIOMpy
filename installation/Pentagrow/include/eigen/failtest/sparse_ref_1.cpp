#include "../eeigen/Sparse"

#ifdef EIGEN_SHOULD_FAIL_TO_BUILD
#define CV_QUALIFIER const
#else
#define CV_QUALIFIER
#endif

using namespace eeigen;

void call_ref(Ref<SparseMatrix<float>> a) {}

int main()
{
  SparseMatrix<float> a(10, 10);
  CV_QUALIFIER SparseMatrix<float> &ac(a);
  call_ref(ac);
}
