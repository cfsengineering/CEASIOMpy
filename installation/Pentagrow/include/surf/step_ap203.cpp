
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
 #include "stepline.h"

#include "step_ap203.h"

// automatically created by surf/tools/fedex.py -- do not edit

// ------------ StepAheadOrBehind

const char *StepAheadOrBehind::stringrep[] = {
    ".AHEAD.",
    ".BEHIND.",    };

// ------------ StepApprovedItem

const char *StepApprovedItem::stringrep[] = {
    "PRODUCT_DEFINITION_FORMATION",
    "PRODUCT_DEFINITION",
    "CONFIGURATION_EFFECTIVITY",
    "CONFIGURATION_ITEM",
    "SECURITY_CLASSIFICATION",
    "CHANGE_REQUEST",
    "CHANGE",
    "START_REQUEST",
    "START_WORK",
    "CERTIFICATION",
    "CONTRACT",    };

// ------------ StepAxis2Placement

const char *StepAxis2Placement::stringrep[] = {
    "AXIS2_PLACEMENT_2D",
    "AXIS2_PLACEMENT_3D",    };

// ------------ StepBSplineCurveForm

const char *StepBSplineCurveForm::stringrep[] = {
    ".POLYLINE_FORM.",
    ".CIRCULAR_ARC.",
    ".ELLIPTIC_ARC.",
    ".PARABOLIC_ARC.",
    ".HYPERBOLIC_ARC.",
    ".UNSPECIFIED.",    };

// ------------ StepBSplineSurfaceForm

const char *StepBSplineSurfaceForm::stringrep[] = {
    ".PLANE_SURF.",
    ".CYLINDRICAL_SURF.",
    ".CONICAL_SURF.",
    ".SPHERICAL_SURF.",
    ".TOROIDAL_SURF.",
    ".SURF_OF_REVOLUTION.",
    ".RULED_SURF.",
    ".GENERALISED_CONE.",
    ".QUADRIC_SURF.",
    ".SURF_OF_LINEAR_EXTRUSION.",
    ".UNSPECIFIED.",    };

// ------------ StepBooleanOperand

const char *StepBooleanOperand::stringrep[] = {
    "SOLID_MODEL",    };

// ------------ StepCertifiedItem

const char *StepCertifiedItem::stringrep[] = {
    "SUPPLIED_PART_RELATIONSHIP",    };

// ------------ StepChangeRequestItem

const char *StepChangeRequestItem::stringrep[] = {
    "PRODUCT_DEFINITION_FORMATION",    };

// ------------ StepCharacterizedDefinition

const char *StepCharacterizedDefinition::stringrep[] = {
    "CHARACTERIZED_PRODUCT_DEFINITION",
    "SHAPE_DEFINITION",    };

// ------------ StepCharacterizedProductDefinition

const char *StepCharacterizedProductDefinition::stringrep[] = {
    "PRODUCT_DEFINITION",
    "PRODUCT_DEFINITION_RELATIONSHIP",    };

// ------------ StepClassifiedItem

const char *StepClassifiedItem::stringrep[] = {
    "PRODUCT_DEFINITION_FORMATION",
    "ASSEMBLY_COMPONENT_USAGE",    };

// ------------ StepContractedItem

const char *StepContractedItem::stringrep[] = {
    "PRODUCT_DEFINITION_FORMATION",    };

// ------------ StepCurveOnSurface

const char *StepCurveOnSurface::stringrep[] = {
    "PCURVE",
    "SURFACE_CURVE",
    "COMPOSITE_CURVE_ON_SURFACE",    };

// ------------ StepDateTimeItem

const char *StepDateTimeItem::stringrep[] = {
    "PRODUCT_DEFINITION",
    "CHANGE_REQUEST",
    "START_REQUEST",
    "CHANGE",
    "START_WORK",
    "APPROVAL_PERSON_ORGANIZATION",
    "CONTRACT",
    "SECURITY_CLASSIFICATION",
    "CERTIFICATION",    };

// ------------ StepDateTimeSelect

const char *StepDateTimeSelect::stringrep[] = {
    "DATE",
    "LOCAL_TIME",
    "DATE_AND_TIME",    };

// ------------ StepFoundedItemSelect

const char *StepFoundedItemSelect::stringrep[] = {
    "FOUNDED_ITEM",
    "REPRESENTATION_ITEM",    };

// ------------ StepGeometricSetSelect

const char *StepGeometricSetSelect::stringrep[] = {
    "POINT",
    "CURVE",
    "SURFACE",    };

// ------------ StepKnotType

const char *StepKnotType::stringrep[] = {
    ".UNIFORM_KNOTS.",
    ".UNSPECIFIED.",
    ".QUASI_UNIFORM_KNOTS.",
    ".PIECEWISE_BEZIER_KNOTS.",    };

// ------------ StepMeasureValue

const char *StepMeasureValue::stringrep[] = {
    "LENGTH_MEASURE",
    "MASS_MEASURE",
    "PLANE_ANGLE_MEASURE",
    "SOLID_ANGLE_MEASURE",
    "AREA_MEASURE",
    "VOLUME_MEASURE",
    "PARAMETER_VALUE",
    "CONTEXT_DEPENDENT_MEASURE",
    "DESCRIPTIVE_MEASURE",
    "POSITIVE_LENGTH_MEASURE",
    "POSITIVE_PLANE_ANGLE_MEASURE",
    "COUNT_MEASURE",    };

// ------------ StepPcurveOrSurface

const char *StepPcurveOrSurface::stringrep[] = {
    "PCURVE",
    "SURFACE",    };

// ------------ StepPersonOrganizationItem

const char *StepPersonOrganizationItem::stringrep[] = {
    "CHANGE",
    "START_WORK",
    "CHANGE_REQUEST",
    "START_REQUEST",
    "CONFIGURATION_ITEM",
    "PRODUCT",
    "PRODUCT_DEFINITION_FORMATION",
    "PRODUCT_DEFINITION",
    "CONTRACT",
    "SECURITY_CLASSIFICATION",    };

// ------------ StepPersonOrganizationSelect

const char *StepPersonOrganizationSelect::stringrep[] = {
    "PERSON",
    "ORGANIZATION",
    "PERSON_AND_ORGANIZATION",    };

// ------------ StepPreferredSurfaceCurveRepresentation

const char *StepPreferredSurfaceCurveRepresentation::stringrep[] = {
    ".CURVE_3D.",
    ".PCURVE_S1.",
    ".PCURVE_S2.",    };

// ------------ StepReversibleTopology

const char *StepReversibleTopology::stringrep[] = {
    "REVERSIBLE_TOPOLOGY_ITEM",
    "LIST_OF_REVERSIBLE_TOPOLOGY_ITEM",
    "SET_OF_REVERSIBLE_TOPOLOGY_ITEM",    };

// ------------ StepReversibleTopologyItem

const char *StepReversibleTopologyItem::stringrep[] = {
    "EDGE",
    "PATH",
    "FACE",
    "FACE_BOUND",
    "CLOSED_SHELL",
    "OPEN_SHELL",    };

// ------------ StepShapeDefinition

const char *StepShapeDefinition::stringrep[] = {
    "PRODUCT_DEFINITION_SHAPE",
    "SHAPE_ASPECT",
    "SHAPE_ASPECT_RELATIONSHIP",    };

// ------------ StepShell

const char *StepShell::stringrep[] = {
    "VERTEX_SHELL",
    "WIRE_SHELL",
    "OPEN_SHELL",
    "CLOSED_SHELL",    };

// ------------ StepSiPrefix

const char *StepSiPrefix::stringrep[] = {
    ".EXA.",
    ".PETA.",
    ".TERA.",
    ".GIGA.",
    ".MEGA.",
    ".KILO.",
    ".HECTO.",
    ".DECA.",
    ".DECI.",
    ".CENTI.",
    ".MILLI.",
    ".MICRO.",
    ".NANO.",
    ".PICO.",
    ".FEMTO.",
    ".ATTO.",    };

// ------------ StepSiUnitName

const char *StepSiUnitName::stringrep[] = {
    ".METRE.",
    ".GRAM.",
    ".SECOND.",
    ".AMPERE.",
    ".KELVIN.",
    ".MOLE.",
    ".CANDELA.",
    ".RADIAN.",
    ".STERADIAN.",
    ".HERTZ.",
    ".NEWTON.",
    ".PASCAL.",
    ".JOULE.",
    ".WATT.",
    ".COULOMB.",
    ".VOLT.",
    ".FARAD.",
    ".OHM.",
    ".SIEMENS.",
    ".WEBER.",
    ".TESLA.",
    ".HENRY.",
    ".DEGREE_CELSIUS.",
    ".LUMEN.",
    ".LUX.",
    ".BECQUEREL.",
    ".GRAY.",
    ".SIEVERT.",    };

// ------------ StepSource

const char *StepSource::stringrep[] = {
    ".MADE.",
    ".BOUGHT.",
    ".NOT_KNOWN.",    };

// ------------ StepSpecifiedItem

const char *StepSpecifiedItem::stringrep[] = {
    "PRODUCT_DEFINITION",
    "SHAPE_ASPECT",    };

// ------------ StepStartRequestItem

const char *StepStartRequestItem::stringrep[] = {
    "PRODUCT_DEFINITION_FORMATION",    };

// ------------ StepSupportedItem

const char *StepSupportedItem::stringrep[] = {
    "ACTION_DIRECTIVE",
    "ACTION",
    "ACTION_METHOD",    };

// ------------ StepSurfaceModel

const char *StepSurfaceModel::stringrep[] = {
    "SHELL_BASED_SURFACE_MODEL",    };

// ------------ StepTransformation

const char *StepTransformation::stringrep[] = {
    "ITEM_DEFINED_TRANSFORMATION",
    "FUNCTIONALLY_DEFINED_TRANSFORMATION",    };

// ------------ StepTransitionCode

const char *StepTransitionCode::stringrep[] = {
    ".DISCONTINUOUS.",
    ".CONTINUOUS.",
    ".CONT_SAME_GRADIENT.",
    ".CONT_SAME_GRADIENT_SAME_CURVATURE.",    };

// ------------ StepTrimmingPreference

const char *StepTrimmingPreference::stringrep[] = {
    ".CARTESIAN.",
    ".PARAMETER.",
    ".UNSPECIFIED.",    };

// ------------ StepTrimmingSelect

const char *StepTrimmingSelect::stringrep[] = {
    "CARTESIAN_POINT",
    "PARAMETER_VALUE",    };

// ------------ StepUnit

const char *StepUnit::stringrep[] = {
    "NAMED_UNIT",    };

// ------------ StepVectorOrDirection

const char *StepVectorOrDirection::stringrep[] = {
    "VECTOR",
    "DIRECTION",    };

// ------------ StepWireframeModel

const char *StepWireframeModel::stringrep[] = {
    "SHELL_BASED_WIREFRAME_MODEL",
    "EDGE_BASED_WIREFRAME_MODEL",    };

// ------------ StepWorkItem

const char *StepWorkItem::stringrep[] = {
    "PRODUCT_DEFINITION_FORMATION",    };

// ------------ StepContractAssignment

bool StepContractAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_contract);
  return ok;
}

void StepContractAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_contract);
}

StepEntity *step_create_contract_assignment(StepFileLine & line)
{
  StepContractAssignment *entity = new StepContractAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepRepresentationMap

bool StepRepresentationMap::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(mapping_origin);
  ok &= line.readAttr(mapped_representation);
  ok &= line.readAttr(map_usage);
  return ok;
}

void StepRepresentationMap::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, mapping_origin); os << ',';
  StepFileLine::writeAttr(os, mapped_representation); os << ',';
  StepFileLine::writeAttr(os, map_usage);
}

StepEntity *step_create_representation_map(StepFileLine & line)
{
  StepRepresentationMap *entity = new StepRepresentationMap;
  entity->read(line);
  return entity;
}
// ------------ StepCertificationAssignment

bool StepCertificationAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_certification);
  return ok;
}

void StepCertificationAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_certification);
}

StepEntity *step_create_certification_assignment(StepFileLine & line)
{
  StepCertificationAssignment *entity = new StepCertificationAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepProductCategoryRelationship

bool StepProductCategoryRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(category);
  ok &= line.readAttr(sub_category);
  return ok;
}

void StepProductCategoryRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, category); os << ',';
  StepFileLine::writeAttr(os, sub_category);
}

StepEntity *step_create_product_category_relationship(StepFileLine & line)
{
  StepProductCategoryRelationship *entity = new StepProductCategoryRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepFoundedItem

bool StepFoundedItem::read(StepFileLine &)
{
  bool ok = true;
  return ok;
}

void StepFoundedItem::write(std::ostream &) const
{
}

StepEntity *step_create_founded_item(StepFileLine & line)
{
  StepFoundedItem *entity = new StepFoundedItem;
  entity->read(line);
  return entity;
}
// ------------ StepActionStatus

bool StepActionStatus::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(status);
  ok &= line.readAttr(assigned_action);
  return ok;
}

void StepActionStatus::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, status); os << ',';
  StepFileLine::writeAttr(os, assigned_action);
}

StepEntity *step_create_action_status(StepFileLine & line)
{
  StepActionStatus *entity = new StepActionStatus;
  entity->read(line);
  return entity;
}
// ------------ StepProduct

bool StepProduct::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(frame_of_reference);
  return ok;
}

void StepProduct::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference);
}

StepEntity *step_create_product(StepFileLine & line)
{
  StepProduct *entity = new StepProduct;
  entity->read(line);
  return entity;
}
// ------------ StepApprovalRelationship

bool StepApprovalRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_approval);
  ok &= line.readAttr(related_approval);
  return ok;
}

void StepApprovalRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_approval); os << ',';
  StepFileLine::writeAttr(os, related_approval);
}

StepEntity *step_create_approval_relationship(StepFileLine & line)
{
  StepApprovalRelationship *entity = new StepApprovalRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepContract

bool StepContract::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(purpose);
  ok &= line.readAttr(kind);
  return ok;
}

void StepContract::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, purpose); os << ',';
  StepFileLine::writeAttr(os, kind);
}

StepEntity *step_create_contract(StepFileLine & line)
{
  StepContract *entity = new StepContract;
  entity->read(line);
  return entity;
}
// ------------ StepRepresentation

bool StepRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_representation(StepFileLine & line)
{
  StepRepresentation *entity = new StepRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepCcDesignCertification

bool StepCcDesignCertification::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_certification);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepCcDesignCertification::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_certification); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_cc_design_certification(StepFileLine & line)
{
  StepCcDesignCertification *entity = new StepCcDesignCertification;
  entity->read(line);
  return entity;
}
// ------------ StepShapeRepresentation

bool StepShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_shape_representation(StepFileLine & line)
{
  StepShapeRepresentation *entity = new StepShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepOrganization

bool StepOrganization::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.option() ? line.readAttr(id) : line.skipAttr();
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  return ok;
}

void StepOrganization::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_organization(StepFileLine & line)
{
  StepOrganization *entity = new StepOrganization;
  entity->read(line);
  return entity;
}
// ------------ StepProductCategory

bool StepProductCategory::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.option() ? line.readAttr(description) : line.skipAttr();
  return ok;
}

void StepProductCategory::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_product_category(StepFileLine & line)
{
  StepProductCategory *entity = new StepProductCategory;
  entity->read(line);
  return entity;
}
// ------------ StepApprovalAssignment

bool StepApprovalAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_approval);
  return ok;
}

void StepApprovalAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_approval);
}

StepEntity *step_create_approval_assignment(StepFileLine & line)
{
  StepApprovalAssignment *entity = new StepApprovalAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepConfigurationItem

bool StepConfigurationItem::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.option() ? line.readAttr(description) : line.skipAttr();
  ok &= line.readAttr(item_concept);
  ok &= line.option() ? line.readAttr(purpose) : line.skipAttr();
  return ok;
}

void StepConfigurationItem::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, item_concept); os << ',';
  StepFileLine::writeAttr(os, purpose);
}

StepEntity *step_create_configuration_item(StepFileLine & line)
{
  StepConfigurationItem *entity = new StepConfigurationItem;
  entity->read(line);
  return entity;
}
// ------------ StepProductRelatedProductCategory

