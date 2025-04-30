/* Copyright (C) 2016 David Eller <david@larosterna.com>
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

#ifndef GENUA_SCOPEDSETTING_H
#define GENUA_SCOPEDSETTING_H

/** Change a scalar within a scope only.
 *
 * Used to ensure exception safety etc. by encapsulating a value setting which
 * needs to be reset when the local scope is left.
 *
 * \verbatim
 *  {
 *    ScopedSetting<bool> guard(m_protect, false);
 *    ...
 *    // m_protect will be reset to its original value on leaving this scope
 *  }
 * \endverbatim
 *
 * \ingroup utility
 */
template <class ValueType>
class ScopedSetting
{
public:

  /// change x to v and reset on destruction
  ScopedSetting(ValueType &x, const ValueType &v) : m_setting(x) {
    m_original = x;
    m_setting = v;
  }

  /// reset original value
  ~ScopedSetting() {m_setting = m_original;}

private:

  /// reference to setting to modify
  ValueType &m_setting;

  /// the stored setting to be reinstated on destruction
  ValueType m_original;
};

#endif // SCOPEDSETTING_H
