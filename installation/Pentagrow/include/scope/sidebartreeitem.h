
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
 
#ifndef SCOPE_SIDEBARTREEITEM_H
#define SCOPE_SIDEBARTREEITEM_H

#include "treeitem.h"
#include "forward.h"
#include <genua/propmacro.h>

class QColor;

/** Item in the sidebar tree.
 *
 *
 */
class SidebarTreeItem : public TreeItem
{
public:

  enum Type { Invalid, MeshRoot, SectionRoot, SectionItem, BocoRoot, BocoItem,
              FieldRoot, FieldLeaf, SolTreeNode };

  /// empty item
  SidebarTreeItem(MxMeshPtr pmx = MxMeshPtr(), int type = Invalid)
    : TreeItem(), m_pmx(pmx), m_type(type),
      m_ifield(NotFound), m_visible(true) {}

  /// recursive construction
  SidebarTreeItem(MxMeshPtr pmx, MxSolutionTreePtr psol);

  /// access type flag
  int type() const {return m_type;}

  /// return present color (only when applicable)
  QColor color() const;

  /// apply color to represented object (section/boco)
  void color(const QColor & clr);

  /// return data for given role
  QVariant data(int role) const;

  /// modify data (rename)
  bool setData(const QVariant &value, int role);

  /// return item flags (indicate whether item is editable etc)
  Qt::ItemFlags flags() const;

  /// construct entire tree, return new root element
  static SidebarTreeItemPtr buildTree(MeshPlotterPtr plotter);

private:

  /// attached mesh
  MxMeshPtr m_pmx;

  /// pointer to node in solution tree
  MxSolutionTreePtr m_psol;

  /// type flag
  int m_type;

  GENUA_PROP(uint, ifield)
  GENUA_PROP(uint, ichild)
  GENUA_PROP(bool, visible)
};

#endif // SIDEBARTREEITEM_H
