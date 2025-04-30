
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
 
/** \mainpage libsurf

  # Introduction

  libsurf contains components which together make up a geometry kernel for
  surface modeling and unstructured mesh generation.


  # Geometry

  <a href="group__geometry.xhtml">[Link to Module Documentation]</a>

  A large part of libsurf implements curve and surface geometry objects which
  are used in the mesh generation functions. Further functionality concerns
  the efficient computation of intersection lines, even for multiple surfaces
  simultaneously, and low-level fundamental functions which facilitate mesh
  generation.

  Note that even though a wide variety of
  different types of curves and surfaces are equally fully supported,
  their performance characteristics differ, simply because of the mathematical
  complexity of their evaluation. Significant effort has been expended to
  speed up the evaluation of cubic (non-rational) b-spline curves and surfaces.


  # Interoperability

  <a href="group__interop.xhtml">[Link to Module Documentation]</a>

  In order to be able to exchange geometry information with external CAD
  systems, libsurf implements reading and writing of IGES and STEP AP203 files.
  More objects support output IGES than STEP i/o.

  When exporting geometry from libsurf to CAD, note that most CAD systems do not
  fully support the standard formats as they are documented. One important
  limitation which is often present regards the number of control points in
  spline surfaces and the maximum permit variation of tangent directions. If
  any of these limits is exceeded, the corresponding surface is either not
  imported at all or automatically split on import.

  # Mesh Generation

  <a href="group__meshgen.xhtml">[Link to Module Documentation]</a>

  libsurf contains two Delaunay-based surface mesh generators. The legacy
  generator used by sumo 2.x uses the classes prefixed by "Dn" while the new,
  much more flexible system is marked by "Dc". The main differences are that
  the "Dc" generator has support for explicitly defined topology information
  and the possibility to work on mapped domains.

  Some support for volume mesh generation is present in the form of interfaces
  to TetGen. Furthermore, class PentaGrow can be used to generate hybrid
  tetrahedral-pentahedral volume meshes for RANS solvers, but requires TetGen
  to be available for the tetrahedral domain.


  # Field Mapping

  <a href="group__mapping.xhtml">[Link to Module Documentation]</a>

  A number of classes are meant for the ratehr specialized task of mapping
  structural displacements of a structural model to aerodynamic surface mesh,
  and the perform the related operation of mapping pressure loads from
  aerodynamic to structural models.


  # Structural Modeling

  <a href="group__structures.xhtml">[Link to Module Documentation]</a>

  Classes prefixed with "Sm" can be used to simplify the creation of global
  shell-and-beam element finite-element models as they are typical for
  global full aircraft models for load distribution and dynamic analyses.

  The group of classes prefixed with "Nst" is designed to read and write
  files to interface with the NASTRAN family of structural finite-element
  solvers originating at NASA.


  # Licensing

  ## Commercial License Usage

  Licensees holding valid commercial licenses may use this file in accordance
  with the terms contained in their respective non-exclusive license agreement.
  For further information contact david@larosterna.com .

  ## GNU General Public License Usage

  Alternatively, this file may be used under the terms of the GNU General
  Public License version 3.0 as published by the Free Software Foundation and
  appearing in the file gpl.txt included in the package containing this file.


  # Deprecated Components

  Some parts of libsurf date back to about 2001 and are no longer used in new
  projects. However, they are still present in order to support legacy software.
  The corresponding classes are marked in the documentation as deprecated.

  */

/** \defgroup geometry Geometry
 *
 * A large part of libsurf implements curve and surface geometry objects which
 * are used in the mesh generation functions.
 *
 * Note that even though a wide variety of
 * different types of curves and surfaces are equally fully supported,
 * their performance characteristics differ, simply because of the mathematical
 * complexity of their evaluation. Significant effort has been expended to
 * speed up the evaluation of cubic (non-rational) b-spline curves and surfaces.
 *
 */

/** \defgroup interop Interoperability
 *
 * \brief Reading and writing of IGES and STEP.
 *
 * In order to be able to exchange geometry information with external CAD
 * systems, libsurf implements reading and writing of IGES and STEP AP203 files.
 *
 */

/** \defgroup meshgen Mesh Generation.
 *
 * \brief Support for surface triangulation.
 *
 * libsurf contains two Delaunay-based surface mesh generators. The legacy
 * generator used by sumo 2.x uses the classes prefixed by "Dn" while the new,
 * much more flexible system is marked by "Dc". The main differences are that
 * the "Dc" generator has support for explicitly defined topology information
 * and the possibility to work on a mapped domains.
 *
 * Some support for volume mesh generation is present in the form of interfaces
 * to TetGen. Furthermore, class PentaGrow can be used to generate hybrid
 * tetrahedral-pentahedral volume meshes for RANS solvers, but requires TetGen
 * to be available for the tetrahedral domain.
 *
 */

