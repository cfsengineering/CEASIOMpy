
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
 

#ifndef SURF_AP203_H
#define SURF_AP203_H

// automatically created by surf/tools/fedex.py -- do not edit

#include "step.h"
#include "stepentity.h"
#include <cassert>

class StepAheadOrBehind : public StepEnum
{
  public:
  typedef enum {
    ahead,
    behind } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 2, stringrep, iv);
      value = (StepAheadOrBehind::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 2);
      os << stringrep[i];
    }
    bool operator== (const StepAheadOrBehind & a) const
      {return value == a.value;}
    bool operator!= (const StepAheadOrBehind & a) const
      {return value != a.value;}
    bool operator== (const StepAheadOrBehind::Code & a) const
      {return value == a;}
    bool operator!= (const StepAheadOrBehind::Code & a) const
      {return value != a;}
  public:
    StepAheadOrBehind::Code value;
  private:
    static const char *stringrep[];
};

class StepApprovedItem : public StepSelect
{
  public:
  enum Code {
    product_definition_formation,
    product_definition,
    configuration_effectivity,
    configuration_item,
    security_classification,
    change_request,
    change,
    start_request,
    start_work,
    certification,
    contract };
  public:
    StepApprovedItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 11, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepApprovedItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepApprovedItem::Code value;
  private:
    static const char *stringrep[];
};

class StepAxis2Placement : public StepSelect
{
  public:
  enum Code {
    axis2_placement_2d,
    axis2_placement_3d };
  public:
    StepAxis2Placement() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepAxis2Placement::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepAxis2Placement::Code value;
  private:
    static const char *stringrep[];
};

class StepBSplineCurveForm : public StepEnum
{
  public:
  typedef enum {
    polyline_form,
    circular_arc,
    elliptic_arc,
    parabolic_arc,
    hyperbolic_arc,
    unspecified } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 6, stringrep, iv);
      value = (StepBSplineCurveForm::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 6);
      os << stringrep[i];
    }
    bool operator== (const StepBSplineCurveForm & a) const
      {return value == a.value;}
    bool operator!= (const StepBSplineCurveForm & a) const
      {return value != a.value;}
    bool operator== (const StepBSplineCurveForm::Code & a) const
      {return value == a;}
    bool operator!= (const StepBSplineCurveForm::Code & a) const
      {return value != a;}
  public:
    StepBSplineCurveForm::Code value;
  private:
    static const char *stringrep[];
};

class StepBSplineSurfaceForm : public StepEnum
{
  public:
  typedef enum {
    plane_surf,
    cylindrical_surf,
    conical_surf,
    spherical_surf,
    toroidal_surf,
    surf_of_revolution,
    ruled_surf,
    generalised_cone,
    quadric_surf,
    surf_of_linear_extrusion,
    unspecified } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 11, stringrep, iv);
      value = (StepBSplineSurfaceForm::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 11);
      os << stringrep[i];
    }
    bool operator== (const StepBSplineSurfaceForm & a) const
      {return value == a.value;}
    bool operator!= (const StepBSplineSurfaceForm & a) const
      {return value != a.value;}
    bool operator== (const StepBSplineSurfaceForm::Code & a) const
      {return value == a;}
    bool operator!= (const StepBSplineSurfaceForm::Code & a) const
      {return value != a;}
  public:
    StepBSplineSurfaceForm::Code value;
  private:
    static const char *stringrep[];
};

class StepBooleanOperand : public StepSelect
{
  public:
  enum Code {
    solid_model };
  public:
    StepBooleanOperand() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 1, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepBooleanOperand::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepBooleanOperand::Code value;
  private:
    static const char *stringrep[];
};

class StepCertifiedItem : public StepSelect
{
  public:
  enum Code {
    supplied_part_relationship };
  public:
    StepCertifiedItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 1, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepCertifiedItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepCertifiedItem::Code value;
  private:
    static const char *stringrep[];
};

class StepChangeRequestItem : public StepSelect
{
  public:
  enum Code {
    product_definition_formation };
  public:
    StepChangeRequestItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 1, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepChangeRequestItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepChangeRequestItem::Code value;
  private:
    static const char *stringrep[];
};

class StepCharacterizedDefinition : public StepSelect
{
  public:
  enum Code {
    characterized_product_definition,
    shape_definition };
  public:
    StepCharacterizedDefinition() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepCharacterizedDefinition::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepCharacterizedDefinition::Code value;
  private:
    static const char *stringrep[];
};

class StepCharacterizedProductDefinition : public StepSelect
{
  public:
  enum Code {
    product_definition,
    product_definition_relationship };
  public:
    StepCharacterizedProductDefinition() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepCharacterizedProductDefinition::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepCharacterizedProductDefinition::Code value;
  private:
    static const char *stringrep[];
};

class StepClassifiedItem : public StepSelect
{
  public:
  enum Code {
    product_definition_formation,
    assembly_component_usage };
  public:
    StepClassifiedItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepClassifiedItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepClassifiedItem::Code value;
  private:
    static const char *stringrep[];
};

class StepContractedItem : public StepSelect
{
  public:
  enum Code {
    product_definition_formation };
  public:
    StepContractedItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 1, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepContractedItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepContractedItem::Code value;
  private:
    static const char *stringrep[];
};

class StepCurveOnSurface : public StepSelect
{
  public:
  enum Code {
    pcurve,
    surface_curve,
    composite_curve_on_surface };
  public:
    StepCurveOnSurface() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 3, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepCurveOnSurface::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepCurveOnSurface::Code value;
  private:
    static const char *stringrep[];
};

class StepDateTimeItem : public StepSelect
{
  public:
  enum Code {
    product_definition,
    change_request,
    start_request,
    change,
    start_work,
    approval_person_organization,
    contract,
    security_classification,
    certification };
  public:
    StepDateTimeItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 9, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepDateTimeItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepDateTimeItem::Code value;
  private:
    static const char *stringrep[];
};

class StepDateTimeSelect : public StepSelect
{
  public:
  enum Code {
    date,
    local_time,
    date_and_time };
  public:
    StepDateTimeSelect() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 3, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepDateTimeSelect::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepDateTimeSelect::Code value;
  private:
    static const char *stringrep[];
};

class StepFoundedItemSelect : public StepSelect
{
  public:
  enum Code {
    founded_item,
    representation_item };
  public:
    StepFoundedItemSelect() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepFoundedItemSelect::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepFoundedItemSelect::Code value;
  private:
    static const char *stringrep[];
};

class StepGeometricSetSelect : public StepSelect
{
  public:
  enum Code {
    point,
    curve,
    surface };
  public:
    StepGeometricSetSelect() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 3, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepGeometricSetSelect::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepGeometricSetSelect::Code value;
  private:
    static const char *stringrep[];
};

class StepKnotType : public StepEnum
{
  public:
  typedef enum {
    uniform_knots,
    unspecified,
    quasi_uniform_knots,
    piecewise_bezier_knots } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 4, stringrep, iv);
      value = (StepKnotType::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 4);
      os << stringrep[i];
    }
    bool operator== (const StepKnotType & a) const
      {return value == a.value;}
    bool operator!= (const StepKnotType & a) const
      {return value != a.value;}
    bool operator== (const StepKnotType::Code & a) const
      {return value == a;}
    bool operator!= (const StepKnotType::Code & a) const
      {return value != a;}
  public:
    StepKnotType::Code value;
  private:
    static const char *stringrep[];
};

class StepMeasureValue : public StepSelect
{
  public:
  enum Code {
    length_measure,
    mass_measure,
    plane_angle_measure,
    solid_angle_measure,
    area_measure,
    volume_measure,
    parameter_value,
    context_dependent_measure,
    descriptive_measure,
    positive_length_measure,
    positive_plane_angle_measure,
    count_measure };
  public:
    StepMeasureValue() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 12, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepMeasureValue::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepMeasureValue::Code value;
  private:
    static const char *stringrep[];
};

class StepPcurveOrSurface : public StepSelect
{
  public:
  enum Code {
    pcurve,
    surface };
  public:
    StepPcurveOrSurface() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepPcurveOrSurface::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepPcurveOrSurface::Code value;
  private:
    static const char *stringrep[];
};

class StepPersonOrganizationItem : public StepSelect
{
  public:
  enum Code {
    change,
    start_work,
    change_request,
    start_request,
    configuration_item,
    product,
    product_definition_formation,
    product_definition,
    contract,
    security_classification };
  public:
    StepPersonOrganizationItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 10, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepPersonOrganizationItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepPersonOrganizationItem::Code value;
  private:
    static const char *stringrep[];
};

class StepPersonOrganizationSelect : public StepSelect
{
  public:
  enum Code {
    person,
    organization,
    person_and_organization };
  public:
    StepPersonOrganizationSelect() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 3, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepPersonOrganizationSelect::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepPersonOrganizationSelect::Code value;
  private:
    static const char *stringrep[];
};

class StepPreferredSurfaceCurveRepresentation : public StepEnum
{
  public:
  typedef enum {
    curve_3d,
    pcurve_s1,
    pcurve_s2 } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 3, stringrep, iv);
      value = (StepPreferredSurfaceCurveRepresentation::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 3);
      os << stringrep[i];
    }
    bool operator== (const StepPreferredSurfaceCurveRepresentation & a) const
      {return value == a.value;}
    bool operator!= (const StepPreferredSurfaceCurveRepresentation & a) const
      {return value != a.value;}
    bool operator== (const StepPreferredSurfaceCurveRepresentation::Code & a) const
      {return value == a;}
    bool operator!= (const StepPreferredSurfaceCurveRepresentation::Code & a) const
      {return value != a;}
  public:
    StepPreferredSurfaceCurveRepresentation::Code value;
  private:
    static const char *stringrep[];
};

class StepReversibleTopology : public StepSelect
{
  public:
  enum Code {
    reversible_topology_item,
    list_of_reversible_topology_item,
    set_of_reversible_topology_item };
  public:
    StepReversibleTopology() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 3, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepReversibleTopology::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepReversibleTopology::Code value;
  private:
    static const char *stringrep[];
};

class StepReversibleTopologyItem : public StepSelect
{
  public:
  enum Code {
    edge,
    path,
    face,
    face_bound,
    closed_shell,
    open_shell };
  public:
    StepReversibleTopologyItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 6, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepReversibleTopologyItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepReversibleTopologyItem::Code value;
  private:
    static const char *stringrep[];
};

class StepShapeDefinition : public StepSelect
{
  public:
  enum Code {
    product_definition_shape,
    shape_aspect,
    shape_aspect_relationship };
  public:
    StepShapeDefinition() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 3, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepShapeDefinition::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepShapeDefinition::Code value;
  private:
    static const char *stringrep[];
};

class StepShell : public StepSelect
{
  public:
  enum Code {
    vertex_shell,
    wire_shell,
    open_shell,
    closed_shell };
  public:
    StepShell() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 4, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepShell::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepShell::Code value;
  private:
    static const char *stringrep[];
};

class StepSiPrefix : public StepEnum
{
  public:
  typedef enum {
    exa,
    peta,
    tera,
    giga,
    mega,
    kilo,
    hecto,
    deca,
    deci,
    centi,
    milli,
    micro,
    nano,
    pico,
    femto,
    atto } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 16, stringrep, iv);
      value = (StepSiPrefix::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 16);
      os << stringrep[i];
    }
    bool operator== (const StepSiPrefix & a) const
      {return value == a.value;}
    bool operator!= (const StepSiPrefix & a) const
      {return value != a.value;}
    bool operator== (const StepSiPrefix::Code & a) const
      {return value == a;}
    bool operator!= (const StepSiPrefix::Code & a) const
      {return value != a;}
  public:
    StepSiPrefix::Code value;
  private:
    static const char *stringrep[];
};

class StepSiUnitName : public StepEnum
{
  public:
  typedef enum {
    metre,
    gram,
    second,
    ampere,
    kelvin,
    mole,
    candela,
    radian,
    steradian,
    hertz,
    newton,
    pascal,
    joule,
    watt,
    coulomb,
    volt,
    farad,
    ohm,
    siemens,
    weber,
    tesla,
    henry,
    degree_celsius,
    lumen,
    lux,
    becquerel,
    gray,
    sievert } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 28, stringrep, iv);
      value = (StepSiUnitName::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 28);
      os << stringrep[i];
    }
    bool operator== (const StepSiUnitName & a) const
      {return value == a.value;}
    bool operator!= (const StepSiUnitName & a) const
      {return value != a.value;}
    bool operator== (const StepSiUnitName::Code & a) const
      {return value == a;}
    bool operator!= (const StepSiUnitName::Code & a) const
      {return value != a;}
  public:
    StepSiUnitName::Code value;
  private:
    static const char *stringrep[];
};

class StepSource : public StepEnum
{
  public:
  typedef enum {
    made,
    bought,
    not_known } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 3, stringrep, iv);
      value = (StepSource::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 3);
      os << stringrep[i];
    }
    bool operator== (const StepSource & a) const
      {return value == a.value;}
    bool operator!= (const StepSource & a) const
      {return value != a.value;}
    bool operator== (const StepSource::Code & a) const
      {return value == a;}
    bool operator!= (const StepSource::Code & a) const
      {return value != a;}
  public:
    StepSource::Code value;
  private:
    static const char *stringrep[];
};

class StepSpecifiedItem : public StepSelect
{
  public:
  enum Code {
    product_definition,
    shape_aspect };
  public:
    StepSpecifiedItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepSpecifiedItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepSpecifiedItem::Code value;
  private:
    static const char *stringrep[];
};

class StepStartRequestItem : public StepSelect
{
  public:
  enum Code {
    product_definition_formation };
  public:
    StepStartRequestItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 1, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepStartRequestItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepStartRequestItem::Code value;
  private:
    static const char *stringrep[];
};

class StepSupportedItem : public StepSelect
{
  public:
  enum Code {
    action_directive,
    action,
    action_method };
  public:
    StepSupportedItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 3, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepSupportedItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepSupportedItem::Code value;
  private:
    static const char *stringrep[];
};

class StepSurfaceModel : public StepSelect
{
  public:
  enum Code {
    shell_based_surface_model };
  public:
    StepSurfaceModel() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 1, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepSurfaceModel::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepSurfaceModel::Code value;
  private:
    static const char *stringrep[];
};

class StepTransformation : public StepSelect
{
  public:
  enum Code {
    item_defined_transformation,
    functionally_defined_transformation };
  public:
    StepTransformation() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepTransformation::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepTransformation::Code value;
  private:
    static const char *stringrep[];
};

