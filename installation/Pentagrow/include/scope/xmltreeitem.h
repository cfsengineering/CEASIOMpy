
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
 
#ifndef SCOPE_XMLTREEITEM_H
#define SCOPE_XMLTREEITEM_H

#include "treeitem.h"
#include <genua/defines.h>

class XmlElement;

class XmlTreeItem : public TreeItem
{
public:

  /// construct empty item
  XmlTreeItem() : TreeItem(), m_element(0) {}

  /// recursive construction
  void build(uint row, XmlTreeItemPtr parent, const XmlElement *elm);

  /// access mapped XML element
  const XmlElement *element() const {return m_element;}

  /// return element name
  QVariant data(int role) const;

private:

  /// XML element associated with this item
  const XmlElement *m_element;
};

#endif // XMLTREEITEM_H
