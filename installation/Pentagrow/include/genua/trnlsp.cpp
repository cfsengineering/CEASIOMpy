
#include "trnlsp.h"
#include <mkl.h>

namespace mkl {

int Success = TR_SUCCESS;
int InvalidOption = TR_INVALID_OPTION;
int OutOfMemory = TR_OUT_OF_MEMORY;
int IterationsExceeded = -1;
int RadiusTooSmall = -2;
int Converged = -3;
int SingularJacobian = -4;
int NoXChange = -5;
int Extremum = -6;

int trnlspbc_init(void *handle, const int &n, const int &m, const float *x,
                  const float *LW, const float *UP, const float *eps,
                  const int &iter1, const int &iter2, const float &rs)
{
  assert(handle != nullptr);
  return strnlspbc_init( (_TRNSPBC_HANDLE_t*) handle, &n, &m, x,
                         LW, UP, eps, &iter1, &iter2, &rs);
}

int trnlspbc_init(void *handle, const int &n, const int &m, const double *x,
                  const double *LW, const double *UP, const double *eps,
                  const int &iter1, const int &iter2, const double &rs)
{
  assert(handle != nullptr);
  return dtrnlspbc_init( (_TRNSPBC_HANDLE_t*) handle, &n, &m, x,
                         LW, UP, eps, &iter1, &iter2, &rs);
}

int trnlspbc_check(void *handle, const int &n,
                        const int &m, const float *fjac, const float *fvec,
                        const float *LW, const float *UP, const float *eps,
                        int *info)
{
  assert(handle != nullptr);
  return strnlspbc_check((_TRNSPBC_HANDLE_t*) handle, &n, &m, fjac, fvec,
                         LW, UP, eps, info);
}

int trnlspbc_check(void *handle, const int &n,
                        const int &m, const double *fjac, const double *fvec,
                        const double *LW, const double *UP, const double *eps,
                        int *info)
{
  assert(handle != nullptr);
  return dtrnlspbc_check((_TRNSPBC_HANDLE_t*) handle, &n, &m, fjac, fvec,
                         LW, UP, eps, info);
}

int trnlspbc_solve(void *handle, float *fvec, float *fjac, int &request)
{
  assert(handle != nullptr);
  return strnlspbc_solve((_TRNSPBC_HANDLE_t*) handle, fvec, fjac, &request);
}

int trnlspbc_solve(void *handle, double *fvec, double *fjac, int &request)
{
  assert(handle != nullptr);
  return dtrnlspbc_solve((_TRNSPBC_HANDLE_t*) handle, fvec, fjac, &request);
}

int trnlspbc_delete(void *handle, const float *)
{
  return strnlspbc_delete((_TRNSPBC_HANDLE_t*) handle);
}

int trnlspbc_delete(void *handle, const double *)
{
  return dtrnlspbc_delete((_TRNSPBC_HANDLE_t*) handle);
}

}
