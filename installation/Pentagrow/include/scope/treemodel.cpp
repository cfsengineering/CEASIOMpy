
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
 
#include "treemodel.h"
#include "treeitem.h"

QModelIndex TreeModel::index(int row, int column,
                             const QModelIndex &parent) const
{
  TreeItem *parentItem(m_root.get());
  void *ptr = parent.internalPointer();
  if (parent.isValid() and ptr != 0)
    parentItem = static_cast<TreeItem*>( ptr );

  if (parentItem != 0 and uint(row) < parentItem->children())
    return createIndex(row, column, (void *) parentItem->childItem(row).get());

  return QModelIndex();
}

QModelIndex TreeModel::parent(const QModelIndex &child) const
{
  if (not child.isValid())
    return QModelIndex();

  void *ptr = child.internalPointer();
  if (child.isValid() and ptr != 0) {
    TreeItem *item = static_cast<TreeItem*>( ptr );
    TreeItem *parentItem = item->parentItem().get();
    if (parentItem == m_root.get())
      return QModelIndex();
    else if (parentItem != 0)
      return createIndex(parentItem->row(), 0, (void *) parentItem);
  }

  return QModelIndex();
}

int TreeModel::rowCount(const QModelIndex &parent) const
{ 
  if (not parent.isValid()) {
    return (m_root != nullptr) ? m_root->children() : 0;
  }

  void *ptr = parent.internalPointer();
  if (ptr != 0) {
    TreeItem *parentItem = static_cast<TreeItem*>( ptr );
    return parentItem->children();
  }

  return 0;
}

int TreeModel::columnCount(const QModelIndex &) const
{
  return 1;
}

QVariant TreeModel::data(const QModelIndex &index, int role) const
{
  QVariant var;

  void *ptr = index.internalPointer();
  if (ptr != 0) {
    TreeItem *item = static_cast<TreeItem*>( ptr );
    return item->data(role);
  }

  return var;
}

bool TreeModel::setData(const QModelIndex &index,
                        const QVariant &value, int role)
{
  void *ptr = index.internalPointer();
  if (ptr != 0) {
    TreeItem *item = static_cast<TreeItem*>( ptr );
    return item->setData(value, role);
  }

  return false;
}

Qt::ItemFlags TreeModel::flags(const QModelIndex &index) const
{
  Qt::ItemFlags flgs = QAbstractItemModel::flags(index);

  if (not index.isValid())
    return flgs;

  void *ptr = index.internalPointer();
  if (ptr != 0) {
    TreeItem *item = static_cast<TreeItem*>( ptr );
    return item->flags();
  }

  return flgs;
}
