
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
 
#ifndef SURF_MATERIALPROPERTY_H
#define SURF_MATERIALPROPERTY_H

#include "forward.h"
#include <genua/propmacro.h>

/** Base class for material property definitions.
 *
 * \ingroup structures
 * \sa IsotropicMaterial
 */
class MaterialProperty
{
public:

  /// indicates that a value is not set
  static const Real NoValue;

  /// predefined materials
  enum BuiltinMatID { AA2024T3Sheet,      ///< 2024 T3 Sheet t > 0.01 in
                      AA2024T3Plate76,    ///< 2024 T3 Plate t < 3 in
                      AA2024T8Sheet13,    ///< 2024 T8 Sheet,Plate t < 0.5 in
                      AA7050T74Plate200,  ///< 7050 T74 Plate < 8in
                      AA7050T76Plate63,  ///< 7050 T76 Plate < 2.5in
                      AA7055T77Plate37,  ///< 7055 T77 Plate < 1.5in
                      AA7150T77Extrusion13, ///< 7150 T77 Extrusion, t < 0.5in
                      AISI4130Sheet,        ///< AISI 4130 Steel, sheet, tubing
                      AISI4340Tempered,     ///< AISI 4340 Quenched and tempered < 3.5in
                      PH138MoH950Bar, ///< PH13-8Mo H950 Bar, t < 9 in
                      PH174H900Bar, ///< 17-4 PH H900 Bar, t < 8 in
                      PH177TH1050Sheet, ///< 17-7 PH TH 1050 Sheet, t < 0.2 in
                      Ti6Al4VPlateAnnealed, ///< Ti-6Al-4V Annealed plate, < 2in
                      Ti6Al4VExtrusionAged, ///< Ti-6Al-4V Aged extrusion, < 1in
                      EpoxyResin, ///< Typical values for solid LR285 epoxy
                      M21T700, ///< HexPly M21 + Torayca T700, Vf 0.6
                      CfFabricEpoxyManual, ///< HS Carbon/LR285, low-temp
                      SGfFabricEpoxyManual, ///< S-Glass/LR285, low-temp
                    };

  /// undefined material
  MaterialProperty(uint id = NotFound) : m_iid(id) {}

  /// destruct
  virtual ~MaterialProperty();

  /// write NASTRAN bulk data card
  virtual void writeNastran(std::ostream &os) const = 0;

  /// write xml representation
  virtual XmlElement toXml() const = 0;

  /// import from xml representation
  virtual void fromXml(const XmlElement &xe) = 0;

  /// generate a material from builtin ID
  static MaterialPropertyPtr builtinMaterial(BuiltinMatID mat, uint id=1);

  /// create material from XML representation
  static MaterialPropertyPtr createFromXml(const XmlElement &xe);

  /// lookup an iid in material library
  static MaterialPropertyPtr lookup(const MaterialPropertyArray &db, uint id);

  /// write a material database to file
  static XmlElement collectionToXml(const MaterialPropertyArray &db);

  /// load a material database from file
  static MaterialPropertyArray collectionFromXml(const XmlElement &xe);

protected:

  /// write value in NASTRAN bulk data if defined
  void bulkIfValid(Real v, std::ostream &os) const;

  /// generate xml representattion with basic attributes
  XmlElement baseXml(const std::string &tagname) const;

  /// extract base class attributes from xml element
  void baseFromXml(const XmlElement &xe);

  /// integer ID code for NASTRAN
  GENUA_PROP(uint, iid)

  /// material name
  GENUA_PROP(std::string, name)

  /// material density
  GENUA_PROP_INI(Real, rho, NoValue)

  /// for materials used in laminates, a default ILSS
  GENUA_PROP_INI(Real, allowableILSS, NoValue)
};

inline bool operator< (MaterialPropertyPtr a, MaterialPropertyPtr b)
{
  assert(a != nullptr);
  assert(b != nullptr);
  return a->iid() < b->iid();
}

inline bool operator< (MaterialPropertyPtr a, uint b)
{
  assert(a != nullptr);
  return a->iid() < b;
}

inline bool operator< (uint a, MaterialPropertyPtr b)
{
  assert(b != nullptr);
  return a < b->iid();
}

