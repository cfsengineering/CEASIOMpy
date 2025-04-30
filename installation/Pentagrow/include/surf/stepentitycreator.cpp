
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
 

// automatically created by surf/tools/fedex.py -- do not edit

#include "stepentitycreator.h"
#include "step_ap203.h"

// ------------ StepEntityCreator

StepEntityCreator::StepEntityCreator()
{
  fmap["CONTRACT_ASSIGNMENT"] = step_create_contract_assignment;
  fmap["REPRESENTATION_MAP"] = step_create_representation_map;
  fmap["CERTIFICATION_ASSIGNMENT"] = step_create_certification_assignment;
  fmap["PRODUCT_CATEGORY_RELATIONSHIP"] = step_create_product_category_relationship;
  fmap["FOUNDED_ITEM"] = step_create_founded_item;
  fmap["ACTION_STATUS"] = step_create_action_status;
  fmap["PRODUCT"] = step_create_product;
  fmap["APPROVAL_RELATIONSHIP"] = step_create_approval_relationship;
  fmap["CONTRACT"] = step_create_contract;
  fmap["REPRESENTATION"] = step_create_representation;
  fmap["CC_DESIGN_CERTIFICATION"] = step_create_cc_design_certification;
  fmap["SHAPE_REPRESENTATION"] = step_create_shape_representation;
  fmap["ORGANIZATION"] = step_create_organization;
  fmap["PRODUCT_CATEGORY"] = step_create_product_category;
  fmap["APPROVAL_ASSIGNMENT"] = step_create_approval_assignment;
  fmap["CONFIGURATION_ITEM"] = step_create_configuration_item;
  fmap["PRODUCT_RELATED_PRODUCT_CATEGORY"] = step_create_product_related_product_category;
  fmap["DATE_TIME_ROLE"] = step_create_date_time_role;
  fmap["EFFECTIVITY"] = step_create_effectivity;
  fmap["APPLICATION_CONTEXT_ELEMENT"] = step_create_application_context_element;
  fmap["MEASURE_WITH_UNIT"] = step_create_measure_with_unit;
  fmap["DIMENSIONAL_EXPONENTS"] = step_create_dimensional_exponents;
  fmap["SERIAL_NUMBERED_EFFECTIVITY"] = step_create_serial_numbered_effectivity;
  fmap["VERSIONED_ACTION_REQUEST"] = step_create_versioned_action_request;
  fmap["ADVANCED_BREP_SHAPE_REPRESENTATION"] = step_create_advanced_brep_shape_representation;
  fmap["PRODUCT_DEFINITION_CONTEXT"] = step_create_product_definition_context;
  fmap["PRODUCT_DEFINITION_EFFECTIVITY"] = step_create_product_definition_effectivity;
  fmap["DOCUMENT"] = step_create_document;
  fmap["GEOMETRICALLY_BOUNDED_SURFACE_SHAPE_REPRESENTATION"] = step_create_geometrically_bounded_surface_shape_representation;
  fmap["ADDRESS"] = step_create_address;
  fmap["MASS_MEASURE_WITH_UNIT"] = step_create_mass_measure_with_unit;
  fmap["PROPERTY_DEFINITION"] = step_create_property_definition;
  fmap["ORGANIZATIONAL_PROJECT"] = step_create_organizational_project;
  fmap["PRODUCT_CONCEPT"] = step_create_product_concept;
  fmap["EDGE_BASED_WIREFRAME_SHAPE_REPRESENTATION"] = step_create_edge_based_wireframe_shape_representation;
  fmap["CONTRACT_TYPE"] = step_create_contract_type;
  fmap["PRODUCT_CONCEPT_CONTEXT"] = step_create_product_concept_context;
  fmap["DATE"] = step_create_date;
  fmap["SECURITY_CLASSIFICATION_ASSIGNMENT"] = step_create_security_classification_assignment;
  fmap["PERSON"] = step_create_person;
  fmap["CC_DESIGN_CONTRACT"] = step_create_cc_design_contract;
  fmap["APPROVAL_STATUS"] = step_create_approval_status;
  fmap["FACETED_BREP_SHAPE_REPRESENTATION"] = step_create_faceted_brep_shape_representation;
  fmap["SECURITY_CLASSIFICATION_LEVEL"] = step_create_security_classification_level;
  fmap["DEFINITIONAL_REPRESENTATION"] = step_create_definitional_representation;
  fmap["SURFACE_PATCH"] = step_create_surface_patch;
  fmap["CC_DESIGN_APPROVAL"] = step_create_cc_design_approval;
  fmap["WEEK_OF_YEAR_AND_DAY_DATE"] = step_create_week_of_year_and_day_date;
  fmap["DESIGN_CONTEXT"] = step_create_design_context;
  fmap["LOCAL_TIME"] = step_create_local_time;
  fmap["PROPERTY_DEFINITION_REPRESENTATION"] = step_create_property_definition_representation;
  fmap["ACTION_REQUEST_STATUS"] = step_create_action_request_status;
  fmap["SHAPE_DEFINITION_REPRESENTATION"] = step_create_shape_definition_representation;
  fmap["DOCUMENT_REFERENCE"] = step_create_document_reference;
  fmap["NAMED_UNIT"] = step_create_named_unit;
  fmap["ACTION_REQUEST_ASSIGNMENT"] = step_create_action_request_assignment;
  fmap["DATE_AND_TIME"] = step_create_date_and_time;
  fmap["CONFIGURATION_DESIGN"] = step_create_configuration_design;
  fmap["CONTEXT_DEPENDENT_SHAPE_REPRESENTATION"] = step_create_context_dependent_shape_representation;
  fmap["REPRESENTATION_ITEM"] = step_create_representation_item;
  fmap["APPLICATION_CONTEXT"] = step_create_application_context;
  fmap["ORDINAL_DATE"] = step_create_ordinal_date;
  fmap["CERTIFICATION_TYPE"] = step_create_certification_type;
  fmap["ITEM_DEFINED_TRANSFORMATION"] = step_create_item_defined_transformation;
  fmap["CONFIGURATION_EFFECTIVITY"] = step_create_configuration_effectivity;
  fmap["DOCUMENT_WITH_CLASS"] = step_create_document_with_class;
  fmap["PRODUCT_CONTEXT"] = step_create_product_context;
  fmap["DOCUMENT_USAGE_CONSTRAINT"] = step_create_document_usage_constraint;
  fmap["CC_DESIGN_SPECIFICATION_REFERENCE"] = step_create_cc_design_specification_reference;
  fmap["FUNCTIONALLY_DEFINED_TRANSFORMATION"] = step_create_functionally_defined_transformation;
  fmap["PERSONAL_ADDRESS"] = step_create_personal_address;
  fmap["VOLUME_MEASURE_WITH_UNIT"] = step_create_volume_measure_with_unit;
  fmap["MANIFOLD_SURFACE_SHAPE_REPRESENTATION"] = step_create_manifold_surface_shape_representation;
  fmap["SHAPE_ASPECT_RELATIONSHIP"] = step_create_shape_aspect_relationship;
  fmap["CALENDAR_DATE"] = step_create_calendar_date;
  fmap["PERSON_AND_ORGANIZATION_ASSIGNMENT"] = step_create_person_and_organization_assignment;
  fmap["ACTION_ASSIGNMENT"] = step_create_action_assignment;
  fmap["SHAPE_ASPECT"] = step_create_shape_aspect;
  fmap["LENGTH_MEASURE_WITH_UNIT"] = step_create_length_measure_with_unit;
  fmap["ALTERNATE_PRODUCT_RELATIONSHIP"] = step_create_alternate_product_relationship;
  fmap["DOCUMENT_RELATIONSHIP"] = step_create_document_relationship;
  fmap["ACTION_DIRECTIVE"] = step_create_action_directive;
  fmap["APPLICATION_PROTOCOL_DEFINITION"] = step_create_application_protocol_definition;
  fmap["PRODUCT_DEFINITION"] = step_create_product_definition;
  fmap["LOT_EFFECTIVITY"] = step_create_lot_effectivity;
  fmap["SHELL_BASED_WIREFRAME_SHAPE_REPRESENTATION"] = step_create_shell_based_wireframe_shape_representation;
  fmap["COORDINATED_UNIVERSAL_TIME_OFFSET"] = step_create_coordinated_universal_time_offset;
  fmap["APPROVAL_PERSON_ORGANIZATION"] = step_create_approval_person_organization;
  fmap["SOLID_ANGLE_MEASURE_WITH_UNIT"] = step_create_solid_angle_measure_with_unit;
  fmap["SECURITY_CLASSIFICATION"] = step_create_security_classification;
  fmap["PLANE_ANGLE_MEASURE_WITH_UNIT"] = step_create_plane_angle_measure_with_unit;
  fmap["PRODUCT_DEFINITION_RELATIONSHIP"] = step_create_product_definition_relationship;
  fmap["REPRESENTATION_CONTEXT"] = step_create_representation_context;
  fmap["DATED_EFFECTIVITY"] = step_create_dated_effectivity;
  fmap["COMPOSITE_CURVE_SEGMENT"] = step_create_composite_curve_segment;
  fmap["SOLID_ANGLE_UNIT"] = step_create_solid_angle_unit;
  fmap["ACTION_METHOD"] = step_create_action_method;
  fmap["ORGANIZATION_RELATIONSHIP"] = step_create_organization_relationship;
  fmap["START_REQUEST"] = step_create_start_request;
  fmap["ACTION"] = step_create_action;
  fmap["CHANGE"] = step_create_change;
  fmap["CHANGE_REQUEST"] = step_create_change_request;
  fmap["AREA_MEASURE_WITH_UNIT"] = step_create_area_measure_with_unit;
  fmap["APPROVAL_DATE_TIME"] = step_create_approval_date_time;
  fmap["APPROVAL_ROLE"] = step_create_approval_role;
  fmap["PERSON_AND_ORGANIZATION_ROLE"] = step_create_person_and_organization_role;
  fmap["VOLUME_UNIT"] = step_create_volume_unit;
  fmap["PRODUCT_DEFINITION_FORMATION"] = step_create_product_definition_formation;
  fmap["APPROVAL"] = step_create_approval;
  fmap["TOPOLOGICAL_REPRESENTATION_ITEM"] = step_create_topological_representation_item;
  fmap["PRODUCT_DEFINITION_USAGE"] = step_create_product_definition_usage;
  fmap["ACTION_REQUEST_SOLUTION"] = step_create_action_request_solution;
  fmap["REPRESENTATION_RELATIONSHIP"] = step_create_representation_relationship;
  fmap["DOCUMENT_TYPE"] = step_create_document_type;
  fmap["DATE_AND_TIME_ASSIGNMENT"] = step_create_date_and_time_assignment;
  fmap["PERSON_AND_ORGANIZATION"] = step_create_person_and_organization;
  fmap["CERTIFICATION"] = step_create_certification;
  fmap["VERTEX"] = step_create_vertex;
  fmap["PRODUCT_DEFINITION_SHAPE"] = step_create_product_definition_shape;
  fmap["ASSEMBLY_COMPONENT_USAGE_SUBSTITUTE"] = step_create_assembly_component_usage_substitute;
  fmap["CONVERSION_BASED_UNIT"] = step_create_conversion_based_unit;
  fmap["EXECUTED_ACTION"] = step_create_executed_action;
  fmap["CC_DESIGN_SECURITY_CLASSIFICATION"] = step_create_cc_design_security_classification;
  fmap["EDGE"] = step_create_edge;
  fmap["SUPPLIED_PART_RELATIONSHIP"] = step_create_supplied_part_relationship;
  fmap["START_WORK"] = step_create_start_work;
  fmap["ORGANIZATIONAL_ADDRESS"] = step_create_organizational_address;
  fmap["MAPPED_ITEM"] = step_create_mapped_item;
  fmap["GLOBAL_UNIT_ASSIGNED_CONTEXT"] = step_create_global_unit_assigned_context;
  fmap["REPARAMETRISED_COMPOSITE_CURVE_SEGMENT"] = step_create_reparametrised_composite_curve_segment;
  fmap["LOOP"] = step_create_loop;
  fmap["PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE"] = step_create_product_definition_formation_with_specified_source;
  fmap["PRODUCT_DEFINITION_WITH_ASSOCIATED_DOCUMENTS"] = step_create_product_definition_with_associated_documents;
  fmap["PLANE_ANGLE_UNIT"] = step_create_plane_angle_unit;
  fmap["LENGTH_UNIT"] = step_create_length_unit;
  fmap["AREA_UNIT"] = step_create_area_unit;
  fmap["GEOMETRIC_REPRESENTATION_CONTEXT"] = step_create_geometric_representation_context;
  fmap["WIRE_SHELL"] = step_create_wire_shell;
  fmap["ASSEMBLY_COMPONENT_USAGE"] = step_create_assembly_component_usage;
  fmap["FACE"] = step_create_face;
  fmap["SI_UNIT"] = step_create_si_unit;
  fmap["UNCERTAINTY_MEASURE_WITH_UNIT"] = step_create_uncertainty_measure_with_unit;
  fmap["PATH"] = step_create_path;
  fmap["CONNECTED_FACE_SET"] = step_create_connected_face_set;
  fmap["ORIENTED_FACE"] = step_create_oriented_face;
  fmap["GEOMETRICALLY_BOUNDED_WIREFRAME_SHAPE_REPRESENTATION"] = step_create_geometrically_bounded_wireframe_shape_representation;
  fmap["MASS_UNIT"] = step_create_mass_unit;
  fmap["PARAMETRIC_REPRESENTATION_CONTEXT"] = step_create_parametric_representation_context;
  fmap["SPECIFIED_HIGHER_USAGE_OCCURRENCE"] = step_create_specified_higher_usage_occurrence;
  fmap["GEOMETRIC_REPRESENTATION_ITEM"] = step_create_geometric_representation_item;
  fmap["CC_DESIGN_DATE_AND_TIME_ASSIGNMENT"] = step_create_cc_design_date_and_time_assignment;
  fmap["GEOMETRIC_SET"] = step_create_geometric_set;
  fmap["CC_DESIGN_PERSON_AND_ORGANIZATION_ASSIGNMENT"] = step_create_cc_design_person_and_organization_assignment;
  fmap["CONNECTED_EDGE_SET"] = step_create_connected_edge_set;
  fmap["CONTEXT_DEPENDENT_UNIT"] = step_create_context_dependent_unit;
  fmap["GEOMETRIC_CURVE_SET"] = step_create_geometric_curve_set;
  fmap["ORIENTED_EDGE"] = step_create_oriented_edge;
  fmap["CLOSED_SHELL"] = step_create_closed_shell;
  fmap["SHAPE_REPRESENTATION_RELATIONSHIP"] = step_create_shape_representation_relationship;
  fmap["GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT"] = step_create_global_uncertainty_assigned_context;
  fmap["REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION"] = step_create_representation_relationship_with_transformation;
  fmap["MECHANICAL_CONTEXT"] = step_create_mechanical_context;
  fmap["ORIENTED_CLOSED_SHELL"] = step_create_oriented_closed_shell;
  fmap["DIRECTION"] = step_create_direction;
  fmap["VERTEX_SHELL"] = step_create_vertex_shell;
  fmap["NEXT_ASSEMBLY_USAGE_OCCURRENCE"] = step_create_next_assembly_usage_occurrence;
  fmap["ORIENTED_PATH"] = step_create_oriented_path;
  fmap["FACE_BOUND"] = step_create_face_bound;
  fmap["VECTOR"] = step_create_vector;
  fmap["DIRECTED_ACTION"] = step_create_directed_action;
  fmap["SURFACE"] = step_create_surface;
  fmap["SHELL_BASED_SURFACE_MODEL"] = step_create_shell_based_surface_model;
  fmap["DESIGN_MAKE_FROM_RELATIONSHIP"] = step_create_design_make_from_relationship;
  fmap["POLY_LOOP"] = step_create_poly_loop;
  fmap["CURVE"] = step_create_curve;
  fmap["PROMISSORY_USAGE_OCCURRENCE"] = step_create_promissory_usage_occurrence;
  fmap["POINT"] = step_create_point;
  fmap["QUANTIFIED_ASSEMBLY_COMPONENT_USAGE"] = step_create_quantified_assembly_component_usage;
  fmap["FACE_OUTER_BOUND"] = step_create_face_outer_bound;
  fmap["OPEN_SHELL"] = step_create_open_shell;
  fmap["ELEMENTARY_SURFACE"] = step_create_elementary_surface;
  fmap["POINT_ON_CURVE"] = step_create_point_on_curve;
  fmap["CURVE_REPLICA"] = step_create_curve_replica;
  fmap["VERTEX_LOOP"] = step_create_vertex_loop;
  fmap["VERTEX_POINT"] = step_create_vertex_point;
  fmap["SOLID_MODEL"] = step_create_solid_model;
  fmap["SHELL_BASED_WIREFRAME_MODEL"] = step_create_shell_based_wireframe_model;
  fmap["PLACEMENT"] = step_create_placement;
  fmap["POINT_ON_SURFACE"] = step_create_point_on_surface;
  fmap["CARTESIAN_POINT"] = step_create_cartesian_point;
  fmap["EDGE_LOOP"] = step_create_edge_loop;
  fmap["LINE"] = step_create_line;
  fmap["CONIC"] = step_create_conic;
  fmap["FACE_SURFACE"] = step_create_face_surface;
  fmap["CARTESIAN_TRANSFORMATION_OPERATOR"] = step_create_cartesian_transformation_operator;
  fmap["POINT_REPLICA"] = step_create_point_replica;
  fmap["MANIFOLD_SOLID_BREP"] = step_create_manifold_solid_brep;
  fmap["BREP_WITH_VOIDS"] = step_create_brep_with_voids;
  fmap["SURFACE_CURVE"] = step_create_surface_curve;
  fmap["AXIS2_PLACEMENT_3D"] = step_create_axis2_placement_3d;
  fmap["SURFACE_REPLICA"] = step_create_surface_replica;
  fmap["HYPERBOLA"] = step_create_hyperbola;
  fmap["BOUNDED_SURFACE"] = step_create_bounded_surface;
  fmap["PLANE"] = step_create_plane;
  fmap["EDGE_BASED_WIREFRAME_MODEL"] = step_create_edge_based_wireframe_model;
  fmap["EDGE_CURVE"] = step_create_edge_curve;
  fmap["PARABOLA"] = step_create_parabola;
  fmap["OFFSET_CURVE_3D"] = step_create_offset_curve_3d;
  fmap["SPHERICAL_SURFACE"] = step_create_spherical_surface;
  fmap["DEGENERATE_PCURVE"] = step_create_degenerate_pcurve;
  fmap["B_SPLINE_SURFACE"] = step_create_b_spline_surface;
  fmap["CURVE_BOUNDED_SURFACE"] = step_create_curve_bounded_surface;
  fmap["RECTANGULAR_COMPOSITE_SURFACE"] = step_create_rectangular_composite_surface;
  fmap["ELLIPSE"] = step_create_ellipse;
  fmap["RATIONAL_B_SPLINE_SURFACE"] = step_create_rational_b_spline_surface;
  fmap["SWEPT_SURFACE"] = step_create_swept_surface;
  fmap["AXIS2_PLACEMENT_2D"] = step_create_axis2_placement_2d;
  fmap["CONICAL_SURFACE"] = step_create_conical_surface;
  fmap["OFFSET_SURFACE"] = step_create_offset_surface;
  fmap["FACETED_BREP"] = step_create_faceted_brep;
  fmap["SURFACE_OF_REVOLUTION"] = step_create_surface_of_revolution;
  fmap["SURFACE_OF_LINEAR_EXTRUSION"] = step_create_surface_of_linear_extrusion;
  fmap["PCURVE"] = step_create_pcurve;
  fmap["UNIFORM_SURFACE"] = step_create_uniform_surface;
  fmap["BOUNDED_CURVE"] = step_create_bounded_curve;
  fmap["QUASI_UNIFORM_SURFACE"] = step_create_quasi_uniform_surface;
  fmap["TOROIDAL_SURFACE"] = step_create_toroidal_surface;
  fmap["ORIENTED_OPEN_SHELL"] = step_create_oriented_open_shell;
  fmap["CYLINDRICAL_SURFACE"] = step_create_cylindrical_surface;
  fmap["INTERSECTION_CURVE"] = step_create_intersection_curve;
  fmap["RECTANGULAR_TRIMMED_SURFACE"] = step_create_rectangular_trimmed_surface;
  fmap["SEAM_CURVE"] = step_create_seam_curve;
  fmap["ADVANCED_FACE"] = step_create_advanced_face;
  fmap["DEGENERATE_TOROIDAL_SURFACE"] = step_create_degenerate_toroidal_surface;
  fmap["POLYLINE"] = step_create_polyline;
  fmap["CIRCLE"] = step_create_circle;
  fmap["BOUNDED_SURFACE_CURVE"] = step_create_bounded_surface_curve;
  fmap["AXIS1_PLACEMENT"] = step_create_axis1_placement;
  fmap["CARTESIAN_TRANSFORMATION_OPERATOR_3D"] = step_create_cartesian_transformation_operator_3d;
  fmap["EVALUATED_DEGENERATE_PCURVE"] = step_create_evaluated_degenerate_pcurve;
  fmap["BEZIER_SURFACE"] = step_create_bezier_surface;
  fmap["B_SPLINE_SURFACE_WITH_KNOTS"] = step_create_b_spline_surface_with_knots;
  fmap["B_SPLINE_CURVE"] = step_create_b_spline_curve;
  fmap["TRIMMED_CURVE"] = step_create_trimmed_curve;
  fmap["QUASI_UNIFORM_CURVE"] = step_create_quasi_uniform_curve;
  fmap["COMPOSITE_CURVE"] = step_create_composite_curve;
  fmap["BOUNDED_PCURVE"] = step_create_bounded_pcurve;
  fmap["UNIFORM_CURVE"] = step_create_uniform_curve;
  fmap["COMPOSITE_CURVE_ON_SURFACE"] = step_create_composite_curve_on_surface;
  fmap["BEZIER_CURVE"] = step_create_bezier_curve;
  fmap["RATIONAL_B_SPLINE_CURVE"] = step_create_rational_b_spline_curve;
  fmap["BOUNDARY_CURVE"] = step_create_boundary_curve;
  fmap["OUTER_BOUNDARY_CURVE"] = step_create_outer_boundary_curve;
  fmap["B_SPLINE_CURVE_WITH_KNOTS"] = step_create_b_spline_curve_with_knots;
}

StepEntity *StepEntityCreator::create(StepFileLine & line, const std::string & key) const
{
  StepEntity *ep = 0;
  FunctionMap::const_iterator itr = fmap.find(key);
  if (itr != fmap.end())
    ep = (*(*itr->second))(line);
  return ep;
}

