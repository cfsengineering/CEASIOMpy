
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
 
#ifndef GENUA_MXSOLUTIONTREE_H
#define GENUA_MXSOLUTIONTREE_H

#include "mxannotated.h"
#include "xmlelement.h"
#include "forward.h"

/** Tree-based structure for multiple solutions in single MxMesh file.
 *
 * \ingroup mesh
 * \sa MxMesh, MxMeshField
 */
class MxSolutionTree : public MxAnnotated
{
public:

  /// create empty tree
  MxSolutionTree() {}

  /// create named tree
  explicit MxSolutionTree(const std::string &s) : m_name(s) {}

  /// access node name
  const std::string & name() const {return m_name;}

  /// change node name
  void rename(const std::string &s) {m_name = s;}

  /// number of children in node
  uint children() const {return m_siblings.size();}

  /// access child node i
  MxSolutionTreePtr child(uint i) const {return m_siblings[i];}

  /// find child node by name
  MxSolutionTreePtr findChild(const std::string &s) const;

  /// append child node
  uint append(MxSolutionTreePtr node) {
    m_siblings.push_back(node);
    return m_siblings.size() - 1;
  }

  /// create and append child node
  MxSolutionTreePtr append(const std::string &s);

  /// append field index
  uint appendField(uint ifield) {
    m_fields.push_back(ifield);
    return m_fields.size() - 1;
  }

  /// append field index
  void appendFields(const Indices &idx);

  /// access indices of fields associated with this node
  const Indices & fields() const {return m_fields;}

  /// access indices of fields associated with this node
  void fields(const Indices &f) {m_fields = f;}

  /// erase field index from this and all siblings
  void eraseField(uint k);

  /// check whether node contains field k
  bool containsField(uint k) const;

  /// a tree node is a top branch if all child nodes are leaves
  bool isTopBranch();

  /// find first tree node containing field k
  MxSolutionTreePtr findFirstWith(uint k) const;

  /// create XML representation
  XmlElement toXml(bool share = false) const;

  /// recover tree from XML representation
  void fromXml(const XmlElement &xe);

#ifdef HAVE_HDF5

  /// generate a HDF5 representation
  void writeHdf5(Hdf5Group &parent);

#endif

  /// create subtree
  static MxSolutionTreePtr create(const std::string &s) {
    return boost::make_shared<MxSolutionTree>(s);
  }

private:

  /// node name
  std::string m_name;

  /// child nodes (any number)
  MxSolutionTreeArray m_siblings;

  /// indices of fields associated with this node
  Indices m_fields;
};


#endif // MXSOLUTIONTREE_H
