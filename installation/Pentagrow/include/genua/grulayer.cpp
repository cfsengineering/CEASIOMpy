#include "grulayer.h"
#include "cbvops.h"
#include "simdsupport.h"
#include <eeigen/Dense>

// naive implementation to allow compiler to vectorize

inline static float sigmoid(float x)
{
  float t = expf(-x);
  return 1.0f / (1.0f + t);
}

inline static float sigtanh(float x)
{
  float t1 = expf(-x);
  float t2 = 1.0f / t1;
  return (t2 - t1) / (t2 + t1);
}

void GRULayer::allocate(size_t nx, size_t nh)
{
  // necessary for alignment
  assert(nh % 16 == 0);
  m_nx = nx;
  m_nh = nh;
  m_wx.allocate(3 * nh, nx);
  m_wh.allocate(3 * nh, nh);
  m_bx.allocate(3 * nh);
  m_bh.allocate(3 * nh);
  m_xg.allocate(3 * nh);
  m_hg.allocate(3 * nh);
  m_h.allocate(nh);
}

const DVector<float> &GRULayer::forward(const DVector<float> &x)
{
  m_xg.mmap() = m_wx.cmap() * x.cmap() + m_bx.cmap();
  m_hg.mmap() = m_wh.cmap() * m_h.cmap() + m_bh.cmap();

  const float *prx = m_xg.pointer();
  const float *pzx = m_xg.pointer() + m_nh;
  const float *pnx = m_xg.pointer() + 2 * m_nh;

  const float *prh = m_hg.pointer();
  const float *pzh = m_hg.pointer() + m_nh;
  const float *pnh = m_hg.pointer() + 2 * m_nh;

  float *ph = m_h.pointer();

  // TODO: Explicit vectorization
  // determine next state
  OMP_SIMD("aligned(prx,prh,pzx,pzh,pnx,pnh,ph:8)")
  for (size_t i = 0; i < m_nh; ++i)
  {
    float r = sigmoid(prx[i] + prh[i]);
    float z = sigmoid(pzx[i] + pzh[i]);
    float n = sigtanh(pnx[i] + r * pnh[i]);
    ph[i] = (1.0f - z) * n + z * ph[i];
  }

  return m_h;
}
