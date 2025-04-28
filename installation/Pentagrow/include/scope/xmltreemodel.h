
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
 
#ifndef SCOPE_XMLTREEMODEL_H
#define SCOPE_XMLTREEMODEL_H

#include "treemodel.h"

class XmlElement;

/** Item model for XML trees.
 *
 */
class XmlTreeModel : public TreeModel
{
public:

  /// construct empty model
  XmlTreeModel(QObject *parent = 0) : TreeModel(parent) {}

  /// attach to XML element
  void build(const XmlElement *rootElement);
};

#endif // XMLTREEMODEL_H