/** \defgroup structures Structural Modeling
 *
 * \brief Creating NASTRAN models and reading results
 *
 * Classes prefixed with "Sm" can be used to simplify the creation of global
 * shell-and-beam element finite-element models as they are typical for
 * global full aircraft models for load distribution and dynamic analyses.
 *
 * The group of classes prefixed with "Nst" is designed to read and write
 * files to interface with the NASTRAN family of structural finite-element
 * solvers originating at NASA.
 *
 */

/** \defgroup mapping Field Mapping
 *
 * \brief Interpolation between different mesh types.
 *
 * A number of classes are meant for the ratehr specialized task of mapping
 * structural displacements of a structural model to aerodynamic surface mesh,
 * and the perform the related operation of mapping pressure loads from
 * aerodynamic to structural models.
 *
 */

#ifndef SURF_FORWARD_H
#define SURF_FORWARD_H

#include <genua/forward.h>

typedef std::pair<uint,uint> IndexPair;
typedef std::vector<IndexPair> IndexPairArray;

class AbstractCurve;
typedef boost::shared_ptr<AbstractCurve> AbstractCurvePtr;
typedef std::vector<AbstractCurvePtr> AbstractCurveArray;
class MappedCurve;
typedef boost::shared_ptr<MappedCurve> MappedCurvePtr;
class Curve;
typedef boost::shared_ptr<Curve> CurvePtr;
typedef std::vector<CurvePtr> CurvePtrArray;
class Airfoil;
typedef boost::shared_ptr<Airfoil> AirfoilPtr;
typedef std::vector<AirfoilPtr> AirfoilPtrArray;
class AirfoilCollection;
class AirfoilFitter;
class OpenFrame;
class SymFrame;
class EllipFrame;
class EggFrame;
class CompositeCurve;
typedef boost::shared_ptr<CompositeCurve> CompositeCurvePtr;
class PolySplineCurve;
typedef boost::shared_ptr<PolySplineCurve> PolySplineCurvePtr;
class BezierSegment;

class AbstractUvCurve;
typedef boost::shared_ptr<AbstractUvCurve> AbstractUvCurvePtr;
typedef std::vector<AbstractUvCurvePtr> AbstractUvCurveArray;
typedef std::pair<AbstractUvCurvePtr,AbstractUvCurvePtr> AbstractUvCurvePair;
class UvPolyline;
typedef boost::shared_ptr<UvPolyline> UvPolylinePtr;
class UvCubicCurve;
typedef boost::shared_ptr<UvCubicCurve> UvCubicCurvePtr;
template <int P> class UvSplineCurve;

class Surface;
typedef boost::shared_ptr<Surface> SurfacePtr;
typedef std::vector<SurfacePtr> SurfaceArray;
class SkinSurface;
typedef boost::shared_ptr<SkinSurface> SkinSurfacePtr;
class LinearSurf;
typedef boost::shared_ptr<LinearSurf> LinearSurfPtr;
class Cylinder;
typedef boost::shared_ptr<Cylinder> CylinderPtr;
class RevoSurf;
typedef boost::shared_ptr<RevoSurf> RevoSurfPtr;
class PlaneSurface;
typedef boost::shared_ptr<PlaneSurface> PlaneSurfacePtr;
class PolySplineSurf;
typedef boost::shared_ptr<PolySplineSurf> PolySplineSurfPtr;
class RationalSplineSurf;
typedef boost::shared_ptr<RationalSplineSurf> RationalSplineSurfPtr;
class StitchedSurf;
typedef boost::shared_ptr<StitchedSurf> StitchedSurfPtr;
class SymSurf;
typedef boost::shared_ptr<SymSurf> SymSurfPtr;
class SubSurface;
typedef boost::shared_ptr<SubSurface> SubSurfacePtr;
typedef std::vector<SubSurfacePtr> SubSurfaceList;
class InstanceSurf;
typedef boost::shared_ptr<InstanceSurf> InstanceSurfPtr;
class TranSurf;
typedef boost::shared_ptr<TranSurf> TranSurfPtr;
class WakeSurf;
typedef boost::shared_ptr<WakeSurf> WakeSurfPtr;
class RingCapSurf;
typedef boost::shared_ptr<RingCapSurf> RingCapSurfPtr;
class LongCapSurf;
typedef boost::shared_ptr<LongCapSurf> LongCapSurfPtr;
class SlavedWake;
typedef boost::shared_ptr<SlavedWake> SlavedWakePtr;

// interoperability

class IgesFile;
class IgesEntity;
struct IgesDirEntry;
typedef boost::shared_ptr<IgesEntity> IgesEntityPtr;

class StepFile;
class StepEntity;

