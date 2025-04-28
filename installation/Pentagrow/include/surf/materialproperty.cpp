
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
 
#include "materialproperty.h"
#include <genua/strutils.h>
#include <genua/xmlelement.h>
#include <iostream>

using namespace std;

const Real MaterialProperty::NoValue = std::numeric_limits<Real>::max();

MaterialProperty::~MaterialProperty() {}

MaterialPropertyPtr MaterialProperty::createFromXml(const XmlElement &xe)
{
  if (xe.name() == "MaterialID") {
    DummyMaterialPtr m = boost::make_shared<DummyMaterial>();
    m->fromXml(xe);
    return boost::dynamic_pointer_cast<MaterialProperty>(m);
  } else if (xe.name() == "IsotropicMaterial") {
    IsotropicMaterialPtr m = boost::make_shared<IsotropicMaterial>();
    m->fromXml(xe);
    return boost::dynamic_pointer_cast<MaterialProperty>(m);
  } else if (xe.name() == "OrthotropicMaterial") {
    OrthotropicMaterialPtr m = boost::make_shared<OrthotropicMaterial>();
    m->fromXml(xe);
    return boost::dynamic_pointer_cast<MaterialProperty>(m);
  }
  return MaterialPropertyPtr();
}

MaterialPropertyPtr MaterialProperty::lookup(const MaterialPropertyArray &db,
                                             uint id)
{
  if (id == NotFound)
    return nullptr;

  auto pred = [&](const MaterialPropertyPtr &m) {
    return (m != nullptr) ? (m->iid() == id) : false;
  };
  MaterialPropertyArray::const_iterator pos;
  pos = std::find_if(db.begin(), db.end(), pred);
  return (pos != db.end()) ? *pos : MaterialPropertyPtr();
}

