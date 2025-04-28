#include "mappedcurve.h"

MappedCurve::MappedCurve(const AbstractCurvePtr &acp, Real scale, Real offset)
  : AbstractCurve(acp->name())
{
  init(acp, scale, offset);
}

void MappedCurve::init(const AbstractCurvePtr &acp, Real scale, Real offset)
{
  m_base = acp;
  m_scale = scale;
  m_offset = offset;
}

MappedCurve *MappedCurve::clone() const
{
  MappedCurve *pc = new MappedCurve(name());
  pc->m_base = AbstractCurvePtr( m_base->clone() );
  pc->m_offset = m_offset;
  pc->m_scale = m_scale;
  return pc;
}

Vct3 MappedCurve::eval(Real t) const
{
  Real s = m_offset + m_scale*t;
  return m_base->eval(s);
}

Vct3 MappedCurve::derive(Real t, uint k) const
{
  // C(s(t)), dC/dt = dC/ds * ds/dt
  Real s = m_offset + m_scale*t;
  return m_base->derive(s, k) * std::pow(m_scale, int(k));
}

void MappedCurve::tgline(Real t, Vct3 &c, Vct3 &dc) const
{
  Real s = m_offset + m_scale*t;
  m_base->tgline(s, c, dc);;
  dc *= m_scale;
}

void MappedCurve::apply()
{
  m_base->setTrafoMatrix( RFrame::trafoMatrix() );
  m_base->apply();
  RFrame::clear();
}

XmlElement MappedCurve::toXml(bool share) const
{
  XmlElement xe("MappedCurve");
  xe["name"] = name();
  xe["scale"] = str(m_scale);
  xe["offset"] = str(m_offset);

  assert(m_base != nullptr);
  if (m_base != nullptr)
    xe.append( m_base->toXml(share) );

  return xe;
}

void MappedCurve::fromXml(const XmlElement &xe)
{
  rename( xe.attribute("name") );
  m_scale = xe.attr2float("scale", m_scale);
  m_offset = xe.attr2float("offset", m_offset);
  for (const XmlElement &child : xe) {
    AbstractCurvePtr acp = AbstractCurve::createFromXml(child);
    if (acp != nullptr) {
      m_base = acp;
      break;
    }
  }

  assert(m_base != nullptr);
}
