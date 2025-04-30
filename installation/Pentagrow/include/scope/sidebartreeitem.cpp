
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

#include "sidebartreeitem.h"
#include "meshplotter.h"
#include "util.h"
#include <genua/mxmesh.h>
#include <genua/mxsolutiontree.h>

#include <QFont>
#include <QBrush>
#include <QColor>
#include <QDebug>

SidebarTreeItem::SidebarTreeItem(MxMeshPtr pmx, MxSolutionTreePtr psol)
  : TreeItem(), m_pmx(pmx), m_psol(psol),
    m_type(SolTreeNode), m_ifield(NotFound), m_ichild(NotFound), m_visible(true)
{
  const int n = m_psol->children();
  for (int i=0; i<n; ++i) {
    SidebarTreeItemPtr item;
    item = boost::make_shared<SidebarTreeItem>(m_pmx, m_psol->child(i));
    item->ichild(i);
    appendChild( item );
  }

  if (n == 0) {
    const Indices & fields( m_psol->fields() );
    const int m = fields.size();
    for (int i=0; i<m; ++i) {
      SidebarTreeItemPtr item;
      item = boost::make_shared<SidebarTreeItem>(m_pmx, FieldLeaf);
      item->m_ifield = fields[i];
      assert(item->m_ifield < m_pmx->nfields());
      appendChild(item);
    }
  }
}

SidebarTreeItemPtr SidebarTreeItem::buildTree(MeshPlotterPtr plotter)
{
  if (not plotter)
    return 0;

  MxMeshPtr pmx = plotter->pmesh();
  if (not pmx)
    return 0;

  SidebarTreeItemPtr root, sections, bocos, fields;
  root = boost::make_shared<SidebarTreeItem>(pmx, MeshRoot);
  sections = boost::make_shared<SidebarTreeItem>(pmx, SectionRoot);
  bocos = boost::make_shared<SidebarTreeItem>(pmx, BocoRoot);
  fields = boost::make_shared<SidebarTreeItem>(pmx, FieldRoot);

  root->appendChild( sections );
  root->appendChild( bocos );

  for (uint i=0; i<pmx->nsections(); ++i) {
    SidebarTreeItemPtr item;
    item = boost::make_shared<SidebarTreeItem>(pmx, SectionItem);
    item->m_row = i;
    item->visible( plotter->section(i).visible() );
    sections->appendChild(item);
  }

  for (uint i=0; i<pmx->nbocos(); ++i) {
    SidebarTreeItemPtr item;
    item = boost::make_shared<SidebarTreeItem>(pmx, BocoItem);
    item->m_row = i;
    uint isec = pmx->mappedSection( i );
    if (isec != NotFound)
      item->visible( plotter->section(isec).visible() );
    bocos->appendChild(item);
  }

  MxSolutionTreePtr psol = pmx->solutionTree();
  if (psol) {
    root->appendChild( boost::make_shared<SidebarTreeItem>(pmx, psol) );
    qDebug("Added solution tree: %s", psol->name().c_str());
  } else {
    qDebug("No solution tree in this mesh.");
  }

  // add fields node last - may be very long
  root->appendChild( fields );
  for (uint i=0; i<pmx->nfields(); ++i) {
    SidebarTreeItemPtr item;
    item = boost::make_shared<SidebarTreeItem>(pmx, FieldLeaf);
    item->m_row = item->m_ifield = i;
    fields->appendChild(item);
  }

  return root;
}

QColor SidebarTreeItem::color() const
{
  Color c(0.5f, 0.5f, 0.5f);
  if (m_pmx) {

    if (m_type == SectionItem) {
      c = m_pmx->section( m_row ).displayColor();
    } else if (m_type == BocoItem) {
      c = m_pmx->boco( m_row ).displayColor();
    }
  }
  return QColor( c.red(), c.green(), c.blue() );
}

void SidebarTreeItem::color(const QColor &clr)
{
  if (not m_pmx)
    return;

  Color c( (float) clr.redF(), (float) clr.greenF(), (float) clr.blueF() );
  if (m_type == SectionItem) {
    m_pmx->section( m_row ).displayColor(c);
  } else if (m_type == BocoItem) {
    m_pmx->boco( m_row ).displayColor(c);
  }
}

QVariant SidebarTreeItem::data(int role) const
{
  QVariant var;

  if (role == Qt::DisplayRole) {

    switch (m_type) {

    case Invalid:
      return var;

    case SectionRoot:
      return QVariant( tr("Mesh Sections") );

    case SectionItem:
      return QVariant( QString::fromStdString( m_pmx->section(m_row).name() ) );

    case BocoRoot:
      return QVariant( tr("Element Groups") );

    case BocoItem:
      return QVariant( QString::fromStdString( m_pmx->boco(m_row).name() ) );

    case FieldRoot:
      return QVariant( tr("Data Fields") );

    case FieldLeaf:
      assert(m_ifield != NotFound);
      return QVariant( QString::fromStdString( m_pmx->field(m_ifield).name() ) );

    case SolTreeNode:
      assert(m_psol);
      return QVariant( QString::fromStdString(m_psol->name()) );

    }

  } else if (role == Qt::ToolTipRole) {

    switch (m_type) {

    case Invalid:
      return var;

    case SectionRoot:
      return QVariant( tr("%1 elements, %2 nodes")
                       .arg(m_pmx->nelements())
                       .arg(m_pmx->nnodes()) );

    case SectionItem:
      return QVariant( tr("%1 elements")
                       .arg(m_pmx->section(m_row).nelements()));

    case BocoRoot:
      return var;

    case BocoItem:
      return QVariant( tr("%1 elements")
                       .arg(m_pmx->boco(m_row).nelements()) );

    case FieldRoot:
      return QVariant( tr("%1 fields").arg(m_pmx->nfields()) );

    case FieldLeaf:
      assert(m_ifield != NotFound);
      return QVariant( tr("Index %1").arg(m_ifield) );

    case SolTreeNode:
      assert(m_psol);
      return QVariant( tr("Node %1, fields: %2, children: %3")
                       .arg(m_ichild+1)
                       .arg(m_psol->fields().size())
                       .arg(m_psol->children()));

    }

  } else if (role == Qt::FontRole) {

    QFont font;
    switch (m_type) {

    case SectionRoot:
    case BocoRoot:
    case FieldRoot:
    case SolTreeNode:
      font.setWeight( QFont::Bold );
      return QVariant(font);

    default:
      return var;

    }

  } else if (role == Qt::ForegroundRole) {

    if (not m_visible) {
      return QBrush( QColor(153, 153, 153) );
    }

  }

  return var;
}

bool SidebarTreeItem::setData(const QVariant &value, int role)
{
  if (role == Qt::EditRole) {

    std::string s = str(value.toString());
    switch (m_type) {

    case SectionItem:
      m_pmx->section(m_row).rename(s);
      return true;

    case BocoItem:
      m_pmx->boco(m_row).rename(s);
      return true;

    case FieldLeaf:
      assert(m_pmx);
      assert( m_ifield < m_pmx->nfields() );
      m_pmx->field(m_ifield).rename(s);
      return true;

    case SolTreeNode:
      assert(m_psol);
      m_psol->rename(s);
      return true;

    default:
      return false;
    }

  }

  return false;
}

Qt::ItemFlags SidebarTreeItem::flags() const
{
  Qt::ItemFlags flags = TreeItem::flags();

  switch (m_type) {

  case SectionItem:
  case BocoItem:
  case FieldLeaf:
  case SolTreeNode:
    flags |= Qt::ItemIsEditable;
    break;

  default:
    break;
  }

  return flags;
}

