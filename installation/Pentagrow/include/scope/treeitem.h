
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
 
#ifndef SCOPE_TREEITEM_H
#define SCOPE_TREEITEM_H

#include "forward.h"
#include <QVariant>
#include <QObject>
#include <vector>
#include <cassert>

/** Base class for items used in a tree view.
 *
 */
class TreeItem : public QObject
{
public:

  /// construct undefined item
  TreeItem() : m_row(0), m_col(0) {}

  /// construct defined item
  TreeItem(TreeItemPtr p, int row = 0, int col = 0)
    : m_parent(p), m_row(row), m_col(col) {}

  /// deletes all child items
  virtual ~TreeItem() {}

  /// access row index
  int row() const {return m_row;}

  /// access row index
  int col() const {return m_col;}

  /// access parent item
  TreeItemPtr parentItem() const {return m_parent;}

  /// cast parent to specified type
  template <class ItemType>
  boost::shared_ptr<ItemType> parentAs() const {
    return boost::dynamic_pointer_cast<ItemType>( m_parent );
  }

  /// count child items
  uint children() const {return m_siblings.size();}

  /// access child at index k
  TreeItemPtr childItem(uint k) const {
    assert(k < m_siblings.size());
    return m_siblings[k];
  }

  /// cast child to specified type
  template <class ItemType>
  boost::shared_ptr<ItemType> childAs(uint k) const {
    return boost::dynamic_pointer_cast<ItemType>( childItem(k) );
  }

  /// append child item
  uint appendChild(TreeItemPtr kid) {
    kid->m_parent = TreeItemPtr(this, null_deleter());
    m_siblings.push_back(kid);
    return m_siblings.size() + 1;
  }

  /// return data for given role
  virtual QVariant data(int role) const;

  /// set data for given role
  virtual bool setData(const QVariant &value, int role);

  /// return item flags (indicate whether item is editable etc)
  virtual Qt::ItemFlags flags() const;

protected:

  /// delete child items
  virtual void destroy();

protected:

  /// child items
  std::vector<TreeItemPtr> m_siblings;

  /// parent item
  TreeItemPtr m_parent;

  /// row and column indices
  int m_row, m_col;
};

#endif // TREEITEM_H
