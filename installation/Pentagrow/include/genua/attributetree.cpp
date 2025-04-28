
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
 
#include "attributetree.h"

uint AttributeTree::index(const AttributeTree::KeyType &key) const
{
    AttributeArray::const_iterator pos;
    auto cmp = [&](const Attribute &a, const KeyType &b) {return a.first < b;};
    pos = std::lower_bound( m_attr.cbegin(), m_attr.cend(), key, cmp);
    return (pos != m_attr.end()) ?
                (std::distance(m_attr.cbegin(), pos)) :
                NotFound;
}