bool StepProductRelatedProductCategory::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.option() ? line.readAttr(description) : line.skipAttr();
  ok &= line.readAttr(products);
  return ok;
}

void StepProductRelatedProductCategory::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, products);
}

StepEntity *step_create_product_related_product_category(StepFileLine & line)
{
  StepProductRelatedProductCategory *entity = new StepProductRelatedProductCategory;
  entity->read(line);
  return entity;
}
// ------------ StepDateTimeRole

bool StepDateTimeRole::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepDateTimeRole::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_date_time_role(StepFileLine & line)
{
  StepDateTimeRole *entity = new StepDateTimeRole;
  entity->read(line);
  return entity;
}
// ------------ StepEffectivity

bool StepEffectivity::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  return ok;
}

void StepEffectivity::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id);
}

StepEntity *step_create_effectivity(StepFileLine & line)
{
  StepEffectivity *entity = new StepEffectivity;
  entity->read(line);
  return entity;
}
// ------------ StepApplicationContextElement

bool StepApplicationContextElement::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(frame_of_reference);
  return ok;
}

void StepApplicationContextElement::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference);
}

StepEntity *step_create_application_context_element(StepFileLine & line)
{
  StepApplicationContextElement *entity = new StepApplicationContextElement;
  entity->read(line);
  return entity;
}
// ------------ StepMeasureWithUnit

bool StepMeasureWithUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= value_component.read(line);
  ok &= unit_component.read(line);
  return ok;
}

void StepMeasureWithUnit::write(std::ostream & os) const
{
  value_component.write(os); os << ',';
  unit_component.write(os);
}

StepEntity *step_create_measure_with_unit(StepFileLine & line)
{
  StepMeasureWithUnit *entity = new StepMeasureWithUnit;
  entity->read(line);
  return entity;
}
// ------------ StepDimensionalExponents

bool StepDimensionalExponents::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(length_exponent);
  ok &= line.readAttr(mass_exponent);
  ok &= line.readAttr(time_exponent);
  ok &= line.readAttr(electric_current_exponent);
  ok &= line.readAttr(thermodynamic_temperature_exponent);
  ok &= line.readAttr(amount_of_substance_exponent);
  ok &= line.readAttr(luminous_intensity_exponent);
  return ok;
}

void StepDimensionalExponents::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, length_exponent); os << ',';
  StepFileLine::writeAttr(os, mass_exponent); os << ',';
  StepFileLine::writeAttr(os, time_exponent); os << ',';
  StepFileLine::writeAttr(os, electric_current_exponent); os << ',';
  StepFileLine::writeAttr(os, thermodynamic_temperature_exponent); os << ',';
  StepFileLine::writeAttr(os, amount_of_substance_exponent); os << ',';
  StepFileLine::writeAttr(os, luminous_intensity_exponent);
}

StepEntity *step_create_dimensional_exponents(StepFileLine & line)
{
  StepDimensionalExponents *entity = new StepDimensionalExponents;
  entity->read(line);
  return entity;
}
// ------------ StepSerialNumberedEffectivity

bool StepSerialNumberedEffectivity::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(effectivity_start_id);
  ok &= line.option() ? line.readAttr(effectivity_end_id) : line.skipAttr();
  return ok;
}

void StepSerialNumberedEffectivity::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, effectivity_start_id); os << ',';
  StepFileLine::writeAttr(os, effectivity_end_id);
}

StepEntity *step_create_serial_numbered_effectivity(StepFileLine & line)
{
  StepSerialNumberedEffectivity *entity = new StepSerialNumberedEffectivity;
  entity->read(line);
  return entity;
}
// ------------ StepVersionedActionRequest

bool StepVersionedActionRequest::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(version);
  ok &= line.readAttr(purpose);
  ok &= line.readAttr(description);
  return ok;
}

void StepVersionedActionRequest::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, version); os << ',';
  StepFileLine::writeAttr(os, purpose); os << ',';
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_versioned_action_request(StepFileLine & line)
{
  StepVersionedActionRequest *entity = new StepVersionedActionRequest;
  entity->read(line);
  return entity;
}
// ------------ StepAdvancedBrepShapeRepresentation

bool StepAdvancedBrepShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepAdvancedBrepShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_advanced_brep_shape_representation(StepFileLine & line)
{
  StepAdvancedBrepShapeRepresentation *entity = new StepAdvancedBrepShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinitionContext

bool StepProductDefinitionContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(frame_of_reference);
  ok &= line.readAttr(life_cycle_stage);
  return ok;
}

void StepProductDefinitionContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference); os << ',';
  StepFileLine::writeAttr(os, life_cycle_stage);
}

StepEntity *step_create_product_definition_context(StepFileLine & line)
{
  StepProductDefinitionContext *entity = new StepProductDefinitionContext;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinitionEffectivity

bool StepProductDefinitionEffectivity::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(usage);
  return ok;
}

void StepProductDefinitionEffectivity::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, usage);
}

StepEntity *step_create_product_definition_effectivity(StepFileLine & line)
{
  StepProductDefinitionEffectivity *entity = new StepProductDefinitionEffectivity;
  entity->read(line);
  return entity;
}
// ------------ StepDocument

bool StepDocument::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(kind);
  return ok;
}

void StepDocument::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, kind);
}

StepEntity *step_create_document(StepFileLine & line)
{
  StepDocument *entity = new StepDocument;
  entity->read(line);
  return entity;
}
// ------------ StepGeometricallyBoundedSurfaceShapeRepresentation

bool StepGeometricallyBoundedSurfaceShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepGeometricallyBoundedSurfaceShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_geometrically_bounded_surface_shape_representation(StepFileLine & line)
{
  StepGeometricallyBoundedSurfaceShapeRepresentation *entity = new StepGeometricallyBoundedSurfaceShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepAddress

bool StepAddress::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.option() ? line.readAttr(internal_location) : line.skipAttr();
  ok &= line.option() ? line.readAttr(street_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(street) : line.skipAttr();
  ok &= line.option() ? line.readAttr(postal_box) : line.skipAttr();
  ok &= line.option() ? line.readAttr(town) : line.skipAttr();
  ok &= line.option() ? line.readAttr(region) : line.skipAttr();
  ok &= line.option() ? line.readAttr(postal_code) : line.skipAttr();
  ok &= line.option() ? line.readAttr(country) : line.skipAttr();
  ok &= line.option() ? line.readAttr(facsimile_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(telephone_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(electronic_mail_address) : line.skipAttr();
  ok &= line.option() ? line.readAttr(telex_number) : line.skipAttr();
  return ok;
}

void StepAddress::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, internal_location); os << ',';
  StepFileLine::writeAttr(os, street_number); os << ',';
  StepFileLine::writeAttr(os, street); os << ',';
  StepFileLine::writeAttr(os, postal_box); os << ',';
  StepFileLine::writeAttr(os, town); os << ',';
  StepFileLine::writeAttr(os, region); os << ',';
  StepFileLine::writeAttr(os, postal_code); os << ',';
  StepFileLine::writeAttr(os, country); os << ',';
  StepFileLine::writeAttr(os, facsimile_number); os << ',';
  StepFileLine::writeAttr(os, telephone_number); os << ',';
  StepFileLine::writeAttr(os, electronic_mail_address); os << ',';
  StepFileLine::writeAttr(os, telex_number);
}

StepEntity *step_create_address(StepFileLine & line)
{
  StepAddress *entity = new StepAddress;
  entity->read(line);
  return entity;
}
// ------------ StepMassMeasureWithUnit

bool StepMassMeasureWithUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= value_component.read(line);
  ok &= unit_component.read(line);
  return ok;
}

void StepMassMeasureWithUnit::write(std::ostream & os) const
{
  value_component.write(os); os << ',';
  unit_component.write(os);
}

StepEntity *step_create_mass_measure_with_unit(StepFileLine & line)
{
  StepMassMeasureWithUnit *entity = new StepMassMeasureWithUnit;
  entity->read(line);
  return entity;
}
// ------------ StepPropertyDefinition

bool StepPropertyDefinition::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= definition.read(line);
  return ok;
}

void StepPropertyDefinition::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  definition.write(os);
}

StepEntity *step_create_property_definition(StepFileLine & line)
{
  StepPropertyDefinition *entity = new StepPropertyDefinition;
  entity->read(line);
  return entity;
}
// ------------ StepOrganizationalProject

bool StepOrganizationalProject::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(responsible_organizations);
  return ok;
}

void StepOrganizationalProject::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, responsible_organizations);
}

StepEntity *step_create_organizational_project(StepFileLine & line)
{
  StepOrganizationalProject *entity = new StepOrganizationalProject;
  entity->read(line);
  return entity;
}
// ------------ StepProductConcept

bool StepProductConcept::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(market_context);
  return ok;
}

void StepProductConcept::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, market_context);
}

StepEntity *step_create_product_concept(StepFileLine & line)
{
  StepProductConcept *entity = new StepProductConcept;
  entity->read(line);
  return entity;
}
// ------------ StepEdgeBasedWireframeShapeRepresentation

bool StepEdgeBasedWireframeShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepEdgeBasedWireframeShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_edge_based_wireframe_shape_representation(StepFileLine & line)
{
  StepEdgeBasedWireframeShapeRepresentation *entity = new StepEdgeBasedWireframeShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepContractType

bool StepContractType::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(description);
  return ok;
}

void StepContractType::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_contract_type(StepFileLine & line)
{
  StepContractType *entity = new StepContractType;
  entity->read(line);
  return entity;
}
// ------------ StepProductConceptContext

bool StepProductConceptContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(frame_of_reference);
  ok &= line.readAttr(market_segment_type);
  return ok;
}

void StepProductConceptContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference); os << ',';
  StepFileLine::writeAttr(os, market_segment_type);
}

StepEntity *step_create_product_concept_context(StepFileLine & line)
{
  StepProductConceptContext *entity = new StepProductConceptContext;
  entity->read(line);
  return entity;
}
// ------------ StepDate

bool StepDate::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(year_component);
  return ok;
}

void StepDate::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, year_component);
}

StepEntity *step_create_date(StepFileLine & line)
{
  StepDate *entity = new StepDate;
  entity->read(line);
  return entity;
}
// ------------ StepSecurityClassificationAssignment

bool StepSecurityClassificationAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_security_classification);
  return ok;
}

void StepSecurityClassificationAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_security_classification);
}

StepEntity *step_create_security_classification_assignment(StepFileLine & line)
{
  StepSecurityClassificationAssignment *entity = new StepSecurityClassificationAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepPerson

bool StepPerson::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.option() ? line.readAttr(last_name) : line.skipAttr();
  ok &= line.option() ? line.readAttr(first_name) : line.skipAttr();
  ok &= line.option() ? line.readAttr(middle_names) : line.skipAttr();
  ok &= line.option() ? line.readAttr(prefix_titles) : line.skipAttr();
  ok &= line.option() ? line.readAttr(suffix_titles) : line.skipAttr();
  return ok;
}

void StepPerson::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, last_name); os << ',';
  StepFileLine::writeAttr(os, first_name); os << ',';
  StepFileLine::writeAttr(os, middle_names); os << ',';
  StepFileLine::writeAttr(os, prefix_titles); os << ',';
  StepFileLine::writeAttr(os, suffix_titles);
}

StepEntity *step_create_person(StepFileLine & line)
{
  StepPerson *entity = new StepPerson;
  entity->read(line);
  return entity;
}
// ------------ StepCcDesignContract

bool StepCcDesignContract::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_contract);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepCcDesignContract::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_contract); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_cc_design_contract(StepFileLine & line)
{
  StepCcDesignContract *entity = new StepCcDesignContract;
  entity->read(line);
  return entity;
}
// ------------ StepApprovalStatus

bool StepApprovalStatus::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepApprovalStatus::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_approval_status(StepFileLine & line)
{
  StepApprovalStatus *entity = new StepApprovalStatus;
  entity->read(line);
  return entity;
}
// ------------ StepFacetedBrepShapeRepresentation

bool StepFacetedBrepShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepFacetedBrepShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_faceted_brep_shape_representation(StepFileLine & line)
{
  StepFacetedBrepShapeRepresentation *entity = new StepFacetedBrepShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepSecurityClassificationLevel

bool StepSecurityClassificationLevel::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepSecurityClassificationLevel::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_security_classification_level(StepFileLine & line)
{
  StepSecurityClassificationLevel *entity = new StepSecurityClassificationLevel;
  entity->read(line);
  return entity;
}
// ------------ StepDefinitionalRepresentation

bool StepDefinitionalRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepDefinitionalRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_definitional_representation(StepFileLine & line)
{
  StepDefinitionalRepresentation *entity = new StepDefinitionalRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepSurfacePatch

bool StepSurfacePatch::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(parent_surface);
  ok &= u_transition.read(line);
  ok &= v_transition.read(line);
  ok &= line.readAttr(u_sense);
  ok &= line.readAttr(v_sense);
  ok &= line.readAttr(using_surfaces);
  return ok;
}

void StepSurfacePatch::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, parent_surface); os << ',';
  u_transition.write(os); os << ',';
  v_transition.write(os); os << ',';
  StepFileLine::writeAttr(os, u_sense); os << ',';
  StepFileLine::writeAttr(os, v_sense); os << ',';
  StepFileLine::writeAttr(os, using_surfaces);
}

StepEntity *step_create_surface_patch(StepFileLine & line)
{
  StepSurfacePatch *entity = new StepSurfacePatch;
  entity->read(line);
  return entity;
}
// ------------ StepCcDesignApproval

bool StepCcDesignApproval::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_approval);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepCcDesignApproval::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_approval); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_cc_design_approval(StepFileLine & line)
{
  StepCcDesignApproval *entity = new StepCcDesignApproval;
  entity->read(line);
  return entity;
}
// ------------ StepWeekOfYearAndDayDate

bool StepWeekOfYearAndDayDate::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(year_component);
  ok &= line.readAttr(week_component);
  ok &= line.option() ? line.readAttr(day_component) : line.skipAttr();
  return ok;
}

void StepWeekOfYearAndDayDate::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, year_component); os << ',';
  StepFileLine::writeAttr(os, week_component); os << ',';
  StepFileLine::writeAttr(os, day_component);
}

StepEntity *step_create_week_of_year_and_day_date(StepFileLine & line)
{
  StepWeekOfYearAndDayDate *entity = new StepWeekOfYearAndDayDate;
  entity->read(line);
  return entity;
}
// ------------ StepDesignContext

bool StepDesignContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(frame_of_reference);
  ok &= line.readAttr(life_cycle_stage);
  return ok;
}

void StepDesignContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference); os << ',';
  StepFileLine::writeAttr(os, life_cycle_stage);
}

StepEntity *step_create_design_context(StepFileLine & line)
{
  StepDesignContext *entity = new StepDesignContext;
  entity->read(line);
  return entity;
}
// ------------ StepLocalTime

bool StepLocalTime::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(hour_component);
  ok &= line.option() ? line.readAttr(minute_component) : line.skipAttr();
  ok &= line.option() ? line.readAttr(second_component) : line.skipAttr();
  ok &= line.readAttr(zone);
  return ok;
}

void StepLocalTime::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, hour_component); os << ',';
  StepFileLine::writeAttr(os, minute_component); os << ',';
  StepFileLine::writeAttr(os, second_component); os << ',';
  StepFileLine::writeAttr(os, zone);
}

StepEntity *step_create_local_time(StepFileLine & line)
{
  StepLocalTime *entity = new StepLocalTime;
  entity->read(line);
  return entity;
}
// ------------ StepPropertyDefinitionRepresentation

bool StepPropertyDefinitionRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(definition);
  ok &= line.readAttr(used_representation);
  return ok;
}

void StepPropertyDefinitionRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, definition); os << ',';
  StepFileLine::writeAttr(os, used_representation);
}

StepEntity *step_create_property_definition_representation(StepFileLine & line)
{
  StepPropertyDefinitionRepresentation *entity = new StepPropertyDefinitionRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepActionRequestStatus

bool StepActionRequestStatus::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(status);
  ok &= line.readAttr(assigned_request);
  return ok;
}

void StepActionRequestStatus::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, status); os << ',';
  StepFileLine::writeAttr(os, assigned_request);
}

