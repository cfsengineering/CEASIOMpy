
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
 
#ifndef SCOPE_XMLDISPLAY_H
#define SCOPE_XMLDISPLAY_H

#include "ui_xmldisplay.h"

class XmlTreeModel;
class XmlAttrTableModel;
class XmlElement;

/** A widget for displaying XML content.
 *
 * This widget combines a tree view showing the hierarchical structure of the
 * XML object, with a table for the attribute and a test browser for string
 * payloads.
 *
 *\sa XmlTreeModel
 */
class XmlDisplay : public QWidget, private Ui::XmlDisplay
{
  Q_OBJECT
  
public:

  /// empty display w/o content
  explicit XmlDisplay(QWidget *parent = 0);
  
  /// set XmlElement to display (pointed-to object must survive display instance!)
  void display(const XmlElement *element);

public slots:

  /// detach whenever dialog is hidden
  void detach();

private slots:

  /// adapt attribute and text display to selected element
  void elementDetails(const QModelIndex &index);

protected:

  /// runtime changes
  void changeEvent(QEvent *e);

private:

  /// adapter for tree view
  XmlTreeModel *m_treeModel;

  /// adapter for attribute table
  XmlAttrTableModel *m_tableModel;
};

#endif // XMLDISPLAY_H
