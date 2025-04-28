
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
 
#include "xmltreemodel.h"
#include "xmltreeitem.h"
#include <genua/xmlelement.h>
#include <QAbstractItemModel>

void XmlTreeModel::build(const XmlElement *rootElement)
{
  // QAbstractItemModel::reset();
  beginResetModel();
  XmlTreeItemPtr rootItem = boost::make_shared<XmlTreeItem>();
  rootItem->build(0u, nullptr, rootElement);
  m_root = rootItem;
  endResetModel();
}


