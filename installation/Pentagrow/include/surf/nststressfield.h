
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
 
#ifndef SURF_NSTSTRESSFIELD_H
#define SURF_NSTSTRESSFIELD_H

#include "forward.h"
#include <genua/propmacro.h>

class NstElementStressRecord;

/** Container for NASTRAN stress data.
 *
 * As the stress state for different element types differs, the number of
 * stress components (direction, normal/shear) is variable. There will hence be
 * one stress field for each element type group, for each subcase and
 * for each composite ply index.
 *
 * \ingroup structures
 * \sa NstMesh, NstElementStressRecord
 */
class NstStressField
{
public:

  /// default construction
  NstStressField() = default;

  /// default copy
  NstStressField(const NstStressField &) = default;

  /// move construction spelled out for MSVC
  NstStressField(NstStressField &&rhs) {
    *this = std::move(rhs);
  }

  /// default assignment
  NstStressField &operator= (const NstStressField &rhs) = default;

  /// move assignment spelled out for MSVC
  NstStressField &operator= (NstStressField &&rhs) {
    if (this != &rhs) {
      m_componentName = std::move(rhs.m_componentName);
      m_eid = std::move(rhs.m_eid);
      m_stress = std::move(rhs.m_stress);
      m_label = std::move(rhs.m_label);
      m_subcase = rhs.m_subcase;
      m_laminateIndex = rhs.m_laminateIndex;
      m_itemCode = rhs.m_itemCode;
      m_mergedInto = rhs.m_mergedInto;
    }
    return *this;
  }

  /// number of element ids registered
  uint nelements() const {return m_eid.size();}

  /// number of components present
  uint ncomponents() const {return m_componentName.size();}

  /// name of the stress component k
  const std::string &componentName(uint k) const {return m_componentName[k];}

  /// setup for a stress item code
  void setup(uint itemCode, uint countHint = 4096);

  /// register a stress record
  void append(const NstElementStressRecord &rcd);

  /// create element index map, assuming feid[k] contains EID of element k
  void mapEid(const DVector<int> &feid, Indices &map) const;

  /// inject component k into vector v using element index map created earlier
  void inject(uint k, const Indices &eidMap, Vector &v) const;

  /// return element class of this field
  int elementClass() const;

  /// merge with another field if possible, return whether merge completed
  bool merge(const NstStressField &rhs);

  /// whether field was merged into another one
  bool isMerged() const {return m_mergedInto != NotFound;}

private:

  typedef DVector<float> StressVector;
  typedef std::vector<StressVector> StressBlock;

  /// stress component names
  StringArray m_componentName;

  /// Nastran element ids, EID, one element per row
  Indices m_eid;

  /// outer index is stress component, inner index is element index
  StressBlock m_stress;

  GENUA_PROP(std::string, label)
  GENUA_PROP(uint, subcase)
  GENUA_PROP(uint, laminateIndex)
  GENUA_PROP(uint, itemCode)
  GENUA_PROP_INI(uint, mergedInto, NotFound)
};

#endif // NSTSTRESSFIELD_H
