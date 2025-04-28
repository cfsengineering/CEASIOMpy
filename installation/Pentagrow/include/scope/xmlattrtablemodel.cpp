
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
 
#include "xmlattrtablemodel.h"
#include <genua/xmlelement.h>

#include <QDebug>

void XmlAttrTableModel::display(const XmlElement *element)
{
  beginResetModel();
  m_element = element;
  endResetModel();
}

int XmlAttrTableModel::rowCount(const QModelIndex &) const
{
  if (m_element == 0)
    return 0;

  return std::distance(m_element->attrBegin(), m_element->attrEnd());
}

QVariant XmlAttrTableModel::data(const QModelIndex &index, int role) const
{
  QVariant var;
  if (not index.isValid())
    return var;
  else if (m_element == 0)
    return var;

  if (role == Qt::DisplayRole) {
    uint nattr = std::distance(m_element->attrBegin(), m_element->attrEnd());
    uint row = index.row();
    if (row >= nattr)
      return var;
    XmlElement::attr_iterator itr = m_element->attrBegin();
    std::advance(itr, row);
    if (index.column() == 0)
      var = QString::fromStdString( itr->first );
    else if (index.column() == 1)
      var = QString::fromStdString( itr->second );
  }

  return var;
}

QVariant XmlAttrTableModel::headerData(int section,
                                       Qt::Orientation orientation,
                                       int role) const
{
  QVariant var;
  if (m_element == 0)
    return var;

  if (orientation == Qt::Horizontal and role == Qt::DisplayRole) {
    if (section == 0)
      var = QString("Attribute");
    else if (section == 1)
      var = QString("Value");
  }

  return var;
}