StepEntity *step_create_action_request_status(StepFileLine & line)
{
  StepActionRequestStatus *entity = new StepActionRequestStatus;
  entity->read(line);
  return entity;
}
// ------------ StepShapeDefinitionRepresentation

bool StepShapeDefinitionRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(definition);
  ok &= line.readAttr(used_representation);
  return ok;
}

void StepShapeDefinitionRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, definition); os << ',';
  StepFileLine::writeAttr(os, used_representation);
}

StepEntity *step_create_shape_definition_representation(StepFileLine & line)
{
  StepShapeDefinitionRepresentation *entity = new StepShapeDefinitionRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepDocumentReference

bool StepDocumentReference::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_document);
  ok &= line.readAttr(source);
  return ok;
}

void StepDocumentReference::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_document); os << ',';
  StepFileLine::writeAttr(os, source);
}

StepEntity *step_create_document_reference(StepFileLine & line)
{
  StepDocumentReference *entity = new StepDocumentReference;
  entity->read(line);
  return entity;
}
// ------------ StepNamedUnit

bool StepNamedUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  return ok;
}

void StepNamedUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions);
}

StepEntity *step_create_named_unit(StepFileLine & line)
{
  StepNamedUnit *entity = new StepNamedUnit;
  entity->read(line);
  return entity;
}
// ------------ StepActionRequestAssignment

bool StepActionRequestAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_action_request);
  return ok;
}

void StepActionRequestAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_action_request);
}

StepEntity *step_create_action_request_assignment(StepFileLine & line)
{
  StepActionRequestAssignment *entity = new StepActionRequestAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepDateAndTime

bool StepDateAndTime::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(date_component);
  ok &= line.readAttr(time_component);
  return ok;
}

void StepDateAndTime::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, date_component); os << ',';
  StepFileLine::writeAttr(os, time_component);
}

StepEntity *step_create_date_and_time(StepFileLine & line)
{
  StepDateAndTime *entity = new StepDateAndTime;
  entity->read(line);
  return entity;
}
// ------------ StepConfigurationDesign

bool StepConfigurationDesign::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(configuration);
  ok &= line.readAttr(design);
  return ok;
}

void StepConfigurationDesign::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, configuration); os << ',';
  StepFileLine::writeAttr(os, design);
}

StepEntity *step_create_configuration_design(StepFileLine & line)
{
  StepConfigurationDesign *entity = new StepConfigurationDesign;
  entity->read(line);
  return entity;
}
// ------------ StepContextDependentShapeRepresentation

bool StepContextDependentShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(representation_relation);
  ok &= line.readAttr(represented_product_relation);
  return ok;
}

void StepContextDependentShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, representation_relation); os << ',';
  StepFileLine::writeAttr(os, represented_product_relation);
}

StepEntity *step_create_context_dependent_shape_representation(StepFileLine & line)
{
  StepContextDependentShapeRepresentation *entity = new StepContextDependentShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepRepresentationItem

bool StepRepresentationItem::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepRepresentationItem::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_representation_item(StepFileLine & line)
{
  StepRepresentationItem *entity = new StepRepresentationItem;
  entity->read(line);
  return entity;
}
// ------------ StepApplicationContext

bool StepApplicationContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(application);
  ok &= line.readAttr(context_elements);
  return ok;
}

void StepApplicationContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, application); os << ',';
  StepFileLine::writeAttr(os, context_elements);
}

StepEntity *step_create_application_context(StepFileLine & line)
{
  StepApplicationContext *entity = new StepApplicationContext;
  entity->read(line);
  return entity;
}
// ------------ StepOrdinalDate

bool StepOrdinalDate::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(year_component);
  ok &= line.readAttr(day_component);
  return ok;
}

void StepOrdinalDate::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, year_component); os << ',';
  StepFileLine::writeAttr(os, day_component);
}

StepEntity *step_create_ordinal_date(StepFileLine & line)
{
  StepOrdinalDate *entity = new StepOrdinalDate;
  entity->read(line);
  return entity;
}
// ------------ StepCertificationType

bool StepCertificationType::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(description);
  return ok;
}

void StepCertificationType::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_certification_type(StepFileLine & line)
{
  StepCertificationType *entity = new StepCertificationType;
  entity->read(line);
  return entity;
}
// ------------ StepItemDefinedTransformation

bool StepItemDefinedTransformation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(transform_item_1);
  ok &= line.readAttr(transform_item_2);
  return ok;
}

void StepItemDefinedTransformation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, transform_item_1); os << ',';
  StepFileLine::writeAttr(os, transform_item_2);
}

StepEntity *step_create_item_defined_transformation(StepFileLine & line)
{
  StepItemDefinedTransformation *entity = new StepItemDefinedTransformation;
  entity->read(line);
  return entity;
}
// ------------ StepConfigurationEffectivity

bool StepConfigurationEffectivity::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(usage);
  ok &= line.readAttr(configuration);
  return ok;
}

void StepConfigurationEffectivity::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, usage); os << ',';
  StepFileLine::writeAttr(os, configuration);
}

StepEntity *step_create_configuration_effectivity(StepFileLine & line)
{
  StepConfigurationEffectivity *entity = new StepConfigurationEffectivity;
  entity->read(line);
  return entity;
}
// ------------ StepDocumentWithClass

bool StepDocumentWithClass::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(kind);
  ok &= line.readAttr(identifier_class);
  return ok;
}

void StepDocumentWithClass::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, kind); os << ',';
  StepFileLine::writeAttr(os, identifier_class);
}

StepEntity *step_create_document_with_class(StepFileLine & line)
{
  StepDocumentWithClass *entity = new StepDocumentWithClass;
  entity->read(line);
  return entity;
}
// ------------ StepProductContext

bool StepProductContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(frame_of_reference);
  ok &= line.readAttr(discipline_type);
  return ok;
}

void StepProductContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference); os << ',';
  StepFileLine::writeAttr(os, discipline_type);
}

StepEntity *step_create_product_context(StepFileLine & line)
{
  StepProductContext *entity = new StepProductContext;
  entity->read(line);
  return entity;
}
// ------------ StepDocumentUsageConstraint

bool StepDocumentUsageConstraint::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(source);
  ok &= line.readAttr(subject_element);
  ok &= line.readAttr(subject_element_value);
  return ok;
}

void StepDocumentUsageConstraint::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, source); os << ',';
  StepFileLine::writeAttr(os, subject_element); os << ',';
  StepFileLine::writeAttr(os, subject_element_value);
}

StepEntity *step_create_document_usage_constraint(StepFileLine & line)
{
  StepDocumentUsageConstraint *entity = new StepDocumentUsageConstraint;
  entity->read(line);
  return entity;
}
// ------------ StepCcDesignSpecificationReference

bool StepCcDesignSpecificationReference::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_document);
  ok &= line.readAttr(source);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepCcDesignSpecificationReference::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_document); os << ',';
  StepFileLine::writeAttr(os, source); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_cc_design_specification_reference(StepFileLine & line)
{
  StepCcDesignSpecificationReference *entity = new StepCcDesignSpecificationReference;
  entity->read(line);
  return entity;
}
// ------------ StepFunctionallyDefinedTransformation

bool StepFunctionallyDefinedTransformation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  return ok;
}

void StepFunctionallyDefinedTransformation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_functionally_defined_transformation(StepFileLine & line)
{
  StepFunctionallyDefinedTransformation *entity = new StepFunctionallyDefinedTransformation;
  entity->read(line);
  return entity;
}
// ------------ StepPersonalAddress

bool StepPersonalAddress::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.option() ? line.readAttr(internal_location) : line.skipAttr();
  ok &= line.option() ? line.readAttr(street_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(street) : line.skipAttr();
  ok &= line.option() ? line.readAttr(postal_box) : line.skipAttr();
  ok &= line.option() ? line.readAttr(town) : line.skipAttr();
  ok &= line.option() ? line.readAttr(region) : line.skipAttr();
  ok &= line.option() ? line.readAttr(postal_code) : line.skipAttr();
  ok &= line.option() ? line.readAttr(country) : line.skipAttr();
  ok &= line.option() ? line.readAttr(facsimile_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(telephone_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(electronic_mail_address) : line.skipAttr();
  ok &= line.option() ? line.readAttr(telex_number) : line.skipAttr();
  ok &= line.readAttr(people);
  ok &= line.readAttr(description);
  return ok;
}

void StepPersonalAddress::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, internal_location); os << ',';
  StepFileLine::writeAttr(os, street_number); os << ',';
  StepFileLine::writeAttr(os, street); os << ',';
  StepFileLine::writeAttr(os, postal_box); os << ',';
  StepFileLine::writeAttr(os, town); os << ',';
  StepFileLine::writeAttr(os, region); os << ',';
  StepFileLine::writeAttr(os, postal_code); os << ',';
  StepFileLine::writeAttr(os, country); os << ',';
  StepFileLine::writeAttr(os, facsimile_number); os << ',';
  StepFileLine::writeAttr(os, telephone_number); os << ',';
  StepFileLine::writeAttr(os, electronic_mail_address); os << ',';
  StepFileLine::writeAttr(os, telex_number); os << ',';
  StepFileLine::writeAttr(os, people); os << ',';
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_personal_address(StepFileLine & line)
{
  StepPersonalAddress *entity = new StepPersonalAddress;
  entity->read(line);
  return entity;
}
// ------------ StepVolumeMeasureWithUnit

bool StepVolumeMeasureWithUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= value_component.read(line);
  ok &= unit_component.read(line);
  return ok;
}

void StepVolumeMeasureWithUnit::write(std::ostream & os) const
{
  value_component.write(os); os << ',';
  unit_component.write(os);
}

StepEntity *step_create_volume_measure_with_unit(StepFileLine & line)
{
  StepVolumeMeasureWithUnit *entity = new StepVolumeMeasureWithUnit;
  entity->read(line);
  return entity;
}
// ------------ StepManifoldSurfaceShapeRepresentation

bool StepManifoldSurfaceShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepManifoldSurfaceShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_manifold_surface_shape_representation(StepFileLine & line)
{
  StepManifoldSurfaceShapeRepresentation *entity = new StepManifoldSurfaceShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepShapeAspectRelationship

bool StepShapeAspectRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_shape_aspect);
  ok &= line.readAttr(related_shape_aspect);
  return ok;
}

void StepShapeAspectRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_shape_aspect); os << ',';
  StepFileLine::writeAttr(os, related_shape_aspect);
}

StepEntity *step_create_shape_aspect_relationship(StepFileLine & line)
{
  StepShapeAspectRelationship *entity = new StepShapeAspectRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepCalendarDate

bool StepCalendarDate::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(year_component);
  ok &= line.readAttr(day_component);
  ok &= line.readAttr(month_component);
  return ok;
}

void StepCalendarDate::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, year_component); os << ',';
  StepFileLine::writeAttr(os, day_component); os << ',';
  StepFileLine::writeAttr(os, month_component);
}

StepEntity *step_create_calendar_date(StepFileLine & line)
{
  StepCalendarDate *entity = new StepCalendarDate;
  entity->read(line);
  return entity;
}
// ------------ StepPersonAndOrganizationAssignment

bool StepPersonAndOrganizationAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_person_and_organization);
  ok &= line.readAttr(role);
  return ok;
}

void StepPersonAndOrganizationAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_person_and_organization); os << ',';
  StepFileLine::writeAttr(os, role);
}

StepEntity *step_create_person_and_organization_assignment(StepFileLine & line)
{
  StepPersonAndOrganizationAssignment *entity = new StepPersonAndOrganizationAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepActionAssignment

bool StepActionAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_action);
  return ok;
}

void StepActionAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_action);
}

StepEntity *step_create_action_assignment(StepFileLine & line)
{
  StepActionAssignment *entity = new StepActionAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepShapeAspect

bool StepShapeAspect::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(of_shape);
  ok &= product_definitional.read(line);
  return ok;
}

void StepShapeAspect::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, of_shape); os << ',';
  product_definitional.write(os);
}

StepEntity *step_create_shape_aspect(StepFileLine & line)
{
  StepShapeAspect *entity = new StepShapeAspect;
  entity->read(line);
  return entity;
}
// ------------ StepLengthMeasureWithUnit

bool StepLengthMeasureWithUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= value_component.read(line);
  ok &= unit_component.read(line);
  return ok;
}

void StepLengthMeasureWithUnit::write(std::ostream & os) const
{
  value_component.write(os); os << ',';
  unit_component.write(os);
}

StepEntity *step_create_length_measure_with_unit(StepFileLine & line)
{
  StepLengthMeasureWithUnit *entity = new StepLengthMeasureWithUnit;
  entity->read(line);
  return entity;
}
// ------------ StepAlternateProductRelationship

bool StepAlternateProductRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(definition);
  ok &= line.readAttr(alternate);
  ok &= line.readAttr(base);
  ok &= line.readAttr(basis);
  return ok;
}

void StepAlternateProductRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, definition); os << ',';
  StepFileLine::writeAttr(os, alternate); os << ',';
  StepFileLine::writeAttr(os, base); os << ',';
  StepFileLine::writeAttr(os, basis);
}

StepEntity *step_create_alternate_product_relationship(StepFileLine & line)
{
  StepAlternateProductRelationship *entity = new StepAlternateProductRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepDocumentRelationship

bool StepDocumentRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_document);
  ok &= line.readAttr(related_document);
  return ok;
}

void StepDocumentRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_document); os << ',';
  StepFileLine::writeAttr(os, related_document);
}

StepEntity *step_create_document_relationship(StepFileLine & line)
{
  StepDocumentRelationship *entity = new StepDocumentRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepActionDirective

bool StepActionDirective::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(analysis);
  ok &= line.readAttr(comment);
  ok &= line.readAttr(requests);
  return ok;
}

void StepActionDirective::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, analysis); os << ',';
  StepFileLine::writeAttr(os, comment); os << ',';
  StepFileLine::writeAttr(os, requests);
}

StepEntity *step_create_action_directive(StepFileLine & line)
{
  StepActionDirective *entity = new StepActionDirective;
  entity->read(line);
  return entity;
}
// ------------ StepApplicationProtocolDefinition

bool StepApplicationProtocolDefinition::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(status);
  ok &= line.readAttr(application_interpreted_model_schema_name);
  ok &= line.readAttr(application_protocol_year);
  ok &= line.readAttr(application);
  return ok;
}

void StepApplicationProtocolDefinition::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, status); os << ',';
  StepFileLine::writeAttr(os, application_interpreted_model_schema_name); os << ',';
  StepFileLine::writeAttr(os, application_protocol_year); os << ',';
  StepFileLine::writeAttr(os, application);
}

StepEntity *step_create_application_protocol_definition(StepFileLine & line)
{
  StepApplicationProtocolDefinition *entity = new StepApplicationProtocolDefinition;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinition

bool StepProductDefinition::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(description);
  ok &= line.readAttr(formation);
  ok &= line.readAttr(frame_of_reference);
  return ok;
}

void StepProductDefinition::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, formation); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference);
}

StepEntity *step_create_product_definition(StepFileLine & line)
{
  StepProductDefinition *entity = new StepProductDefinition;
  entity->read(line);
  return entity;
}
// ------------ StepLotEffectivity

bool StepLotEffectivity::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(effectivity_lot_id);
  ok &= line.readAttr(effectivity_lot_size);
  return ok;
}

void StepLotEffectivity::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, effectivity_lot_id); os << ',';
  StepFileLine::writeAttr(os, effectivity_lot_size);
}

StepEntity *step_create_lot_effectivity(StepFileLine & line)
{
  StepLotEffectivity *entity = new StepLotEffectivity;
  entity->read(line);
  return entity;
}
// ------------ StepShellBasedWireframeShapeRepresentation

bool StepShellBasedWireframeShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepShellBasedWireframeShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_shell_based_wireframe_shape_representation(StepFileLine & line)
{
  StepShellBasedWireframeShapeRepresentation *entity = new StepShellBasedWireframeShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepCoordinatedUniversalTimeOffset

bool StepCoordinatedUniversalTimeOffset::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(hour_offset);
  ok &= line.option() ? line.readAttr(minute_offset) : line.skipAttr();
  ok &= sense.read(line);
  return ok;
}