MaterialPropertyPtr
MaterialProperty::builtinMaterial(BuiltinMatID mat, uint id)
{
  const Real ksi = 6.89475908677537e6;
  const Real lbin3 = 27679.9047;

  MaterialPropertyPtr m;
  boost::shared_ptr<IsotropicMaterial> mi;
  boost::shared_ptr<OrthotropicMaterial> mo;
  switch (mat) {

  case AA2024T3Sheet:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Aluminum 2024 T3 Sheet");
    mi->rho( 0.1 * lbin3 );
    mi->poisson( 0.33 );
    mi->youngsModulus( 10.5e3 * ksi );
    mi->shearModulus( 4.0e3*ksi );
    mi->thermalExpansion( 12.8e-6 );
    mi->stressTension( 63*ksi );
    mi->stressCompression( 1.5*39*ksi );
    mi->stressShear( 39*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case AA2024T3Plate76:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Aluminum 2024 T3 Plate");
    mi->rho( 0.1 * lbin3 );
    mi->poisson( 0.33 );
    mi->youngsModulus( 10.7e3 * ksi );
    mi->shearModulus( 4.0e3*ksi );
    mi->thermalExpansion( 12.8e-6 );
    mi->stressTension( 60*ksi );
    mi->stressCompression( 1.5*37*ksi );
    mi->stressShear( 35*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case AA2024T8Sheet13:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Aluminum 2024 T8 Plate");
    mi->rho( 0.1 * lbin3 );
    mi->poisson( 0.33 );
    mi->youngsModulus( 10.7e3 * ksi );
    mi->shearModulus( 4.0e3*ksi );
    mi->thermalExpansion( 12.8e-6 );
    mi->stressTension( 67*ksi );
    mi->stressCompression( 67*ksi );
    mi->stressShear( 38*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case AA7050T74Plate200:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Aluminum 7050 T74 Plate < 200mm");
    mi->rho( 0.102 * lbin3 );
    mi->poisson( 0.33 );
    mi->youngsModulus( 10.3e3 * ksi );
    mi->shearModulus( 3.9e3*ksi );
    mi->thermalExpansion( 12.8e-6 );
    mi->stressTension( 68*ksi );
    mi->stressCompression( 68*ksi );
    mi->stressShear( 44*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case AA7050T76Plate63:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Aluminum 7050 T76 Plate < 63mm");
    mi->rho( 0.102 * lbin3 );
    mi->poisson( 0.33 );
    mi->youngsModulus( 10.3e3 * ksi );
    mi->shearModulus( 4.0e3*ksi );
    mi->thermalExpansion( 12.8e-6 );
    mi->stressTension( 75*ksi );
    mi->stressCompression( 75*ksi );
    mi->stressShear( 44*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case AA7055T77Plate37:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Aluminum 7055 T77 Plate < 37mm");
    mi->rho( 0.103 * lbin3 );
    mi->poisson( 0.32 );
    mi->youngsModulus( 10.4e3 * ksi );
    mi->shearModulus( 3.9e3*ksi );
    mi->thermalExpansion( 12.8e-6 );
    mi->stressTension( 89*ksi );
    mi->stressCompression( 89*ksi );
    mi->stressShear( 48*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case AA7150T77Extrusion13:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Aluminum 7150 T77 Extrusion");
    mi->rho( 0.102 * lbin3 );
    mi->poisson( 0.33 );
    mi->youngsModulus( 10.4e3 * ksi );
    mi->shearModulus( 4.0e3*ksi );
    mi->thermalExpansion( 12.8e-6 );
    mi->stressTension( 82*ksi );
    mi->stressCompression( 82*ksi );
    mi->stressShear( 46*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case AISI4130Sheet:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Low-Alloy Steel AISI 4130");
    mi->rho( 0.283 * lbin3 );
    mi->poisson( 0.32 );
    mi->youngsModulus( 29.0e3 * ksi );
    mi->shearModulus( 11.0e3 * ksi );
    mi->thermalExpansion( 6.8e-6 );
    mi->stressTension( 95*ksi );
    mi->stressCompression( 95*ksi );
    mi->stressShear( 57*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

    // S-values for AISI 4340

  case AISI4340Tempered:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Low-Alloy Steel AISI 4340 Tempered");
    mi->rho( 0.283 * lbin3 );
    mi->poisson( 0.32 );
    mi->youngsModulus( 29.0e3 * ksi );
    mi->shearModulus( 11.0e3 * ksi );
    mi->thermalExpansion( 6.8e-6 );
    mi->stressTension( 160*ksi );
    mi->stressCompression( 160*ksi );
    mi->stressShear( 96*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case PH138MoH950Bar:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Stainless Steel PH13-8Mo Bar");
    mi->rho( 0.279 * lbin3 );
    mi->poisson( 0.28 );
    mi->youngsModulus( 28.3e3 * ksi );
    mi->shearModulus( 11.0e3 * ksi );
    mi->thermalExpansion( 5.8e-6 );
    mi->stressTension( 217*ksi );
    mi->stressCompression( 217*ksi );
    mi->stressShear( 117*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case PH174H900Bar:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Stainless Steel 17-4 PH Bar");
    mi->rho( 0.27 * lbin3 );
    mi->poisson( 0.27 );
    mi->youngsModulus( 28.5e3 * ksi );
    mi->shearModulus( 11.2e3 * ksi );
    mi->thermalExpansion( 5.8e-6 );
    mi->stressTension( 190*ksi );
    mi->stressCompression( 190*ksi );
    mi->stressShear( 123*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case PH177TH1050Sheet:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Stainless Steel 17-7 PH Sheet < 5mm");
    mi->rho( 0.276 * lbin3 );
    mi->poisson( 0.28 );
    mi->youngsModulus( 29.0e3 * ksi );
    mi->shearModulus( 11.5e3 * ksi );
    mi->thermalExpansion( 6.5e-6 );
    mi->stressTension( 177*ksi );
    mi->stressCompression( 177*ksi );
    mi->stressShear( 112*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case Ti6Al4VPlateAnnealed:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Titanium Ti-6Al-4V Annealed Plate < 50 mm");
    mi->rho( 0.160 * lbin3 );
    mi->poisson( 0.31 );
    mi->youngsModulus( 16.0e3 * ksi );
    mi->shearModulus( 6.2e3 * ksi );
    mi->thermalExpansion( 4.9e-6 );
    mi->stressTension( 130*ksi );
    mi->stressCompression( 130*ksi );
    mi->stressShear( 79*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case Ti6Al4VExtrusionAged:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Titanium Ti-6Al-4V Aged Extrusion < 25 mm");
    mi->rho( 0.160 * lbin3 );
    mi->poisson( 0.31 );
    mi->youngsModulus( 16.9e3 * ksi );
    mi->shearModulus( 6.2e3 * ksi );
    mi->thermalExpansion( 4.9e-6 );
    mi->stressTension( 147*ksi );
    mi->stressCompression( 147*ksi );
    mi->stressShear( 89*ksi );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

    // composite materials below are indicative only,
    // from manufacturer's datasheet plus assumptions on missing values

  case EpoxyResin:
    mi = boost::make_shared<IsotropicMaterial>(id);
    mi->name("Epoxy resin LR285 (typical values)");
    mi->rho( 1190. );
    mi->poisson( 0.35 );
    mi->youngsModulus( 3.3e9 );
    mi->shearModulus( mi->youngsModulus()*0.5 /(1.0 + mi->poisson())  );
    mi->thermalExpansion( 55e-6 );  // approximation
    mi->stressTension( 70e6 );
    mi->stressCompression( 120e6 );
    mi->stressShear( 42e6 );
    mi->allowableILSS( mi->stressShear() );
    m = boost::dynamic_pointer_cast<MaterialProperty>(mi);
    break;

  case CfFabricEpoxyManual:
    mo = boost::make_shared<OrthotropicMaterial>(id);
    mo->name("HT Carbon Fabric 44% LR285 Hand Laminate");
    mo->plyThickness(0.255e-3);  // Style 452, 200g/sqm
    mo->rho(1160.);
    mo->poisson12(0.124);
    mo->youngsModulus1(53e9);
    mo->youngsModulus2(52.7e9);
    mo->shearModulus12(2.4e9);
    mo->shearModulus1Z( mo->shearModulus12() );
    mo->shearModulus2Z( mo->shearModulus12() );
    mo->allowableCompression1(250e6);
    mo->allowableCompression2(250e6);
    mo->allowableTension1(505e6);
    mo->allowableTension2(505e6);
    mo->allowableShear(35e6);
    mo->allowableILSS( 60e6 );
    mo->allowableIsStress(true);
    m = boost::dynamic_pointer_cast<MaterialProperty>(mo);
    break;

  case SGfFabricEpoxyManual:
    mo = boost::make_shared<OrthotropicMaterial>(id);
    mo->name("S Glass Fabric 44% LR285 Hand Laminate");
    mo->plyThickness(0.251e-3);  // Style 92125, 280g/sqm
    mo->rho(1360.);
    mo->poisson12(0.07);
    mo->youngsModulus1(20e9);
    mo->youngsModulus2(20e9);
    mo->shearModulus12(3.1e9);
    mo->shearModulus1Z( mo->shearModulus12() );
    mo->shearModulus2Z( mo->shearModulus12() );
    mo->allowableCompression1(187e6);
    mo->allowableCompression2(187e6);
    mo->allowableTension1(375e6);
    mo->allowableTension2(375e6);
    mo->allowableShear(40e6);
    mo->allowableILSS( 60e6 );
    mo->allowableIsStress(true);
    m = boost::dynamic_pointer_cast<MaterialProperty>(mo);
    break;

  case M21T700:
    mo = boost::make_shared<OrthotropicMaterial>(id);
    mo->name("HexPly M21 60% T700");
    mo->plyThickness(0.131e-3);
    mo->rho(1580.0);
    mo->poisson12(0.31);
    mo->youngsModulus1(118e9);
    mo->youngsModulus2(8.4e9);
    mo->shearModulus12(4.7e9);
    mo->shearModulus1Z( mo->shearModulus12() );
    mo->shearModulus2Z( mo->shearModulus12() );
    mo->allowableCompression1(1460e6);
    mo->allowableCompression2(50e6);
    mo->allowableTension1(2314e6);
    mo->allowableTension2(50e6);
    mo->allowableShear(113e6);
    mo->allowableILSS( 110e6 );
    mo->allowableIsStress(true);
    m = boost::dynamic_pointer_cast<MaterialProperty>(mo);
  }

  return m;
}

MaterialPropertyArray MaterialProperty::collectionFromXml(const XmlElement &xe)
{
  MaterialPropertyArray db;
  for (const XmlElement &x : xe) {
    MaterialPropertyPtr m = MaterialProperty::createFromXml(x);
    if (m != nullptr)
      db.push_back(m);
  }
  return db;
}

XmlElement MaterialProperty::collectionToXml(const MaterialPropertyArray &db)
{
  XmlElement xe("MaterialCollection");
  for (const MaterialPropertyPtr &mpp : db)
    xe.append( mpp->toXml() );
  return xe;
}

void MaterialProperty::bulkIfValid(Real v, std::ostream &os) const
{
  if (v != NoValue)
    os << nstr(v) << ", ";
  else
    os << ',';
}

void MaterialProperty::baseFromXml(const XmlElement &xe)
{
  name( xe.attribute("name") );
  iid( xe.attr2int("iid", iid()) );
  rho( xe.attr2float("rho", rho()) );
}

XmlElement MaterialProperty::baseXml(const string &tagname) const
{
  XmlElement xe(tagname);
  xe["name"] = name();
  if (iid() != NotFound)
    xe["iid"] = str(iid());
  if (rho() != NoValue)
    xe["rho"] = str(rho());
  return xe;
}

// -----------------------------------------------------------------------------

void DummyMaterial::writeNastran(ostream &) const
{
  std::clog << "[w] Attempting to write dummy material to "
               "NASTRAN bulk data file." << std::endl;
}

XmlElement DummyMaterial::toXml() const
{
  XmlElement xe("MaterialID");
  xe["iid"] = str(iid());
  return xe;
}

void DummyMaterial::fromXml(const XmlElement &xe)
{
  iid( xe.attr2int("iid", NotFound) );
}

// -----------------------------------------------------------------------------

IsotropicMaterial::IsotropicMaterial(uint id) : MaterialProperty(id) {}

void IsotropicMaterial::writeNastran(std::ostream &os) const
{
  if (iid() == NotFound or iid() == 0)
    return;

  if (not name().empty())
    os << "$ material: " << name() << endl;
  os << "MAT1, " << iid() << ", ";
  bulkIfValid(youngsModulus(), os);
  bulkIfValid(shearModulus(), os);
  bulkIfValid(poisson(), os);
  bulkIfValid(rho(), os);
  bulkIfValid(thermalExpansion(), os);
  bulkIfValid(refTemperature(), os);
  bulkIfValid(dampingCoefficient(), os);
  os << endl;
  if (stressTension() == NoValue)
    return;

  os << " ,";
  bulkIfValid(stressTension(), os);
  bulkIfValid(stressCompression(), os);
  bulkIfValid(stressShear(), os);
  os << ',' << endl;
}

#undef SETIF_XATTR
#undef FETCH_XATTR
#define SETIF_XATTR(a) if (a() != NoValue)  xe[ #a ] = str(m_##a)
#define FETCH_XATTR(a) a( xe.attr2float( #a , a() ) )

XmlElement IsotropicMaterial::toXml() const
{
  XmlElement xe( this->baseXml("IsotropicMaterial") );
  SETIF_XATTR(youngsModulus);
  SETIF_XATTR(shearModulus);
  SETIF_XATTR(poisson);
  SETIF_XATTR(thermalExpansion);
  SETIF_XATTR(refTemperature);
  SETIF_XATTR(dampingCoefficient);
  SETIF_XATTR(stressTension);
  SETIF_XATTR(stressCompression);
  SETIF_XATTR(stressShear);
  return xe;
}

void IsotropicMaterial::fromXml(const XmlElement &xe)
{
  this->baseFromXml(xe);
  FETCH_XATTR(youngsModulus);
  FETCH_XATTR(shearModulus);
  FETCH_XATTR(poisson);
  FETCH_XATTR(thermalExpansion);
  FETCH_XATTR(refTemperature);
  FETCH_XATTR(dampingCoefficient);
  FETCH_XATTR(stressTension);
  FETCH_XATTR(stressCompression);
  FETCH_XATTR(stressShear);
}

// -----------------------------------------------------------------------------

OrthotropicMaterial::OrthotropicMaterial(uint id) : MaterialProperty(id) {}

void OrthotropicMaterial::writeNastran(ostream &os) const
{
  if (iid() == NotFound or iid() == 0)
    return;

  if (not name().empty())
    os << "$ material: " << name() << endl;
  os << "MAT8, " << iid() << ", ";
  bulkIfValid(youngsModulus1(), os);
  bulkIfValid(youngsModulus2(), os);
  bulkIfValid(poisson12(), os);
  bulkIfValid(shearModulus12(), os);
  bulkIfValid(shearModulus1Z(), os);
  bulkIfValid(shearModulus2Z(), os);
  bulkIfValid(rho(), os);
  os << endl;

  os << " ,";
  bulkIfValid(thermalExpansion1(), os);
  bulkIfValid(thermalExpansion2(), os);
  bulkIfValid(refTemperature(), os);
  bulkIfValid(allowableTension1(), os);
  bulkIfValid(allowableCompression1(), os);
  bulkIfValid(allowableTension2(), os);
  bulkIfValid(allowableCompression2(), os);
  bulkIfValid(allowableShear(), os);
  os << endl;

  os << " ,";
  bulkIfValid(dampingCoefficient(), os);
  bulkIfValid(tsaiWuInteraction(), os);
  if (allowableIsStress())
    os << endl;
  else
    os << "1.0" << endl;
}

XmlElement OrthotropicMaterial::toXml() const
{
  XmlElement xe( this->baseXml("OrthotropicMaterial") );
  xe["allowableIsStress"] = allowableIsStress() ? ("true") : ("false");
  SETIF_XATTR(youngsModulus1);
  SETIF_XATTR(youngsModulus2);
  SETIF_XATTR(shearModulus12);
  SETIF_XATTR(shearModulus1Z);
  SETIF_XATTR(shearModulus2Z);
  SETIF_XATTR(poisson12);
  SETIF_XATTR(thermalExpansion1);
  SETIF_XATTR(thermalExpansion2);
  SETIF_XATTR(refTemperature);
  SETIF_XATTR(dampingCoefficient);
  SETIF_XATTR(allowableTension1);
  SETIF_XATTR(allowableTension2);
  SETIF_XATTR(allowableCompression1);
  SETIF_XATTR(allowableCompression2);
  SETIF_XATTR(allowableShear);
  SETIF_XATTR(tsaiWuInteraction);
  SETIF_XATTR(plyThickness);
  return xe;
}

void OrthotropicMaterial::fromXml(const XmlElement &xe)
{
  this->baseFromXml(xe);
  allowableIsStress( xe.attribute("allowableIsStress", "true") == "true" );
  FETCH_XATTR(youngsModulus1);
  FETCH_XATTR(youngsModulus2);
  FETCH_XATTR(shearModulus12);
  FETCH_XATTR(shearModulus1Z);
  FETCH_XATTR(shearModulus2Z);
  FETCH_XATTR(poisson12);
  FETCH_XATTR(thermalExpansion1);
  FETCH_XATTR(thermalExpansion2);
  FETCH_XATTR(refTemperature);
  FETCH_XATTR(dampingCoefficient);
  FETCH_XATTR(allowableTension1);
  FETCH_XATTR(allowableTension2);
  FETCH_XATTR(allowableCompression1);
  FETCH_XATTR(allowableCompression2);
  FETCH_XATTR(allowableShear);
  FETCH_XATTR(tsaiWuInteraction);
  FETCH_XATTR(plyThickness);
}

#undef SETIF_XATTR
#undef FETCH_XATTR


