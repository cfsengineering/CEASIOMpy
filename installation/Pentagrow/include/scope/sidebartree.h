
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
 
#ifndef SCOPE_SIDEBARTREE_H
#define SCOPE_SIDEBARTREE_H

#include "forward.h"
#include <QTreeView>
#include <QModelIndex>

class QMenu;
class QAction;

/** Tree view for mesh structure.
 *
 *  This is the tree-view widget for the left-hand pane which contains the
 *  hierarchical display of the mesh structure. This view class handles
 *  mostly context menu user interaction.
 *
 * \sa SidebarTreeModel, SidebarTreeItem
 */
class SidebarTree : public QTreeView
{
  Q_OBJECT

public:

  /// create tree view
  SidebarTree(QWidget *parent);

signals:

  /// request to show/hide an entire section
  void showSection(int isec, bool flag = true);

  /// request to show/hide an element group
  void showBoco(int iboco, bool flag = true);

  /// request to edit a section
  void editSection(int isec);

  /// request to edit an element group
  void editBoco(int iboco);

  /// request editing of field properties
  void editField(int ifield);

  /// show contour plot for field
  void plotField(int ifield);

  /// emitted when section/boco colors changed
  void colorsChanged(int isection=-1);

private slots:

  /// dispatch to signal
  void contextShow();

  /// dispatch to signal
  void contextShow(SidebarTreeItem *item);

  /// dispatch to signal
  void contextEdit();

  /// open color editor
  void contextColor();

  /// dispatch click on index to suitable signal
  void indexClicked(const QModelIndex &index);

protected:

  /// return item where context menu clicked
  SidebarTreeItem *contextItem() const;

  /// open specialized context menu
  void openContextMenu(const QPoint &pos, const QModelIndex &index);

  /// open specialized context menu
  void openContextMenu(const QPoint &pos);

  /// handle context menu event, emit signal
  void contextMenuEvent(QContextMenuEvent *event);

  /// process context menu action


private:

  /// model index where context menu was requested
  QModelIndex m_contextIndex;

  /// context menu action : show/hide section or boco
  QAction *m_showAct;

  /// context menu action : open edit dialog
  QAction *m_editAct;

  /// context menu action : open color change dialog
  QAction *m_colorAct;

  /// context menu
  QMenu *m_contextMenu;
};

#endif // SIDEBARTREE_H
