
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

#include "sidebartree.h"
#include "sidebartreeitem.h"
#include <QMenu>
#include <QAction>
#include <QContextMenuEvent>
#include <QPoint>
#include <QColorDialog>

SidebarTree::SidebarTree(QWidget *parent) : QTreeView(parent)
{
  // context menu actions
  m_contextMenu = new QMenu;
  m_showAct = m_contextMenu->addAction(tr("Show/hide"));
  m_showAct->setShortcut( Qt::Key_F9 );
  connect( m_showAct, SIGNAL(triggered()), this, SLOT(contextShow()) );

  m_editAct = m_contextMenu->addAction(tr("Edit..."),
                                       this, SLOT(contextEdit()));
  m_colorAct = m_contextMenu->addAction(tr("Color..."),
                                        this, SLOT(contextColor()));

  connect( this, SIGNAL(clicked(QModelIndex)),
           this, SLOT(indexClicked(QModelIndex)) );

  setSelectionMode(QAbstractItemView::ExtendedSelection);
}

void SidebarTree::contextShow()
{
  QModelIndexList selection = selectedIndexes();
  if (selection.size() > 1) {
    for (const QModelIndex &index : selection) {
      if (not index.isValid())
        continue;
      void *ptr = index.internalPointer();
      if (ptr == 0)
        continue;
      SidebarTreeItem *item = static_cast<SidebarTreeItem*>( ptr );
      contextShow(item);
    }
  } else {
    contextShow(contextItem());
  }
}

void SidebarTree::contextShow(SidebarTreeItem *item)
{
  if (item == 0)
    return;

  bool flag = (not item->visible());
  if (item->type() == SidebarTreeItem::SectionItem) {
    emit showSection( item->row(), flag );
    item->visible( flag );
  } else if (item->type() == SidebarTreeItem::BocoItem) {
    emit showBoco( item->row(), flag );
    item->visible( flag );
  }
}

void SidebarTree::contextEdit()
{
  SidebarTreeItem *item = contextItem();
  if (item == 0)
    return;

  if (item->type() == SidebarTreeItem::SectionRoot)
    emit editSection( -1 );
  else if (item->type() == SidebarTreeItem::SectionItem)
    emit editSection( item->row() );
  else if (item->type() == SidebarTreeItem::BocoRoot)
    emit editBoco( -1 );
  else if (item->type() == SidebarTreeItem::BocoItem)
    emit editBoco( item->row() );
  else if (item->type() == SidebarTreeItem::FieldRoot)
    emit editField( -1 );
  else if (item->type() == SidebarTreeItem::FieldLeaf)
    emit editField( item->row() );
}

void SidebarTree::contextColor()
{
  QModelIndexList selection = selectedIndexes();
  if (selection.size() < 2) {

    SidebarTreeItem *item = contextItem();
    if (item == 0)
      return;

    if (item->type() == SidebarTreeItem::SectionItem or
        item->type() == SidebarTreeItem::BocoItem)
    {
      QColor itemColor( item->color() );
      itemColor = QColorDialog::getColor( itemColor, this );
      item->color(itemColor);
      if (item->type() == SidebarTreeItem::SectionItem)
        emit colorsChanged(item->row());
      else
        emit colorsChanged();
    }

    return;
  }

  // multiple selection
  QColor itemColor = QColorDialog::getColor( QColor(), this );
  for (const QModelIndex &index : selection) {
    if (not index.isValid())
      continue;
    void *ptr = index.internalPointer();
    if (ptr == 0)
      continue;
    SidebarTreeItem *item = static_cast<SidebarTreeItem*>( ptr );
    if (item->type() == SidebarTreeItem::SectionItem or
        item->type() == SidebarTreeItem::BocoItem)
    {
      item->color(itemColor);
    }
  }
  emit colorsChanged();
}

void SidebarTree::indexClicked(const QModelIndex &index)
{
  if (not index.isValid())
    return;

  void *ptr = index.internalPointer();
  if (ptr == 0)
    return;

  SidebarTreeItem *item = static_cast<SidebarTreeItem*>( ptr );
  if (item->type() == SidebarTreeItem::FieldLeaf) {
    uint fix = item->ifield();
    if (fix != NotFound)
      emit plotField(fix);
  }
}

SidebarTreeItem *SidebarTree::contextItem() const
{
  if (not m_contextIndex.isValid())
    return 0;

  void *ptr = m_contextIndex.internalPointer();
  if (ptr == 0)
    return 0;

  SidebarTreeItem *item = static_cast<SidebarTreeItem*>( ptr );
  return item;
}

void SidebarTree::contextMenuEvent(QContextMenuEvent *event)
{
  const QPoint & p( event->pos() );
  QModelIndexList selection = selectedIndexes();
  if (selection.size() > 1) {
    openContextMenu(p);
    event->accept();
    return;
  }

  const QModelIndex & index( indexAt(p) );
  if (index.isValid()) {
    openContextMenu(p, index);
    event->accept();
    return;
  }
  QTreeView::contextMenuEvent(event);
}

void SidebarTree::openContextMenu(const QPoint &pos, const QModelIndex &index)
{
  if (not index.isValid())
    return;

  void *ptr = index.internalPointer();
  if (ptr == 0)
    return;

  m_contextIndex = index;
  SidebarTreeItem *item = static_cast<SidebarTreeItem*>( ptr );

  m_showAct->setVisible(false);
  m_colorAct->setVisible(false);
  m_editAct->setVisible(false);

  switch (item->type()) {

  case SidebarTreeItem::Invalid:
    return;

  case SidebarTreeItem::SectionItem:
  case SidebarTreeItem::BocoItem:
    m_showAct->setText( item->visible() ? tr("Hide item") : tr("Show item") );
    m_showAct->setVisible(true);
    m_colorAct->setVisible(true);
  case SidebarTreeItem::SectionRoot:
  case SidebarTreeItem::BocoRoot:
    m_editAct->setVisible(true);
    break;

  case SidebarTreeItem::FieldLeaf:
    m_editAct->setVisible(true);
    break;

  default:
    return;
  }

  m_contextMenu->popup( mapToGlobal(pos) );
}

void SidebarTree::openContextMenu(const QPoint &pos)
{
  // called when multiple items are selected
  m_showAct->setText( tr("Toggle visible") );
  m_showAct->setVisible(true);
  m_colorAct->setVisible(true);
  m_editAct->setVisible(false);

  m_contextMenu->popup( mapToGlobal(pos) );
}


