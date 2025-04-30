
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
 
#include "xmltreeitem.h"
#include <genua/xmlelement.h>
#include <QString>

void XmlTreeItem::build(uint row, XmlTreeItemPtr parent,
                        const XmlElement *elm)
{
  TreeItem::destroy();
  m_parent = parent;
  m_element = elm;
  m_row = row;

  XmlTreeItemPtr self(this, null_deleter());
  if (elm != 0) {
    uint crow = 0;
    XmlElement::const_iterator itr, last = elm->end();
    for (itr = elm->begin(); itr != last; ++itr) {
      XmlTreeItemPtr item = boost::make_shared<XmlTreeItem>();
      const XmlElement &child(*itr);
      item->build(crow, self, &child);
      m_siblings.push_back( item );
      ++crow;
    }
  }
}

QVariant XmlTreeItem::data(int role) const
{
  QVariant var;
  if (m_element == 0)
    return var;

  if (role == Qt::DisplayRole) {
    var = QString::fromStdString( m_element->name() );
  }

  return var;
}
