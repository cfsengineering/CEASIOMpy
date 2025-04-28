
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
 
#ifndef SCOPE_TREEMODEL_H
#define SCOPE_TREEMODEL_H

#include "forward.h"
#include <QAbstractItemModel>

class TreeItem;

/** Base class for tree models to be used with tree view widgets.
 *
 *
 *\sa TreeItem
 */
class TreeModel : public QAbstractItemModel
{
public:

  /// initialize empty model
  TreeModel(QObject *parent=0) : QAbstractItemModel(parent), m_root(0) {}

  /// destroy tree model
  virtual ~TreeModel() {}

  /// number of rows for child of parent index
  int rowCount(const QModelIndex &parent = QModelIndex()) const;

  /// one column for the time being; may add more later
  int columnCount(const QModelIndex &parent = QModelIndex()) const;

  /// return text representation to display in tree view
  QVariant data(const QModelIndex &index, int role) const;

  /// allow editing for items which support name changes
  bool setData(const QModelIndex &index,
               const QVariant &value, int role = Qt::EditRole);

  /// tell the view that some items are editable
  Qt::ItemFlags flags(const QModelIndex &index) const;

  /// create child item index at row/column
  QModelIndex index(int row, int column, const QModelIndex &parent) const;

  /// access parent index
  QModelIndex parent(const QModelIndex &child) const;

protected:

  /// root item of the tree
  TreeItemPtr m_root;
};

#endif // TREEMODEL_H