class StepTransitionCode : public StepEnum
{
  public:
  typedef enum {
    discontinuous,
    continuous,
    cont_same_gradient,
    cont_same_gradient_same_curvature } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 4, stringrep, iv);
      value = (StepTransitionCode::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 4);
      os << stringrep[i];
    }
    bool operator== (const StepTransitionCode & a) const
      {return value == a.value;}
    bool operator!= (const StepTransitionCode & a) const
      {return value != a.value;}
    bool operator== (const StepTransitionCode::Code & a) const
      {return value == a;}
    bool operator!= (const StepTransitionCode::Code & a) const
      {return value != a;}
  public:
    StepTransitionCode::Code value;
  private:
    static const char *stringrep[];
};

class StepTrimmingPreference : public StepEnum
{
  public:
  typedef enum {
    cartesian,
    parameter,
    unspecified } Code;
  public:
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 3, stringrep, iv);
      value = (StepTrimmingPreference::Code) iv;
      return ok;
    }
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 3);
      os << stringrep[i];
    }
    bool operator== (const StepTrimmingPreference & a) const
      {return value == a.value;}
    bool operator!= (const StepTrimmingPreference & a) const
      {return value != a.value;}
    bool operator== (const StepTrimmingPreference::Code & a) const
      {return value == a;}
    bool operator!= (const StepTrimmingPreference::Code & a) const
      {return value != a;}
  public:
    StepTrimmingPreference::Code value;
  private:
    static const char *stringrep[];
};

class StepTrimmingSelect : public StepSelect
{
  public:
  enum Code {
    cartesian_point,
    parameter_value };
  public:
    StepTrimmingSelect() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepTrimmingSelect::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepTrimmingSelect::Code value;
  private:
    static const char *stringrep[];
};

class StepUnit : public StepSelect
{
  public:
  enum Code {
    named_unit };
  public:
    StepUnit() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 1, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepUnit::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepUnit::Code value;
  private:
    static const char *stringrep[];
};

class StepVectorOrDirection : public StepSelect
{
  public:
  enum Code {
    vector,
    direction };
  public:
    StepVectorOrDirection() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepVectorOrDirection::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepVectorOrDirection::Code value;
  private:
    static const char *stringrep[];
};

class StepWireframeModel : public StepSelect
{
  public:
  enum Code {
    shell_based_wireframe_model,
    edge_based_wireframe_model };
  public:
    StepWireframeModel() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 2, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepWireframeModel::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepWireframeModel::Code value;
  private:
    static const char *stringrep[];
};

class StepWorkItem : public StepSelect
{
  public:
  enum Code {
    product_definition_formation };
  public:
    StepWorkItem() : StepSelect() {} 
    bool read(StepFileLine & line) {
      bool ok = StepSelect::read(line, 1, stringrep);
      if (ok and keyIndex >= 0) 
        value = (StepWorkItem::Code) keyIndex;
      return (type != NotSet);
    }
    void write(std::ostream & os) const {
      StepSelect::write(os, stringrep);
    }
  public:
    StepWorkItem::Code value;
  private:
    static const char *stringrep[];
};

class StepContractAssignment : public StepEntity
{
  public:
    StepContractAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_contract(0) {}
    virtual ~StepContractAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONTRACT_ASSIGNMENT";}
  public:
    StepID assigned_contract; // contract
};

StepEntity *step_create_contract_assignment(StepFileLine & line);

class StepRepresentationMap : public StepEntity
{
  public:
    StepRepresentationMap(StepID entityId=0) : StepEntity(entityId) , mapping_origin(0), mapped_representation(0) {}
    virtual ~StepRepresentationMap() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "REPRESENTATION_MAP";}
  public:
    StepID mapping_origin; // representation_item
    StepID mapped_representation; // representation
    std::vector<StepID> map_usage; // mapping_source
};

StepEntity *step_create_representation_map(StepFileLine & line);

class StepCertificationAssignment : public StepEntity
{
  public:
    StepCertificationAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_certification(0) {}
    virtual ~StepCertificationAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CERTIFICATION_ASSIGNMENT";}
  public:
    StepID assigned_certification; // certification
};

StepEntity *step_create_certification_assignment(StepFileLine & line);

class StepProductCategoryRelationship : public StepEntity
{
  public:
    StepProductCategoryRelationship(StepID entityId=0) : StepEntity(entityId) , category(0), sub_category(0) {}
    virtual ~StepProductCategoryRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_CATEGORY_RELATIONSHIP";}
  public:
    std::string name; // label
    std::string description; // text
    StepID category; // product_category
    StepID sub_category; // product_category
};

StepEntity *step_create_product_category_relationship(StepFileLine & line);

class StepFoundedItem : public StepEntity
{
  public:
    StepFoundedItem(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepFoundedItem() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "FOUNDED_ITEM";}
};

StepEntity *step_create_founded_item(StepFileLine & line);

class StepActionStatus : public StepEntity
{
  public:
    StepActionStatus(StepID entityId=0) : StepEntity(entityId) , assigned_action(0) {}
    virtual ~StepActionStatus() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ACTION_STATUS";}
  public:
    std::string status; // label
    StepID assigned_action; // executed_action
};

StepEntity *step_create_action_status(StepFileLine & line);

