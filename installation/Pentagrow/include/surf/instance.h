
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
 

#ifndef SURF_INSTANCE_H
#define SURF_INSTANCE_H

#include <genua/defines.h>
#include <genua/transformation.h>
#include <genua/xmlelement.h>
#include <boost/shared_ptr.hpp>
#include <string>

class Instance;
typedef boost::shared_ptr<Instance> InstancePtr;
typedef std::vector<InstancePtr> InstanceArray;

class IgesFile;
struct IgesDirEntry;

/** Base class for geometric object instancing.

  An Instance object allows to use one or a set of complex geometric objects
  (such as surfaces) multiple times with different names and transformations.
  This particular class is a base class which does not contain any object but
  provides top-level functionality only.

  \ingroup geometry
  \sa TrafoTpl
*/
class Instance
{
public:

  /// undefined instance
  Instance() : m_iid(NotFound) {}

  /// base class
  virtual ~Instance() {}

  /// access instance name
  const std::string & name() const {return m_name;}

  /// access instance name
  void rename(const std::string & s) {m_name = s;}

  /// access id
  uint id() const {return m_iid;}

  /// access id
  void id(uint i) {m_iid = i;}

  /// define sort order
  bool operator< (const Instance & a) const {return (id() < a.id());}

  /// reset transformation to identity
  void identity() { m_placement.identity(); }

  /// access transformation components
  const Vct3 & scaling() const {return m_placement.scaling();}

  /// access transformation components
  const Vct3 & rotation() const {return m_placement.rotation();}

  /// access transformation components
  const Vct3 & translation() const {return m_placement.translation();}

  /// set scaling factors
  template <typename FType>
  void scale(FType sx, FType sy, FType sz) { m_placement.scale(sx, sy, sz); }

  /// set rotation angles
  template <typename FType>
  void rotate(FType rx, FType ry, FType rz) { m_placement.rotate(rx, ry, rz); }

  /// set translation vector
  template <typename FType>
  void translate(FType tx, FType ty, FType tz) {
    m_placement.translate(tx, ty, tz);
  }

  /// set transformation explicitely
  void transform(const Trafo3d & tf) {m_placement = tf;}

  /// access current transformation
  const Trafo3d & currentTransform() const {return m_placement;}

  /// xml element for instance data only
  virtual XmlElement toXml(bool share) const;

  /// retrieve instance data from xml element
  virtual void fromXml(const XmlElement & xe);

protected:

  /// transformation of the contained object
  Trafo3d m_placement;

  /// name of this instance of the contained object
  std::string m_name;

  /// unique integer id used for sorting
  uint m_iid;
};

/// define sorting order for ref-counted pointers
inline bool operator< (const InstancePtr & a, const InstancePtr & b)
{
  return (a->id() < b->id());
}

/** Instance containing indices of geometric objects.

  An Instance which contains geometric objects referenced by indices, which is
  the design pattern used in IGES files. This particular class just stores the
  IGES directory entry indices for the referenced objects just like IGES
  entity 308. IndexInstance does not have knowledge about the referenced objects.

  In a way, IndexInstance can be misused to gather a number of entities in an
  IGES file, tag them with a name and apply a transformation. Should the indices
  refer to another container (not the IGES file), they must first be mapped to
  IGES directory entry indices before exporting toIges().

  \sa Instance, IgesFile, IgesSingularSubfigure
  */
class IndexInstance : public Instance
{
public:

  /// empty instance
  IndexInstance() : Instance() {}

  /// base class
  virtual ~IndexInstance() {}

  /// number of object indices
  uint size() const {return m_objects.size();}

  /// remove all object indices
  void clear() {m_objects.clear();}

  /// resize object index storage and invalidate
  void resize(uint n) {
    m_objects.resize(n);
    std::fill(m_objects.begin(), m_objects.end(), NotFound);
  }

  /// swap out object indices
  void swap(Indices & idx) {m_objects.swap(idx);}

  /// append object index
  uint append(uint k) {
    m_objects.push_back(k);
    return m_objects.size()-1;
  }

  /// access object index k
  const uint & operator[] (uint k) const {return m_objects[k];}

  /// access object index k
  uint & operator[] (uint k) {return m_objects[k];}

  /// write as a instance of a subfigure entity (entity 308)
  uint toIges(IgesFile & file) const;

  /// retrieve entity indices from IGES file entity 308
  bool fromIges(const IgesFile & file, const IgesDirEntry & entry);

  /// xml element for instance data only
  virtual XmlElement toXml(bool share) const;

  /// retrieve instance data from xml element
  virtual void fromXml(const XmlElement & xe);

protected:

  /// object indices
  Indices m_objects;
};

#endif // INSTANCE_H