class MeshGenerator;
class MeshComponent;
typedef boost::shared_ptr<MeshComponent> MeshComponentPtr;
typedef std::vector<MeshComponentPtr> MeshComponentArray;
class WakeComponent;
class CmpAssembly;
class AsyComponent;
typedef boost::shared_ptr<AsyComponent> AsyComponentPtr;
typedef std::vector<AsyComponentPtr> AsyComponentArray;
class MgProgressCtrl;
typedef boost::shared_ptr<MgProgressCtrl> MgProgressPtr;

class IgesFile;
struct IgesDirEntry;
class IgesEntity;
class StepFile;

class DnMesh;
class DnTriangle;
typedef std::vector<DnTriangle> DnTriangleArray;
class DnCriterion;
typedef boost::shared_ptr<DnCriterion> DnCriterionPtr;
class DnRefineCriterion;
typedef boost::shared_ptr<DnRefineCriterion> DnRefineCriterionPtr;
class InitGrid;
class CascadeMesh;

class Product;
class ProductTree;
typedef boost::shared_ptr<ProductTree> ProductTreePtr;
typedef std::vector<ProductTreePtr> ProductArray;
class Instance;

class NstMesh;

class PentaGrow;
typedef boost::shared_ptr<PentaGrow> PentaGrowPtr;

// field mapping

class DispInterpolator;
class RbfInterpolator;
class SurfInterpolator;

// mesh generation

class DelaunayCore;
class DcFace;
class DcEdge;
class DcGeometry;
class DcMeshCritBase;
typedef boost::shared_ptr<DcMeshCritBase> DcMeshCritBasePtr;
class DcMeshCrit;
typedef boost::shared_ptr<DcMeshCrit> DcMeshCritPtr;
class DcMeshHeightCrit;
typedef boost::shared_ptr<DcMeshHeightCrit> DcMeshHeightCritPtr;
class DcMeshSourceCrit;
typedef boost::shared_ptr<DcMeshSourceCrit> DcMeshSourceCritPtr;
class DcMeshMultiCrit;
typedef boost::shared_ptr<DcMeshMultiCrit> DcMeshMultiCritPtr;
class UvMapping;
class UvMapDelaunay;
typedef boost::shared_ptr<UvMapDelaunay> UvMapDelaunayPtr;
class PatchMeshGenerator;
typedef boost::shared_ptr<PatchMeshGenerator> MeshGeneratorPtr;
class DcMeshGenerator;

#ifdef HAVE_JRSTRIANGLE
class JrsMeshGenerator;
#endif

// Topology

class TopoVertex;
class TopoEdge;
class TopoFace;
class Topology;
class TopoIsecSegment;
typedef std::vector<TopoIsecSegment> TopoIsecArray;

class TopoPart;
typedef boost::shared_ptr<TopoPart> TopoPartPtr;
typedef std::vector<TopoPartPtr> TopoPartArray;
class WingPart;
typedef boost::shared_ptr<WingPart> WingPartPtr;
class BasicPart;
typedef boost::shared_ptr<BasicPart> BasicPartPtr;
class HexBoxPart;
typedef boost::shared_ptr<HexBoxPart> HexBoxPartPtr;

// structural modelling

class MaterialProperty;
typedef boost::shared_ptr<MaterialProperty> MaterialPropertyPtr;
typedef std::vector<MaterialPropertyPtr> MaterialPropertyArray;
class DummyMaterial;
typedef boost::shared_ptr<DummyMaterial> DummyMaterialPtr;
class IsotropicMaterial;
typedef boost::shared_ptr<IsotropicMaterial> IsotropicMaterialPtr;
class OrthotropicMaterial;
typedef boost::shared_ptr<OrthotropicMaterial> OrthotropicMaterialPtr;

class ElementProperty;
typedef boost::shared_ptr<ElementProperty> ElementPropertyPtr;
typedef std::vector<ElementPropertyPtr> ElementPropertyArray;
class PlainShellProperty;
typedef boost::shared_ptr<PlainShellProperty> PlainShellPropertyPtr;
class CompositeShellProperty;
typedef boost::shared_ptr<CompositeShellProperty> CompositeShellPropertyPtr;

class SmBodyMesh;
class SmWingMesh;
class SmRibMesh;

class IgesFile;
struct IgesDirEntry;
class IgesEntity;
class IgesLineEntity;
class IgesCircularArc;
class IgesCompositeCurve;
class IgesPlane;
class IgesPoint;
class IgesRuledSurface;
class IgesRevolutionSurface;
class IgesTrafoMatrix;
class IgesSplineCurve;
class IgesSplineSurface;
class IgesCurveOnSurface;
class IgesTrimmedSurface;
class IgesSubfigure;
class IgesColorDefinition;
class IgesNameProperty;
class IgesSingularSubfigure;

#endif // SURF_FORWARD_H
