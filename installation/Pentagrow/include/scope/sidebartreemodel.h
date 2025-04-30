
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
 
#ifndef SCOPE_SIDEBARTREEMODEL_H
#define SCOPE_SIDEBARTREEMODEL_H

#include "treemodel.h"
#include "forward.h"

/** Item model for the sidebar tree.
 *
 * \sa SideBarTreeItem, TreeModel
 */
class SidebarTreeModel : public TreeModel
{
Q_OBJECT

public:

  /// initialize with parent object
  SidebarTreeModel(QObject *parent = 0) : TreeModel(parent) {}

  /// rebuild tree from mesh
  void construct(MeshPlotterPtr plotter);

public slots:

  /// mark section visibility
  void markSectionVisible(int isec, bool flag);

  /// mark boco visibility
  void markBocoVisible(int iboco, bool flag);

private:

  /// mark section visibility
  void markSectionVisible(TreeItem *item, int isec, bool flag);

  /// mark boco visibility
  void markBocoVisible(TreeItem *item, int iboco, bool flag);
};

#endif // SIDEBARTREEMODEL_H
