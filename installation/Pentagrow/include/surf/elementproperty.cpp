
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

#include "elementproperty.h"
#include "materialproperty.h"
#include <genua/strutils.h>
#include <genua/algo.h>
#include <genua/trigo.h>
#include <genua/xmlelement.h>
#include <iostream>

using namespace std;

const Real ElementProperty::NoValue = std::numeric_limits<Real>::max();

#undef SETIF_XATTR
#undef FETCH_XATTR
#define SETIF_XATTR(a) if (a() != NoValue)  xe[ #a ] = str(m_##a)
#define FETCH_XATTR(a) a( xe.attr2float( #a , a() ) )

ElementProperty::~ElementProperty() {}

void ElementProperty::storeMaterials(MaterialPropertyArray &) {}

void ElementProperty::loadMaterials(const MaterialPropertyArray &) {}

XmlElement ElementProperty::toXml(bool) const
{
  XmlElement xe("ElementProperty");
  xe["name"] = name();
  xe["iid"] = str(iid());
  xe["nonStructuralMass"] = str(nonStructuralMass());
  return xe;
}

void ElementProperty::fromXml(const XmlElement &xe)
{
  name( xe.attribute("name") );
  iid( xe.attr2int("iid", iid()) );
  FETCH_XATTR(nonStructuralMass);
}

XmlElement ElementProperty::collectionToXml(const ElementPropertyArray &c)
{
  XmlElement xe("ElementPropertyCollection");

  // add element properties and collect materials
  MaterialPropertyArray matlib;
  for (const ElementPropertyPtr &ep : c) {
    ep->storeMaterials(matlib);
    xe.append(ep->toXml());
  }
  xe.append( MaterialProperty::collectionToXml(matlib) );
  return xe;
}

void ElementProperty::bulkIfValid(Real v, std::ostream &os) const
{
  if (v != NoValue)
    os << nstr(v) << ", ";
  else
    os << ',';
}

void PlainShellProperty::storeMaterials(MaterialPropertyArray &matlib)
{
  if (membraneMaterial() != nullptr) {
    insert_once(matlib, membraneMaterial());
  }
  if (bendingMaterial() != nullptr and !equivalent(membraneMaterial(),
                                                   bendingMaterial())) {
    insert_once(matlib, bendingMaterial());
  }
  if (shearMaterial() != nullptr and !equivalent(membraneMaterial(),
                                                 shearMaterial())) {
    insert_once(matlib, shearMaterial());
  }
  if (couplingMaterial() != nullptr and !equivalent(membraneMaterial(),
                                                    couplingMaterial())) {
    insert_once(matlib, couplingMaterial());
  }
}

void PlainShellProperty::loadMaterials(const MaterialPropertyArray &matlib)
{
  if (membraneMaterial() != nullptr)
    membraneMaterial(MaterialProperty::lookup(matlib,
                                              membraneMaterial()->iid()));
  if (bendingMaterial() != nullptr)
    bendingMaterial(MaterialProperty::lookup(matlib,
                                             bendingMaterial()->iid()));
  if (shearMaterial() != nullptr)
    shearMaterial(MaterialProperty::lookup(matlib,
                                           shearMaterial()->iid()));
  if (couplingMaterial() != nullptr)
    couplingMaterial(MaterialProperty::lookup(matlib,
                                              couplingMaterial()->iid()));

}

void PlainShellProperty::writeNastran(ostream &os) const
{
  if (iid() == 0 or iid() == NotFound)
    return;

  os << "PSHELL, " << iid() << ", ";
  if (membraneMaterial() != nullptr)
    os << membraneMaterial()->iid();
  os << ", ";
  bulkIfValid(thickness(), os);
  if (bendingMaterial() != nullptr)
    os << bendingMaterial()->iid();
  os << ", ";
  bulkIfValid(bendingMomentRatio(), os);
  if (shearMaterial() != nullptr)
    os << shearMaterial()->iid();
  os << ", ";
  bulkIfValid(shearThicknessRatio(), os);
  bulkIfValid(nonStructuralMass(), os);
  os << endl;

  if (bottomFiberDistance() == NoValue and topFiberDistance() == NoValue)
    return;

  os << "  , ";
  bulkIfValid(bottomFiberDistance(), os);
  bulkIfValid(topFiberDistance(), os);
  if (couplingMaterial() != nullptr)
    os << couplingMaterial()->iid();
  os << ", " << endl;
}

XmlElement PlainShellProperty::toXml(bool share) const
{
  XmlElement xe = ElementProperty::toXml(share);
  xe.rename("PlainShellProperty");
  xe["bendingMomentRatio"] = str(bendingMomentRatio());
  SETIF_XATTR(thickness);
  SETIF_XATTR(shearThicknessRatio);
  SETIF_XATTR(bottomFiberDistance);
  SETIF_XATTR(topFiberDistance);

  if (membraneMaterial() != nullptr)
    xe["membraneMaterialID"] = str( membraneMaterial()->iid() );
  if (bendingMaterial() != nullptr)
    xe["bendingMaterialID"] = str( bendingMaterial()->iid() );
  if (shearMaterial() != nullptr)
    xe["shearMaterialID"] = str( shearMaterial()->iid() );
  if (couplingMaterial() != nullptr)
    xe["couplingMaterialID"] = str( couplingMaterial()->iid() );

  return xe;
}

