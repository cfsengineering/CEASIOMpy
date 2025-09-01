#include "linearlayer.h"
#include <eeigen/Dense>

void LinearLayer::allocate(size_t nx, size_t ny)
{
  m_wgt.allocate(ny, nx);
  m_bias.allocate(ny);
  m_y.allocate(ny);
}

const DVector<float> &LinearLayer::forward(const DVector<float> &x)
{
  m_y.mmap() = m_wgt.cmap() * x.cmap() + m_bias.cmap();
  return m_y;
}