void StepCoordinatedUniversalTimeOffset::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, hour_offset); os << ',';
  StepFileLine::writeAttr(os, minute_offset); os << ',';
  sense.write(os);
}

StepEntity *step_create_coordinated_universal_time_offset(StepFileLine & line)
{
  StepCoordinatedUniversalTimeOffset *entity = new StepCoordinatedUniversalTimeOffset;
  entity->read(line);
  return entity;
}
// ------------ StepApprovalPersonOrganization

bool StepApprovalPersonOrganization::read(StepFileLine & line)
{
  bool ok = true;
  ok &= person_organization.read(line);
  ok &= line.readAttr(authorized_approval);
  ok &= line.readAttr(role);
  return ok;
}

void StepApprovalPersonOrganization::write(std::ostream & os) const
{
  person_organization.write(os); os << ',';
  StepFileLine::writeAttr(os, authorized_approval); os << ',';
  StepFileLine::writeAttr(os, role);
}

StepEntity *step_create_approval_person_organization(StepFileLine & line)
{
  StepApprovalPersonOrganization *entity = new StepApprovalPersonOrganization;
  entity->read(line);
  return entity;
}
// ------------ StepSolidAngleMeasureWithUnit

bool StepSolidAngleMeasureWithUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= value_component.read(line);
  ok &= unit_component.read(line);
  return ok;
}

void StepSolidAngleMeasureWithUnit::write(std::ostream & os) const
{
  value_component.write(os); os << ',';
  unit_component.write(os);
}

StepEntity *step_create_solid_angle_measure_with_unit(StepFileLine & line)
{
  StepSolidAngleMeasureWithUnit *entity = new StepSolidAngleMeasureWithUnit;
  entity->read(line);
  return entity;
}
// ------------ StepSecurityClassification

bool StepSecurityClassification::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(purpose);
  ok &= line.readAttr(security_level);
  return ok;
}

void StepSecurityClassification::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, purpose); os << ',';
  StepFileLine::writeAttr(os, security_level);
}

StepEntity *step_create_security_classification(StepFileLine & line)
{
  StepSecurityClassification *entity = new StepSecurityClassification;
  entity->read(line);
  return entity;
}
// ------------ StepPlaneAngleMeasureWithUnit

bool StepPlaneAngleMeasureWithUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= value_component.read(line);
  ok &= unit_component.read(line);
  return ok;
}

void StepPlaneAngleMeasureWithUnit::write(std::ostream & os) const
{
  value_component.write(os); os << ',';
  unit_component.write(os);
}

StepEntity *step_create_plane_angle_measure_with_unit(StepFileLine & line)
{
  StepPlaneAngleMeasureWithUnit *entity = new StepPlaneAngleMeasureWithUnit;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinitionRelationship

bool StepProductDefinitionRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  return ok;
}

void StepProductDefinitionRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition);
}

StepEntity *step_create_product_definition_relationship(StepFileLine & line)
{
  StepProductDefinitionRelationship *entity = new StepProductDefinitionRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepRepresentationContext

bool StepRepresentationContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(context_identifier);
  ok &= line.readAttr(context_type);
  ok &= line.readAttr(representations_in_context);
  return ok;
}

void StepRepresentationContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, context_identifier); os << ',';
  StepFileLine::writeAttr(os, context_type); os << ',';
  StepFileLine::writeAttr(os, representations_in_context);
}

StepEntity *step_create_representation_context(StepFileLine & line)
{
  StepRepresentationContext *entity = new StepRepresentationContext;
  entity->read(line);
  return entity;
}
// ------------ StepDatedEffectivity

bool StepDatedEffectivity::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(effectivity_start_date);
  ok &= line.option() ? line.readAttr(effectivity_end_date) : line.skipAttr();
  return ok;
}

void StepDatedEffectivity::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, effectivity_start_date); os << ',';
  StepFileLine::writeAttr(os, effectivity_end_date, '$');
}

StepEntity *step_create_dated_effectivity(StepFileLine & line)
{
  StepDatedEffectivity *entity = new StepDatedEffectivity;
  entity->read(line);
  return entity;
}
// ------------ StepCompositeCurveSegment

bool StepCompositeCurveSegment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= transition.read(line);
  ok &= line.readAttr(same_sense);
  ok &= line.readAttr(parent_curve);
  ok &= line.readAttr(using_curves);
  return ok;
}

void StepCompositeCurveSegment::write(std::ostream & os) const
{
  transition.write(os); os << ',';
  StepFileLine::writeAttr(os, same_sense); os << ',';
  StepFileLine::writeAttr(os, parent_curve); os << ',';
  StepFileLine::writeAttr(os, using_curves);
}

StepEntity *step_create_composite_curve_segment(StepFileLine & line)
{
  StepCompositeCurveSegment *entity = new StepCompositeCurveSegment;
  entity->read(line);
  return entity;
}
// ------------ StepSolidAngleUnit

bool StepSolidAngleUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  return ok;
}

void StepSolidAngleUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions);
}

StepEntity *step_create_solid_angle_unit(StepFileLine & line)
{
  StepSolidAngleUnit *entity = new StepSolidAngleUnit;
  entity->read(line);
  return entity;
}
// ------------ StepActionMethod

bool StepActionMethod::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(consequence);
  ok &= line.readAttr(purpose);
  return ok;
}

void StepActionMethod::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, consequence); os << ',';
  StepFileLine::writeAttr(os, purpose);
}

StepEntity *step_create_action_method(StepFileLine & line)
{
  StepActionMethod *entity = new StepActionMethod;
  entity->read(line);
  return entity;
}
// ------------ StepOrganizationRelationship

bool StepOrganizationRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_organization);
  ok &= line.readAttr(related_organization);
  return ok;
}

void StepOrganizationRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_organization); os << ',';
  StepFileLine::writeAttr(os, related_organization);
}

StepEntity *step_create_organization_relationship(StepFileLine & line)
{
  StepOrganizationRelationship *entity = new StepOrganizationRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepStartRequest

bool StepStartRequest::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_action_request);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepStartRequest::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_action_request); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_start_request(StepFileLine & line)
{
  StepStartRequest *entity = new StepStartRequest;
  entity->read(line);
  return entity;
}
// ------------ StepAction

bool StepAction::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(chosen_method);
  return ok;
}

void StepAction::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, chosen_method);
}

StepEntity *step_create_action(StepFileLine & line)
{
  StepAction *entity = new StepAction;
  entity->read(line);
  return entity;
}
// ------------ StepChange

bool StepChange::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_action);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepChange::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_action); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_change(StepFileLine & line)
{
  StepChange *entity = new StepChange;
  entity->read(line);
  return entity;
}
// ------------ StepChangeRequest

bool StepChangeRequest::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_action_request);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepChangeRequest::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_action_request); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_change_request(StepFileLine & line)
{
  StepChangeRequest *entity = new StepChangeRequest;
  entity->read(line);
  return entity;
}
// ------------ StepAreaMeasureWithUnit

bool StepAreaMeasureWithUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= value_component.read(line);
  ok &= unit_component.read(line);
  return ok;
}

void StepAreaMeasureWithUnit::write(std::ostream & os) const
{
  value_component.write(os); os << ',';
  unit_component.write(os);
}

StepEntity *step_create_area_measure_with_unit(StepFileLine & line)
{
  StepAreaMeasureWithUnit *entity = new StepAreaMeasureWithUnit;
  entity->read(line);
  return entity;
}
// ------------ StepApprovalDateTime

bool StepApprovalDateTime::read(StepFileLine & line)
{
  bool ok = true;
  ok &= date_time.read(line);
  ok &= line.readAttr(dated_approval);
  return ok;
}

void StepApprovalDateTime::write(std::ostream & os) const
{
  date_time.write(os); os << ',';
  StepFileLine::writeAttr(os, dated_approval);
}

StepEntity *step_create_approval_date_time(StepFileLine & line)
{
  StepApprovalDateTime *entity = new StepApprovalDateTime;
  entity->read(line);
  return entity;
}
// ------------ StepApprovalRole

bool StepApprovalRole::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(role);
  return ok;
}

void StepApprovalRole::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, role);
}

StepEntity *step_create_approval_role(StepFileLine & line)
{
  StepApprovalRole *entity = new StepApprovalRole;
  entity->read(line);
  return entity;
}
// ------------ StepPersonAndOrganizationRole

bool StepPersonAndOrganizationRole::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepPersonAndOrganizationRole::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_person_and_organization_role(StepFileLine & line)
{
  StepPersonAndOrganizationRole *entity = new StepPersonAndOrganizationRole;
  entity->read(line);
  return entity;
}
// ------------ StepVolumeUnit

bool StepVolumeUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  return ok;
}

void StepVolumeUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions);
}

StepEntity *step_create_volume_unit(StepFileLine & line)
{
  StepVolumeUnit *entity = new StepVolumeUnit;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinitionFormation

bool StepProductDefinitionFormation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(description);
  ok &= line.readAttr(of_product);
  return ok;
}

void StepProductDefinitionFormation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, of_product);
}

StepEntity *step_create_product_definition_formation(StepFileLine & line)
{
  StepProductDefinitionFormation *entity = new StepProductDefinitionFormation;
  entity->read(line);
  return entity;
}
// ------------ StepApproval

bool StepApproval::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(status);
  ok &= line.readAttr(level);
  return ok;
}

void StepApproval::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, status); os << ',';
  StepFileLine::writeAttr(os, level);
}

StepEntity *step_create_approval(StepFileLine & line)
{
  StepApproval *entity = new StepApproval;
  entity->read(line);
  return entity;
}
// ------------ StepTopologicalRepresentationItem

bool StepTopologicalRepresentationItem::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepTopologicalRepresentationItem::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_topological_representation_item(StepFileLine & line)
{
  StepTopologicalRepresentationItem *entity = new StepTopologicalRepresentationItem;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinitionUsage

bool StepProductDefinitionUsage::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  return ok;
}

void StepProductDefinitionUsage::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition);
}

StepEntity *step_create_product_definition_usage(StepFileLine & line)
{
  StepProductDefinitionUsage *entity = new StepProductDefinitionUsage;
  entity->read(line);
  return entity;
}
// ------------ StepActionRequestSolution

bool StepActionRequestSolution::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(method);
  ok &= line.readAttr(request);
  return ok;
}

void StepActionRequestSolution::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, method); os << ',';
  StepFileLine::writeAttr(os, request);
}

StepEntity *step_create_action_request_solution(StepFileLine & line)
{
  StepActionRequestSolution *entity = new StepActionRequestSolution;
  entity->read(line);
  return entity;
}
// ------------ StepRepresentationRelationship

bool StepRepresentationRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(rep_1);
  ok &= line.readAttr(rep_2);
  return ok;
}

void StepRepresentationRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, rep_1); os << ',';
  StepFileLine::writeAttr(os, rep_2);
}

StepEntity *step_create_representation_relationship(StepFileLine & line)
{
  StepRepresentationRelationship *entity = new StepRepresentationRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepDocumentType

bool StepDocumentType::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(product_data_type);
  return ok;
}

void StepDocumentType::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, product_data_type);
}

StepEntity *step_create_document_type(StepFileLine & line)
{
  StepDocumentType *entity = new StepDocumentType;
  entity->read(line);
  return entity;
}
// ------------ StepDateAndTimeAssignment

bool StepDateAndTimeAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_date_and_time);
  ok &= line.readAttr(role);
  return ok;
}

void StepDateAndTimeAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_date_and_time); os << ',';
  StepFileLine::writeAttr(os, role);
}

StepEntity *step_create_date_and_time_assignment(StepFileLine & line)
{
  StepDateAndTimeAssignment *entity = new StepDateAndTimeAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepPersonAndOrganization

bool StepPersonAndOrganization::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(the_person);
  ok &= line.readAttr(the_organization);
  return ok;
}

void StepPersonAndOrganization::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, the_person); os << ',';
  StepFileLine::writeAttr(os, the_organization);
}

StepEntity *step_create_person_and_organization(StepFileLine & line)
{
  StepPersonAndOrganization *entity = new StepPersonAndOrganization;
  entity->read(line);
  return entity;
}
// ------------ StepCertification

bool StepCertification::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(purpose);
  ok &= line.readAttr(kind);
  return ok;
}

void StepCertification::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, purpose); os << ',';
  StepFileLine::writeAttr(os, kind);
}

StepEntity *step_create_certification(StepFileLine & line)
{
  StepCertification *entity = new StepCertification;
  entity->read(line);
  return entity;
}
// ------------ StepVertex

bool StepVertex::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepVertex::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_vertex(StepFileLine & line)
{
  StepVertex *entity = new StepVertex;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinitionShape

bool StepProductDefinitionShape::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= definition.read(line);
  return ok;
}

void StepProductDefinitionShape::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  definition.write(os);
}

StepEntity *step_create_product_definition_shape(StepFileLine & line)
{
  StepProductDefinitionShape *entity = new StepProductDefinitionShape;
  entity->read(line);
  return entity;
}
// ------------ StepAssemblyComponentUsageSubstitute

bool StepAssemblyComponentUsageSubstitute::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(definition);
  ok &= line.readAttr(base);
  ok &= line.readAttr(substitute);
  return ok;
}

void StepAssemblyComponentUsageSubstitute::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, definition); os << ',';
  StepFileLine::writeAttr(os, base); os << ',';
  StepFileLine::writeAttr(os, substitute);
}

StepEntity *step_create_assembly_component_usage_substitute(StepFileLine & line)
{
  StepAssemblyComponentUsageSubstitute *entity = new StepAssemblyComponentUsageSubstitute;
  entity->read(line);
  return entity;
}
// ------------ StepConversionBasedUnit

bool StepConversionBasedUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  ok &= line.readAttr(name);
  ok &= line.readAttr(conversion_factor);
  return ok;
}

void StepConversionBasedUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, conversion_factor);
}

StepEntity *step_create_conversion_based_unit(StepFileLine & line)
{
  StepConversionBasedUnit *entity = new StepConversionBasedUnit;
  entity->read(line);
  return entity;
}
// ------------ StepExecutedAction

bool StepExecutedAction::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(chosen_method);
  return ok;
}

void StepExecutedAction::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, chosen_method);
}

StepEntity *step_create_executed_action(StepFileLine & line)
{
  StepExecutedAction *entity = new StepExecutedAction;
  entity->read(line);
  return entity;
}
// ------------ StepCcDesignSecurityClassification

bool StepCcDesignSecurityClassification::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_security_classification);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepCcDesignSecurityClassification::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_security_classification); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_cc_design_security_classification(StepFileLine & line)
{
  StepCcDesignSecurityClassification *entity = new StepCcDesignSecurityClassification;
  entity->read(line);
  return entity;
}
// ------------ StepEdge

bool StepEdge::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(edge_start);
  ok &= line.readAttr(edge_end);
  return ok;
}

void StepEdge::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, edge_start); os << ',';
  StepFileLine::writeAttr(os, edge_end);
}

StepEntity *step_create_edge(StepFileLine & line)
{
  StepEdge *entity = new StepEdge;
  entity->read(line);
  return entity;
}
// ------------ StepSuppliedPartRelationship

bool StepSuppliedPartRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  return ok;
}

void StepSuppliedPartRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition);
}

StepEntity *step_create_supplied_part_relationship(StepFileLine & line)
{
  StepSuppliedPartRelationship *entity = new StepSuppliedPartRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepStartWork

bool StepStartWork::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_action);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepStartWork::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_action); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_start_work(StepFileLine & line)
{
  StepStartWork *entity = new StepStartWork;
  entity->read(line);
  return entity;
}
// ------------ StepOrganizationalAddress