void PlainShellProperty::fromXml(const XmlElement &xe)
{
  ElementProperty::fromXml(xe);
  FETCH_XATTR(thickness);
  FETCH_XATTR(shearThicknessRatio);
  FETCH_XATTR(bottomFiberDistance);
  FETCH_XATTR(topFiberDistance);

  m_membraneMaterial.reset();
  m_bendingMaterial.reset();
  m_shearMaterial.reset();
  m_couplingMaterial.reset();

  XmlElement::attr_iterator ita, last = xe.attrEnd();
  for (ita = xe.attrBegin(); ita != last; ++ita) {
    if (ita->first == "membraneMaterialID")
      m_membraneMaterial =
          boost::make_shared<DummyMaterial>( std::stoi(ita->second) );
    else if (ita->first == "bendingMaterialID")
      m_bendingMaterial =
          boost::make_shared<DummyMaterial>( std::stoi(ita->second) );
    else if (ita->first == "shearMaterialID")
      m_shearMaterial =
          boost::make_shared<DummyMaterial>( std::stoi(ita->second) );
    else if (ita->first == "bendingMaterialID")
      m_couplingMaterial =
          boost::make_shared<DummyMaterial>( std::stoi(ita->second) );
  }
}

uint CompositeShellProperty::append(const CompositeShellProperty::Layer &a)
{
  m_layup.push_back(a);
  allowableILSS( std::min(allowableILSS(), a.material->allowableILSS()) );
  return m_layup.size() - 1;
}

void CompositeShellProperty::storeMaterials(MaterialPropertyArray &matlib)
{
  for (const Layer &ply : m_layup)
    insert_once(matlib, ply.material);
}

void CompositeShellProperty::loadMaterials(const MaterialPropertyArray &matlib)
{
  for (Layer &ply : m_layup)
    if (ply.material != nullptr)
      ply.material = MaterialProperty::lookup(matlib, ply.material->iid());
}

void CompositeShellProperty::writeNastran(std::ostream &os) const
{
  if (iid() == 0 or iid() == NotFound or m_layup.empty())
    return;

  if (not name().empty())
    os << "$ composite element property: " << name() << endl;
  os << "PCOMP, " << iid() << ", ";
  bulkIfValid(refToBottomDistance(), os);
  bulkIfValid(nonStructuralMass(), os);
  bulkIfValid(allowableILSS(), os);
  os << failureTheory() << ", ";
  bulkIfValid(refTemperature(), os);
  bulkIfValid(dampingCoefficient(), os);
  os << ',' << endl;

  for (size_t i=0; i<m_layup.size(); ++i) {
    const Layer &lam( m_layup[i] );
    uint mid = lam.material->iid();
    if (mid == 0 or mid == NotFound)
      continue;
    os << " , " << mid << ", "
       << nstr(lam.thickness) << ", " << nstr(deg(lam.theta));
    if (i%2 == 1)
      os << endl;
  }
  if (m_layup.size()%2 == 1)
    os << endl;
}

XmlElement CompositeShellProperty::toXml(bool share) const
{
  XmlElement xe = ElementProperty::toXml(share);
  xe.rename("CompositeShellProperty");
  xe["failureTheory"] = failureTheory();
  SETIF_XATTR(refToBottomDistance);
  SETIF_XATTR(allowableILSS);
  SETIF_XATTR(refTemperature);
  SETIF_XATTR(dampingCoefficient);
  for (const Layer &ply : m_layup)
    xe.append( ply.toXml() );
  return xe;
}

void CompositeShellProperty::fromXml(const XmlElement &xe)
{
  m_layup.clear();
  ElementProperty::fromXml(xe);
  failureTheory( xe.attribute("failureTheory") );
  FETCH_XATTR(refToBottomDistance);
  FETCH_XATTR(allowableILSS);
  FETCH_XATTR(refTemperature);
  FETCH_XATTR(dampingCoefficient);
  for (const XmlElement &child : xe) {
    if (child.name() == "Layer") {
      Layer ply(nullptr, 0.0);
      ply.fromXml(child);
      m_layup.push_back(ply);
    }
  }
}

CompositeShellProperty::Layer::Layer(OrthotropicMaterialPtr mat, Real angle)
  : material(mat), thickness(mat != nullptr ? mat->plyThickness() : 0.0),
    theta(angle) {}

XmlElement CompositeShellProperty::Layer::toXml() const
{
  XmlElement xe("Layer");
  xe["thickness"] = str(thickness);
  xe["theta"] = str(theta);
  if (material != nullptr)
    xe["materialID"] = str(material->iid());
  return xe;
}

void CompositeShellProperty::Layer::fromXml(const XmlElement &xe)
{
  thickness = xe.attr2float("thickness", 0.0);
  theta = xe.attr2float("theta", 0.0);
  uint mid = xe.attr2int("materialID", 0);
  if (mid != 0)
    material = boost::make_shared<DummyMaterial>(mid);
  else
    material.reset();
}



