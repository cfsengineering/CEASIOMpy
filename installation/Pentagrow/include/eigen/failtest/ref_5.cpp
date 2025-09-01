#include "../eeigen/Core"

using namespace eeigen;

void call_ref(Ref<VectorXf> a) {}

int main()
{
  VectorXf a(10);
  DenseBase<VectorXf> &ac(a);
#ifdef EIGEN_SHOULD_FAIL_TO_BUILD
  call_ref(ac);
#else
  call_ref(ac.derived());
#endif
}
