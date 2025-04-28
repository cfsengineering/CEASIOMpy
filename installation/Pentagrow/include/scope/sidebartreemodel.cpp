
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
 
#include "sidebartreemodel.h"
#include "sidebartreeitem.h"

void SidebarTreeModel::construct(MeshPlotterPtr plotter)
{
  beginResetModel();
  m_root = SidebarTreeItem::buildTree(plotter);
  endResetModel();
}

void SidebarTreeModel::markSectionVisible(int isec, bool flag)
{
  if (m_root != nullptr)
    markSectionVisible(m_root.get(), isec, flag);
}

void SidebarTreeModel::markBocoVisible(int iboco, bool flag)
{
  if (m_root != nullptr)
    markBocoVisible(m_root.get(), iboco, flag);
}

void SidebarTreeModel::markSectionVisible(TreeItem *tritem, int isec, bool flag)
{
  SidebarTreeItem *item = dynamic_cast<SidebarTreeItem*>( tritem );
  if (item != 0) {
    if (item->type() == SidebarTreeItem::SectionItem) {
      if (item->row() == isec)
        item->visible(flag);
    } else if (item->children() > 0) {
      for (uint i=0; i<item->children(); ++i)
        markSectionVisible((SidebarTreeItem*) item->childItem(i).get(), isec, flag);
    }
  }
}

void SidebarTreeModel::markBocoVisible(TreeItem *tritem, int isec, bool flag)
{
  SidebarTreeItem *item = dynamic_cast<SidebarTreeItem*>( tritem );
  if (item != 0) {
    if (item->type() == SidebarTreeItem::BocoItem) {
      if (item->row() == isec)
        item->visible(flag);
    } else if (item->children() > 0) {
      for (uint i=0; i<item->children(); ++i)
        markBocoVisible((SidebarTreeItem*) item->childItem(i).get(), isec, flag);
    }
  }
}