bool StepOrganizationalAddress::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.option() ? line.readAttr(internal_location) : line.skipAttr();
  ok &= line.option() ? line.readAttr(street_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(street) : line.skipAttr();
  ok &= line.option() ? line.readAttr(postal_box) : line.skipAttr();
  ok &= line.option() ? line.readAttr(town) : line.skipAttr();
  ok &= line.option() ? line.readAttr(region) : line.skipAttr();
  ok &= line.option() ? line.readAttr(postal_code) : line.skipAttr();
  ok &= line.option() ? line.readAttr(country) : line.skipAttr();
  ok &= line.option() ? line.readAttr(facsimile_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(telephone_number) : line.skipAttr();
  ok &= line.option() ? line.readAttr(electronic_mail_address) : line.skipAttr();
  ok &= line.option() ? line.readAttr(telex_number) : line.skipAttr();
  ok &= line.readAttr(organizations);
  ok &= line.readAttr(description);
  return ok;
}

void StepOrganizationalAddress::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, internal_location); os << ',';
  StepFileLine::writeAttr(os, street_number); os << ',';
  StepFileLine::writeAttr(os, street); os << ',';
  StepFileLine::writeAttr(os, postal_box); os << ',';
  StepFileLine::writeAttr(os, town); os << ',';
  StepFileLine::writeAttr(os, region); os << ',';
  StepFileLine::writeAttr(os, postal_code); os << ',';
  StepFileLine::writeAttr(os, country); os << ',';
  StepFileLine::writeAttr(os, facsimile_number); os << ',';
  StepFileLine::writeAttr(os, telephone_number); os << ',';
  StepFileLine::writeAttr(os, electronic_mail_address); os << ',';
  StepFileLine::writeAttr(os, telex_number); os << ',';
  StepFileLine::writeAttr(os, organizations); os << ',';
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_organizational_address(StepFileLine & line)
{
  StepOrganizationalAddress *entity = new StepOrganizationalAddress;
  entity->read(line);
  return entity;
}
// ------------ StepMappedItem

bool StepMappedItem::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(mapping_source);
  ok &= line.readAttr(mapping_target);
  return ok;
}

void StepMappedItem::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, mapping_source); os << ',';
  StepFileLine::writeAttr(os, mapping_target);
}

StepEntity *step_create_mapped_item(StepFileLine & line)
{
  StepMappedItem *entity = new StepMappedItem;
  entity->read(line);
  return entity;
}
// ------------ StepGlobalUnitAssignedContext

bool StepGlobalUnitAssignedContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(context_identifier);
  ok &= line.readAttr(context_type);
  ok &= line.readAttr(representations_in_context);
  ok &= line.readSelectArray(units);
  return ok;
}

void StepGlobalUnitAssignedContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, context_identifier); os << ',';
  StepFileLine::writeAttr(os, context_type); os << ',';
  StepFileLine::writeAttr(os, representations_in_context); os << ',';
  StepFileLine::writeSelectArray(os, units);
}

StepEntity *step_create_global_unit_assigned_context(StepFileLine & line)
{
  StepGlobalUnitAssignedContext *entity = new StepGlobalUnitAssignedContext;
  entity->read(line);
  return entity;
}
// ------------ StepReparametrisedCompositeCurveSegment

bool StepReparametrisedCompositeCurveSegment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= transition.read(line);
  ok &= line.readAttr(same_sense);
  ok &= line.readAttr(parent_curve);
  ok &= line.readAttr(using_curves);
  ok &= line.readAttr(param_length);
  return ok;
}

void StepReparametrisedCompositeCurveSegment::write(std::ostream & os) const
{
  transition.write(os); os << ',';
  StepFileLine::writeAttr(os, same_sense); os << ',';
  StepFileLine::writeAttr(os, parent_curve); os << ',';
  StepFileLine::writeAttr(os, using_curves); os << ',';
  StepFileLine::writeAttr(os, param_length);
}

StepEntity *step_create_reparametrised_composite_curve_segment(StepFileLine & line)
{
  StepReparametrisedCompositeCurveSegment *entity = new StepReparametrisedCompositeCurveSegment;
  entity->read(line);
  return entity;
}
// ------------ StepLoop

bool StepLoop::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepLoop::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_loop(StepFileLine & line)
{
  StepLoop *entity = new StepLoop;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinitionFormationWithSpecifiedSource

bool StepProductDefinitionFormationWithSpecifiedSource::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(description);
  ok &= line.readAttr(of_product);
  ok &= make_or_buy.read(line);
  return ok;
}

void StepProductDefinitionFormationWithSpecifiedSource::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, of_product); os << ',';
  make_or_buy.write(os);
}

StepEntity *step_create_product_definition_formation_with_specified_source(StepFileLine & line)
{
  StepProductDefinitionFormationWithSpecifiedSource *entity = new StepProductDefinitionFormationWithSpecifiedSource;
  entity->read(line);
  return entity;
}
// ------------ StepProductDefinitionWithAssociatedDocuments

bool StepProductDefinitionWithAssociatedDocuments::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(description);
  ok &= line.readAttr(formation);
  ok &= line.readAttr(frame_of_reference);
  ok &= line.readAttr(documentation_ids);
  return ok;
}

void StepProductDefinitionWithAssociatedDocuments::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, formation); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference); os << ',';
  StepFileLine::writeAttr(os, documentation_ids);
}

StepEntity *step_create_product_definition_with_associated_documents(StepFileLine & line)
{
  StepProductDefinitionWithAssociatedDocuments *entity = new StepProductDefinitionWithAssociatedDocuments;
  entity->read(line);
  return entity;
}
// ------------ StepPlaneAngleUnit

bool StepPlaneAngleUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  return ok;
}

void StepPlaneAngleUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions);
}

StepEntity *step_create_plane_angle_unit(StepFileLine & line)
{
  StepPlaneAngleUnit *entity = new StepPlaneAngleUnit;
  entity->read(line);
  return entity;
}
// ------------ StepLengthUnit

bool StepLengthUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  return ok;
}

void StepLengthUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions);
}

StepEntity *step_create_length_unit(StepFileLine & line)
{
  StepLengthUnit *entity = new StepLengthUnit;
  entity->read(line);
  return entity;
}
// ------------ StepAreaUnit

bool StepAreaUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  return ok;
}

void StepAreaUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions);
}

StepEntity *step_create_area_unit(StepFileLine & line)
{
  StepAreaUnit *entity = new StepAreaUnit;
  entity->read(line);
  return entity;
}
// ------------ StepGeometricRepresentationContext

bool StepGeometricRepresentationContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(context_identifier);
  ok &= line.readAttr(context_type);
  ok &= line.readAttr(representations_in_context);
  ok &= line.readAttr(coordinate_space_dimension);
  return ok;
}

void StepGeometricRepresentationContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, context_identifier); os << ',';
  StepFileLine::writeAttr(os, context_type); os << ',';
  StepFileLine::writeAttr(os, representations_in_context); os << ',';
  StepFileLine::writeAttr(os, coordinate_space_dimension);
}

StepEntity *step_create_geometric_representation_context(StepFileLine & line)
{
  StepGeometricRepresentationContext *entity = new StepGeometricRepresentationContext;
  entity->read(line);
  return entity;
}
// ------------ StepWireShell

bool StepWireShell::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(wire_shell_extent);
  return ok;
}

void StepWireShell::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, wire_shell_extent);
}

StepEntity *step_create_wire_shell(StepFileLine & line)
{
  StepWireShell *entity = new StepWireShell;
  entity->read(line);
  return entity;
}
// ------------ StepAssemblyComponentUsage

bool StepAssemblyComponentUsage::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  ok &= line.option() ? line.readAttr(reference_designator) : line.skipAttr();
  return ok;
}

void StepAssemblyComponentUsage::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition); os << ',';
  StepFileLine::writeAttr(os, reference_designator);
}

StepEntity *step_create_assembly_component_usage(StepFileLine & line)
{
  StepAssemblyComponentUsage *entity = new StepAssemblyComponentUsage;
  entity->read(line);
  return entity;
}
// ------------ StepFace

bool StepFace::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(bounds);
  return ok;
}

void StepFace::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, bounds);
}

StepEntity *step_create_face(StepFileLine & line)
{
  StepFace *entity = new StepFace;
  entity->read(line);
  return entity;
}
// ------------ StepSiUnit

bool StepSiUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  ok &= line.option() ? prefix.read(line) : line.skipAttr();
  ok &= name.read(line);
  return ok;
}

void StepSiUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions); os << ',';
  prefix.write(os); os << ',';
  name.write(os);
}

StepEntity *step_create_si_unit(StepFileLine & line)
{
  StepSiUnit *entity = new StepSiUnit;
  entity->read(line);
  return entity;
}
// ------------ StepUncertaintyMeasureWithUnit

bool StepUncertaintyMeasureWithUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= value_component.read(line);
  ok &= unit_component.read(line);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  return ok;
}

void StepUncertaintyMeasureWithUnit::write(std::ostream & os) const
{
  value_component.write(os); os << ',';
  unit_component.write(os); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description);
}

StepEntity *step_create_uncertainty_measure_with_unit(StepFileLine & line)
{
  StepUncertaintyMeasureWithUnit *entity = new StepUncertaintyMeasureWithUnit;
  entity->read(line);
  return entity;
}
// ------------ StepPath

bool StepPath::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(edge_list);
  return ok;
}

void StepPath::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, edge_list);
}

StepEntity *step_create_path(StepFileLine & line)
{
  StepPath *entity = new StepPath;
  entity->read(line);
  return entity;
}
// ------------ StepConnectedFaceSet

bool StepConnectedFaceSet::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(cfs_faces);
  return ok;
}

void StepConnectedFaceSet::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, cfs_faces);
}

StepEntity *step_create_connected_face_set(StepFileLine & line)
{
  StepConnectedFaceSet *entity = new StepConnectedFaceSet;
  entity->read(line);
  return entity;
}
// ------------ StepOrientedFace

bool StepOrientedFace::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(bounds);
  ok &= line.readAttr(face_element);
  ok &= line.readAttr(orientation);
  return ok;
}

void StepOrientedFace::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, bounds); os << ',';
  StepFileLine::writeAttr(os, face_element); os << ',';
  StepFileLine::writeAttr(os, orientation);
}

StepEntity *step_create_oriented_face(StepFileLine & line)
{
  StepOrientedFace *entity = new StepOrientedFace;
  entity->read(line);
  return entity;
}
// ------------ StepGeometricallyBoundedWireframeShapeRepresentation

bool StepGeometricallyBoundedWireframeShapeRepresentation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(items);
  ok &= line.readAttr(context_of_items);
  return ok;
}

void StepGeometricallyBoundedWireframeShapeRepresentation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, items); os << ',';
  StepFileLine::writeAttr(os, context_of_items);
}

StepEntity *step_create_geometrically_bounded_wireframe_shape_representation(StepFileLine & line)
{
  StepGeometricallyBoundedWireframeShapeRepresentation *entity = new StepGeometricallyBoundedWireframeShapeRepresentation;
  entity->read(line);
  return entity;
}
// ------------ StepMassUnit

bool StepMassUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  return ok;
}

void StepMassUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions);
}

StepEntity *step_create_mass_unit(StepFileLine & line)
{
  StepMassUnit *entity = new StepMassUnit;
  entity->read(line);
  return entity;
}
// ------------ StepParametricRepresentationContext

bool StepParametricRepresentationContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(context_identifier);
  ok &= line.readAttr(context_type);
  ok &= line.readAttr(representations_in_context);
  return ok;
}

void StepParametricRepresentationContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, context_identifier); os << ',';
  StepFileLine::writeAttr(os, context_type); os << ',';
  StepFileLine::writeAttr(os, representations_in_context);
}

StepEntity *step_create_parametric_representation_context(StepFileLine & line)
{
  StepParametricRepresentationContext *entity = new StepParametricRepresentationContext;
  entity->read(line);
  return entity;
}
// ------------ StepSpecifiedHigherUsageOccurrence

bool StepSpecifiedHigherUsageOccurrence::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  ok &= line.option() ? line.readAttr(reference_designator) : line.skipAttr();
  ok &= line.readAttr(upper_usage);
  ok &= line.readAttr(next_usage);
  return ok;
}

void StepSpecifiedHigherUsageOccurrence::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition); os << ',';
  StepFileLine::writeAttr(os, reference_designator); os << ',';
  StepFileLine::writeAttr(os, upper_usage); os << ',';
  StepFileLine::writeAttr(os, next_usage);
}

StepEntity *step_create_specified_higher_usage_occurrence(StepFileLine & line)
{
  StepSpecifiedHigherUsageOccurrence *entity = new StepSpecifiedHigherUsageOccurrence;
  entity->read(line);
  return entity;
}
// ------------ StepGeometricRepresentationItem

bool StepGeometricRepresentationItem::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepGeometricRepresentationItem::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_geometric_representation_item(StepFileLine & line)
{
  StepGeometricRepresentationItem *entity = new StepGeometricRepresentationItem;
  entity->read(line);
  return entity;
}
// ------------ StepCcDesignDateAndTimeAssignment

bool StepCcDesignDateAndTimeAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_date_and_time);
  ok &= line.readAttr(role);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepCcDesignDateAndTimeAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_date_and_time); os << ',';
  StepFileLine::writeAttr(os, role); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_cc_design_date_and_time_assignment(StepFileLine & line)
{
  StepCcDesignDateAndTimeAssignment *entity = new StepCcDesignDateAndTimeAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepGeometricSet

bool StepGeometricSet::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readSelectArray(elements);
  return ok;
}

void StepGeometricSet::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeSelectArray(os, elements);
}

StepEntity *step_create_geometric_set(StepFileLine & line)
{
  StepGeometricSet *entity = new StepGeometricSet;
  entity->read(line);
  return entity;
}
// ------------ StepCcDesignPersonAndOrganizationAssignment

bool StepCcDesignPersonAndOrganizationAssignment::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(assigned_person_and_organization);
  ok &= line.readAttr(role);
  ok &= line.readSelectArray(items);
  return ok;
}

void StepCcDesignPersonAndOrganizationAssignment::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, assigned_person_and_organization); os << ',';
  StepFileLine::writeAttr(os, role); os << ',';
  StepFileLine::writeSelectArray(os, items);
}

StepEntity *step_create_cc_design_person_and_organization_assignment(StepFileLine & line)
{
  StepCcDesignPersonAndOrganizationAssignment *entity = new StepCcDesignPersonAndOrganizationAssignment;
  entity->read(line);
  return entity;
}
// ------------ StepConnectedEdgeSet

bool StepConnectedEdgeSet::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(ces_edges);
  return ok;
}

void StepConnectedEdgeSet::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, ces_edges);
}

StepEntity *step_create_connected_edge_set(StepFileLine & line)
{
  StepConnectedEdgeSet *entity = new StepConnectedEdgeSet;
  entity->read(line);
  return entity;
}
// ------------ StepContextDependentUnit

bool StepContextDependentUnit::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(dimensions);
  ok &= line.readAttr(name);
  return ok;
}

void StepContextDependentUnit::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, dimensions); os << ',';
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_context_dependent_unit(StepFileLine & line)
{
  StepContextDependentUnit *entity = new StepContextDependentUnit;
  entity->read(line);
  return entity;
}
// ------------ StepGeometricCurveSet

bool StepGeometricCurveSet::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readSelectArray(elements);
  return ok;
}

void StepGeometricCurveSet::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeSelectArray(os, elements);
}

StepEntity *step_create_geometric_curve_set(StepFileLine & line)
{
  StepGeometricCurveSet *entity = new StepGeometricCurveSet;
  entity->read(line);
  return entity;
}
// ------------ StepOrientedEdge

bool StepOrientedEdge::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(edge_start);
  ok &= line.readAttr(edge_end);
  ok &= line.readAttr(edge_element);
  ok &= line.readAttr(orientation);
  return ok;
}

void StepOrientedEdge::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, edge_start); os << ',';
  StepFileLine::writeAttr(os, edge_end); os << ',';
  StepFileLine::writeAttr(os, edge_element); os << ',';
  StepFileLine::writeAttr(os, orientation);
}

StepEntity *step_create_oriented_edge(StepFileLine & line)
{
  StepOrientedEdge *entity = new StepOrientedEdge;
  entity->read(line);
  return entity;
}
// ------------ StepClosedShell

bool StepClosedShell::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(cfs_faces);
  return ok;
}

void StepClosedShell::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, cfs_faces);
}

StepEntity *step_create_closed_shell(StepFileLine & line)
{
  StepClosedShell *entity = new StepClosedShell;
  entity->read(line);
  return entity;
}
// ------------ StepShapeRepresentationRelationship

