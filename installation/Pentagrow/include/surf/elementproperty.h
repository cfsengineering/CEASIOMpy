
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
 
#ifndef SURF_ELEMENTPROPERTY_H
#define SURF_ELEMENTPROPERTY_H

#include "forward.h"
#include <genua/propmacro.h>

/** Base class for structural element properties.
 *
 * \ingroup structures
 */
class ElementProperty
{
public:

  static const Real NoValue;

  /// create empty property
  ElementProperty(uint id=NotFound) : m_iid(id) {}

  /// virtual destruction
  virtual ~ElementProperty();

  /// add all materials used by this property to material library
  virtual void storeMaterials(MaterialPropertyArray &matlib);

  /// recover all materials from library
  virtual void loadMaterials(const MaterialPropertyArray &matlib);

  /// write property card in NASTRAN bulk data format
  virtual void writeNastran(std::ostream &os) const = 0;

  /// return XML representation
  virtual XmlElement toXml(bool share=false) const;

  /// recover from XML representation
  virtual void fromXml(const XmlElement &xe);

  /// retrieve element and material property data from a collection
  static XmlElement collectionToXml(const ElementPropertyArray &c);

protected:

  /// write value in NASTRAN bulk data if defined
  void bulkIfValid(Real v, std::ostream &os) const;

  GENUA_PROP(uint, iid)
  GENUA_PROP(std::string, name)
  GENUA_PROP_INI(Real, nonStructuralMass, 0.0)
};

/** Shell element property.
 *
 * \ingroup structures
 * \sa ElementProperty, MaterialProperty
 */
class PlainShellProperty : public ElementProperty
{
public:

  /// empty property definition
  PlainShellProperty(uint id=NotFound) : ElementProperty(id) {}

  /// add all materials used by this property to material library
  virtual void storeMaterials(MaterialPropertyArray &matlib);

  /// recover all materials from library
  virtual void loadMaterials(const MaterialPropertyArray &matlib);

  /// write property card in NASTRAN bulk data format
  virtual void writeNastran(std::ostream &os) const;

  /// return XML representation
  virtual XmlElement toXml(bool share=false) const;

  /// recover from XML representation
  virtual void fromXml(const XmlElement &xe);

private:

  GENUA_PROP(MaterialPropertyPtr, membraneMaterial)
  GENUA_PROP(MaterialPropertyPtr, bendingMaterial)
  GENUA_PROP(MaterialPropertyPtr, shearMaterial)
  GENUA_PROP(MaterialPropertyPtr, couplingMaterial)
  GENUA_PROP_INI(Real, thickness, NoValue)
  GENUA_PROP_INI(Real, bendingMomentRatio, 1.0)
  GENUA_PROP_INI(Real, shearThicknessRatio, NoValue)
  GENUA_PROP_INI(Real, bottomFiberDistance, NoValue)
  GENUA_PROP_INI(Real, topFiberDistance, NoValue)
};

/** Element properties for layered composite shell elements.
 *
 * \ingroup structures
 * \sa OrthotropicMaterial
 */
class CompositeShellProperty : public ElementProperty
{
public:

  using ElementProperty::NoValue;

  struct Layer {

    /// create a layer from full specification
    Layer(MaterialPropertyPtr mat, Real t, Real angle)
      : material(mat), thickness(t), theta(angle) {}

    /// create a layer using material's default ply thickness
    Layer(OrthotropicMaterialPtr mat, Real angle=0.0);

    /// material used in this ply
    MaterialPropertyPtr material;

    /// layer thickness
    Real thickness = 0.0;

    /// angle (radian!)
    Real theta = 0.0;

    /// return XML representation
    XmlElement toXml() const;

    /// recover from XML representation
    void fromXml(const XmlElement &xe);
  };

  /// empty layup definition
  CompositeShellProperty(uint id=NotFound) : ElementProperty(id) {}

  /// add another layer
  uint append(const Layer &a);

  /// number of layers/plies
  uint nlayers() const {return m_layup.size();}

  /// erase all layers
  void clear() {m_layup.clear();}

  /// add all materials used by this property to material library
  virtual void storeMaterials(MaterialPropertyArray &matlib);

  /// recover all materials from library
  virtual void loadMaterials(const MaterialPropertyArray &matlib);

  /// write property card in NASTRAN bulk data format
  virtual void writeNastran(std::ostream &os) const;

  /// return XML representation
  virtual XmlElement toXml(bool share=false) const;

  /// recover from XML representation
  virtual void fromXml(const XmlElement &xe);

private:

  /// all layers, sorted bottom up
  std::vector<Layer> m_layup;

  GENUA_PROP_INI(Real, refToBottomDistance, NoValue)
  GENUA_PROP_INI(Real, allowableILSS, NoValue)
  GENUA_PROP_INI(Real, refTemperature, NoValue)
  GENUA_PROP_INI(Real, dampingCoefficient, NoValue)
  GENUA_PROP_INI(std::string, failureTheory, "")
};

#endif // ELEMENTPROPERTY_H
