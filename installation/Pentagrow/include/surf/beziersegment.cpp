#include "beziersegment.h"
#include <genua/transformation.h>

BezierSegment *BezierSegment::clone() const
{
  return new BezierSegment(*this);
}

void BezierSegment::byTangents(const Vct3 &p0, const Vct3 &t0,
                               const Vct3 &p1, const Vct3 &t1)
{
  m_cp[0] = p0;
  m_cp[1] = p0 + t0 / 3.0;
  m_cp[2] = p1 - t1 / 3.0;
  m_cp[3] = p1;
}

Vct3 BezierSegment::derive(Real t, uint k) const
{
  if (k == 0) {
    return this->eval(t);
  } else if (k == 1) {
    return 3*sq(1-t)* (m_cp[1] - m_cp[0])
        +  6*(1-t)*t* (m_cp[2] - m_cp[1])
        +  3*sq(t)*   (m_cp[3] - m_cp[2]);
  } else if (k == 2) {
    return 6*(1-t)*(m_cp[2] - 2.0*m_cp[1] + m_cp[0])
        +  6*t    *(m_cp[3] - 2.0*m_cp[2] + m_cp[1]);
  }

  return Vct3(0.0, 0.0, 0.0);
}

void BezierSegment::apply()
{
  const Mtx44 & tfm = RFrame::trafoMatrix();
  for (int k=0; k<4; ++k)
    Trafo3d::transformPoint(tfm, m_cp[k]);

  RFrame::clear();
}
