
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
 
#include "xmldisplay.h"
#include "xmltreemodel.h"
#include "xmltreeitem.h"
#include "xmlattrtablemodel.h"
#include <genua/xmlelement.h>
#include <genua/dvector.h>
#include <sstream>

using namespace std;

XmlDisplay::XmlDisplay(QWidget *parent) : QWidget(parent)
{
  setupUi(this);

  m_treeModel = new XmlTreeModel(this);
  m_tableModel = new XmlAttrTableModel(this);

  m_treeView->setModel( m_treeModel );
  m_tableView->setModel( m_tableModel );

  connect( m_treeView, SIGNAL(clicked(QModelIndex)),
           this, SLOT(elementDetails(QModelIndex)) );
}

void XmlDisplay::display(const XmlElement *element)
{
  m_tableModel->display(element);
  m_treeModel->build(element);
}

void XmlDisplay::detach()
{
  display(0);
}

void XmlDisplay::elementDetails(const QModelIndex &index)
{
  if (not index.isValid())
    return;

  XmlTreeItem *item(0);
  const XmlElement *element(0);
  item = static_cast<XmlTreeItem*>( index.internalPointer() );
  if (item == 0)
    return;
  element = item->element();
  if (element == 0)
    return;

  m_tableModel->display(element);

  const std::string & txt( element->text() );
  if (not txt.empty()) {
    m_textBrowser->setText( QString::fromStdString(txt) );
  } else {
    const uint bufsize(4096);
    const uint nbytes = std::min( bufsize, (uint) element->blobBytes() );
    stringstream ss;
    if (element->blobType() == TypeCode::Int32) {
      const int nv = nbytes/4;
      DVector<int> values(nv);
      element->fetch(nv, values.pointer());
      for (int i=0; i<nv; ++i)
        ss << values[i] << ' ';
    } else if (element->blobType() == TypeCode::Float64) {
      const int nv = nbytes/8;
      DVector<double> values(nv);
      element->fetch(nv, values.pointer());
      for (int i=0; i<nv; ++i)
        ss << values[i] << ' ';
    }
    m_textBrowser->setText( QString::fromStdString(ss.str()) );
  }
}

void XmlDisplay::changeEvent(QEvent *e)
{
  QWidget::changeEvent(e);
  switch (e->type()) {
  case QEvent::LanguageChange:
    retranslateUi(this);
    break;
  default:
    break;
  }
}