bool StepShapeRepresentationRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(rep_1);
  ok &= line.readAttr(rep_2);
  return ok;
}

void StepShapeRepresentationRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, rep_1); os << ',';
  StepFileLine::writeAttr(os, rep_2);
}

StepEntity *step_create_shape_representation_relationship(StepFileLine & line)
{
  StepShapeRepresentationRelationship *entity = new StepShapeRepresentationRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepGlobalUncertaintyAssignedContext

bool StepGlobalUncertaintyAssignedContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(context_identifier);
  ok &= line.readAttr(context_type);
  ok &= line.readAttr(representations_in_context);
  ok &= line.readAttr(uncertainty);
  return ok;
}

void StepGlobalUncertaintyAssignedContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, context_identifier); os << ',';
  StepFileLine::writeAttr(os, context_type); os << ',';
  StepFileLine::writeAttr(os, representations_in_context); os << ',';
  StepFileLine::writeAttr(os, uncertainty);
}

StepEntity *step_create_global_uncertainty_assigned_context(StepFileLine & line)
{
  StepGlobalUncertaintyAssignedContext *entity = new StepGlobalUncertaintyAssignedContext;
  entity->read(line);
  return entity;
}
// ------------ StepRepresentationRelationshipWithTransformation

bool StepRepresentationRelationshipWithTransformation::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(rep_1);
  ok &= line.readAttr(rep_2);
  ok &= transformation_operator.read(line);
  return ok;
}

void StepRepresentationRelationshipWithTransformation::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, rep_1); os << ',';
  StepFileLine::writeAttr(os, rep_2); os << ',';
  transformation_operator.write(os);
}

StepEntity *step_create_representation_relationship_with_transformation(StepFileLine & line)
{
  StepRepresentationRelationshipWithTransformation *entity = new StepRepresentationRelationshipWithTransformation;
  entity->read(line);
  return entity;
}
// ------------ StepMechanicalContext

bool StepMechanicalContext::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(frame_of_reference);
  ok &= line.readAttr(discipline_type);
  return ok;
}

void StepMechanicalContext::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, frame_of_reference); os << ',';
  StepFileLine::writeAttr(os, discipline_type);
}

StepEntity *step_create_mechanical_context(StepFileLine & line)
{
  StepMechanicalContext *entity = new StepMechanicalContext;
  entity->read(line);
  return entity;
}
// ------------ StepOrientedClosedShell

bool StepOrientedClosedShell::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(cfs_faces);
  ok &= line.readAttr(closed_shell_element);
  ok &= line.readAttr(orientation);
  return ok;
}

void StepOrientedClosedShell::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, cfs_faces); os << ',';
  StepFileLine::writeAttr(os, closed_shell_element); os << ',';
  StepFileLine::writeAttr(os, orientation);
}

StepEntity *step_create_oriented_closed_shell(StepFileLine & line)
{
  StepOrientedClosedShell *entity = new StepOrientedClosedShell;
  entity->read(line);
  return entity;
}
// ------------ StepDirection

bool StepDirection::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readArrayAttr<3>(direction_ratios);
  return ok;
}

void StepDirection::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeArrayAttr<3>(os, direction_ratios);
}

StepEntity *step_create_direction(StepFileLine & line)
{
  StepDirection *entity = new StepDirection;
  entity->read(line);
  return entity;
}
// ------------ StepVertexShell

bool StepVertexShell::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(vertex_shell_extent);
  return ok;
}

void StepVertexShell::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, vertex_shell_extent);
}

StepEntity *step_create_vertex_shell(StepFileLine & line)
{
  StepVertexShell *entity = new StepVertexShell;
  entity->read(line);
  return entity;
}
// ------------ StepNextAssemblyUsageOccurrence

bool StepNextAssemblyUsageOccurrence::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  ok &= line.option() ? line.readAttr(reference_designator) : line.skipAttr();
  return ok;
}

void StepNextAssemblyUsageOccurrence::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition); os << ',';
  StepFileLine::writeAttr(os, reference_designator);
}

StepEntity *step_create_next_assembly_usage_occurrence(StepFileLine & line)
{
  StepNextAssemblyUsageOccurrence *entity = new StepNextAssemblyUsageOccurrence;
  entity->read(line);
  return entity;
}
// ------------ StepOrientedPath

bool StepOrientedPath::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(edge_list);
  ok &= line.readAttr(path_element);
  ok &= line.readAttr(orientation);
  return ok;
}

void StepOrientedPath::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, edge_list); os << ',';
  StepFileLine::writeAttr(os, path_element); os << ',';
  StepFileLine::writeAttr(os, orientation);
}

StepEntity *step_create_oriented_path(StepFileLine & line)
{
  StepOrientedPath *entity = new StepOrientedPath;
  entity->read(line);
  return entity;
}
// ------------ StepFaceBound

bool StepFaceBound::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(bound);
  ok &= line.readAttr(orientation);
  return ok;
}

void StepFaceBound::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, bound); os << ',';
  StepFileLine::writeAttr(os, orientation);
}

StepEntity *step_create_face_bound(StepFileLine & line)
{
  StepFaceBound *entity = new StepFaceBound;
  entity->read(line);
  return entity;
}
// ------------ StepVector

bool StepVector::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(orientation);
  ok &= line.readAttr(magnitude);
  return ok;
}

void StepVector::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, orientation); os << ',';
  StepFileLine::writeAttr(os, magnitude);
}

StepEntity *step_create_vector(StepFileLine & line)
{
  StepVector *entity = new StepVector;
  entity->read(line);
  return entity;
}
// ------------ StepDirectedAction

bool StepDirectedAction::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(chosen_method);
  ok &= line.readAttr(directive);
  return ok;
}

void StepDirectedAction::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, chosen_method); os << ',';
  StepFileLine::writeAttr(os, directive);
}

StepEntity *step_create_directed_action(StepFileLine & line)
{
  StepDirectedAction *entity = new StepDirectedAction;
  entity->read(line);
  return entity;
}
// ------------ StepSurface

bool StepSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_surface(StepFileLine & line)
{
  StepSurface *entity = new StepSurface;
  entity->read(line);
  return entity;
}
// ------------ StepShellBasedSurfaceModel

bool StepShellBasedSurfaceModel::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readSelectArray(sbsm_boundary);
  return ok;
}

void StepShellBasedSurfaceModel::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeSelectArray(os, sbsm_boundary);
}

StepEntity *step_create_shell_based_surface_model(StepFileLine & line)
{
  StepShellBasedSurfaceModel *entity = new StepShellBasedSurfaceModel;
  entity->read(line);
  return entity;
}
// ------------ StepDesignMakeFromRelationship

bool StepDesignMakeFromRelationship::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  return ok;
}

void StepDesignMakeFromRelationship::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition);
}

StepEntity *step_create_design_make_from_relationship(StepFileLine & line)
{
  StepDesignMakeFromRelationship *entity = new StepDesignMakeFromRelationship;
  entity->read(line);
  return entity;
}
// ------------ StepPolyLoop

bool StepPolyLoop::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(polygon);
  return ok;
}

void StepPolyLoop::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, polygon);
}

StepEntity *step_create_poly_loop(StepFileLine & line)
{
  StepPolyLoop *entity = new StepPolyLoop;
  entity->read(line);
  return entity;
}
// ------------ StepCurve

bool StepCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_curve(StepFileLine & line)
{
  StepCurve *entity = new StepCurve;
  entity->read(line);
  return entity;
}
// ------------ StepPromissoryUsageOccurrence

bool StepPromissoryUsageOccurrence::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  ok &= line.option() ? line.readAttr(reference_designator) : line.skipAttr();
  return ok;
}

void StepPromissoryUsageOccurrence::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition); os << ',';
  StepFileLine::writeAttr(os, reference_designator);
}

StepEntity *step_create_promissory_usage_occurrence(StepFileLine & line)
{
  StepPromissoryUsageOccurrence *entity = new StepPromissoryUsageOccurrence;
  entity->read(line);
  return entity;
}
// ------------ StepPoint

bool StepPoint::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepPoint::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_point(StepFileLine & line)
{
  StepPoint *entity = new StepPoint;
  entity->read(line);
  return entity;
}
// ------------ StepQuantifiedAssemblyComponentUsage

bool StepQuantifiedAssemblyComponentUsage::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(id);
  ok &= line.readAttr(name);
  ok &= line.readAttr(description);
  ok &= line.readAttr(relating_product_definition);
  ok &= line.readAttr(related_product_definition);
  ok &= line.option() ? line.readAttr(reference_designator) : line.skipAttr();
  ok &= line.readAttr(quantity);
  return ok;
}

void StepQuantifiedAssemblyComponentUsage::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, id); os << ',';
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, description); os << ',';
  StepFileLine::writeAttr(os, relating_product_definition); os << ',';
  StepFileLine::writeAttr(os, related_product_definition); os << ',';
  StepFileLine::writeAttr(os, reference_designator); os << ',';
  StepFileLine::writeAttr(os, quantity);
}

StepEntity *step_create_quantified_assembly_component_usage(StepFileLine & line)
{
  StepQuantifiedAssemblyComponentUsage *entity = new StepQuantifiedAssemblyComponentUsage;
  entity->read(line);
  return entity;
}
// ------------ StepFaceOuterBound

bool StepFaceOuterBound::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(bound);
  ok &= line.readAttr(orientation);
  return ok;
}

void StepFaceOuterBound::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, bound); os << ',';
  StepFileLine::writeAttr(os, orientation);
}

StepEntity *step_create_face_outer_bound(StepFileLine & line)
{
  StepFaceOuterBound *entity = new StepFaceOuterBound;
  entity->read(line);
  return entity;
}
// ------------ StepOpenShell

bool StepOpenShell::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(cfs_faces);
  return ok;
}

void StepOpenShell::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, cfs_faces);
}

StepEntity *step_create_open_shell(StepFileLine & line)
{
  StepOpenShell *entity = new StepOpenShell;
  entity->read(line);
  return entity;
}
// ------------ StepElementarySurface

bool StepElementarySurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(position);
  return ok;
}

void StepElementarySurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, position);
}

StepEntity *step_create_elementary_surface(StepFileLine & line)
{
  StepElementarySurface *entity = new StepElementarySurface;
  entity->read(line);
  return entity;
}
// ------------ StepPointOnCurve

bool StepPointOnCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_curve);
  ok &= line.readAttr(point_parameter);
  return ok;
}

void StepPointOnCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_curve); os << ',';
  StepFileLine::writeAttr(os, point_parameter);
}

StepEntity *step_create_point_on_curve(StepFileLine & line)
{
  StepPointOnCurve *entity = new StepPointOnCurve;
  entity->read(line);
  return entity;
}
// ------------ StepCurveReplica

bool StepCurveReplica::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(parent_curve);
  ok &= line.readAttr(transformation);
  return ok;
}

void StepCurveReplica::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, parent_curve); os << ',';
  StepFileLine::writeAttr(os, transformation);
}

StepEntity *step_create_curve_replica(StepFileLine & line)
{
  StepCurveReplica *entity = new StepCurveReplica;
  entity->read(line);
  return entity;
}
// ------------ StepVertexLoop

bool StepVertexLoop::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(loop_vertex);
  return ok;
}

void StepVertexLoop::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, loop_vertex);
}

StepEntity *step_create_vertex_loop(StepFileLine & line)
{
  StepVertexLoop *entity = new StepVertexLoop;
  entity->read(line);
  return entity;
}
// ------------ StepVertexPoint

bool StepVertexPoint::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(vertex_geometry);
  return ok;
}

void StepVertexPoint::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, vertex_geometry);
}

StepEntity *step_create_vertex_point(StepFileLine & line)
{
  StepVertexPoint *entity = new StepVertexPoint;
  entity->read(line);
  return entity;
}
// ------------ StepSolidModel

bool StepSolidModel::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepSolidModel::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_solid_model(StepFileLine & line)
{
  StepSolidModel *entity = new StepSolidModel;
  entity->read(line);
  return entity;
}
// ------------ StepShellBasedWireframeModel

bool StepShellBasedWireframeModel::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readSelectArray(sbwm_boundary);
  return ok;
}

void StepShellBasedWireframeModel::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeSelectArray(os, sbwm_boundary);
}

StepEntity *step_create_shell_based_wireframe_model(StepFileLine & line)
{
  StepShellBasedWireframeModel *entity = new StepShellBasedWireframeModel;
  entity->read(line);
  return entity;
}
// ------------ StepPlacement

bool StepPlacement::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(location);
  return ok;
}

void StepPlacement::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, location);
}

StepEntity *step_create_placement(StepFileLine & line)
{
  StepPlacement *entity = new StepPlacement;
  entity->read(line);
  return entity;
}
// ------------ StepPointOnSurface

bool StepPointOnSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_surface);
  ok &= line.readAttr(point_parameter_u);
  ok &= line.readAttr(point_parameter_v);
  return ok;
}

void StepPointOnSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_surface); os << ',';
  StepFileLine::writeAttr(os, point_parameter_u); os << ',';
  StepFileLine::writeAttr(os, point_parameter_v);
}

StepEntity *step_create_point_on_surface(StepFileLine & line)
{
  StepPointOnSurface *entity = new StepPointOnSurface;
  entity->read(line);
  return entity;
}
// ------------ StepCartesianPoint

bool StepCartesianPoint::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readArrayAttr<3>(coordinates);
  return ok;
}

void StepCartesianPoint::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeArrayAttr<3>(os, coordinates);
}

StepEntity *step_create_cartesian_point(StepFileLine & line)
{
  StepCartesianPoint *entity = new StepCartesianPoint;
  entity->read(line);
  return entity;
}
// ------------ StepEdgeLoop

bool StepEdgeLoop::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(edge_list);
  return ok;
}

void StepEdgeLoop::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, edge_list);
}

StepEntity *step_create_edge_loop(StepFileLine & line)
{
  StepEdgeLoop *entity = new StepEdgeLoop;
  entity->read(line);
  return entity;
}
// ------------ StepLine

bool StepLine::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(pnt);
  ok &= line.readAttr(dir);
  return ok;
}

void StepLine::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, pnt); os << ',';
  StepFileLine::writeAttr(os, dir);
}

StepEntity *step_create_line(StepFileLine & line)
{
  StepLine *entity = new StepLine;
  entity->read(line);
  return entity;
}
// ------------ StepConic

bool StepConic::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= position.read(line);
  return ok;
}

void StepConic::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  position.write(os);
}

StepEntity *step_create_conic(StepFileLine & line)
{
  StepConic *entity = new StepConic;
  entity->read(line);
  return entity;
}
// ------------ StepFaceSurface

bool StepFaceSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(bounds);
  ok &= line.readAttr(face_geometry);
  ok &= line.readAttr(same_sense);
  return ok;
}

void StepFaceSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, bounds); os << ',';
  StepFileLine::writeAttr(os, face_geometry); os << ',';
  StepFileLine::writeAttr(os, same_sense);
}

StepEntity *step_create_face_surface(StepFileLine & line)
{
  StepFaceSurface *entity = new StepFaceSurface;
  entity->read(line);
  return entity;
}
// ------------ StepCartesianTransformationOperator

bool StepCartesianTransformationOperator::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.option() ? line.readAttr(axis1) : line.skipAttr();
  ok &= line.option() ? line.readAttr(axis2) : line.skipAttr();
  ok &= line.readAttr(local_origin);
  ok &= line.option() ? line.readAttr(scale) : line.skipAttr();
  return ok;
}

void StepCartesianTransformationOperator::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, axis1, '$'); os << ',';
  StepFileLine::writeAttr(os, axis2, '$'); os << ',';
  StepFileLine::writeAttr(os, local_origin); os << ',';
  StepFileLine::writeAttr(os, scale);
}

StepEntity *step_create_cartesian_transformation_operator(StepFileLine & line)
{
  StepCartesianTransformationOperator *entity = new StepCartesianTransformationOperator;
  entity->read(line);
  return entity;
}
// ------------ StepPointReplica

bool StepPointReplica::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(parent_pt);
  ok &= line.readAttr(transformation);
  return ok;
}

void StepPointReplica::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, parent_pt); os << ',';
  StepFileLine::writeAttr(os, transformation);
}

