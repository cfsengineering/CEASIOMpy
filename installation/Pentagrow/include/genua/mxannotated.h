
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
 
#ifndef GENUA_MXANNOTATED_H
#define GENUA_MXANNOTATED_H

#include "xmlelement.h"

/** Base class for annotated mesh objects.
 *
 *  Mesh objects associated with MxMesh all share the possibility to embed
 * hierarchical annotations. These are contained in the MxAnnotated parent
 * class.
 *
 * \ingroup mesh
 * \sa MxMesh
 */
class MxAnnotated
{
public:

  /// empty annotations
  MxAnnotated() : xnote("MxNote") {}

  /// default copy
  MxAnnotated(const MxAnnotated &) = default;

  /// move constructor
  MxAnnotated(MxAnnotated &&a) : xnote(std::move(a.xnote)) {}

  /// meant as a base class
  virtual ~MxAnnotated() {}

  /// default copy asignment
  MxAnnotated & operator= (const MxAnnotated &) = default;

  /// move assignment
  MxAnnotated & operator= (MxAnnotated &&a) {
    if (this != &a)
      xnote = std::move(a.xnote);
    return *this;
  }

  /// set the contents of the complete annotation object
  void note(const XmlElement & xe);

  /// retrieve xml annotation object
  const XmlElement & note() const {return xnote;}

  /// append annotation element
  void annotate(const XmlElement & xe);

  /// iterate over annotations
  XmlElement::const_iterator noteBegin() const {return xnote.begin();}

  /// iterate over annotations
  XmlElement::const_iterator noteEnd() const {return xnote.end();}

  /// assign attribute, i.e. key-value pair in top-level annotation
  void attribute(const std::string &key, const std::string &value) {
    xnote[key] = value;
  }

  /// retrieve attribute; return empty string if not present
  std::string attribute(const std::string &key) const;

protected:

  /// xml annotation
  XmlElement xnote;
};

#endif // MXANNOTATED_H
