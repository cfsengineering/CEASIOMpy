
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#include "nststressfield.h"
#include "nstelementstress.h"
#include <genua/dvector.h>
#include <genua/xcept.h>

using namespace std;

void NstStressField::setup(uint icode, uint countHint)
{
  itemCode(icode);

  uint nsigma = 0;
  if ( NstElementStressRecord::isCompositeShell(itemCode()) ) {
    nsigma = 4;
    m_componentName.resize(nsigma);
    m_componentName[0] = "C|Normal-1"; // [0]
    m_componentName[1] = "C|Normal-2"; // [1]
    m_componentName[2] = "C|Shear-12"; // [2]
    m_componentName[3] = "C|MaxShear"; // [8]
  } else if (NstElementStressRecord::isLinearShell(itemCode())) {
    nsigma = 8;
    m_componentName.resize(nsigma);
    m_componentName[0] = "Z1|Normal-x"; // [1]
    m_componentName[1] = "Z1|Normal-y"; // [2]
    m_componentName[2] = "Z1|Shear-xy"; // [3]
    m_componentName[3] = "Z1|VonMises"; // [7]
    m_componentName[4] = "Z2|Normal-x"; // [9]
    m_componentName[5] = "Z2|Normal-y"; // [10]
    m_componentName[6] = "Z2|Shear-xy"; // [11]
    m_componentName[7] = "Z2|VonMises"; // [15]
  } else if (NstElementStressRecord::isSolid(itemCode())) {
    nsigma = 7;
    m_componentName.resize(nsigma);
    m_componentName[0] = "S|Normal-x"; // [0]
    m_componentName[1] = "S|Normal-y"; // [8]
    m_componentName[2] = "S|Normal-z"; // [14]
    m_componentName[3] = "S|Shear-xy"; // [1]
    m_componentName[4] = "S|Shear-yz"; // [9]
    m_componentName[5] = "S|Shear-zx"; // [15]
    m_componentName[6] = "S|VonMises"; // [7]
  } else {
    throw Error("NstStressField does not support element type "+str(icode));
  }

  m_eid.reserve(countHint);
  m_stress.resize(nsigma);
  for (uint j=0; j<nsigma; ++j)
    m_stress[j].reserve(countHint);
}

void NstStressField::append(const NstElementStressRecord &rcd)
{
  assert( rcd.laminateIndex == laminateIndex() );

  m_eid.push_back( rcd.eid );

#ifndef NDEBUG
  for (int i=0; i<16; ++i)
    assert(isfinite(rcd.sigma[i]));
#endif

  if (NstElementStressRecord::isCompositeShell(itemCode())) {
    m_stress[0].push_back( rcd.sigma[0] );
    m_stress[1].push_back( rcd.sigma[1] );
    m_stress[2].push_back( rcd.sigma[2] );
    m_stress[3].push_back( rcd.sigma[8] );
  } else if (NstElementStressRecord::isLinearShell(itemCode())) {
    m_stress[0].push_back( rcd.sigma[1] );
    m_stress[1].push_back( rcd.sigma[2] );
    m_stress[2].push_back( rcd.sigma[3] );
    m_stress[3].push_back( rcd.sigma[7] );
    m_stress[4].push_back( rcd.sigma[9] );
    m_stress[5].push_back( rcd.sigma[10] );
    m_stress[6].push_back( rcd.sigma[11] );
    m_stress[7].push_back( rcd.sigma[15] );
  } else if (NstElementStressRecord::isSolid(itemCode())) {
    m_stress[0].push_back( rcd.sigma[0] );
    m_stress[1].push_back( rcd.sigma[8] );
    m_stress[2].push_back( rcd.sigma[14] );
    m_stress[3].push_back( rcd.sigma[1] );
    m_stress[4].push_back( rcd.sigma[9] );
    m_stress[5].push_back( rcd.sigma[15] );
    m_stress[6].push_back( rcd.sigma[7] );
  }
}

void NstStressField::mapEid(const DVector<int> &feid, Indices &map) const
{
  const size_t n = m_eid.size();
  map.resize(n);
  for (size_t i=0; i<n; ++i) {
    DVector<int>::const_iterator pos;
    pos = std::find(feid.begin(), feid.end(), int(m_eid[i]));
    map[i] = (pos != feid.end()) ? std::distance(feid.begin(), pos) : NotFound;
  }
}

void NstStressField::inject(uint k, const Indices &eidMap, Vector &v) const
{
  const size_t n = m_eid.size();
  for (size_t i=0; i<n; ++i) {
    uint idx = eidMap[i];
    if (idx != NotFound) {
      assert(isfinite(m_stress[k][i]));
      v[idx] = m_stress[k][i];
    }
  }
}

int NstStressField::elementClass() const
{
  return NstElementStressRecord::elementClass(itemCode());
}

bool NstStressField::merge(const NstStressField &rhs)
{
  if ( elementClass() != rhs.elementClass() )
    return false;
  if ( subcase() != rhs.subcase() )
    return false;
  if ( laminateIndex() != rhs.laminateIndex() )
    return false;

  const size_t nsigma = ncomponents();
  if (nsigma != rhs.ncomponents())
    return false;

  for (size_t j=0; j<nsigma; ++j) {
    if ( componentName(j) != rhs.componentName(j) )
      return false;
  }

  // compatible!
  m_eid.insert( m_eid.end(), rhs.m_eid.begin(), rhs.m_eid.end() );
  for (size_t j=0; j<nsigma; ++j) {
    StressVector &s( m_stress[j] );
    const StressVector &r( rhs.m_stress[j] );
    s.insert(s.end(), r.begin(), r.end());
  }

  return true;
}