StepEntity *step_create_point_replica(StepFileLine & line)
{
  StepPointReplica *entity = new StepPointReplica;
  entity->read(line);
  return entity;
}
// ------------ StepManifoldSolidBrep

bool StepManifoldSolidBrep::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(outer);
  return ok;
}

void StepManifoldSolidBrep::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, outer);
}

StepEntity *step_create_manifold_solid_brep(StepFileLine & line)
{
  StepManifoldSolidBrep *entity = new StepManifoldSolidBrep;
  entity->read(line);
  return entity;
}
// ------------ StepBrepWithVoids

bool StepBrepWithVoids::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(outer);
  ok &= line.readAttr(voids);
  return ok;
}

void StepBrepWithVoids::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, outer); os << ',';
  StepFileLine::writeAttr(os, voids);
}

StepEntity *step_create_brep_with_voids(StepFileLine & line)
{
  StepBrepWithVoids *entity = new StepBrepWithVoids;
  entity->read(line);
  return entity;
}
// ------------ StepSurfaceCurve

bool StepSurfaceCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(curve_3d);
  ok &= line.readSelectArray<2>(associated_geometry);
  ok &= master_representation.read(line);
  return ok;
}

void StepSurfaceCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, curve_3d); os << ',';
  StepFileLine::writeSelectArray<2>(os, associated_geometry); os << ',';
  master_representation.write(os);
}

StepEntity *step_create_surface_curve(StepFileLine & line)
{
  StepSurfaceCurve *entity = new StepSurfaceCurve;
  entity->read(line);
  return entity;
}
// ------------ StepAxis2Placement3d

bool StepAxis2Placement3d::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(location);
  ok &= line.option() ? line.readAttr(axis) : line.skipAttr();
  ok &= line.option() ? line.readAttr(ref_direction) : line.skipAttr();
  return ok;
}

void StepAxis2Placement3d::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, location); os << ',';
  StepFileLine::writeAttr(os, axis, '$'); os << ',';
  StepFileLine::writeAttr(os, ref_direction, '$');
}

StepEntity *step_create_axis2_placement_3d(StepFileLine & line)
{
  StepAxis2Placement3d *entity = new StepAxis2Placement3d;
  entity->read(line);
  return entity;
}
// ------------ StepSurfaceReplica

bool StepSurfaceReplica::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(parent_surface);
  ok &= line.readAttr(transformation);
  return ok;
}

void StepSurfaceReplica::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, parent_surface); os << ',';
  StepFileLine::writeAttr(os, transformation);
}

StepEntity *step_create_surface_replica(StepFileLine & line)
{
  StepSurfaceReplica *entity = new StepSurfaceReplica;
  entity->read(line);
  return entity;
}
// ------------ StepHyperbola

bool StepHyperbola::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= position.read(line);
  ok &= line.readAttr(semi_axis);
  ok &= line.readAttr(semi_imag_axis);
  return ok;
}

void StepHyperbola::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  position.write(os); os << ',';
  StepFileLine::writeAttr(os, semi_axis); os << ',';
  StepFileLine::writeAttr(os, semi_imag_axis);
}

StepEntity *step_create_hyperbola(StepFileLine & line)
{
  StepHyperbola *entity = new StepHyperbola;
  entity->read(line);
  return entity;
}
// ------------ StepBoundedSurface

bool StepBoundedSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepBoundedSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_bounded_surface(StepFileLine & line)
{
  StepBoundedSurface *entity = new StepBoundedSurface;
  entity->read(line);
  return entity;
}
// ------------ StepPlane

bool StepPlane::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(position);
  return ok;
}

void StepPlane::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, position);
}

StepEntity *step_create_plane(StepFileLine & line)
{
  StepPlane *entity = new StepPlane;
  entity->read(line);
  return entity;
}
// ------------ StepEdgeBasedWireframeModel

bool StepEdgeBasedWireframeModel::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(ebwm_boundary);
  return ok;
}

void StepEdgeBasedWireframeModel::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, ebwm_boundary);
}

StepEntity *step_create_edge_based_wireframe_model(StepFileLine & line)
{
  StepEdgeBasedWireframeModel *entity = new StepEdgeBasedWireframeModel;
  entity->read(line);
  return entity;
}
// ------------ StepEdgeCurve

bool StepEdgeCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(edge_start);
  ok &= line.readAttr(edge_end);
  ok &= line.readAttr(edge_geometry);
  ok &= line.readAttr(same_sense);
  return ok;
}

void StepEdgeCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, edge_start); os << ',';
  StepFileLine::writeAttr(os, edge_end); os << ',';
  StepFileLine::writeAttr(os, edge_geometry); os << ',';
  StepFileLine::writeAttr(os, same_sense);
}

StepEntity *step_create_edge_curve(StepFileLine & line)
{
  StepEdgeCurve *entity = new StepEdgeCurve;
  entity->read(line);
  return entity;
}
// ------------ StepParabola

bool StepParabola::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= position.read(line);
  ok &= line.readAttr(focal_dist);
  return ok;
}

void StepParabola::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  position.write(os); os << ',';
  StepFileLine::writeAttr(os, focal_dist);
}

StepEntity *step_create_parabola(StepFileLine & line)
{
  StepParabola *entity = new StepParabola;
  entity->read(line);
  return entity;
}
// ------------ StepOffsetCurve3d

bool StepOffsetCurve3d::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_curve);
  ok &= line.readAttr(distance);
  ok &= self_intersect.read(line);
  ok &= line.readAttr(ref_direction);
  return ok;
}

void StepOffsetCurve3d::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_curve); os << ',';
  StepFileLine::writeAttr(os, distance); os << ',';
  self_intersect.write(os); os << ',';
  StepFileLine::writeAttr(os, ref_direction);
}

StepEntity *step_create_offset_curve_3d(StepFileLine & line)
{
  StepOffsetCurve3d *entity = new StepOffsetCurve3d;
  entity->read(line);
  return entity;
}
// ------------ StepSphericalSurface

bool StepSphericalSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(position);
  ok &= line.readAttr(radius);
  return ok;
}

void StepSphericalSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, position); os << ',';
  StepFileLine::writeAttr(os, radius);
}

StepEntity *step_create_spherical_surface(StepFileLine & line)
{
  StepSphericalSurface *entity = new StepSphericalSurface;
  entity->read(line);
  return entity;
}
// ------------ StepDegeneratePcurve

bool StepDegeneratePcurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_surface);
  ok &= line.readAttr(reference_to_curve);
  return ok;
}

void StepDegeneratePcurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_surface); os << ',';
  StepFileLine::writeAttr(os, reference_to_curve);
}

StepEntity *step_create_degenerate_pcurve(StepFileLine & line)
{
  StepDegeneratePcurve *entity = new StepDegeneratePcurve;
  entity->read(line);
  return entity;
}
// ------------ StepBSplineSurface

bool StepBSplineSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(u_degree);
  ok &= line.readAttr(v_degree);
  ok &= line.readAttr(control_points_list);
  ok &= surface_form.read(line);
  ok &= u_closed.read(line);
  ok &= v_closed.read(line);
  ok &= self_intersect.read(line);
  return ok;
}

void StepBSplineSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, u_degree); os << ',';
  StepFileLine::writeAttr(os, v_degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  surface_form.write(os); os << ',';
  u_closed.write(os); os << ',';
  v_closed.write(os); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_b_spline_surface(StepFileLine & line)
{
  StepBSplineSurface *entity = new StepBSplineSurface;
  entity->read(line);
  return entity;
}
// ------------ StepCurveBoundedSurface

bool StepCurveBoundedSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_surface);
  ok &= line.readAttr(boundaries);
  ok &= line.readAttr(implicit_outer);
  return ok;
}

void StepCurveBoundedSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_surface); os << ',';
  StepFileLine::writeAttr(os, boundaries); os << ',';
  StepFileLine::writeAttr(os, implicit_outer);
}

StepEntity *step_create_curve_bounded_surface(StepFileLine & line)
{
  StepCurveBoundedSurface *entity = new StepCurveBoundedSurface;
  entity->read(line);
  return entity;
}
// ------------ StepRectangularCompositeSurface

bool StepRectangularCompositeSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(segments);
  return ok;
}

void StepRectangularCompositeSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, segments);
}

StepEntity *step_create_rectangular_composite_surface(StepFileLine & line)
{
  StepRectangularCompositeSurface *entity = new StepRectangularCompositeSurface;
  entity->read(line);
  return entity;
}
// ------------ StepEllipse

bool StepEllipse::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= position.read(line);
  ok &= line.readAttr(semi_axis_1);
  ok &= line.readAttr(semi_axis_2);
  return ok;
}

void StepEllipse::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  position.write(os); os << ',';
  StepFileLine::writeAttr(os, semi_axis_1); os << ',';
  StepFileLine::writeAttr(os, semi_axis_2);
}

StepEntity *step_create_ellipse(StepFileLine & line)
{
  StepEllipse *entity = new StepEllipse;
  entity->read(line);
  return entity;
}
// ------------ StepRationalBSplineSurface

bool StepRationalBSplineSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(u_degree);
  ok &= line.readAttr(v_degree);
  ok &= line.readAttr(control_points_list);
  ok &= surface_form.read(line);
  ok &= u_closed.read(line);
  ok &= v_closed.read(line);
  ok &= self_intersect.read(line);
  ok &= line.readAttr(weights_data);
  return ok;
}

void StepRationalBSplineSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, u_degree); os << ',';
  StepFileLine::writeAttr(os, v_degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  surface_form.write(os); os << ',';
  u_closed.write(os); os << ',';
  v_closed.write(os); os << ',';
  self_intersect.write(os); os << ',';
  StepFileLine::writeAttr(os, weights_data);
}

StepEntity *step_create_rational_b_spline_surface(StepFileLine & line)
{
  StepRationalBSplineSurface *entity = new StepRationalBSplineSurface;
  entity->read(line);
  return entity;
}
// ------------ StepSweptSurface

bool StepSweptSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(swept_curve);
  return ok;
}

void StepSweptSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, swept_curve);
}

StepEntity *step_create_swept_surface(StepFileLine & line)
{
  StepSweptSurface *entity = new StepSweptSurface;
  entity->read(line);
  return entity;
}
// ------------ StepAxis2Placement2d

bool StepAxis2Placement2d::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(location);
  ok &= line.option() ? line.readAttr(ref_direction) : line.skipAttr();
  return ok;
}

void StepAxis2Placement2d::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, location); os << ',';
  StepFileLine::writeAttr(os, ref_direction, '$');
}

StepEntity *step_create_axis2_placement_2d(StepFileLine & line)
{
  StepAxis2Placement2d *entity = new StepAxis2Placement2d;
  entity->read(line);
  return entity;
}
// ------------ StepConicalSurface

bool StepConicalSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(position);
  ok &= line.readAttr(radius);
  ok &= line.readAttr(semi_angle);
  return ok;
}

void StepConicalSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, position); os << ',';
  StepFileLine::writeAttr(os, radius); os << ',';
  StepFileLine::writeAttr(os, semi_angle);
}

StepEntity *step_create_conical_surface(StepFileLine & line)
{
  StepConicalSurface *entity = new StepConicalSurface;
  entity->read(line);
  return entity;
}
// ------------ StepOffsetSurface

bool StepOffsetSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_surface);
  ok &= line.readAttr(distance);
  ok &= self_intersect.read(line);
  return ok;
}

void StepOffsetSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_surface); os << ',';
  StepFileLine::writeAttr(os, distance); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_offset_surface(StepFileLine & line)
{
  StepOffsetSurface *entity = new StepOffsetSurface;
  entity->read(line);
  return entity;
}
// ------------ StepFacetedBrep

bool StepFacetedBrep::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(outer);
  return ok;
}

void StepFacetedBrep::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, outer);
}

StepEntity *step_create_faceted_brep(StepFileLine & line)
{
  StepFacetedBrep *entity = new StepFacetedBrep;
  entity->read(line);
  return entity;
}
// ------------ StepSurfaceOfRevolution

bool StepSurfaceOfRevolution::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(swept_curve);
  ok &= line.readAttr(axis_position);
  return ok;
}

void StepSurfaceOfRevolution::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, swept_curve); os << ',';
  StepFileLine::writeAttr(os, axis_position);
}

StepEntity *step_create_surface_of_revolution(StepFileLine & line)
{
  StepSurfaceOfRevolution *entity = new StepSurfaceOfRevolution;
  entity->read(line);
  return entity;
}
// ------------ StepSurfaceOfLinearExtrusion

bool StepSurfaceOfLinearExtrusion::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(swept_curve);
  ok &= line.readAttr(extrusion_axis);
  return ok;
}

void StepSurfaceOfLinearExtrusion::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, swept_curve); os << ',';
  StepFileLine::writeAttr(os, extrusion_axis);
}

StepEntity *step_create_surface_of_linear_extrusion(StepFileLine & line)
{
  StepSurfaceOfLinearExtrusion *entity = new StepSurfaceOfLinearExtrusion;
  entity->read(line);
  return entity;
}
// ------------ StepPcurve

bool StepPcurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_surface);
  ok &= line.readAttr(reference_to_curve);
  return ok;
}

void StepPcurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_surface); os << ',';
  StepFileLine::writeAttr(os, reference_to_curve);
}

StepEntity *step_create_pcurve(StepFileLine & line)
{
  StepPcurve *entity = new StepPcurve;
  entity->read(line);
  return entity;
}
// ------------ StepUniformSurface

bool StepUniformSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(u_degree);
  ok &= line.readAttr(v_degree);
  ok &= line.readAttr(control_points_list);
  ok &= surface_form.read(line);
  ok &= u_closed.read(line);
  ok &= v_closed.read(line);
  ok &= self_intersect.read(line);
  return ok;
}

void StepUniformSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, u_degree); os << ',';
  StepFileLine::writeAttr(os, v_degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  surface_form.write(os); os << ',';
  u_closed.write(os); os << ',';
  v_closed.write(os); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_uniform_surface(StepFileLine & line)
{
  StepUniformSurface *entity = new StepUniformSurface;
  entity->read(line);
  return entity;
}
// ------------ StepBoundedCurve

bool StepBoundedCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  return ok;
}

void StepBoundedCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name);
}

StepEntity *step_create_bounded_curve(StepFileLine & line)
{
  StepBoundedCurve *entity = new StepBoundedCurve;
  entity->read(line);
  return entity;
}
// ------------ StepQuasiUniformSurface

bool StepQuasiUniformSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(u_degree);
  ok &= line.readAttr(v_degree);
  ok &= line.readAttr(control_points_list);
  ok &= surface_form.read(line);
  ok &= u_closed.read(line);
  ok &= v_closed.read(line);
  ok &= self_intersect.read(line);
  return ok;
}

void StepQuasiUniformSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, u_degree); os << ',';
  StepFileLine::writeAttr(os, v_degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  surface_form.write(os); os << ',';
  u_closed.write(os); os << ',';
  v_closed.write(os); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_quasi_uniform_surface(StepFileLine & line)
{
  StepQuasiUniformSurface *entity = new StepQuasiUniformSurface;
  entity->read(line);
  return entity;
}
// ------------ StepToroidalSurface

bool StepToroidalSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(position);
  ok &= line.readAttr(major_radius);
  ok &= line.readAttr(minor_radius);
  return ok;
}

void StepToroidalSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, position); os << ',';
  StepFileLine::writeAttr(os, major_radius); os << ',';
  StepFileLine::writeAttr(os, minor_radius);
}

StepEntity *step_create_toroidal_surface(StepFileLine & line)
{
  StepToroidalSurface *entity = new StepToroidalSurface;
  entity->read(line);
  return entity;
}
// ------------ StepOrientedOpenShell

bool StepOrientedOpenShell::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(cfs_faces);
  ok &= line.readAttr(open_shell_element);
  ok &= line.readAttr(orientation);
  return ok;
}

void StepOrientedOpenShell::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, cfs_faces); os << ',';
  StepFileLine::writeAttr(os, open_shell_element); os << ',';
  StepFileLine::writeAttr(os, orientation);
}

StepEntity *step_create_oriented_open_shell(StepFileLine & line)
{
  StepOrientedOpenShell *entity = new StepOrientedOpenShell;
  entity->read(line);
  return entity;
}
// ------------ StepCylindricalSurface

