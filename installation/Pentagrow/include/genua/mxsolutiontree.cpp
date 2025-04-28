
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
 
#include "mxsolutiontree.h"
#include "strutils.h"

MxSolutionTreePtr MxSolutionTree::findChild(const std::string &s) const
{
  for (uint i=0; i<m_siblings.size(); ++i)
    if (m_siblings[i]->name() == s)
      return m_siblings[i];
  return MxSolutionTreePtr();
}

void MxSolutionTree::appendFields(const Indices &idx)
{
  m_fields.insert( m_fields.end(), idx.begin(), idx.end() );
}

void MxSolutionTree::eraseField(uint k)
{
  Indices::iterator pos;
  pos = std::find(m_fields.begin(), m_fields.end(), k);
  if (pos != m_fields.end())
    m_fields.erase(pos);
  for (uint j=0; j<m_fields.size(); ++j) {
    uint & fix( m_fields[j] );
    if (fix > k)
      --fix;
  }
  for (uint j=0; j<m_siblings.size(); ++j)
    m_siblings[j]->eraseField(k);
}

bool MxSolutionTree::isTopBranch()
{
  const int n = children();
  if (n < 1)
    return false;

  for (int i=0; i<n; ++i)
    if ( child(i)->children() > 0 )
      return false;

  return true;
}

bool MxSolutionTree::containsField(uint k) const
{
  return std::find(m_fields.begin(), m_fields.end(), k) != m_fields.end();
}

MxSolutionTreePtr MxSolutionTree::findFirstWith(uint k) const
{
  for (const MxSolutionTreePtr &itr : m_siblings) {
    if (itr->containsField(k))
      return itr;
    if (itr->children() > 0) {
      MxSolutionTreePtr ptr = itr->findFirstWith(k);
      if (ptr != nullptr)
        return ptr;
    }
  }
  return MxSolutionTreePtr();
}

XmlElement MxSolutionTree::toXml(bool share) const
{
  XmlElement xe("MxSolutionTree");
  xe["name"] = m_name;
  xe["children"] = str(m_siblings.size());

  if (not xnote.name().empty())
    xe.append(xnote);

  for (uint i=0; i<m_siblings.size(); ++i)
    xe.append( m_siblings[i]->toXml(share) );

  if (not m_fields.empty()) {
    XmlElement xf("Fields");
    xf["count"] = str(m_fields.size());
    xf.asBinary(m_fields.size(), &m_fields[0], share);
    xe.append(std::move(xf));
  }

  return xe;
}

void MxSolutionTree::fromXml(const XmlElement &xe)
{
  m_siblings.clear();
  m_fields.clear();
  m_name = xe.attribute("name");

  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "MxSolutionTree") {
      MxSolutionTreePtr childNode(new MxSolutionTree);
      childNode->fromXml(*itr);
      m_siblings.push_back( childNode );
    } else if (itr->name() == "Fields") {
      m_fields.resize( Int(itr->attribute("count")) );
      itr->fetch( m_fields.size(), &m_fields[0] );
    } else if (itr->name() == "MxMeshNote" or itr->name() == "MxNote") {
      note(*itr);
    }
  }
}

MxSolutionTreePtr MxSolutionTree::append(const std::string &s)
{
  MxSolutionTreePtr p = MxSolutionTree::create(s);
  this->append(p);
  return p;
}
