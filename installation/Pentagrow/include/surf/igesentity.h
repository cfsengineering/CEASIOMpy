
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
 
#ifndef SURF_IGESENTITY_H
#define SURF_IGESENTITY_H

#include "forward.h"
#include "igesdirentry.h"
#include <vector>

/** Base class for entities in IGES files.

  All IGES entity classes inherit from this base. Different geometric objects
  require different types and amounts of numerical data to represent it, and
  this base class provides facilities to dump those blocks of data into the
  IGES file in a standard-compliant manner.

  \ingroup interop
  \sa IgesFile
*/
class IgesEntity
{
public:
  
  enum IgesEntityClass { NoClass = 0,
                         PointClass = 1,
                         LineClass = 2,
                         CurveClass = 4,
                         SurfaceClass = 8,
                         StructureClass = 16,
                         AnyClass = 31};

  /// create entity type etype
  IgesEntity(int ety) : plcpre(-1), plcpost(-1) {
    entry.etype = ety;
  }

  /// destroy
  virtual ~IgesEntity() {}

  /// entity type
  int etype() const {return entry.etype;}

  /// entity class identifier
  int classOf() const {return IgesEntity::classOf(entry.etype);}

  /// access the form field of the directory entry
  void form(int f) {entry.form = f;}

  /// access status field: blank (0/1)
  void blank(int b) {entry.blank = b;}

  /// access status field: subordinate switch (0-3)
  void subswitch(int b) {entry.subswitch = b;}

  /// access status field: use flag (0-6)
  void useflag(int b) {entry.useflag = b;}

  /// access status field: hierachy flag (0-2)
  void hierarchy(int b) {entry.hierarchy = b;}

  /// access transformation matrix field
  void trafoMatrix(int tfi) {entry.trafm = tfi;}

  /// access transformation matrix field
  int trafoMatrix() {return entry.trafm;}

  /// set entity label (use only 8 characters)
  void label(const char *s);

  /// return label, if present
  std::string label() const {return entry.label();}

  /// set entity subscript
  void subscript(int s) {entry.esubscript = s;}

  /// add reference to assoc/note DE
  void addNoteRef(int ide) {addprop1.push_back(ide);}

  /// add reference to property/attribute table DE
  void addPropRef(int ide) {addprop2.push_back(ide);}

  /// parameter data index
  uint pindex() const {return entry.pdata;}

  /// number of notes
  uint nNoteRef() const {return addprop1.size();}

  /// number of property references
  uint nPropRef() const {return addprop2.size();}

  /// access note reference k
  int noteRef(uint k) const {assert(k<nNoteRef()); return addprop1[k];}

  /// access property reference k
  int propRef(uint k) const {assert(k<nPropRef()); return addprop2[k];}

  /// append entity to file
  int append(IgesFile & igfile);

  /// retrieve entity from file
  bool retrieve(const IgesFile & igfile);

  /// this function must be overloaded by entities
  virtual void definition(IgesFile & file) = 0;

  /// parse parameter data from string
  virtual uint parse(const std::string & pds, const Indices & vpos);

  /// generate a new entity from code, return zero if not implemented
  static IgesEntity *create(const IgesDirEntry & e);

  /// convenience function
  template <class EType>
  static bool as(const IgesEntityPtr & ep, EType & t) {
    const EType *et = dynamic_cast<const EType*>(ep.get());
    if (et == 0)
      return false;
    else
      t = *et;
    return true;
  }

  /// identity class of entity number
  static int classOf(int etype) {
    switch (etype) {
    case 100:
    case 102:
    case 104:
      return CurveClass;
    case 108:
      return SurfaceClass;
    case 110:
      return LineClass;
    case 112:
      return CurveClass;
    case 114:
      return SurfaceClass;
    case 116:
      return PointClass;
    case 118:
    case 120:
    case 122:
      return SurfaceClass;
    case 124:
      return StructureClass;
    case 126:
      return CurveClass;
    case 128:
      return SurfaceClass;
    case 134:
      return PointClass;
    case 142:
      return CurveClass;
    case 144:
      return SurfaceClass;
    case 190:
    case 192:
    case 194:
    case 196:
    case 198:
      return SurfaceClass;
    case 308:
    case 314:
    case 402:
    case 406:
    case 408:
      return StructureClass;
    default:
      return NoClass;
    };
    return NoClass;
  }

protected:

  /// convenience conversion function
  static int asInt(const char *s, int k) {
    char *tail;
    int v = strtol(&s[k], &tail, 10);
    assert(tail != &s[k]);
    return v;
  }

  /// convenience conversion function
  static double asDouble(const char *s, int k) {
    char *tail;
    double v = strtod(&s[k], &tail);
    if (tail != &s[k] and tail != 0 and *tail == 'D') { // catch Rhino's format: 3.141D0
      long xp = strtol(tail+1, 0, 10);
      v *= exp(2.30258509299405*xp);
    }
    return v;
  }

protected:

  /// directory entry
  IgesDirEntry entry;

  /// line counts in parameter section
  int plcpre, plcpost;

  /// additional properties (two groups)
  std::vector<int> addprop1, addprop2;
};

///** Group associativity.
  
//  Entity 402, form 7, unordered group without back pointers.

//  */
//class IgesGroupAssoc : public IgesEntity
//{
//public:

//  /// create empty entry
//  IgesGroupAssoc() : IgesEntity(402) { form(7); }

//  /// add pointer to DE of group member
//  void addGroupMember(int ide) {mptr.push_back(ide);}

//  /// assemble definition
//  void definition(IgesFile & igfile);

//private:

//  /// directory entry pointers of the group members
//  std::vector<int> mptr;
//};



#endif