inline bool equivalent(MaterialPropertyPtr a, MaterialPropertyPtr b)
{
  assert(a != nullptr);
  assert(b != nullptr);
  return a->iid() == b->iid();
}

inline bool equivalent(MaterialPropertyPtr a, uint b)
{
  assert(a != nullptr);
  return a->iid() == b;
}

inline bool equivalent(uint a, MaterialPropertyPtr b)
{
  assert(b != nullptr);
  return a == b->iid();
}

/** Internallay used placeholder.
 *
 * \ingroup structures
 * \sa MaterialProperty
 */
class DummyMaterial : public MaterialProperty
{
public:

  using MaterialProperty::NoValue;

  /// undefined material
  DummyMaterial(uint id = NotFound) : MaterialProperty(id) {}

  /// issues a warning and does nothing elase
  virtual void writeNastran(std::ostream &os) const;

  /// write xml representation (id only)
  virtual XmlElement toXml() const;

  /// import from xml representation (id only)
  virtual void fromXml(const XmlElement &xe);
};

/** Plain isotropic material.
 *
 * \ingroup structures
 * \sa MaterialProperty
 */
class IsotropicMaterial : public MaterialProperty
{
public:

  using MaterialProperty::NoValue;

  /// undefined material
  IsotropicMaterial(uint id = NotFound);

  /// write NASTRAN bulk data card
  virtual void writeNastran(std::ostream &os) const;

  /// write xml representation
  virtual XmlElement toXml() const;

  /// import from xml representation
  virtual void fromXml(const XmlElement &xe);

  GENUA_PROP_INI(Real, youngsModulus, NoValue)
  GENUA_PROP_INI(Real, shearModulus, NoValue)
  GENUA_PROP_INI(Real, poisson, NoValue)
  GENUA_PROP_INI(Real, thermalExpansion, NoValue)
  GENUA_PROP_INI(Real, refTemperature, NoValue)
  GENUA_PROP_INI(Real, dampingCoefficient, NoValue)
  GENUA_PROP_INI(Real, stressTension, NoValue)
  GENUA_PROP_INI(Real, stressCompression, NoValue)
  GENUA_PROP_INI(Real, stressShear, NoValue)
};

/** Orthotropic shell material.
 *
 * \ingroup structures
 * \sa MaterialProperty
 */
class OrthotropicMaterial : public MaterialProperty
{
public:

  using MaterialProperty::NoValue;

  /// undefined material
  OrthotropicMaterial(uint id = NotFound);

  /// write NASTRAN bulk data card
  virtual void writeNastran(std::ostream &os) const;

  /// write xml representation
  virtual XmlElement toXml() const;

  /// import from xml representation
  virtual void fromXml(const XmlElement &xe);

  GENUA_PROP_INI(Real, youngsModulus1, NoValue)
  GENUA_PROP_INI(Real, youngsModulus2, NoValue)
  GENUA_PROP_INI(Real, poisson12, NoValue)
  GENUA_PROP_INI(Real, shearModulus12, NoValue)
  GENUA_PROP_INI(Real, shearModulus1Z, NoValue)
  GENUA_PROP_INI(Real, shearModulus2Z, NoValue)
  GENUA_PROP_INI(Real, thermalExpansion1, NoValue)
  GENUA_PROP_INI(Real, thermalExpansion2, NoValue)
  GENUA_PROP_INI(Real, refTemperature, NoValue)
  GENUA_PROP_INI(Real, dampingCoefficient, NoValue)
  GENUA_PROP_INI(Real, allowableTension1, NoValue)
  GENUA_PROP_INI(Real, allowableCompression1, NoValue)
  GENUA_PROP_INI(Real, allowableTension2, NoValue)
  GENUA_PROP_INI(Real, allowableCompression2, NoValue)
  GENUA_PROP_INI(Real, allowableShear, NoValue)
  GENUA_PROP_INI(Real, tsaiWuInteraction, NoValue)
  GENUA_PROP_INI(Real, plyThickness, NoValue)
  GENUA_PROP_INI(bool, allowableIsStress, true)
};

#endif // MATERIALPROPERTY_H
