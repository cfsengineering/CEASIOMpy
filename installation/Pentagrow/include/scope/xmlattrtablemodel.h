
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
 
#ifndef SCOPE_XMLATTRTABLEMODEL_H
#define SCOPE_XMLATTRTABLEMODEL_H

#include <QAbstractTableModel>
#include <QObject>

class XmlElement;

/** Table model for XML element attributes
 *
 *
 *\sa XmlTreeModel
 */
class XmlAttrTableModel : public QAbstractTableModel
{
public:

  /// construct empty table model
  XmlAttrTableModel(QObject *parent = 0)
    : QAbstractTableModel(parent), m_element(0) {}

  /// set XML element to display
  void display(const XmlElement *element);

  /// number of attributes
  int rowCount(const QModelIndex &) const;

  /// number of columns is always 2
  int columnCount(const QModelIndex &) const {return 2;}

  /// return attribute key / value
  QVariant data(const QModelIndex &index, int role) const;

  /// return header labels
  QVariant headerData(int section, Qt::Orientation orientation, int role) const;

private:

  /// the element whose attributes make up the table
  const XmlElement *m_element;
};

#endif // XMLATTRTABLEMODEL_H