bool StepCylindricalSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(position);
  ok &= line.readAttr(radius);
  return ok;
}

void StepCylindricalSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, position); os << ',';
  StepFileLine::writeAttr(os, radius);
}

StepEntity *step_create_cylindrical_surface(StepFileLine & line)
{
  StepCylindricalSurface *entity = new StepCylindricalSurface;
  entity->read(line);
  return entity;
}
// ------------ StepIntersectionCurve

bool StepIntersectionCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(curve_3d);
  ok &= line.readSelectArray<2>(associated_geometry);
  ok &= master_representation.read(line);
  return ok;
}

void StepIntersectionCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, curve_3d); os << ',';
  StepFileLine::writeSelectArray<2>(os, associated_geometry); os << ',';
  master_representation.write(os);
}

StepEntity *step_create_intersection_curve(StepFileLine & line)
{
  StepIntersectionCurve *entity = new StepIntersectionCurve;
  entity->read(line);
  return entity;
}
// ------------ StepRectangularTrimmedSurface

bool StepRectangularTrimmedSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_surface);
  ok &= line.readAttr(u1);
  ok &= line.readAttr(u2);
  ok &= line.readAttr(v1);
  ok &= line.readAttr(v2);
  ok &= line.readAttr(usense);
  ok &= line.readAttr(vsense);
  return ok;
}

void StepRectangularTrimmedSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_surface); os << ',';
  StepFileLine::writeAttr(os, u1); os << ',';
  StepFileLine::writeAttr(os, u2); os << ',';
  StepFileLine::writeAttr(os, v1); os << ',';
  StepFileLine::writeAttr(os, v2); os << ',';
  StepFileLine::writeAttr(os, usense); os << ',';
  StepFileLine::writeAttr(os, vsense);
}

StepEntity *step_create_rectangular_trimmed_surface(StepFileLine & line)
{
  StepRectangularTrimmedSurface *entity = new StepRectangularTrimmedSurface;
  entity->read(line);
  return entity;
}
// ------------ StepSeamCurve

bool StepSeamCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(curve_3d);
  ok &= line.readSelectArray<2>(associated_geometry);
  ok &= master_representation.read(line);
  return ok;
}

void StepSeamCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, curve_3d); os << ',';
  StepFileLine::writeSelectArray<2>(os, associated_geometry); os << ',';
  master_representation.write(os);
}

StepEntity *step_create_seam_curve(StepFileLine & line)
{
  StepSeamCurve *entity = new StepSeamCurve;
  entity->read(line);
  return entity;
}
// ------------ StepAdvancedFace

bool StepAdvancedFace::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(bounds);
  ok &= line.readAttr(face_geometry);
  ok &= line.readAttr(same_sense);
  return ok;
}

void StepAdvancedFace::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, bounds); os << ',';
  StepFileLine::writeAttr(os, face_geometry); os << ',';
  StepFileLine::writeAttr(os, same_sense);
}

StepEntity *step_create_advanced_face(StepFileLine & line)
{
  StepAdvancedFace *entity = new StepAdvancedFace;
  entity->read(line);
  return entity;
}
// ------------ StepDegenerateToroidalSurface

bool StepDegenerateToroidalSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(position);
  ok &= line.readAttr(major_radius);
  ok &= line.readAttr(minor_radius);
  ok &= line.readAttr(select_outer);
  return ok;
}

void StepDegenerateToroidalSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, position); os << ',';
  StepFileLine::writeAttr(os, major_radius); os << ',';
  StepFileLine::writeAttr(os, minor_radius); os << ',';
  StepFileLine::writeAttr(os, select_outer);
}

StepEntity *step_create_degenerate_toroidal_surface(StepFileLine & line)
{
  StepDegenerateToroidalSurface *entity = new StepDegenerateToroidalSurface;
  entity->read(line);
  return entity;
}
// ------------ StepPolyline

bool StepPolyline::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(points);
  return ok;
}

void StepPolyline::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, points);
}

StepEntity *step_create_polyline(StepFileLine & line)
{
  StepPolyline *entity = new StepPolyline;
  entity->read(line);
  return entity;
}
// ------------ StepCircle

bool StepCircle::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= position.read(line);
  ok &= line.readAttr(radius);
  return ok;
}

void StepCircle::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  position.write(os); os << ',';
  StepFileLine::writeAttr(os, radius);
}

StepEntity *step_create_circle(StepFileLine & line)
{
  StepCircle *entity = new StepCircle;
  entity->read(line);
  return entity;
}
// ------------ StepBoundedSurfaceCurve

bool StepBoundedSurfaceCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(curve_3d);
  ok &= line.readSelectArray<2>(associated_geometry);
  ok &= master_representation.read(line);
  return ok;
}

void StepBoundedSurfaceCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, curve_3d); os << ',';
  StepFileLine::writeSelectArray<2>(os, associated_geometry); os << ',';
  master_representation.write(os);
}

StepEntity *step_create_bounded_surface_curve(StepFileLine & line)
{
  StepBoundedSurfaceCurve *entity = new StepBoundedSurfaceCurve;
  entity->read(line);
  return entity;
}
// ------------ StepAxis1Placement

bool StepAxis1Placement::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(location);
  ok &= line.option() ? line.readAttr(axis) : line.skipAttr();
  return ok;
}

void StepAxis1Placement::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, location); os << ',';
  StepFileLine::writeAttr(os, axis, '$');
}

StepEntity *step_create_axis1_placement(StepFileLine & line)
{
  StepAxis1Placement *entity = new StepAxis1Placement;
  entity->read(line);
  return entity;
}
// ------------ StepCartesianTransformationOperator3d

bool StepCartesianTransformationOperator3d::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.option() ? line.readAttr(axis1) : line.skipAttr();
  ok &= line.option() ? line.readAttr(axis2) : line.skipAttr();
  ok &= line.readAttr(local_origin);
  ok &= line.option() ? line.readAttr(scale) : line.skipAttr();
  ok &= line.option() ? line.readAttr(axis3) : line.skipAttr();
  return ok;
}

void StepCartesianTransformationOperator3d::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, axis1, '$'); os << ',';
  StepFileLine::writeAttr(os, axis2, '$'); os << ',';
  StepFileLine::writeAttr(os, local_origin); os << ',';
  StepFileLine::writeAttr(os, scale); os << ',';
  StepFileLine::writeAttr(os, axis3, '$');
}

StepEntity *step_create_cartesian_transformation_operator_3d(StepFileLine & line)
{
  StepCartesianTransformationOperator3d *entity = new StepCartesianTransformationOperator3d;
  entity->read(line);
  return entity;
}
// ------------ StepEvaluatedDegeneratePcurve

bool StepEvaluatedDegeneratePcurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_surface);
  ok &= line.readAttr(reference_to_curve);
  ok &= line.readAttr(equivalent_point);
  return ok;
}

void StepEvaluatedDegeneratePcurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_surface); os << ',';
  StepFileLine::writeAttr(os, reference_to_curve); os << ',';
  StepFileLine::writeAttr(os, equivalent_point);
}

StepEntity *step_create_evaluated_degenerate_pcurve(StepFileLine & line)
{
  StepEvaluatedDegeneratePcurve *entity = new StepEvaluatedDegeneratePcurve;
  entity->read(line);
  return entity;
}
// ------------ StepBezierSurface

bool StepBezierSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(u_degree);
  ok &= line.readAttr(v_degree);
  ok &= line.readAttr(control_points_list);
  ok &= surface_form.read(line);
  ok &= u_closed.read(line);
  ok &= v_closed.read(line);
  ok &= self_intersect.read(line);
  return ok;
}

void StepBezierSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, u_degree); os << ',';
  StepFileLine::writeAttr(os, v_degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  surface_form.write(os); os << ',';
  u_closed.write(os); os << ',';
  v_closed.write(os); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_bezier_surface(StepFileLine & line)
{
  StepBezierSurface *entity = new StepBezierSurface;
  entity->read(line);
  return entity;
}
// ------------ StepBSplineSurfaceWithKnots

bool StepBSplineSurfaceWithKnots::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(u_degree);
  ok &= line.readAttr(v_degree);
  ok &= line.readAttr(control_points_list);
  ok &= surface_form.read(line);
  ok &= u_closed.read(line);
  ok &= v_closed.read(line);
  ok &= self_intersect.read(line);
  ok &= line.readAttr(u_multiplicities);
  ok &= line.readAttr(v_multiplicities);
  ok &= line.readAttr(u_knots);
  ok &= line.readAttr(v_knots);
  ok &= knot_spec.read(line);
  return ok;
}

void StepBSplineSurfaceWithKnots::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, u_degree); os << ',';
  StepFileLine::writeAttr(os, v_degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  surface_form.write(os); os << ',';
  u_closed.write(os); os << ',';
  v_closed.write(os); os << ',';
  self_intersect.write(os); os << ',';
  StepFileLine::writeAttr(os, u_multiplicities); os << ',';
  StepFileLine::writeAttr(os, v_multiplicities); os << ',';
  StepFileLine::writeAttr(os, u_knots); os << ',';
  StepFileLine::writeAttr(os, v_knots); os << ',';
  knot_spec.write(os);
}

StepEntity *step_create_b_spline_surface_with_knots(StepFileLine & line)
{
  StepBSplineSurfaceWithKnots *entity = new StepBSplineSurfaceWithKnots;
  entity->read(line);
  return entity;
}
// ------------ StepBSplineCurve

bool StepBSplineCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(degree);
  ok &= line.readAttr(control_points_list);
  ok &= curve_form.read(line);
  ok &= closed_curve.read(line);
  ok &= self_intersect.read(line);
  return ok;
}

void StepBSplineCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  curve_form.write(os); os << ',';
  closed_curve.write(os); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_b_spline_curve(StepFileLine & line)
{
  StepBSplineCurve *entity = new StepBSplineCurve;
  entity->read(line);
  return entity;
}
// ------------ StepTrimmedCurve

bool StepTrimmedCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_curve);
  ok &= line.readSelectArray<2>(trim_1);
  ok &= line.readSelectArray<2>(trim_2);
  ok &= line.readAttr(sense_agreement);
  ok &= master_representation.read(line);
  return ok;
}

void StepTrimmedCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_curve); os << ',';
  StepFileLine::writeSelectArray<2>(os, trim_1); os << ',';
  StepFileLine::writeSelectArray<2>(os, trim_2); os << ',';
  StepFileLine::writeAttr(os, sense_agreement); os << ',';
  master_representation.write(os);
}

StepEntity *step_create_trimmed_curve(StepFileLine & line)
{
  StepTrimmedCurve *entity = new StepTrimmedCurve;
  entity->read(line);
  return entity;
}
// ------------ StepQuasiUniformCurve

bool StepQuasiUniformCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(degree);
  ok &= line.readAttr(control_points_list);
  ok &= curve_form.read(line);
  ok &= closed_curve.read(line);
  ok &= self_intersect.read(line);
  return ok;
}

void StepQuasiUniformCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  curve_form.write(os); os << ',';
  closed_curve.write(os); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_quasi_uniform_curve(StepFileLine & line)
{
  StepQuasiUniformCurve *entity = new StepQuasiUniformCurve;
  entity->read(line);
  return entity;
}
// ------------ StepCompositeCurve

bool StepCompositeCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(segments);
  ok &= self_intersect.read(line);
  return ok;
}

void StepCompositeCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, segments); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_composite_curve(StepFileLine & line)
{
  StepCompositeCurve *entity = new StepCompositeCurve;
  entity->read(line);
  return entity;
}
// ------------ StepBoundedPcurve

bool StepBoundedPcurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(basis_surface);
  ok &= line.readAttr(reference_to_curve);
  return ok;
}

void StepBoundedPcurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, basis_surface); os << ',';
  StepFileLine::writeAttr(os, reference_to_curve);
}

StepEntity *step_create_bounded_pcurve(StepFileLine & line)
{
  StepBoundedPcurve *entity = new StepBoundedPcurve;
  entity->read(line);
  return entity;
}
// ------------ StepUniformCurve

bool StepUniformCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(degree);
  ok &= line.readAttr(control_points_list);
  ok &= curve_form.read(line);
  ok &= closed_curve.read(line);
  ok &= self_intersect.read(line);
  return ok;
}

void StepUniformCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  curve_form.write(os); os << ',';
  closed_curve.write(os); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_uniform_curve(StepFileLine & line)
{
  StepUniformCurve *entity = new StepUniformCurve;
  entity->read(line);
  return entity;
}
// ------------ StepCompositeCurveOnSurface

bool StepCompositeCurveOnSurface::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(segments);
  ok &= self_intersect.read(line);
  return ok;
}

void StepCompositeCurveOnSurface::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, segments); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_composite_curve_on_surface(StepFileLine & line)
{
  StepCompositeCurveOnSurface *entity = new StepCompositeCurveOnSurface;
  entity->read(line);
  return entity;
}
// ------------ StepBezierCurve

bool StepBezierCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(degree);
  ok &= line.readAttr(control_points_list);
  ok &= curve_form.read(line);
  ok &= closed_curve.read(line);
  ok &= self_intersect.read(line);
  return ok;
}

void StepBezierCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  curve_form.write(os); os << ',';
  closed_curve.write(os); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_bezier_curve(StepFileLine & line)
{
  StepBezierCurve *entity = new StepBezierCurve;
  entity->read(line);
  return entity;
}
// ------------ StepRationalBSplineCurve

bool StepRationalBSplineCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(degree);
  ok &= line.readAttr(control_points_list);
  ok &= curve_form.read(line);
  ok &= closed_curve.read(line);
  ok &= self_intersect.read(line);
  ok &= line.readAttr(weights_data);
  return ok;
}

void StepRationalBSplineCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  curve_form.write(os); os << ',';
  closed_curve.write(os); os << ',';
  self_intersect.write(os); os << ',';
  StepFileLine::writeAttr(os, weights_data);
}

StepEntity *step_create_rational_b_spline_curve(StepFileLine & line)
{
  StepRationalBSplineCurve *entity = new StepRationalBSplineCurve;
  entity->read(line);
  return entity;
}
// ------------ StepBoundaryCurve

bool StepBoundaryCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(segments);
  ok &= self_intersect.read(line);
  return ok;
}

void StepBoundaryCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, segments); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_boundary_curve(StepFileLine & line)
{
  StepBoundaryCurve *entity = new StepBoundaryCurve;
  entity->read(line);
  return entity;
}
// ------------ StepOuterBoundaryCurve

bool StepOuterBoundaryCurve::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(segments);
  ok &= self_intersect.read(line);
  return ok;
}

void StepOuterBoundaryCurve::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, segments); os << ',';
  self_intersect.write(os);
}

StepEntity *step_create_outer_boundary_curve(StepFileLine & line)
{
  StepOuterBoundaryCurve *entity = new StepOuterBoundaryCurve;
  entity->read(line);
  return entity;
}
// ------------ StepBSplineCurveWithKnots

bool StepBSplineCurveWithKnots::read(StepFileLine & line)
{
  bool ok = true;
  ok &= line.readAttr(name);
  ok &= line.readAttr(degree);
  ok &= line.readAttr(control_points_list);
  ok &= curve_form.read(line);
  ok &= closed_curve.read(line);
  ok &= self_intersect.read(line);
  ok &= line.readAttr(knot_multiplicities);
  ok &= line.readAttr(knots);
  ok &= knot_spec.read(line);
  return ok;
}

void StepBSplineCurveWithKnots::write(std::ostream & os) const
{
  StepFileLine::writeAttr(os, name); os << ',';
  StepFileLine::writeAttr(os, degree); os << ',';
  StepFileLine::writeAttr(os, control_points_list); os << ',';
  curve_form.write(os); os << ',';
  closed_curve.write(os); os << ',';
  self_intersect.write(os); os << ',';
  StepFileLine::writeAttr(os, knot_multiplicities); os << ',';
  StepFileLine::writeAttr(os, knots); os << ',';
  knot_spec.write(os);
}

StepEntity *step_create_b_spline_curve_with_knots(StepFileLine & line)
{
  StepBSplineCurveWithKnots *entity = new StepBSplineCurveWithKnots;
  entity->read(line);
  return entity;
}