class StepProduct : public StepEntity
{
  public:
    StepProduct(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepProduct() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    std::vector<StepID> frame_of_reference; // product_context
};

StepEntity *step_create_product(StepFileLine & line);

class StepApprovalRelationship : public StepEntity
{
  public:
    StepApprovalRelationship(StepID entityId=0) : StepEntity(entityId) , relating_approval(0), related_approval(0) {}
    virtual ~StepApprovalRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPROVAL_RELATIONSHIP";}
  public:
    std::string name; // label
    std::string description; // text
    StepID relating_approval; // approval
    StepID related_approval; // approval
};

StepEntity *step_create_approval_relationship(StepFileLine & line);

class StepContract : public StepEntity
{
  public:
    StepContract(StepID entityId=0) : StepEntity(entityId) , kind(0) {}
    virtual ~StepContract() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONTRACT";}
  public:
    std::string name; // label
    std::string purpose; // text
    StepID kind; // contract_type
};

StepEntity *step_create_contract(StepFileLine & line);

class StepRepresentation : public StepEntity
{
  public:
    StepRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_representation(StepFileLine & line);

class StepCcDesignCertification : public StepEntity
{
  public:
    StepCcDesignCertification(StepID entityId=0) : StepEntity(entityId) , assigned_certification(0) {}
    virtual ~StepCcDesignCertification() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CC_DESIGN_CERTIFICATION";}
  public:
    StepID assigned_certification; // certification
    std::vector<StepCertifiedItem> items; // certified_item
};

StepEntity *step_create_cc_design_certification(StepFileLine & line);

class StepShapeRepresentation : public StepEntity
{
  public:
    StepShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SHAPE_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_shape_representation(StepFileLine & line);

class StepOrganization : public StepEntity
{
  public:
    StepOrganization(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepOrganization() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORGANIZATION";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
};

StepEntity *step_create_organization(StepFileLine & line);

class StepProductCategory : public StepEntity
{
  public:
    StepProductCategory(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepProductCategory() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_CATEGORY";}
  public:
    std::string name; // label
    std::string description; // text
};

StepEntity *step_create_product_category(StepFileLine & line);

class StepApprovalAssignment : public StepEntity
{
  public:
    StepApprovalAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_approval(0) {}
    virtual ~StepApprovalAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPROVAL_ASSIGNMENT";}
  public:
    StepID assigned_approval; // approval
};

StepEntity *step_create_approval_assignment(StepFileLine & line);

class StepConfigurationItem : public StepEntity
{
  public:
    StepConfigurationItem(StepID entityId=0) : StepEntity(entityId) , item_concept(0) {}
    virtual ~StepConfigurationItem() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONFIGURATION_ITEM";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID item_concept; // product_concept
    std::string purpose; // label
};

StepEntity *step_create_configuration_item(StepFileLine & line);

class StepProductRelatedProductCategory : public StepEntity
{
  public:
    StepProductRelatedProductCategory(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepProductRelatedProductCategory() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_RELATED_PRODUCT_CATEGORY";}
  public:
    std::string name; // label
    std::string description; // text
    std::vector<StepID> products; // product
};

StepEntity *step_create_product_related_product_category(StepFileLine & line);

class StepDateTimeRole : public StepEntity
{
  public:
    StepDateTimeRole(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepDateTimeRole() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DATE_TIME_ROLE";}
  public:
    std::string name; // label
};

StepEntity *step_create_date_time_role(StepFileLine & line);

class StepEffectivity : public StepEntity
{
  public:
    StepEffectivity(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepEffectivity() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "EFFECTIVITY";}
  public:
    std::string id; // identifier
};

StepEntity *step_create_effectivity(StepFileLine & line);

class StepApplicationContextElement : public StepEntity
{
  public:
    StepApplicationContextElement(StepID entityId=0) : StepEntity(entityId) , frame_of_reference(0) {}
    virtual ~StepApplicationContextElement() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPLICATION_CONTEXT_ELEMENT";}
  public:
    std::string name; // label
    StepID frame_of_reference; // application_context
};

StepEntity *step_create_application_context_element(StepFileLine & line);

class StepMeasureWithUnit : public StepEntity
{
  public:
    StepMeasureWithUnit(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepMeasureWithUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "MEASURE_WITH_UNIT";}
  public:
    StepMeasureValue value_component; // measure_value
    StepUnit unit_component; // unit
};

StepEntity *step_create_measure_with_unit(StepFileLine & line);

class StepDimensionalExponents : public StepEntity
{
  public:
    StepDimensionalExponents(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepDimensionalExponents() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DIMENSIONAL_EXPONENTS";}
  public:
    double length_exponent; // REAL
    double mass_exponent; // REAL
    double time_exponent; // REAL
    double electric_current_exponent; // REAL
    double thermodynamic_temperature_exponent; // REAL
    double amount_of_substance_exponent; // REAL
    double luminous_intensity_exponent; // REAL
};

StepEntity *step_create_dimensional_exponents(StepFileLine & line);

class StepSerialNumberedEffectivity : public StepEntity
{
  public:
    StepSerialNumberedEffectivity(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepSerialNumberedEffectivity() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SERIAL_NUMBERED_EFFECTIVITY";}
  public:
    std::string id; // identifier
    std::string effectivity_start_id; // identifier
    std::string effectivity_end_id; // identifier
};

StepEntity *step_create_serial_numbered_effectivity(StepFileLine & line);

class StepVersionedActionRequest : public StepEntity
{
  public:
    StepVersionedActionRequest(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepVersionedActionRequest() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "VERSIONED_ACTION_REQUEST";}
  public:
    std::string id; // identifier
    std::string version; // label
    std::string purpose; // text
    std::string description; // text
};

StepEntity *step_create_versioned_action_request(StepFileLine & line);

class StepAdvancedBrepShapeRepresentation : public StepEntity
{
  public:
    StepAdvancedBrepShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepAdvancedBrepShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ADVANCED_BREP_SHAPE_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_advanced_brep_shape_representation(StepFileLine & line);

class StepProductDefinitionContext : public StepEntity
{
  public:
    StepProductDefinitionContext(StepID entityId=0) : StepEntity(entityId) , frame_of_reference(0) {}
    virtual ~StepProductDefinitionContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION_CONTEXT";}
  public:
    std::string name; // label
    StepID frame_of_reference; // application_context
    std::string life_cycle_stage; // label
};

StepEntity *step_create_product_definition_context(StepFileLine & line);

class StepProductDefinitionEffectivity : public StepEntity
{
  public:
    StepProductDefinitionEffectivity(StepID entityId=0) : StepEntity(entityId) , usage(0) {}
    virtual ~StepProductDefinitionEffectivity() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION_EFFECTIVITY";}
  public:
    std::string id; // identifier
    StepID usage; // product_definition_relationship
};

StepEntity *step_create_product_definition_effectivity(StepFileLine & line);

class StepDocument : public StepEntity
{
  public:
    StepDocument(StepID entityId=0) : StepEntity(entityId) , kind(0) {}
    virtual ~StepDocument() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DOCUMENT";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID kind; // document_type
};

StepEntity *step_create_document(StepFileLine & line);

class StepGeometricallyBoundedSurfaceShapeRepresentation : public StepEntity
{
  public:
    StepGeometricallyBoundedSurfaceShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepGeometricallyBoundedSurfaceShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "GEOMETRICALLY_BOUNDED_SURFACE_SHAPE_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_geometrically_bounded_surface_shape_representation(StepFileLine & line);

class StepAddress : public StepEntity
{
  public:
    StepAddress(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepAddress() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ADDRESS";}
  public:
    std::string internal_location; // label
    std::string street_number; // label
    std::string street; // label
    std::string postal_box; // label
    std::string town; // label
    std::string region; // label
    std::string postal_code; // label
    std::string country; // label
    std::string facsimile_number; // label
    std::string telephone_number; // label
    std::string electronic_mail_address; // label
    std::string telex_number; // label
};

StepEntity *step_create_address(StepFileLine & line);

class StepMassMeasureWithUnit : public StepEntity
{
  public:
    StepMassMeasureWithUnit(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepMassMeasureWithUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "MASS_MEASURE_WITH_UNIT";}
  public:
    StepMeasureValue value_component; // measure_value
    StepUnit unit_component; // unit
};

StepEntity *step_create_mass_measure_with_unit(StepFileLine & line);

class StepPropertyDefinition : public StepEntity
{
  public:
    StepPropertyDefinition(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPropertyDefinition() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PROPERTY_DEFINITION";}
  public:
    std::string name; // label
    std::string description; // text
    StepCharacterizedDefinition definition; // characterized_definition
};

StepEntity *step_create_property_definition(StepFileLine & line);

class StepOrganizationalProject : public StepEntity
{
  public:
    StepOrganizationalProject(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepOrganizationalProject() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORGANIZATIONAL_PROJECT";}
  public:
    std::string name; // label
    std::string description; // text
    std::vector<StepID> responsible_organizations; // organization
};

StepEntity *step_create_organizational_project(StepFileLine & line);

class StepProductConcept : public StepEntity
{
  public:
    StepProductConcept(StepID entityId=0) : StepEntity(entityId) , market_context(0) {}
    virtual ~StepProductConcept() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_CONCEPT";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID market_context; // product_concept_context
};

StepEntity *step_create_product_concept(StepFileLine & line);

class StepEdgeBasedWireframeShapeRepresentation : public StepEntity
{
  public:
    StepEdgeBasedWireframeShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepEdgeBasedWireframeShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "EDGE_BASED_WIREFRAME_SHAPE_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_edge_based_wireframe_shape_representation(StepFileLine & line);

class StepContractType : public StepEntity
{
  public:
    StepContractType(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepContractType() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONTRACT_TYPE";}
  public:
    std::string description; // label
};

StepEntity *step_create_contract_type(StepFileLine & line);

class StepProductConceptContext : public StepEntity
{
  public:
    StepProductConceptContext(StepID entityId=0) : StepEntity(entityId) , frame_of_reference(0) {}
    virtual ~StepProductConceptContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_CONCEPT_CONTEXT";}
  public:
    std::string name; // label
    StepID frame_of_reference; // application_context
    std::string market_segment_type; // label
};

StepEntity *step_create_product_concept_context(StepFileLine & line);

class StepDate : public StepEntity
{
  public:
    StepDate(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepDate() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DATE";}
  public:
    int year_component; // year_number
};

StepEntity *step_create_date(StepFileLine & line);

class StepSecurityClassificationAssignment : public StepEntity
{
  public:
    StepSecurityClassificationAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_security_classification(0) {}
    virtual ~StepSecurityClassificationAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SECURITY_CLASSIFICATION_ASSIGNMENT";}
  public:
    StepID assigned_security_classification; // security_classification
};

StepEntity *step_create_security_classification_assignment(StepFileLine & line);

class StepPerson : public StepEntity
{
  public:
    StepPerson(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPerson() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PERSON";}
  public:
    std::string id; // identifier
    std::string last_name; // label
    std::string first_name; // label
    std::vector<std::string> middle_names; // label
    std::vector<std::string> prefix_titles; // label
    std::vector<std::string> suffix_titles; // label
};

StepEntity *step_create_person(StepFileLine & line);

class StepCcDesignContract : public StepEntity
{
  public:
    StepCcDesignContract(StepID entityId=0) : StepEntity(entityId) , assigned_contract(0) {}
    virtual ~StepCcDesignContract() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CC_DESIGN_CONTRACT";}
  public:
    StepID assigned_contract; // contract
    std::vector<StepContractedItem> items; // contracted_item
};

StepEntity *step_create_cc_design_contract(StepFileLine & line);

class StepApprovalStatus : public StepEntity
{
  public:
    StepApprovalStatus(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepApprovalStatus() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPROVAL_STATUS";}
  public:
    std::string name; // label
};

StepEntity *step_create_approval_status(StepFileLine & line);

class StepFacetedBrepShapeRepresentation : public StepEntity
{
  public:
    StepFacetedBrepShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepFacetedBrepShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "FACETED_BREP_SHAPE_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_faceted_brep_shape_representation(StepFileLine & line);

class StepSecurityClassificationLevel : public StepEntity
{
  public:
    StepSecurityClassificationLevel(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepSecurityClassificationLevel() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SECURITY_CLASSIFICATION_LEVEL";}
  public:
    std::string name; // label
};

StepEntity *step_create_security_classification_level(StepFileLine & line);

class StepDefinitionalRepresentation : public StepEntity
{
  public:
    StepDefinitionalRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepDefinitionalRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DEFINITIONAL_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_definitional_representation(StepFileLine & line);

class StepSurfacePatch : public StepEntity
{
  public:
    StepSurfacePatch(StepID entityId=0) : StepEntity(entityId) , parent_surface(0) {}
    virtual ~StepSurfacePatch() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SURFACE_PATCH";}
  public:
    StepID parent_surface; // bounded_surface
    StepTransitionCode u_transition; // transition_code
    StepTransitionCode v_transition; // transition_code
    bool u_sense; // BOOLEAN
    bool v_sense; // BOOLEAN
    std::vector<StepID> using_surfaces; // FOR
};

StepEntity *step_create_surface_patch(StepFileLine & line);

class StepCcDesignApproval : public StepEntity
{
  public:
    StepCcDesignApproval(StepID entityId=0) : StepEntity(entityId) , assigned_approval(0) {}
    virtual ~StepCcDesignApproval() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CC_DESIGN_APPROVAL";}
  public:
    StepID assigned_approval; // approval
    std::vector<StepApprovedItem> items; // approved_item
};

StepEntity *step_create_cc_design_approval(StepFileLine & line);

class StepWeekOfYearAndDayDate : public StepEntity
{
  public:
    StepWeekOfYearAndDayDate(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepWeekOfYearAndDayDate() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "WEEK_OF_YEAR_AND_DAY_DATE";}
  public:
    int year_component; // year_number
    int week_component; // week_in_year_number
    int day_component; // day_in_week_number
};

StepEntity *step_create_week_of_year_and_day_date(StepFileLine & line);

class StepDesignContext : public StepEntity
{
  public:
    StepDesignContext(StepID entityId=0) : StepEntity(entityId) , frame_of_reference(0) {}
    virtual ~StepDesignContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DESIGN_CONTEXT";}
  public:
    std::string name; // label
    StepID frame_of_reference; // application_context
    std::string life_cycle_stage; // label
};

StepEntity *step_create_design_context(StepFileLine & line);

class StepLocalTime : public StepEntity
{
  public:
    StepLocalTime(StepID entityId=0) : StepEntity(entityId) , zone(0) {}
    virtual ~StepLocalTime() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "LOCAL_TIME";}
  public:
    int hour_component; // hour_in_day
    int minute_component; // minute_in_hour
    double second_component; // second_in_minute
    StepID zone; // coordinated_universal_time_offset
};

StepEntity *step_create_local_time(StepFileLine & line);

class StepPropertyDefinitionRepresentation : public StepEntity
{
  public:
    StepPropertyDefinitionRepresentation(StepID entityId=0) : StepEntity(entityId) , definition(0), used_representation(0) {}
    virtual ~StepPropertyDefinitionRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PROPERTY_DEFINITION_REPRESENTATION";}
  public:
    StepID definition; // property_definition
    StepID used_representation; // representation
};

StepEntity *step_create_property_definition_representation(StepFileLine & line);

class StepActionRequestStatus : public StepEntity
{
  public:
    StepActionRequestStatus(StepID entityId=0) : StepEntity(entityId) , assigned_request(0) {}
    virtual ~StepActionRequestStatus() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ACTION_REQUEST_STATUS";}
  public:
    std::string status; // label
    StepID assigned_request; // versioned_action_request
};

StepEntity *step_create_action_request_status(StepFileLine & line);

class StepShapeDefinitionRepresentation : public StepEntity
{
  public:
    StepShapeDefinitionRepresentation(StepID entityId=0) : StepEntity(entityId) , definition(0), used_representation(0) {}
    virtual ~StepShapeDefinitionRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SHAPE_DEFINITION_REPRESENTATION";}
  public:
    StepID definition; // property_definition
    StepID used_representation; // representation
};

StepEntity *step_create_shape_definition_representation(StepFileLine & line);

class StepDocumentReference : public StepEntity
{
  public:
    StepDocumentReference(StepID entityId=0) : StepEntity(entityId) , assigned_document(0) {}
    virtual ~StepDocumentReference() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DOCUMENT_REFERENCE";}
  public:
    StepID assigned_document; // document
    std::string source; // label
};

StepEntity *step_create_document_reference(StepFileLine & line);

class StepNamedUnit : public StepEntity
{
  public:
    StepNamedUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepNamedUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "NAMED_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
};

StepEntity *step_create_named_unit(StepFileLine & line);

class StepActionRequestAssignment : public StepEntity
{
  public:
    StepActionRequestAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_action_request(0) {}
    virtual ~StepActionRequestAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ACTION_REQUEST_ASSIGNMENT";}
  public:
    StepID assigned_action_request; // versioned_action_request
};

StepEntity *step_create_action_request_assignment(StepFileLine & line);

class StepDateAndTime : public StepEntity
{
  public:
    StepDateAndTime(StepID entityId=0) : StepEntity(entityId) , date_component(0), time_component(0) {}
    virtual ~StepDateAndTime() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DATE_AND_TIME";}
  public:
    StepID date_component; // date
    StepID time_component; // local_time
};

StepEntity *step_create_date_and_time(StepFileLine & line);

class StepConfigurationDesign : public StepEntity
{
  public:
    StepConfigurationDesign(StepID entityId=0) : StepEntity(entityId) , configuration(0), design(0) {}
    virtual ~StepConfigurationDesign() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONFIGURATION_DESIGN";}
  public:
    StepID configuration; // configuration_item
    StepID design; // product_definition_formation
};

StepEntity *step_create_configuration_design(StepFileLine & line);

class StepContextDependentShapeRepresentation : public StepEntity
{
  public:
    StepContextDependentShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , representation_relation(0), represented_product_relation(0) {}
    virtual ~StepContextDependentShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONTEXT_DEPENDENT_SHAPE_REPRESENTATION";}
  public:
    StepID representation_relation; // shape_representation_relationship
    StepID represented_product_relation; // product_definition_shape
};

StepEntity *step_create_context_dependent_shape_representation(StepFileLine & line);

class StepRepresentationItem : public StepEntity
{
  public:
    StepRepresentationItem(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepRepresentationItem() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "REPRESENTATION_ITEM";}
  public:
    std::string name; // label
};

StepEntity *step_create_representation_item(StepFileLine & line);

class StepApplicationContext : public StepEntity
{
  public:
    StepApplicationContext(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepApplicationContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPLICATION_CONTEXT";}
  public:
    std::string application; // text
    std::vector<StepID> context_elements; // FOR
};

StepEntity *step_create_application_context(StepFileLine & line);

class StepOrdinalDate : public StepEntity
{
  public:
    StepOrdinalDate(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepOrdinalDate() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORDINAL_DATE";}
  public:
    int year_component; // year_number
    int day_component; // day_in_year_number
};

StepEntity *step_create_ordinal_date(StepFileLine & line);

class StepCertificationType : public StepEntity
{
  public:
    StepCertificationType(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepCertificationType() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CERTIFICATION_TYPE";}
  public:
    std::string description; // label
};

StepEntity *step_create_certification_type(StepFileLine & line);

class StepItemDefinedTransformation : public StepEntity
{
  public:
    StepItemDefinedTransformation(StepID entityId=0) : StepEntity(entityId) , transform_item_1(0), transform_item_2(0) {}
    virtual ~StepItemDefinedTransformation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ITEM_DEFINED_TRANSFORMATION";}
  public:
    std::string name; // label
    std::string description; // text
    StepID transform_item_1; // representation_item
    StepID transform_item_2; // representation_item
};

StepEntity *step_create_item_defined_transformation(StepFileLine & line);

class StepConfigurationEffectivity : public StepEntity
{
  public:
    StepConfigurationEffectivity(StepID entityId=0) : StepEntity(entityId) , usage(0), configuration(0) {}
    virtual ~StepConfigurationEffectivity() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONFIGURATION_EFFECTIVITY";}
  public:
    std::string id; // identifier
    StepID usage; // product_definition_relationship
    StepID configuration; // configuration_design
};

StepEntity *step_create_configuration_effectivity(StepFileLine & line);

class StepDocumentWithClass : public StepEntity
{
  public:
    StepDocumentWithClass(StepID entityId=0) : StepEntity(entityId) , kind(0) {}
    virtual ~StepDocumentWithClass() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DOCUMENT_WITH_CLASS";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID kind; // document_type
    std::string identifier_class; // identifier
};

StepEntity *step_create_document_with_class(StepFileLine & line);

class StepProductContext : public StepEntity
{
  public:
    StepProductContext(StepID entityId=0) : StepEntity(entityId) , frame_of_reference(0) {}
    virtual ~StepProductContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_CONTEXT";}
  public:
    std::string name; // label
    StepID frame_of_reference; // application_context
    std::string discipline_type; // label
};

StepEntity *step_create_product_context(StepFileLine & line);

class StepDocumentUsageConstraint : public StepEntity
{
  public:
    StepDocumentUsageConstraint(StepID entityId=0) : StepEntity(entityId) , source(0) {}
    virtual ~StepDocumentUsageConstraint() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DOCUMENT_USAGE_CONSTRAINT";}
  public:
    StepID source; // document
    std::string subject_element; // label
    std::string subject_element_value; // text
};

StepEntity *step_create_document_usage_constraint(StepFileLine & line);

class StepCcDesignSpecificationReference : public StepEntity
{
  public:
    StepCcDesignSpecificationReference(StepID entityId=0) : StepEntity(entityId) , assigned_document(0) {}
    virtual ~StepCcDesignSpecificationReference() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CC_DESIGN_SPECIFICATION_REFERENCE";}
  public:
    StepID assigned_document; // document
    std::string source; // label
    std::vector<StepSpecifiedItem> items; // specified_item
};

StepEntity *step_create_cc_design_specification_reference(StepFileLine & line);

class StepFunctionallyDefinedTransformation : public StepEntity
{
  public:
    StepFunctionallyDefinedTransformation(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepFunctionallyDefinedTransformation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "FUNCTIONALLY_DEFINED_TRANSFORMATION";}
  public:
    std::string name; // label
    std::string description; // text
};

StepEntity *step_create_functionally_defined_transformation(StepFileLine & line);

class StepPersonalAddress : public StepEntity
{
  public:
    StepPersonalAddress(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPersonalAddress() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PERSONAL_ADDRESS";}
  public:
    std::string internal_location; // label
    std::string street_number; // label
    std::string street; // label
    std::string postal_box; // label
    std::string town; // label
    std::string region; // label
    std::string postal_code; // label
    std::string country; // label
    std::string facsimile_number; // label
    std::string telephone_number; // label
    std::string electronic_mail_address; // label
    std::string telex_number; // label
    std::vector<StepID> people; // person
    std::string description; // text
};

StepEntity *step_create_personal_address(StepFileLine & line);

class StepVolumeMeasureWithUnit : public StepEntity
{
  public:
    StepVolumeMeasureWithUnit(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepVolumeMeasureWithUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "VOLUME_MEASURE_WITH_UNIT";}
  public:
    StepMeasureValue value_component; // measure_value
    StepUnit unit_component; // unit
};

StepEntity *step_create_volume_measure_with_unit(StepFileLine & line);

class StepManifoldSurfaceShapeRepresentation : public StepEntity
{
  public:
    StepManifoldSurfaceShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepManifoldSurfaceShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "MANIFOLD_SURFACE_SHAPE_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_manifold_surface_shape_representation(StepFileLine & line);

class StepShapeAspectRelationship : public StepEntity
{
  public:
    StepShapeAspectRelationship(StepID entityId=0) : StepEntity(entityId) , relating_shape_aspect(0), related_shape_aspect(0) {}
    virtual ~StepShapeAspectRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SHAPE_ASPECT_RELATIONSHIP";}
  public:
    std::string name; // label
    std::string description; // text
    StepID relating_shape_aspect; // shape_aspect
    StepID related_shape_aspect; // shape_aspect
};

StepEntity *step_create_shape_aspect_relationship(StepFileLine & line);

class StepCalendarDate : public StepEntity
{
  public:
    StepCalendarDate(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepCalendarDate() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CALENDAR_DATE";}
  public:
    int year_component; // year_number
    int day_component; // day_in_month_number
    int month_component; // month_in_year_number
};

StepEntity *step_create_calendar_date(StepFileLine & line);

class StepPersonAndOrganizationAssignment : public StepEntity
{
  public:
    StepPersonAndOrganizationAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_person_and_organization(0), role(0) {}
    virtual ~StepPersonAndOrganizationAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PERSON_AND_ORGANIZATION_ASSIGNMENT";}
  public:
    StepID assigned_person_and_organization; // person_and_organization
    StepID role; // person_and_organization_role
};

StepEntity *step_create_person_and_organization_assignment(StepFileLine & line);

class StepActionAssignment : public StepEntity
{
  public:
    StepActionAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_action(0) {}
    virtual ~StepActionAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ACTION_ASSIGNMENT";}
  public:
    StepID assigned_action; // action
};

StepEntity *step_create_action_assignment(StepFileLine & line);

class StepShapeAspect : public StepEntity
{
  public:
    StepShapeAspect(StepID entityId=0) : StepEntity(entityId) , of_shape(0) {}
    virtual ~StepShapeAspect() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SHAPE_ASPECT";}
  public:
    std::string name; // label
    std::string description; // text
    StepID of_shape; // product_definition_shape
    StepLogical product_definitional; // LOGICAL
};

StepEntity *step_create_shape_aspect(StepFileLine & line);

class StepLengthMeasureWithUnit : public StepEntity
{
  public:
    StepLengthMeasureWithUnit(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepLengthMeasureWithUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "LENGTH_MEASURE_WITH_UNIT";}
  public:
    StepMeasureValue value_component; // measure_value
    StepUnit unit_component; // unit
};

StepEntity *step_create_length_measure_with_unit(StepFileLine & line);

class StepAlternateProductRelationship : public StepEntity
{
  public:
    StepAlternateProductRelationship(StepID entityId=0) : StepEntity(entityId) , alternate(0), base(0) {}
    virtual ~StepAlternateProductRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ALTERNATE_PRODUCT_RELATIONSHIP";}
  public:
    std::string name; // label
    std::string definition; // text
    StepID alternate; // product
    StepID base; // product
    std::string basis; // text
};

StepEntity *step_create_alternate_product_relationship(StepFileLine & line);

class StepDocumentRelationship : public StepEntity
{
  public:
    StepDocumentRelationship(StepID entityId=0) : StepEntity(entityId) , relating_document(0), related_document(0) {}
    virtual ~StepDocumentRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DOCUMENT_RELATIONSHIP";}
  public:
    std::string name; // label
    std::string description; // text
    StepID relating_document; // document
    StepID related_document; // document
};

StepEntity *step_create_document_relationship(StepFileLine & line);

class StepActionDirective : public StepEntity
{
  public:
    StepActionDirective(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepActionDirective() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ACTION_DIRECTIVE";}
  public:
    std::string name; // label
    std::string description; // text
    std::string analysis; // text
    std::string comment; // text
    std::vector<StepID> requests; // versioned_action_request
};

StepEntity *step_create_action_directive(StepFileLine & line);

class StepApplicationProtocolDefinition : public StepEntity
{
  public:
    StepApplicationProtocolDefinition(StepID entityId=0) : StepEntity(entityId) , application(0) {}
    virtual ~StepApplicationProtocolDefinition() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPLICATION_PROTOCOL_DEFINITION";}
  public:
    std::string status; // label
    std::string application_interpreted_model_schema_name; // label
    int application_protocol_year; // year_number
    StepID application; // application_context
};

StepEntity *step_create_application_protocol_definition(StepFileLine & line);

class StepProductDefinition : public StepEntity
{
  public:
    StepProductDefinition(StepID entityId=0) : StepEntity(entityId) , formation(0), frame_of_reference(0) {}
    virtual ~StepProductDefinition() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION";}
  public:
    std::string id; // identifier
    std::string description; // text
    StepID formation; // product_definition_formation
    StepID frame_of_reference; // product_definition_context
};

StepEntity *step_create_product_definition(StepFileLine & line);

class StepLotEffectivity : public StepEntity
{
  public:
    StepLotEffectivity(StepID entityId=0) : StepEntity(entityId) , effectivity_lot_size(0) {}
    virtual ~StepLotEffectivity() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "LOT_EFFECTIVITY";}
  public:
    std::string id; // identifier
    std::string effectivity_lot_id; // identifier
    StepID effectivity_lot_size; // measure_with_unit
};

StepEntity *step_create_lot_effectivity(StepFileLine & line);

class StepShellBasedWireframeShapeRepresentation : public StepEntity
{
  public:
    StepShellBasedWireframeShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepShellBasedWireframeShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SHELL_BASED_WIREFRAME_SHAPE_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_shell_based_wireframe_shape_representation(StepFileLine & line);

class StepCoordinatedUniversalTimeOffset : public StepEntity
{
  public:
    StepCoordinatedUniversalTimeOffset(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepCoordinatedUniversalTimeOffset() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "COORDINATED_UNIVERSAL_TIME_OFFSET";}
  public:
    int hour_offset; // hour_in_day
    int minute_offset; // minute_in_hour
    StepAheadOrBehind sense; // ahead_or_behind
};

StepEntity *step_create_coordinated_universal_time_offset(StepFileLine & line);

class StepApprovalPersonOrganization : public StepEntity
{
  public:
    StepApprovalPersonOrganization(StepID entityId=0) : StepEntity(entityId) , authorized_approval(0), role(0) {}
    virtual ~StepApprovalPersonOrganization() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPROVAL_PERSON_ORGANIZATION";}
  public:
    StepPersonOrganizationSelect person_organization; // person_organization_select
    StepID authorized_approval; // approval
    StepID role; // approval_role
};

StepEntity *step_create_approval_person_organization(StepFileLine & line);

class StepSolidAngleMeasureWithUnit : public StepEntity
{
  public:
    StepSolidAngleMeasureWithUnit(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepSolidAngleMeasureWithUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SOLID_ANGLE_MEASURE_WITH_UNIT";}
  public:
    StepMeasureValue value_component; // measure_value
    StepUnit unit_component; // unit
};

StepEntity *step_create_solid_angle_measure_with_unit(StepFileLine & line);

class StepSecurityClassification : public StepEntity
{
  public:
    StepSecurityClassification(StepID entityId=0) : StepEntity(entityId) , security_level(0) {}
    virtual ~StepSecurityClassification() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SECURITY_CLASSIFICATION";}
  public:
    std::string name; // label
    std::string purpose; // text
    StepID security_level; // security_classification_level
};

StepEntity *step_create_security_classification(StepFileLine & line);

class StepPlaneAngleMeasureWithUnit : public StepEntity
{
  public:
    StepPlaneAngleMeasureWithUnit(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPlaneAngleMeasureWithUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PLANE_ANGLE_MEASURE_WITH_UNIT";}
  public:
    StepMeasureValue value_component; // measure_value
    StepUnit unit_component; // unit
};

StepEntity *step_create_plane_angle_measure_with_unit(StepFileLine & line);

class StepProductDefinitionRelationship : public StepEntity
{
  public:
    StepProductDefinitionRelationship(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0) {}
    virtual ~StepProductDefinitionRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION_RELATIONSHIP";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
};

StepEntity *step_create_product_definition_relationship(StepFileLine & line);

class StepRepresentationContext : public StepEntity
{
  public:
    StepRepresentationContext(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepRepresentationContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "REPRESENTATION_CONTEXT";}
  public:
    std::string context_identifier; // identifier
    std::string context_type; // text
    std::vector<StepID> representations_in_context; // FOR
};

StepEntity *step_create_representation_context(StepFileLine & line);

class StepDatedEffectivity : public StepEntity
{
  public:
    StepDatedEffectivity(StepID entityId=0) : StepEntity(entityId) , effectivity_start_date(0), effectivity_end_date(0) {}
    virtual ~StepDatedEffectivity() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DATED_EFFECTIVITY";}
  public:
    std::string id; // identifier
    StepID effectivity_start_date; // date_and_time
    StepID effectivity_end_date; // date_and_time
};

StepEntity *step_create_dated_effectivity(StepFileLine & line);

class StepCompositeCurveSegment : public StepEntity
{
  public:
    StepCompositeCurveSegment(StepID entityId=0) : StepEntity(entityId) , parent_curve(0) {}
    virtual ~StepCompositeCurveSegment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "COMPOSITE_CURVE_SEGMENT";}
  public:
    StepTransitionCode transition; // transition_code
    bool same_sense; // BOOLEAN
    StepID parent_curve; // curve
    std::vector<StepID> using_curves; // segments
};

StepEntity *step_create_composite_curve_segment(StepFileLine & line);

class StepSolidAngleUnit : public StepEntity
{
  public:
    StepSolidAngleUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepSolidAngleUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SOLID_ANGLE_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
};

StepEntity *step_create_solid_angle_unit(StepFileLine & line);

class StepActionMethod : public StepEntity
{
  public:
    StepActionMethod(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepActionMethod() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ACTION_METHOD";}
  public:
    std::string name; // label
    std::string description; // text
    std::string consequence; // text
    std::string purpose; // text
};

StepEntity *step_create_action_method(StepFileLine & line);

class StepOrganizationRelationship : public StepEntity
{
  public:
    StepOrganizationRelationship(StepID entityId=0) : StepEntity(entityId) , relating_organization(0), related_organization(0) {}
    virtual ~StepOrganizationRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORGANIZATION_RELATIONSHIP";}
  public:
    std::string name; // label
    std::string description; // text
    StepID relating_organization; // organization
    StepID related_organization; // organization
};

StepEntity *step_create_organization_relationship(StepFileLine & line);

class StepStartRequest : public StepEntity
{
  public:
    StepStartRequest(StepID entityId=0) : StepEntity(entityId) , assigned_action_request(0) {}
    virtual ~StepStartRequest() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "START_REQUEST";}
  public:
    StepID assigned_action_request; // versioned_action_request
    std::vector<StepStartRequestItem> items; // start_request_item
};

StepEntity *step_create_start_request(StepFileLine & line);

class StepAction : public StepEntity
{
  public:
    StepAction(StepID entityId=0) : StepEntity(entityId) , chosen_method(0) {}
    virtual ~StepAction() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ACTION";}
  public:
    std::string name; // label
    std::string description; // text
    StepID chosen_method; // action_method
};

StepEntity *step_create_action(StepFileLine & line);

class StepChange : public StepEntity
{
  public:
    StepChange(StepID entityId=0) : StepEntity(entityId) , assigned_action(0) {}
    virtual ~StepChange() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CHANGE";}
  public:
    StepID assigned_action; // action
    std::vector<StepWorkItem> items; // work_item
};

StepEntity *step_create_change(StepFileLine & line);

class StepChangeRequest : public StepEntity
{
  public:
    StepChangeRequest(StepID entityId=0) : StepEntity(entityId) , assigned_action_request(0) {}
    virtual ~StepChangeRequest() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CHANGE_REQUEST";}
  public:
    StepID assigned_action_request; // versioned_action_request
    std::vector<StepChangeRequestItem> items; // change_request_item
};

StepEntity *step_create_change_request(StepFileLine & line);

class StepAreaMeasureWithUnit : public StepEntity
{
  public:
    StepAreaMeasureWithUnit(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepAreaMeasureWithUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "AREA_MEASURE_WITH_UNIT";}
  public:
    StepMeasureValue value_component; // measure_value
    StepUnit unit_component; // unit
};

StepEntity *step_create_area_measure_with_unit(StepFileLine & line);

class StepApprovalDateTime : public StepEntity
{
  public:
    StepApprovalDateTime(StepID entityId=0) : StepEntity(entityId) , dated_approval(0) {}
    virtual ~StepApprovalDateTime() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPROVAL_DATE_TIME";}
  public:
    StepDateTimeSelect date_time; // date_time_select
    StepID dated_approval; // approval
};

StepEntity *step_create_approval_date_time(StepFileLine & line);

class StepApprovalRole : public StepEntity
{
  public:
    StepApprovalRole(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepApprovalRole() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPROVAL_ROLE";}
  public:
    std::string role; // label
};

StepEntity *step_create_approval_role(StepFileLine & line);

class StepPersonAndOrganizationRole : public StepEntity
{
  public:
    StepPersonAndOrganizationRole(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPersonAndOrganizationRole() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PERSON_AND_ORGANIZATION_ROLE";}
  public:
    std::string name; // label
};

StepEntity *step_create_person_and_organization_role(StepFileLine & line);

class StepVolumeUnit : public StepEntity
{
  public:
    StepVolumeUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepVolumeUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "VOLUME_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
};

StepEntity *step_create_volume_unit(StepFileLine & line);

class StepProductDefinitionFormation : public StepEntity
{
  public:
    StepProductDefinitionFormation(StepID entityId=0) : StepEntity(entityId) , of_product(0) {}
    virtual ~StepProductDefinitionFormation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION_FORMATION";}
  public:
    std::string id; // identifier
    std::string description; // text
    StepID of_product; // product
};

StepEntity *step_create_product_definition_formation(StepFileLine & line);

class StepApproval : public StepEntity
{
  public:
    StepApproval(StepID entityId=0) : StepEntity(entityId) , status(0) {}
    virtual ~StepApproval() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "APPROVAL";}
  public:
    StepID status; // approval_status
    std::string level; // label
};

StepEntity *step_create_approval(StepFileLine & line);

class StepTopologicalRepresentationItem : public StepEntity
{
  public:
    StepTopologicalRepresentationItem(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepTopologicalRepresentationItem() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "TOPOLOGICAL_REPRESENTATION_ITEM";}
  public:
    std::string name; // label
};

StepEntity *step_create_topological_representation_item(StepFileLine & line);

class StepProductDefinitionUsage : public StepEntity
{
  public:
    StepProductDefinitionUsage(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0) {}
    virtual ~StepProductDefinitionUsage() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION_USAGE";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
};

StepEntity *step_create_product_definition_usage(StepFileLine & line);

class StepActionRequestSolution : public StepEntity
{
  public:
    StepActionRequestSolution(StepID entityId=0) : StepEntity(entityId) , method(0), request(0) {}
    virtual ~StepActionRequestSolution() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ACTION_REQUEST_SOLUTION";}
  public:
    StepID method; // action_method
    StepID request; // versioned_action_request
};

StepEntity *step_create_action_request_solution(StepFileLine & line);

class StepRepresentationRelationship : public StepEntity
{
  public:
    StepRepresentationRelationship(StepID entityId=0) : StepEntity(entityId) , rep_1(0), rep_2(0) {}
    virtual ~StepRepresentationRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "REPRESENTATION_RELATIONSHIP";}
  public:
    std::string name; // label
    std::string description; // text
    StepID rep_1; // representation
    StepID rep_2; // representation
};

StepEntity *step_create_representation_relationship(StepFileLine & line);

class StepDocumentType : public StepEntity
{
  public:
    StepDocumentType(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepDocumentType() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DOCUMENT_TYPE";}
  public:
    std::string product_data_type; // label
};

StepEntity *step_create_document_type(StepFileLine & line);

class StepDateAndTimeAssignment : public StepEntity
{
  public:
    StepDateAndTimeAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_date_and_time(0), role(0) {}
    virtual ~StepDateAndTimeAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DATE_AND_TIME_ASSIGNMENT";}
  public:
    StepID assigned_date_and_time; // date_and_time
    StepID role; // date_time_role
};

StepEntity *step_create_date_and_time_assignment(StepFileLine & line);

class StepPersonAndOrganization : public StepEntity
{
  public:
    StepPersonAndOrganization(StepID entityId=0) : StepEntity(entityId) , the_person(0), the_organization(0) {}
    virtual ~StepPersonAndOrganization() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PERSON_AND_ORGANIZATION";}
  public:
    StepID the_person; // person
    StepID the_organization; // organization
};

StepEntity *step_create_person_and_organization(StepFileLine & line);

class StepCertification : public StepEntity
{
  public:
    StepCertification(StepID entityId=0) : StepEntity(entityId) , kind(0) {}
    virtual ~StepCertification() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CERTIFICATION";}
  public:
    std::string name; // label
    std::string purpose; // text
    StepID kind; // certification_type
};

StepEntity *step_create_certification(StepFileLine & line);

class StepVertex : public StepEntity
{
  public:
    StepVertex(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepVertex() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "VERTEX";}
  public:
    std::string name; // label
};

StepEntity *step_create_vertex(StepFileLine & line);

class StepProductDefinitionShape : public StepEntity
{
  public:
    StepProductDefinitionShape(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepProductDefinitionShape() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION_SHAPE";}
  public:
    std::string name; // label
    std::string description; // text
    StepCharacterizedDefinition definition; // characterized_definition
};

StepEntity *step_create_product_definition_shape(StepFileLine & line);

class StepAssemblyComponentUsageSubstitute : public StepEntity
{
  public:
    StepAssemblyComponentUsageSubstitute(StepID entityId=0) : StepEntity(entityId) , base(0), substitute(0) {}
    virtual ~StepAssemblyComponentUsageSubstitute() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ASSEMBLY_COMPONENT_USAGE_SUBSTITUTE";}
  public:
    std::string name; // label
    std::string definition; // text
    StepID base; // assembly_component_usage
    StepID substitute; // assembly_component_usage
};

StepEntity *step_create_assembly_component_usage_substitute(StepFileLine & line);

class StepConversionBasedUnit : public StepEntity
{
  public:
    StepConversionBasedUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0), conversion_factor(0) {}
    virtual ~StepConversionBasedUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONVERSION_BASED_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
    std::string name; // label
    StepID conversion_factor; // measure_with_unit
};

StepEntity *step_create_conversion_based_unit(StepFileLine & line);

class StepExecutedAction : public StepEntity
{
  public:
    StepExecutedAction(StepID entityId=0) : StepEntity(entityId) , chosen_method(0) {}
    virtual ~StepExecutedAction() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "EXECUTED_ACTION";}
  public:
    std::string name; // label
    std::string description; // text
    StepID chosen_method; // action_method
};

StepEntity *step_create_executed_action(StepFileLine & line);

class StepCcDesignSecurityClassification : public StepEntity
{
  public:
    StepCcDesignSecurityClassification(StepID entityId=0) : StepEntity(entityId) , assigned_security_classification(0) {}
    virtual ~StepCcDesignSecurityClassification() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CC_DESIGN_SECURITY_CLASSIFICATION";}
  public:
    StepID assigned_security_classification; // security_classification
    std::vector<StepClassifiedItem> items; // classified_item
};

StepEntity *step_create_cc_design_security_classification(StepFileLine & line);

class StepEdge : public StepEntity
{
  public:
    StepEdge(StepID entityId=0) : StepEntity(entityId) , edge_start(0), edge_end(0) {}
    virtual ~StepEdge() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "EDGE";}
  public:
    std::string name; // label
    StepID edge_start; // vertex
    StepID edge_end; // vertex
};

StepEntity *step_create_edge(StepFileLine & line);

class StepSuppliedPartRelationship : public StepEntity
{
  public:
    StepSuppliedPartRelationship(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0) {}
    virtual ~StepSuppliedPartRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SUPPLIED_PART_RELATIONSHIP";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
};

StepEntity *step_create_supplied_part_relationship(StepFileLine & line);

class StepStartWork : public StepEntity
{
  public:
    StepStartWork(StepID entityId=0) : StepEntity(entityId) , assigned_action(0) {}
    virtual ~StepStartWork() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "START_WORK";}
  public:
    StepID assigned_action; // action
    std::vector<StepWorkItem> items; // work_item
};

StepEntity *step_create_start_work(StepFileLine & line);

class StepOrganizationalAddress : public StepEntity
{
  public:
    StepOrganizationalAddress(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepOrganizationalAddress() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORGANIZATIONAL_ADDRESS";}
  public:
    std::string internal_location; // label
    std::string street_number; // label
    std::string street; // label
    std::string postal_box; // label
    std::string town; // label
    std::string region; // label
    std::string postal_code; // label
    std::string country; // label
    std::string facsimile_number; // label
    std::string telephone_number; // label
    std::string electronic_mail_address; // label
    std::string telex_number; // label
    std::vector<StepID> organizations; // organization
    std::string description; // text
};

StepEntity *step_create_organizational_address(StepFileLine & line);

class StepMappedItem : public StepEntity
{
  public:
    StepMappedItem(StepID entityId=0) : StepEntity(entityId) , mapping_source(0), mapping_target(0) {}
    virtual ~StepMappedItem() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "MAPPED_ITEM";}
  public:
    std::string name; // label
    StepID mapping_source; // representation_map
    StepID mapping_target; // representation_item
};

StepEntity *step_create_mapped_item(StepFileLine & line);

class StepGlobalUnitAssignedContext : public StepEntity
{
  public:
    StepGlobalUnitAssignedContext(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepGlobalUnitAssignedContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "GLOBAL_UNIT_ASSIGNED_CONTEXT";}
  public:
    std::string context_identifier; // identifier
    std::string context_type; // text
    std::vector<StepID> representations_in_context; // FOR
    std::vector<StepUnit> units; // unit
};

StepEntity *step_create_global_unit_assigned_context(StepFileLine & line);

class StepReparametrisedCompositeCurveSegment : public StepEntity
{
  public:
    StepReparametrisedCompositeCurveSegment(StepID entityId=0) : StepEntity(entityId) , parent_curve(0) {}
    virtual ~StepReparametrisedCompositeCurveSegment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "REPARAMETRISED_COMPOSITE_CURVE_SEGMENT";}
  public:
    StepTransitionCode transition; // transition_code
    bool same_sense; // BOOLEAN
    StepID parent_curve; // curve
    std::vector<StepID> using_curves; // segments
    double param_length; // parameter_value
};

StepEntity *step_create_reparametrised_composite_curve_segment(StepFileLine & line);

class StepLoop : public StepEntity
{
  public:
    StepLoop(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepLoop() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "LOOP";}
  public:
    std::string name; // label
};

StepEntity *step_create_loop(StepFileLine & line);

class StepProductDefinitionFormationWithSpecifiedSource : public StepEntity
{
  public:
    StepProductDefinitionFormationWithSpecifiedSource(StepID entityId=0) : StepEntity(entityId) , of_product(0) {}
    virtual ~StepProductDefinitionFormationWithSpecifiedSource() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE";}
  public:
    std::string id; // identifier
    std::string description; // text
    StepID of_product; // product
    StepSource make_or_buy; // source
};

StepEntity *step_create_product_definition_formation_with_specified_source(StepFileLine & line);

class StepProductDefinitionWithAssociatedDocuments : public StepEntity
{
  public:
    StepProductDefinitionWithAssociatedDocuments(StepID entityId=0) : StepEntity(entityId) , formation(0), frame_of_reference(0) {}
    virtual ~StepProductDefinitionWithAssociatedDocuments() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PRODUCT_DEFINITION_WITH_ASSOCIATED_DOCUMENTS";}
  public:
    std::string id; // identifier
    std::string description; // text
    StepID formation; // product_definition_formation
    StepID frame_of_reference; // product_definition_context
    std::vector<StepID> documentation_ids; // document
};

StepEntity *step_create_product_definition_with_associated_documents(StepFileLine & line);

class StepPlaneAngleUnit : public StepEntity
{
  public:
    StepPlaneAngleUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepPlaneAngleUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PLANE_ANGLE_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
};

StepEntity *step_create_plane_angle_unit(StepFileLine & line);

class StepLengthUnit : public StepEntity
{
  public:
    StepLengthUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepLengthUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "LENGTH_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
};

StepEntity *step_create_length_unit(StepFileLine & line);

class StepAreaUnit : public StepEntity
{
  public:
    StepAreaUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepAreaUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "AREA_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
};

StepEntity *step_create_area_unit(StepFileLine & line);

class StepGeometricRepresentationContext : public StepEntity
{
  public:
    StepGeometricRepresentationContext(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepGeometricRepresentationContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "GEOMETRIC_REPRESENTATION_CONTEXT";}
  public:
    std::string context_identifier; // identifier
    std::string context_type; // text
    std::vector<StepID> representations_in_context; // FOR
    int coordinate_space_dimension; // dimension_count
};

StepEntity *step_create_geometric_representation_context(StepFileLine & line);

class StepWireShell : public StepEntity
{
  public:
    StepWireShell(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepWireShell() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "WIRE_SHELL";}
  public:
    std::string name; // label
    std::vector<StepID> wire_shell_extent; // loop
};

StepEntity *step_create_wire_shell(StepFileLine & line);

class StepAssemblyComponentUsage : public StepEntity
{
  public:
    StepAssemblyComponentUsage(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0) {}
    virtual ~StepAssemblyComponentUsage() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ASSEMBLY_COMPONENT_USAGE";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
    std::string reference_designator; // identifier
};

StepEntity *step_create_assembly_component_usage(StepFileLine & line);

class StepFace : public StepEntity
{
  public:
    StepFace(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepFace() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "FACE";}
  public:
    std::string name; // label
    std::vector<StepID> bounds; // face_bound
};

StepEntity *step_create_face(StepFileLine & line);

class StepSiUnit : public StepEntity
{
  public:
    StepSiUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepSiUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SI_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
    StepSiPrefix prefix; // si_prefix
    StepSiUnitName name; // si_unit_name
};

StepEntity *step_create_si_unit(StepFileLine & line);

class StepUncertaintyMeasureWithUnit : public StepEntity
{
  public:
    StepUncertaintyMeasureWithUnit(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepUncertaintyMeasureWithUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "UNCERTAINTY_MEASURE_WITH_UNIT";}
  public:
    StepMeasureValue value_component; // measure_value
    StepUnit unit_component; // unit
    std::string name; // label
    std::string description; // text
};

StepEntity *step_create_uncertainty_measure_with_unit(StepFileLine & line);

class StepPath : public StepEntity
{
  public:
    StepPath(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPath() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PATH";}
  public:
    std::string name; // label
    std::vector<StepID> edge_list; // oriented_edge
};

StepEntity *step_create_path(StepFileLine & line);

class StepConnectedFaceSet : public StepEntity
{
  public:
    StepConnectedFaceSet(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepConnectedFaceSet() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONNECTED_FACE_SET";}
  public:
    std::string name; // label
    std::vector<StepID> cfs_faces; // face
};

StepEntity *step_create_connected_face_set(StepFileLine & line);

class StepOrientedFace : public StepEntity
{
  public:
    StepOrientedFace(StepID entityId=0) : StepEntity(entityId) , face_element(0) {}
    virtual ~StepOrientedFace() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORIENTED_FACE";}
  public:
    std::string name; // label
    std::vector<StepID> bounds; // face_bound
    StepID face_element; // face
    bool orientation; // BOOLEAN
};

StepEntity *step_create_oriented_face(StepFileLine & line);

class StepGeometricallyBoundedWireframeShapeRepresentation : public StepEntity
{
  public:
    StepGeometricallyBoundedWireframeShapeRepresentation(StepID entityId=0) : StepEntity(entityId) , context_of_items(0) {}
    virtual ~StepGeometricallyBoundedWireframeShapeRepresentation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "GEOMETRICALLY_BOUNDED_WIREFRAME_SHAPE_REPRESENTATION";}
  public:
    std::string name; // label
    std::vector<StepID> items; // representation_item
    StepID context_of_items; // representation_context
};

StepEntity *step_create_geometrically_bounded_wireframe_shape_representation(StepFileLine & line);

class StepMassUnit : public StepEntity
{
  public:
    StepMassUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepMassUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "MASS_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
};

StepEntity *step_create_mass_unit(StepFileLine & line);

class StepParametricRepresentationContext : public StepEntity
{
  public:
    StepParametricRepresentationContext(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepParametricRepresentationContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PARAMETRIC_REPRESENTATION_CONTEXT";}
  public:
    std::string context_identifier; // identifier
    std::string context_type; // text
    std::vector<StepID> representations_in_context; // FOR
};

StepEntity *step_create_parametric_representation_context(StepFileLine & line);

class StepSpecifiedHigherUsageOccurrence : public StepEntity
{
  public:
    StepSpecifiedHigherUsageOccurrence(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0), upper_usage(0), next_usage(0) {}
    virtual ~StepSpecifiedHigherUsageOccurrence() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SPECIFIED_HIGHER_USAGE_OCCURRENCE";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
    std::string reference_designator; // identifier
    StepID upper_usage; // assembly_component_usage
    StepID next_usage; // next_assembly_usage_occurrence
};

StepEntity *step_create_specified_higher_usage_occurrence(StepFileLine & line);

class StepGeometricRepresentationItem : public StepEntity
{
  public:
    StepGeometricRepresentationItem(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepGeometricRepresentationItem() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "GEOMETRIC_REPRESENTATION_ITEM";}
  public:
    std::string name; // label
};

StepEntity *step_create_geometric_representation_item(StepFileLine & line);

class StepCcDesignDateAndTimeAssignment : public StepEntity
{
  public:
    StepCcDesignDateAndTimeAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_date_and_time(0), role(0) {}
    virtual ~StepCcDesignDateAndTimeAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CC_DESIGN_DATE_AND_TIME_ASSIGNMENT";}
  public:
    StepID assigned_date_and_time; // date_and_time
    StepID role; // date_time_role
    std::vector<StepDateTimeItem> items; // date_time_item
};

StepEntity *step_create_cc_design_date_and_time_assignment(StepFileLine & line);

class StepGeometricSet : public StepEntity
{
  public:
    StepGeometricSet(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepGeometricSet() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "GEOMETRIC_SET";}
  public:
    std::string name; // label
    std::vector<StepGeometricSetSelect> elements; // geometric_set_select
};

StepEntity *step_create_geometric_set(StepFileLine & line);

class StepCcDesignPersonAndOrganizationAssignment : public StepEntity
{
  public:
    StepCcDesignPersonAndOrganizationAssignment(StepID entityId=0) : StepEntity(entityId) , assigned_person_and_organization(0), role(0) {}
    virtual ~StepCcDesignPersonAndOrganizationAssignment() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CC_DESIGN_PERSON_AND_ORGANIZATION_ASSIGNMENT";}
  public:
    StepID assigned_person_and_organization; // person_and_organization
    StepID role; // person_and_organization_role
    std::vector<StepPersonOrganizationItem> items; // person_organization_item
};

StepEntity *step_create_cc_design_person_and_organization_assignment(StepFileLine & line);

class StepConnectedEdgeSet : public StepEntity
{
  public:
    StepConnectedEdgeSet(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepConnectedEdgeSet() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONNECTED_EDGE_SET";}
  public:
    std::string name; // label
    std::vector<StepID> ces_edges; // edge
};

StepEntity *step_create_connected_edge_set(StepFileLine & line);

class StepContextDependentUnit : public StepEntity
{
  public:
    StepContextDependentUnit(StepID entityId=0) : StepEntity(entityId) , dimensions(0) {}
    virtual ~StepContextDependentUnit() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONTEXT_DEPENDENT_UNIT";}
  public:
    StepID dimensions; // dimensional_exponents
    std::string name; // label
};

StepEntity *step_create_context_dependent_unit(StepFileLine & line);

class StepGeometricCurveSet : public StepEntity
{
  public:
    StepGeometricCurveSet(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepGeometricCurveSet() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "GEOMETRIC_CURVE_SET";}
  public:
    std::string name; // label
    std::vector<StepGeometricSetSelect> elements; // geometric_set_select
};

StepEntity *step_create_geometric_curve_set(StepFileLine & line);

class StepOrientedEdge : public StepEntity
{
  public:
    StepOrientedEdge(StepID entityId=0) : StepEntity(entityId) , edge_start(0), edge_end(0), edge_element(0) {}
    virtual ~StepOrientedEdge() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORIENTED_EDGE";}
  public:
    std::string name; // label
    StepID edge_start; // vertex
    StepID edge_end; // vertex
    StepID edge_element; // edge
    bool orientation; // BOOLEAN
};

StepEntity *step_create_oriented_edge(StepFileLine & line);

class StepClosedShell : public StepEntity
{
  public:
    StepClosedShell(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepClosedShell() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CLOSED_SHELL";}
  public:
    std::string name; // label
    std::vector<StepID> cfs_faces; // face
};

StepEntity *step_create_closed_shell(StepFileLine & line);

class StepShapeRepresentationRelationship : public StepEntity
{
  public:
    StepShapeRepresentationRelationship(StepID entityId=0) : StepEntity(entityId) , rep_1(0), rep_2(0) {}
    virtual ~StepShapeRepresentationRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SHAPE_REPRESENTATION_RELATIONSHIP";}
  public:
    std::string name; // label
    std::string description; // text
    StepID rep_1; // representation
    StepID rep_2; // representation
};

StepEntity *step_create_shape_representation_relationship(StepFileLine & line);

class StepGlobalUncertaintyAssignedContext : public StepEntity
{
  public:
    StepGlobalUncertaintyAssignedContext(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepGlobalUncertaintyAssignedContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT";}
  public:
    std::string context_identifier; // identifier
    std::string context_type; // text
    std::vector<StepID> representations_in_context; // FOR
    std::vector<StepID> uncertainty; // uncertainty_measure_with_unit
};

StepEntity *step_create_global_uncertainty_assigned_context(StepFileLine & line);

class StepRepresentationRelationshipWithTransformation : public StepEntity
{
  public:
    StepRepresentationRelationshipWithTransformation(StepID entityId=0) : StepEntity(entityId) , rep_1(0), rep_2(0) {}
    virtual ~StepRepresentationRelationshipWithTransformation() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION";}
  public:
    std::string name; // label
    std::string description; // text
    StepID rep_1; // representation
    StepID rep_2; // representation
    StepTransformation transformation_operator; // transformation
};

StepEntity *step_create_representation_relationship_with_transformation(StepFileLine & line);

class StepMechanicalContext : public StepEntity
{
  public:
    StepMechanicalContext(StepID entityId=0) : StepEntity(entityId) , frame_of_reference(0) {}
    virtual ~StepMechanicalContext() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "MECHANICAL_CONTEXT";}
  public:
    std::string name; // label
    StepID frame_of_reference; // application_context
    std::string discipline_type; // label
};

StepEntity *step_create_mechanical_context(StepFileLine & line);

class StepOrientedClosedShell : public StepEntity
{
  public:
    StepOrientedClosedShell(StepID entityId=0) : StepEntity(entityId) , closed_shell_element(0) {}
    virtual ~StepOrientedClosedShell() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORIENTED_CLOSED_SHELL";}
  public:
    std::string name; // label
    std::vector<StepID> cfs_faces; // face
    StepID closed_shell_element; // closed_shell
    bool orientation; // BOOLEAN
};

StepEntity *step_create_oriented_closed_shell(StepFileLine & line);

class StepDirection : public StepEntity
{
  public:
    StepDirection(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepDirection() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DIRECTION";}
  public:
    std::string name; // label
    double direction_ratios[3]; // REAL
};

StepEntity *step_create_direction(StepFileLine & line);

class StepVertexShell : public StepEntity
{
  public:
    StepVertexShell(StepID entityId=0) : StepEntity(entityId) , vertex_shell_extent(0) {}
    virtual ~StepVertexShell() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "VERTEX_SHELL";}
  public:
    std::string name; // label
    StepID vertex_shell_extent; // vertex_loop
};

StepEntity *step_create_vertex_shell(StepFileLine & line);

class StepNextAssemblyUsageOccurrence : public StepEntity
{
  public:
    StepNextAssemblyUsageOccurrence(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0) {}
    virtual ~StepNextAssemblyUsageOccurrence() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "NEXT_ASSEMBLY_USAGE_OCCURRENCE";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
    std::string reference_designator; // identifier
};

StepEntity *step_create_next_assembly_usage_occurrence(StepFileLine & line);

class StepOrientedPath : public StepEntity
{
  public:
    StepOrientedPath(StepID entityId=0) : StepEntity(entityId) , path_element(0) {}
    virtual ~StepOrientedPath() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORIENTED_PATH";}
  public:
    std::string name; // label
    std::vector<StepID> edge_list; // oriented_edge
    StepID path_element; // path
    bool orientation; // BOOLEAN
};

StepEntity *step_create_oriented_path(StepFileLine & line);

class StepFaceBound : public StepEntity
{
  public:
    StepFaceBound(StepID entityId=0) : StepEntity(entityId) , bound(0) {}
    virtual ~StepFaceBound() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "FACE_BOUND";}
  public:
    std::string name; // label
    StepID bound; // loop
    bool orientation; // BOOLEAN
};

StepEntity *step_create_face_bound(StepFileLine & line);

class StepVector : public StepEntity
{
  public:
    StepVector(StepID entityId=0) : StepEntity(entityId) , orientation(0) {}
    virtual ~StepVector() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "VECTOR";}
  public:
    std::string name; // label
    StepID orientation; // direction
    double magnitude; // length_measure
};

StepEntity *step_create_vector(StepFileLine & line);

class StepDirectedAction : public StepEntity
{
  public:
    StepDirectedAction(StepID entityId=0) : StepEntity(entityId) , chosen_method(0), directive(0) {}
    virtual ~StepDirectedAction() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DIRECTED_ACTION";}
  public:
    std::string name; // label
    std::string description; // text
    StepID chosen_method; // action_method
    StepID directive; // action_directive
};

StepEntity *step_create_directed_action(StepFileLine & line);

class StepSurface : public StepEntity
{
  public:
    StepSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SURFACE";}
  public:
    std::string name; // label
};

StepEntity *step_create_surface(StepFileLine & line);

class StepShellBasedSurfaceModel : public StepEntity
{
  public:
    StepShellBasedSurfaceModel(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepShellBasedSurfaceModel() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SHELL_BASED_SURFACE_MODEL";}
  public:
    std::string name; // label
    std::vector<StepShell> sbsm_boundary; // shell
};

StepEntity *step_create_shell_based_surface_model(StepFileLine & line);

class StepDesignMakeFromRelationship : public StepEntity
{
  public:
    StepDesignMakeFromRelationship(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0) {}
    virtual ~StepDesignMakeFromRelationship() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DESIGN_MAKE_FROM_RELATIONSHIP";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
};

StepEntity *step_create_design_make_from_relationship(StepFileLine & line);

class StepPolyLoop : public StepEntity
{
  public:
    StepPolyLoop(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPolyLoop() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "POLY_LOOP";}
  public:
    std::string name; // label
    std::vector<StepID> polygon; // cartesian_point
};

StepEntity *step_create_poly_loop(StepFileLine & line);

class StepCurve : public StepEntity
{
  public:
    StepCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CURVE";}
  public:
    std::string name; // label
};

StepEntity *step_create_curve(StepFileLine & line);

class StepPromissoryUsageOccurrence : public StepEntity
{
  public:
    StepPromissoryUsageOccurrence(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0) {}
    virtual ~StepPromissoryUsageOccurrence() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PROMISSORY_USAGE_OCCURRENCE";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
    std::string reference_designator; // identifier
};

StepEntity *step_create_promissory_usage_occurrence(StepFileLine & line);

class StepPoint : public StepEntity
{
  public:
    StepPoint(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPoint() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "POINT";}
  public:
    std::string name; // label
};

StepEntity *step_create_point(StepFileLine & line);

class StepQuantifiedAssemblyComponentUsage : public StepEntity
{
  public:
    StepQuantifiedAssemblyComponentUsage(StepID entityId=0) : StepEntity(entityId) , relating_product_definition(0), related_product_definition(0), quantity(0) {}
    virtual ~StepQuantifiedAssemblyComponentUsage() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "QUANTIFIED_ASSEMBLY_COMPONENT_USAGE";}
  public:
    std::string id; // identifier
    std::string name; // label
    std::string description; // text
    StepID relating_product_definition; // product_definition
    StepID related_product_definition; // product_definition
    std::string reference_designator; // identifier
    StepID quantity; // measure_with_unit
};

StepEntity *step_create_quantified_assembly_component_usage(StepFileLine & line);

class StepFaceOuterBound : public StepEntity
{
  public:
    StepFaceOuterBound(StepID entityId=0) : StepEntity(entityId) , bound(0) {}
    virtual ~StepFaceOuterBound() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "FACE_OUTER_BOUND";}
  public:
    std::string name; // label
    StepID bound; // loop
    bool orientation; // BOOLEAN
};

StepEntity *step_create_face_outer_bound(StepFileLine & line);

class StepOpenShell : public StepEntity
{
  public:
    StepOpenShell(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepOpenShell() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "OPEN_SHELL";}
  public:
    std::string name; // label
    std::vector<StepID> cfs_faces; // face
};

StepEntity *step_create_open_shell(StepFileLine & line);

class StepElementarySurface : public StepEntity
{
  public:
    StepElementarySurface(StepID entityId=0) : StepEntity(entityId) , position(0) {}
    virtual ~StepElementarySurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ELEMENTARY_SURFACE";}
  public:
    std::string name; // label
    StepID position; // axis2_placement_3d
};

StepEntity *step_create_elementary_surface(StepFileLine & line);

class StepPointOnCurve : public StepEntity
{
  public:
    StepPointOnCurve(StepID entityId=0) : StepEntity(entityId) , basis_curve(0) {}
    virtual ~StepPointOnCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "POINT_ON_CURVE";}
  public:
    std::string name; // label
    StepID basis_curve; // curve
    double point_parameter; // parameter_value
};

StepEntity *step_create_point_on_curve(StepFileLine & line);

class StepCurveReplica : public StepEntity
{
  public:
    StepCurveReplica(StepID entityId=0) : StepEntity(entityId) , parent_curve(0), transformation(0) {}
    virtual ~StepCurveReplica() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CURVE_REPLICA";}
  public:
    std::string name; // label
    StepID parent_curve; // curve
    StepID transformation; // cartesian_transformation_operator
};

StepEntity *step_create_curve_replica(StepFileLine & line);

class StepVertexLoop : public StepEntity
{
  public:
    StepVertexLoop(StepID entityId=0) : StepEntity(entityId) , loop_vertex(0) {}
    virtual ~StepVertexLoop() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "VERTEX_LOOP";}
  public:
    std::string name; // label
    StepID loop_vertex; // vertex
};

StepEntity *step_create_vertex_loop(StepFileLine & line);

class StepVertexPoint : public StepEntity
{
  public:
    StepVertexPoint(StepID entityId=0) : StepEntity(entityId) , vertex_geometry(0) {}
    virtual ~StepVertexPoint() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "VERTEX_POINT";}
  public:
    std::string name; // label
    StepID vertex_geometry; // point
};

StepEntity *step_create_vertex_point(StepFileLine & line);

class StepSolidModel : public StepEntity
{
  public:
    StepSolidModel(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepSolidModel() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SOLID_MODEL";}
  public:
    std::string name; // label
};

StepEntity *step_create_solid_model(StepFileLine & line);

class StepShellBasedWireframeModel : public StepEntity
{
  public:
    StepShellBasedWireframeModel(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepShellBasedWireframeModel() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SHELL_BASED_WIREFRAME_MODEL";}
  public:
    std::string name; // label
    std::vector<StepShell> sbwm_boundary; // shell
};

StepEntity *step_create_shell_based_wireframe_model(StepFileLine & line);

class StepPlacement : public StepEntity
{
  public:
    StepPlacement(StepID entityId=0) : StepEntity(entityId) , location(0) {}
    virtual ~StepPlacement() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PLACEMENT";}
  public:
    std::string name; // label
    StepID location; // cartesian_point
};

StepEntity *step_create_placement(StepFileLine & line);

class StepPointOnSurface : public StepEntity
{
  public:
    StepPointOnSurface(StepID entityId=0) : StepEntity(entityId) , basis_surface(0) {}
    virtual ~StepPointOnSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "POINT_ON_SURFACE";}
  public:
    std::string name; // label
    StepID basis_surface; // surface
    double point_parameter_u; // parameter_value
    double point_parameter_v; // parameter_value
};

StepEntity *step_create_point_on_surface(StepFileLine & line);

class StepCartesianPoint : public StepEntity
{
  public:
    StepCartesianPoint(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepCartesianPoint() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CARTESIAN_POINT";}
  public:
    std::string name; // label
    double coordinates[3]; // length_measure
};

StepEntity *step_create_cartesian_point(StepFileLine & line);

class StepEdgeLoop : public StepEntity
{
  public:
    StepEdgeLoop(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepEdgeLoop() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "EDGE_LOOP";}
  public:
    std::string name; // label
    std::vector<StepID> edge_list; // oriented_edge
};

StepEntity *step_create_edge_loop(StepFileLine & line);

class StepLine : public StepEntity
{
  public:
    StepLine(StepID entityId=0) : StepEntity(entityId) , pnt(0), dir(0) {}
    virtual ~StepLine() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "LINE";}
  public:
    std::string name; // label
    StepID pnt; // cartesian_point
    StepID dir; // vector
};

StepEntity *step_create_line(StepFileLine & line);

class StepConic : public StepEntity
{
  public:
    StepConic(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepConic() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONIC";}
  public:
    std::string name; // label
    StepAxis2Placement position; // axis2_placement
};

StepEntity *step_create_conic(StepFileLine & line);

class StepFaceSurface : public StepEntity
{
  public:
    StepFaceSurface(StepID entityId=0) : StepEntity(entityId) , face_geometry(0) {}
    virtual ~StepFaceSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "FACE_SURFACE";}
  public:
    std::string name; // label
    std::vector<StepID> bounds; // face_bound
    StepID face_geometry; // surface
    bool same_sense; // BOOLEAN
};

StepEntity *step_create_face_surface(StepFileLine & line);

class StepCartesianTransformationOperator : public StepEntity
{
  public:
    StepCartesianTransformationOperator(StepID entityId=0) : StepEntity(entityId) , axis1(0), axis2(0), local_origin(0) {}
    virtual ~StepCartesianTransformationOperator() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CARTESIAN_TRANSFORMATION_OPERATOR";}
  public:
    std::string name; // label
    StepID axis1; // direction
    StepID axis2; // direction
    StepID local_origin; // cartesian_point
    double scale; // REAL
};

StepEntity *step_create_cartesian_transformation_operator(StepFileLine & line);

class StepPointReplica : public StepEntity
{
  public:
    StepPointReplica(StepID entityId=0) : StepEntity(entityId) , parent_pt(0), transformation(0) {}
    virtual ~StepPointReplica() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "POINT_REPLICA";}
  public:
    std::string name; // label
    StepID parent_pt; // point
    StepID transformation; // cartesian_transformation_operator
};

StepEntity *step_create_point_replica(StepFileLine & line);

class StepManifoldSolidBrep : public StepEntity
{
  public:
    StepManifoldSolidBrep(StepID entityId=0) : StepEntity(entityId) , outer(0) {}
    virtual ~StepManifoldSolidBrep() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "MANIFOLD_SOLID_BREP";}
  public:
    std::string name; // label
    StepID outer; // closed_shell
};

StepEntity *step_create_manifold_solid_brep(StepFileLine & line);

class StepBrepWithVoids : public StepEntity
{
  public:
    StepBrepWithVoids(StepID entityId=0) : StepEntity(entityId) , outer(0) {}
    virtual ~StepBrepWithVoids() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "BREP_WITH_VOIDS";}
  public:
    std::string name; // label
    StepID outer; // closed_shell
    std::vector<StepID> voids; // oriented_closed_shell
};

StepEntity *step_create_brep_with_voids(StepFileLine & line);

class StepSurfaceCurve : public StepEntity
{
  public:
    StepSurfaceCurve(StepID entityId=0) : StepEntity(entityId) , curve_3d(0) {}
    virtual ~StepSurfaceCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SURFACE_CURVE";}
  public:
    std::string name; // label
    StepID curve_3d; // curve
    StepPcurveOrSurface associated_geometry[2]; // pcurve_or_surface
    StepPreferredSurfaceCurveRepresentation master_representation; // preferred_surface_curve_representation
};

StepEntity *step_create_surface_curve(StepFileLine & line);

class StepAxis2Placement3d : public StepEntity
{
  public:
    StepAxis2Placement3d(StepID entityId=0) : StepEntity(entityId) , location(0), axis(0), ref_direction(0) {}
    virtual ~StepAxis2Placement3d() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "AXIS2_PLACEMENT_3D";}
  public:
    std::string name; // label
    StepID location; // cartesian_point
    StepID axis; // direction
    StepID ref_direction; // direction
};

StepEntity *step_create_axis2_placement_3d(StepFileLine & line);

class StepSurfaceReplica : public StepEntity
{
  public:
    StepSurfaceReplica(StepID entityId=0) : StepEntity(entityId) , parent_surface(0), transformation(0) {}
    virtual ~StepSurfaceReplica() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SURFACE_REPLICA";}
  public:
    std::string name; // label
    StepID parent_surface; // surface
    StepID transformation; // cartesian_transformation_operator_3d
};

StepEntity *step_create_surface_replica(StepFileLine & line);

class StepHyperbola : public StepEntity
{
  public:
    StepHyperbola(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepHyperbola() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "HYPERBOLA";}
  public:
    std::string name; // label
    StepAxis2Placement position; // axis2_placement
    double semi_axis; // positive_length_measure
    double semi_imag_axis; // positive_length_measure
};

StepEntity *step_create_hyperbola(StepFileLine & line);

class StepBoundedSurface : public StepEntity
{
  public:
    StepBoundedSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBoundedSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "BOUNDED_SURFACE";}
  public:
    std::string name; // label
};

StepEntity *step_create_bounded_surface(StepFileLine & line);

class StepPlane : public StepEntity
{
  public:
    StepPlane(StepID entityId=0) : StepEntity(entityId) , position(0) {}
    virtual ~StepPlane() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PLANE";}
  public:
    std::string name; // label
    StepID position; // axis2_placement_3d
};

StepEntity *step_create_plane(StepFileLine & line);

class StepEdgeBasedWireframeModel : public StepEntity
{
  public:
    StepEdgeBasedWireframeModel(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepEdgeBasedWireframeModel() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "EDGE_BASED_WIREFRAME_MODEL";}
  public:
    std::string name; // label
    std::vector<StepID> ebwm_boundary; // connected_edge_set
};

StepEntity *step_create_edge_based_wireframe_model(StepFileLine & line);

class StepEdgeCurve : public StepEntity
{
  public:
    StepEdgeCurve(StepID entityId=0) : StepEntity(entityId) , edge_start(0), edge_end(0), edge_geometry(0) {}
    virtual ~StepEdgeCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "EDGE_CURVE";}
  public:
    std::string name; // label
    StepID edge_start; // vertex
    StepID edge_end; // vertex
    StepID edge_geometry; // curve
    bool same_sense; // BOOLEAN
};

StepEntity *step_create_edge_curve(StepFileLine & line);

class StepParabola : public StepEntity
{
  public:
    StepParabola(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepParabola() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PARABOLA";}
  public:
    std::string name; // label
    StepAxis2Placement position; // axis2_placement
    double focal_dist; // length_measure
};

StepEntity *step_create_parabola(StepFileLine & line);

class StepOffsetCurve3d : public StepEntity
{
  public:
    StepOffsetCurve3d(StepID entityId=0) : StepEntity(entityId) , basis_curve(0), ref_direction(0) {}
    virtual ~StepOffsetCurve3d() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "OFFSET_CURVE_3D";}
  public:
    std::string name; // label
    StepID basis_curve; // curve
    double distance; // length_measure
    StepLogical self_intersect; // LOGICAL
    StepID ref_direction; // direction
};

StepEntity *step_create_offset_curve_3d(StepFileLine & line);

class StepSphericalSurface : public StepEntity
{
  public:
    StepSphericalSurface(StepID entityId=0) : StepEntity(entityId) , position(0) {}
    virtual ~StepSphericalSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SPHERICAL_SURFACE";}
  public:
    std::string name; // label
    StepID position; // axis2_placement_3d
    double radius; // positive_length_measure
};

StepEntity *step_create_spherical_surface(StepFileLine & line);

class StepDegeneratePcurve : public StepEntity
{
  public:
    StepDegeneratePcurve(StepID entityId=0) : StepEntity(entityId) , basis_surface(0), reference_to_curve(0) {}
    virtual ~StepDegeneratePcurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DEGENERATE_PCURVE";}
  public:
    std::string name; // label
    StepID basis_surface; // surface
    StepID reference_to_curve; // definitional_representation
};

StepEntity *step_create_degenerate_pcurve(StepFileLine & line);

class StepBSplineSurface : public StepEntity
{
  public:
    StepBSplineSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBSplineSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "B_SPLINE_SURFACE";}
  public:
    std::string name; // label
    int u_degree; // INTEGER
    int v_degree; // INTEGER
    DMatrix<StepID> control_points_list; // cartesian_point
    StepBSplineSurfaceForm surface_form; // b_spline_surface_form
    StepLogical u_closed; // LOGICAL
    StepLogical v_closed; // LOGICAL
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_b_spline_surface(StepFileLine & line);

class StepCurveBoundedSurface : public StepEntity
{
  public:
    StepCurveBoundedSurface(StepID entityId=0) : StepEntity(entityId) , basis_surface(0) {}
    virtual ~StepCurveBoundedSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CURVE_BOUNDED_SURFACE";}
  public:
    std::string name; // label
    StepID basis_surface; // surface
    std::vector<StepID> boundaries; // boundary_curve
    bool implicit_outer; // BOOLEAN
};

StepEntity *step_create_curve_bounded_surface(StepFileLine & line);

class StepRectangularCompositeSurface : public StepEntity
{
  public:
    StepRectangularCompositeSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepRectangularCompositeSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "RECTANGULAR_COMPOSITE_SURFACE";}
  public:
    std::string name; // label
    DMatrix<StepID> segments; // surface_patch
};

StepEntity *step_create_rectangular_composite_surface(StepFileLine & line);

class StepEllipse : public StepEntity
{
  public:
    StepEllipse(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepEllipse() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ELLIPSE";}
  public:
    std::string name; // label
    StepAxis2Placement position; // axis2_placement
    double semi_axis_1; // positive_length_measure
    double semi_axis_2; // positive_length_measure
};

StepEntity *step_create_ellipse(StepFileLine & line);

class StepRationalBSplineSurface : public StepEntity
{
  public:
    StepRationalBSplineSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepRationalBSplineSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "RATIONAL_B_SPLINE_SURFACE";}
  public:
    std::string name; // label
    int u_degree; // INTEGER
    int v_degree; // INTEGER
    DMatrix<StepID> control_points_list; // cartesian_point
    StepBSplineSurfaceForm surface_form; // b_spline_surface_form
    StepLogical u_closed; // LOGICAL
    StepLogical v_closed; // LOGICAL
    StepLogical self_intersect; // LOGICAL
    DMatrix<double> weights_data; // REAL
};

StepEntity *step_create_rational_b_spline_surface(StepFileLine & line);

class StepSweptSurface : public StepEntity
{
  public:
    StepSweptSurface(StepID entityId=0) : StepEntity(entityId) , swept_curve(0) {}
    virtual ~StepSweptSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SWEPT_SURFACE";}
  public:
    std::string name; // label
    StepID swept_curve; // curve
};

StepEntity *step_create_swept_surface(StepFileLine & line);

class StepAxis2Placement2d : public StepEntity
{
  public:
    StepAxis2Placement2d(StepID entityId=0) : StepEntity(entityId) , location(0), ref_direction(0) {}
    virtual ~StepAxis2Placement2d() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "AXIS2_PLACEMENT_2D";}
  public:
    std::string name; // label
    StepID location; // cartesian_point
    StepID ref_direction; // direction
};

StepEntity *step_create_axis2_placement_2d(StepFileLine & line);

class StepConicalSurface : public StepEntity
{
  public:
    StepConicalSurface(StepID entityId=0) : StepEntity(entityId) , position(0) {}
    virtual ~StepConicalSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CONICAL_SURFACE";}
  public:
    std::string name; // label
    StepID position; // axis2_placement_3d
    double radius; // length_measure
    double semi_angle; // plane_angle_measure
};

StepEntity *step_create_conical_surface(StepFileLine & line);

class StepOffsetSurface : public StepEntity
{
  public:
    StepOffsetSurface(StepID entityId=0) : StepEntity(entityId) , basis_surface(0) {}
    virtual ~StepOffsetSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "OFFSET_SURFACE";}
  public:
    std::string name; // label
    StepID basis_surface; // surface
    double distance; // length_measure
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_offset_surface(StepFileLine & line);

class StepFacetedBrep : public StepEntity
{
  public:
    StepFacetedBrep(StepID entityId=0) : StepEntity(entityId) , outer(0) {}
    virtual ~StepFacetedBrep() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "FACETED_BREP";}
  public:
    std::string name; // label
    StepID outer; // closed_shell
};

StepEntity *step_create_faceted_brep(StepFileLine & line);

class StepSurfaceOfRevolution : public StepEntity
{
  public:
    StepSurfaceOfRevolution(StepID entityId=0) : StepEntity(entityId) , swept_curve(0), axis_position(0) {}
    virtual ~StepSurfaceOfRevolution() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SURFACE_OF_REVOLUTION";}
  public:
    std::string name; // label
    StepID swept_curve; // curve
    StepID axis_position; // axis1_placement
};

StepEntity *step_create_surface_of_revolution(StepFileLine & line);

class StepSurfaceOfLinearExtrusion : public StepEntity
{
  public:
    StepSurfaceOfLinearExtrusion(StepID entityId=0) : StepEntity(entityId) , swept_curve(0), extrusion_axis(0) {}
    virtual ~StepSurfaceOfLinearExtrusion() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SURFACE_OF_LINEAR_EXTRUSION";}
  public:
    std::string name; // label
    StepID swept_curve; // curve
    StepID extrusion_axis; // vector
};

StepEntity *step_create_surface_of_linear_extrusion(StepFileLine & line);

class StepPcurve : public StepEntity
{
  public:
    StepPcurve(StepID entityId=0) : StepEntity(entityId) , basis_surface(0), reference_to_curve(0) {}
    virtual ~StepPcurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "PCURVE";}
  public:
    std::string name; // label
    StepID basis_surface; // surface
    StepID reference_to_curve; // definitional_representation
};

StepEntity *step_create_pcurve(StepFileLine & line);

class StepUniformSurface : public StepEntity
{
  public:
    StepUniformSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepUniformSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "UNIFORM_SURFACE";}
  public:
    std::string name; // label
    int u_degree; // INTEGER
    int v_degree; // INTEGER
    DMatrix<StepID> control_points_list; // cartesian_point
    StepBSplineSurfaceForm surface_form; // b_spline_surface_form
    StepLogical u_closed; // LOGICAL
    StepLogical v_closed; // LOGICAL
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_uniform_surface(StepFileLine & line);

class StepBoundedCurve : public StepEntity
{
  public:
    StepBoundedCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBoundedCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "BOUNDED_CURVE";}
  public:
    std::string name; // label
};

StepEntity *step_create_bounded_curve(StepFileLine & line);

class StepQuasiUniformSurface : public StepEntity
{
  public:
    StepQuasiUniformSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepQuasiUniformSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "QUASI_UNIFORM_SURFACE";}
  public:
    std::string name; // label
    int u_degree; // INTEGER
    int v_degree; // INTEGER
    DMatrix<StepID> control_points_list; // cartesian_point
    StepBSplineSurfaceForm surface_form; // b_spline_surface_form
    StepLogical u_closed; // LOGICAL
    StepLogical v_closed; // LOGICAL
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_quasi_uniform_surface(StepFileLine & line);

class StepToroidalSurface : public StepEntity
{
  public:
    StepToroidalSurface(StepID entityId=0) : StepEntity(entityId) , position(0) {}
    virtual ~StepToroidalSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "TOROIDAL_SURFACE";}
  public:
    std::string name; // label
    StepID position; // axis2_placement_3d
    double major_radius; // positive_length_measure
    double minor_radius; // positive_length_measure
};

StepEntity *step_create_toroidal_surface(StepFileLine & line);

class StepOrientedOpenShell : public StepEntity
{
  public:
    StepOrientedOpenShell(StepID entityId=0) : StepEntity(entityId) , open_shell_element(0) {}
    virtual ~StepOrientedOpenShell() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ORIENTED_OPEN_SHELL";}
  public:
    std::string name; // label
    std::vector<StepID> cfs_faces; // face
    StepID open_shell_element; // open_shell
    bool orientation; // BOOLEAN
};

StepEntity *step_create_oriented_open_shell(StepFileLine & line);

class StepCylindricalSurface : public StepEntity
{
  public:
    StepCylindricalSurface(StepID entityId=0) : StepEntity(entityId) , position(0) {}
    virtual ~StepCylindricalSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CYLINDRICAL_SURFACE";}
  public:
    std::string name; // label
    StepID position; // axis2_placement_3d
    double radius; // positive_length_measure
};

StepEntity *step_create_cylindrical_surface(StepFileLine & line);

class StepIntersectionCurve : public StepEntity
{
  public:
    StepIntersectionCurve(StepID entityId=0) : StepEntity(entityId) , curve_3d(0) {}
    virtual ~StepIntersectionCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "INTERSECTION_CURVE";}
  public:
    std::string name; // label
    StepID curve_3d; // curve
    StepPcurveOrSurface associated_geometry[2]; // pcurve_or_surface
    StepPreferredSurfaceCurveRepresentation master_representation; // preferred_surface_curve_representation
};

StepEntity *step_create_intersection_curve(StepFileLine & line);

class StepRectangularTrimmedSurface : public StepEntity
{
  public:
    StepRectangularTrimmedSurface(StepID entityId=0) : StepEntity(entityId) , basis_surface(0) {}
    virtual ~StepRectangularTrimmedSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "RECTANGULAR_TRIMMED_SURFACE";}
  public:
    std::string name; // label
    StepID basis_surface; // surface
    double u1; // parameter_value
    double u2; // parameter_value
    double v1; // parameter_value
    double v2; // parameter_value
    bool usense; // BOOLEAN
    bool vsense; // BOOLEAN
};

StepEntity *step_create_rectangular_trimmed_surface(StepFileLine & line);

class StepSeamCurve : public StepEntity
{
  public:
    StepSeamCurve(StepID entityId=0) : StepEntity(entityId) , curve_3d(0) {}
    virtual ~StepSeamCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "SEAM_CURVE";}
  public:
    std::string name; // label
    StepID curve_3d; // curve
    StepPcurveOrSurface associated_geometry[2]; // pcurve_or_surface
    StepPreferredSurfaceCurveRepresentation master_representation; // preferred_surface_curve_representation
};

StepEntity *step_create_seam_curve(StepFileLine & line);

class StepAdvancedFace : public StepEntity
{
  public:
    StepAdvancedFace(StepID entityId=0) : StepEntity(entityId) , face_geometry(0) {}
    virtual ~StepAdvancedFace() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "ADVANCED_FACE";}
  public:
    std::string name; // label
    std::vector<StepID> bounds; // face_bound
    StepID face_geometry; // surface
    bool same_sense; // BOOLEAN
};

StepEntity *step_create_advanced_face(StepFileLine & line);

class StepDegenerateToroidalSurface : public StepEntity
{
  public:
    StepDegenerateToroidalSurface(StepID entityId=0) : StepEntity(entityId) , position(0) {}
    virtual ~StepDegenerateToroidalSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "DEGENERATE_TOROIDAL_SURFACE";}
  public:
    std::string name; // label
    StepID position; // axis2_placement_3d
    double major_radius; // positive_length_measure
    double minor_radius; // positive_length_measure
    bool select_outer; // BOOLEAN
};

StepEntity *step_create_degenerate_toroidal_surface(StepFileLine & line);

class StepPolyline : public StepEntity
{
  public:
    StepPolyline(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepPolyline() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "POLYLINE";}
  public:
    std::string name; // label
    std::vector<StepID> points; // cartesian_point
};

StepEntity *step_create_polyline(StepFileLine & line);

class StepCircle : public StepEntity
{
  public:
    StepCircle(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepCircle() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CIRCLE";}
  public:
    std::string name; // label
    StepAxis2Placement position; // axis2_placement
    double radius; // positive_length_measure
};

StepEntity *step_create_circle(StepFileLine & line);

class StepBoundedSurfaceCurve : public StepEntity
{
  public:
    StepBoundedSurfaceCurve(StepID entityId=0) : StepEntity(entityId) , curve_3d(0) {}
    virtual ~StepBoundedSurfaceCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "BOUNDED_SURFACE_CURVE";}
  public:
    std::string name; // label
    StepID curve_3d; // curve
    StepPcurveOrSurface associated_geometry[2]; // pcurve_or_surface
    StepPreferredSurfaceCurveRepresentation master_representation; // preferred_surface_curve_representation
};

StepEntity *step_create_bounded_surface_curve(StepFileLine & line);

class StepAxis1Placement : public StepEntity
{
  public:
    StepAxis1Placement(StepID entityId=0) : StepEntity(entityId) , location(0), axis(0) {}
    virtual ~StepAxis1Placement() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "AXIS1_PLACEMENT";}
  public:
    std::string name; // label
    StepID location; // cartesian_point
    StepID axis; // direction
};

StepEntity *step_create_axis1_placement(StepFileLine & line);

class StepCartesianTransformationOperator3d : public StepEntity
{
  public:
    StepCartesianTransformationOperator3d(StepID entityId=0) : StepEntity(entityId) , axis1(0), axis2(0), local_origin(0), axis3(0) {}
    virtual ~StepCartesianTransformationOperator3d() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "CARTESIAN_TRANSFORMATION_OPERATOR_3D";}
  public:
    std::string name; // label
    StepID axis1; // direction
    StepID axis2; // direction
    StepID local_origin; // cartesian_point
    double scale; // REAL
    StepID axis3; // direction
};

StepEntity *step_create_cartesian_transformation_operator_3d(StepFileLine & line);

class StepEvaluatedDegeneratePcurve : public StepEntity
{
  public:
    StepEvaluatedDegeneratePcurve(StepID entityId=0) : StepEntity(entityId) , basis_surface(0), reference_to_curve(0), equivalent_point(0) {}
    virtual ~StepEvaluatedDegeneratePcurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "EVALUATED_DEGENERATE_PCURVE";}
  public:
    std::string name; // label
    StepID basis_surface; // surface
    StepID reference_to_curve; // definitional_representation
    StepID equivalent_point; // cartesian_point
};

StepEntity *step_create_evaluated_degenerate_pcurve(StepFileLine & line);

class StepBezierSurface : public StepEntity
{
  public:
    StepBezierSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBezierSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "BEZIER_SURFACE";}
  public:
    std::string name; // label
    int u_degree; // INTEGER
    int v_degree; // INTEGER
    DMatrix<StepID> control_points_list; // cartesian_point
    StepBSplineSurfaceForm surface_form; // b_spline_surface_form
    StepLogical u_closed; // LOGICAL
    StepLogical v_closed; // LOGICAL
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_bezier_surface(StepFileLine & line);

class StepBSplineSurfaceWithKnots : public StepEntity
{
  public:
    StepBSplineSurfaceWithKnots(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBSplineSurfaceWithKnots() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "B_SPLINE_SURFACE_WITH_KNOTS";}
  public:
    std::string name; // label
    int u_degree; // INTEGER
    int v_degree; // INTEGER
    DMatrix<StepID> control_points_list; // cartesian_point
    StepBSplineSurfaceForm surface_form; // b_spline_surface_form
    StepLogical u_closed; // LOGICAL
    StepLogical v_closed; // LOGICAL
    StepLogical self_intersect; // LOGICAL
    std::vector<int> u_multiplicities; // INTEGER
    std::vector<int> v_multiplicities; // INTEGER
    std::vector<double> u_knots; // parameter_value
    std::vector<double> v_knots; // parameter_value
    StepKnotType knot_spec; // knot_type
};

StepEntity *step_create_b_spline_surface_with_knots(StepFileLine & line);

class StepBSplineCurve : public StepEntity
{
  public:
    StepBSplineCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBSplineCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "B_SPLINE_CURVE";}
  public:
    std::string name; // label
    int degree; // INTEGER
    std::vector<StepID> control_points_list; // cartesian_point
    StepBSplineCurveForm curve_form; // b_spline_curve_form
    StepLogical closed_curve; // LOGICAL
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_b_spline_curve(StepFileLine & line);

class StepTrimmedCurve : public StepEntity
{
  public:
    StepTrimmedCurve(StepID entityId=0) : StepEntity(entityId) , basis_curve(0) {}
    virtual ~StepTrimmedCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "TRIMMED_CURVE";}
  public:
    std::string name; // label
    StepID basis_curve; // curve
    StepTrimmingSelect trim_1[2]; // trimming_select
    StepTrimmingSelect trim_2[2]; // trimming_select
    bool sense_agreement; // BOOLEAN
    StepTrimmingPreference master_representation; // trimming_preference
};

StepEntity *step_create_trimmed_curve(StepFileLine & line);

class StepQuasiUniformCurve : public StepEntity
{
  public:
    StepQuasiUniformCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepQuasiUniformCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "QUASI_UNIFORM_CURVE";}
  public:
    std::string name; // label
    int degree; // INTEGER
    std::vector<StepID> control_points_list; // cartesian_point
    StepBSplineCurveForm curve_form; // b_spline_curve_form
    StepLogical closed_curve; // LOGICAL
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_quasi_uniform_curve(StepFileLine & line);

class StepCompositeCurve : public StepEntity
{
  public:
    StepCompositeCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepCompositeCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "COMPOSITE_CURVE";}
  public:
    std::string name; // label
    std::vector<StepID> segments; // composite_curve_segment
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_composite_curve(StepFileLine & line);

class StepBoundedPcurve : public StepEntity
{
  public:
    StepBoundedPcurve(StepID entityId=0) : StepEntity(entityId) , basis_surface(0), reference_to_curve(0) {}
    virtual ~StepBoundedPcurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "BOUNDED_PCURVE";}
  public:
    std::string name; // label
    StepID basis_surface; // surface
    StepID reference_to_curve; // definitional_representation
};

StepEntity *step_create_bounded_pcurve(StepFileLine & line);

class StepUniformCurve : public StepEntity
{
  public:
    StepUniformCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepUniformCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "UNIFORM_CURVE";}
  public:
    std::string name; // label
    int degree; // INTEGER
    std::vector<StepID> control_points_list; // cartesian_point
    StepBSplineCurveForm curve_form; // b_spline_curve_form
    StepLogical closed_curve; // LOGICAL
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_uniform_curve(StepFileLine & line);

class StepCompositeCurveOnSurface : public StepEntity
{
  public:
    StepCompositeCurveOnSurface(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepCompositeCurveOnSurface() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "COMPOSITE_CURVE_ON_SURFACE";}
  public:
    std::string name; // label
    std::vector<StepID> segments; // composite_curve_segment
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_composite_curve_on_surface(StepFileLine & line);

class StepBezierCurve : public StepEntity
{
  public:
    StepBezierCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBezierCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "BEZIER_CURVE";}
  public:
    std::string name; // label
    int degree; // INTEGER
    std::vector<StepID> control_points_list; // cartesian_point
    StepBSplineCurveForm curve_form; // b_spline_curve_form
    StepLogical closed_curve; // LOGICAL
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_bezier_curve(StepFileLine & line);

class StepRationalBSplineCurve : public StepEntity
{
  public:
    StepRationalBSplineCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepRationalBSplineCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "RATIONAL_B_SPLINE_CURVE";}
  public:
    std::string name; // label
    int degree; // INTEGER
    std::vector<StepID> control_points_list; // cartesian_point
    StepBSplineCurveForm curve_form; // b_spline_curve_form
    StepLogical closed_curve; // LOGICAL
    StepLogical self_intersect; // LOGICAL
    std::vector<double> weights_data; // REAL
};

StepEntity *step_create_rational_b_spline_curve(StepFileLine & line);

class StepBoundaryCurve : public StepEntity
{
  public:
    StepBoundaryCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBoundaryCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "BOUNDARY_CURVE";}
  public:
    std::string name; // label
    std::vector<StepID> segments; // composite_curve_segment
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_boundary_curve(StepFileLine & line);

class StepOuterBoundaryCurve : public StepEntity
{
  public:
    StepOuterBoundaryCurve(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepOuterBoundaryCurve() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "OUTER_BOUNDARY_CURVE";}
  public:
    std::string name; // label
    std::vector<StepID> segments; // composite_curve_segment
    StepLogical self_intersect; // LOGICAL
};

StepEntity *step_create_outer_boundary_curve(StepFileLine & line);

class StepBSplineCurveWithKnots : public StepEntity
{
  public:
    StepBSplineCurveWithKnots(StepID entityId=0) : StepEntity(entityId)  {}
    virtual ~StepBSplineCurveWithKnots() {}
    virtual bool read(StepFileLine & line);
    virtual void write(std::ostream & os) const;
    virtual const char *keyString() const {return "B_SPLINE_CURVE_WITH_KNOTS";}
  public:
    std::string name; // label
    int degree; // INTEGER
    std::vector<StepID> control_points_list; // cartesian_point
    StepBSplineCurveForm curve_form; // b_spline_curve_form
    StepLogical closed_curve; // LOGICAL
    StepLogical self_intersect; // LOGICAL
    std::vector<int> knot_multiplicities; // INTEGER
    std::vector<double> knots; // parameter_value
    StepKnotType knot_spec; // knot_type
};

StepEntity *step_create_b_spline_curve_with_knots(StepFileLine & line);

#endif
