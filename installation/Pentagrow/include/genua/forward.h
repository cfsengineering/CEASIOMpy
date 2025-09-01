
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

/** \mainpage libgenua

   # Introduction

   libgenua is a library of basic geometric and numeric support functions. It
   contains classes for the efficient representation of meshes for different
   applications, support for various file formats and wrappers around a number
   of external library interfaces.

   The library components can be grouped into a set of modules, which are
   shortly described below. For more detailed documentation of all classes
   contained therein, see the <a href="modules.xhtml">List of modules.</a>.

   # Numerical Algorithms

   <a href="group__numerics.xhtml">[Link to Module Documentation]</a>

   libgenua provides classes which are meant to serve as building blocks for the
   implementation of more involved numerical methods. Furthermore, interfaces
   between these classes and a number of optional external libraries are
   defined.

   At present, this group defines numerical integration rules, vectors and
   matrices (both stack- and heap-based) for general linear algebra work, and
   support for sparse matrices.

   The SIMD short vectors are meant to aid in vectorization. Please refrain from
   using these objects for linear algebra or geometry as that usually does not
   yield any speedup. Instead, replace scalar operations one-to-one with SIMD
   vectors which support most operations that scalar floating-point variables
   can perform.

   Depending on the configuration selected (or auto-detected on Mac and Linux)
   through the QMake .pro files, interfaces are optionally compiled into
   libgenua. Some interfaces are also defined exclusively through header files,
   so that no additional dependecies arise unless the particular header is
   included.

   Optional interfaces are defined for
   - eeigen (linear algebra) : strongly recommended, liberal OSS license
   - LAPACK (linear algebra) : recommended but not required (fallbacks to eeigen)
   - Intel MKL (sparse direct solver, FFT) : recommended, commercial license
   - SPOOLES (sparse direct solver) : optional sparse solver, open source
   - FFTW3 (FFT) : optional, GPL only
   - ARPACK (large-scale eigenvalues) : optional, for scientific computing

   # Geometry

   <a href="group__geometry.xhtml">[Link to Module Documentation]</a>

   This module defines basic geometric primitives for topology operations,
   such as simple classes which can be used to efficiently compute element and
   node connectivity tables for various types of meshes. Furthermore, a
   collection of basic intersection tests on triangles and lines is implemented.

   A second class of objects is used to implement efficient bounding-volume
   hierarchies such as k-DOP trees in various dimensions. Many of the
   corresponding algorithms and containers have been used for a long time and
   have therefore seen relatively extensive optimization (and therefore allow,
   for example, to create low-overhead representations such as implicit binary
   trees defined by storage order).

   To support visualization applications, containers for typical triangle-only
   meshes (including triangle strips and fans) are available.

   # Mesh handling

   <a href="group__mesh.xhtml">[Link to Module Documentation]</a>

   A large part of libgenua serves to support mesh generation implemented in
   libsurf and sumo. There is a fairly wide range of functionality which serves
   to represent meshes of different types in memory and read/write different
   formats.

   File formats compiled into libgenua include
   - CGNS version 2.5, that is, ADF-based formats, to avoid the HDF5 dependency
   - FFA mesh format (version 1) for the EDGE solver
   - NASTRAN bulk and punch data files
   - Subset of ABAQUS mesh format (some element types only)
   - TetGen surface (.smesh) and volume mesh files
   - SU2 plain text format (.SU2)
   - Ensight 7/gold files
   - Legacy VTK file format
   - Stereolithography (STL) files
   - Reading of AEREL result files

   Optional interfaces are defined for
   - The TAU CFD solver via NetCDF, where detected

    Note that some of the classes in this module are marked as deprecated.

   # Concurrency

   <a href="group__concurrency.xhtml">[Link to Module Documentation]</a>

   Classes to support parallelization.

   This module defines task groups and queues which can be used to implement
   more advanced parallel algorithms which cannot be expressed as simple
   data-parallel loops.

   Some of the contents of this module predate std::thread and are obsolete when
   C++ 2011 is available. They are still compiled into libgenua in order to
   support legacy code which still makes use of these features.

   *Note:* If available, the Thread Building Blocks library does likely provide
   alternatives which are better tested and more flexible than this module.


   # Experimental Features

   Objects which have been implemented in order to investigate possible
   performance improvements. Do not use these components in production code.

   # General utilities

   <a href="group__utility.xhtml">[Link to Module Documentation]</a>

   A collection of simple utilities: Color mapping, specialized hash tables,
   Judy Arrays, aligned allocation, macros.



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

  Some parts of libgenua date back to about 2001 and are no longer used in new
  projects. However, they are still present in order to support legacy software.
  The corresponding classes are marked in the documentation as deprecated.

  */

/** \defgroup numerics Numerical algorithms
 *
 * libgenua provides classes which are meant to serve as building blocks for the
 * implementation of more involved numerical methods. Furthermore, interfaces
 * between these classes and a number of optional external libraries are
 * defined.
 *
 * At present, this group defines numerical integration rules, vectors and
 * matrices (both stack- and heap-based) for general linear algebra work, and
 * support for sparse matrices.
 *
 *
 * The SIMD short vectors are meant to aid in vectorization. Please refrain from
 * using these objects for linear algebra or geometry as that usually does not
 * yield any speedup. Instead, replace scalar operations one-to-one with SIMD
 * vectors which support most operations that scalar floating-point variables
 * can perform.
 *
 * Depending on the configuration selected (or auto-detected on Mac and Linux)
 * through the QMake .pro files, interfaces are optionally compiled into
 * libgenua. Some interfaces are also defined exclusively through header files,
 * so that no additional dependecies arise unless the particular header is
 * included.
 *
 * Optional interfaces are defined for
 * - eeigen (linear algebra) : strongly recommended, liberal OSS license
 * - LAPACK (linear algebra) : recommended but not required (fallbacks to eeigen)
 * - Intel MKL (sparse direct solver, FFT) : recommended, commercial license
 * - SPOOLES (sparse direct solver) : optional sparse solver, open source
 * - FFTW3 (FFT) : optional, GPL only
 * - ARPACK (large-scale eigenvalues) : optional, for scientific computing
 *
 */

/** \defgroup geometry Geometry
 *
 * This module defines basic geometric primitives for topology operations,
 * such as simple classes which can be used to efficiently compute element and
 * node connectivity tables for various types of meshes. Furthermore, a
 * collection of basic intersection tests on triangles and lines is implemented.
 *
 * A second class of objects is used to implement efficient bounding-volume
 * hierarchies such as k-DOP trees in various dimensions. Many of the
 * corresponding algorithms and containers have been used for a long time and
 * have therefore seen relatively extensive optimization (and therefore allow,
 * for example, to create low-overhead representations such as implicit binary
 * trees defined by storage order).
 *
 * To support visualization applications, containers for typical triangle-only
 * meshes (including triangle strips and fans) are available.
 *
 */

/** \defgroup mesh Mesh handling
 *
 * A large part of libgenua serves to support mesh generation implemented in
 * libsurf and sumo. There is a fairly wide range of functionality which serves
 * to represent meshes of different types in memory and read/write different
 * formats.
 *
 * File formats compiled into libgenua include
 * - CGNS version 2.5, that is, ADF-based formats, to avoid the HDF5 dependency
 * - FFA mesh format (version 1) for the EDGE solver
 * - NASTRAN bulk and punch data files
 * - Subset of ABAQUS mesh format (some element types only)
 * - TetGen surface (.smesh) and volume mesh files
 * - SU2 plain text format (.SU2)
 * - Ensight 7/gold files
 * - Legacy VTK file format
 * - Stereolithography (STL) files
 * - Reading of AEREL result files
 *
 * Optional interfaces are defined for
 * - The TAU CFD solver via NetCDF, where detected
 *
 *  Note that some of the classes in this module are marked as deprecated.
 */

/** \defgroup io I/O Support
 *
 *
 *
 */

/** \defgroup concurrency Concurrency
 *
 * Classes to support parallelization.
 *
 * This module defines task groups and queues which can be used to implement
 * more advanced parallel algorithms which cannot be expressed as simple
 * data-parallel loops.
 *
 * Some of the contents of this module predate std::thread and are obsolete when
 * C++ 2011 is available. They are still compiled into libgenua in order to
 * support legacy code which still makes use of these features.
 *
 * \b Note: If available, the Thread Building Blocks library does likely provide
 * alternatives which are better tested and more flexible than this module.
 *
 */

/** \defgroup experimental Experimental
 *
 * Objects which have been implemented in order to investigate possible
 * performance improvements. Do not use these components in production code.
 *
 */

/** \defgroup utility General utilities
 *
 * A collection of simple utilities: Color mapping, specialized hash tables,
 * Judy Arrays, aligned allocation, macros.
 *
 */

#ifndef GENUA_FORWARD_H
#define GENUA_FORWARD_H

// foward declarations for classes in libgenua
// to be included instead of full headers to reduce compile times

#include "defines.h"
#ifndef Q_MOC_RUN
#include <boost/shared_ptr.hpp>
#include <boost/make_shared.hpp>
#endif
#include <vector>
#include <set>

class Atmosphere;

class BasicEdge;
typedef std::set<BasicEdge> BasicEdgeSet;
typedef std::vector<BasicEdge> BasicEdgeArray;

class BasicTriangle;
typedef std::set<BasicTriangle> BasicTriangleSet;
typedef std::vector<BasicTriangle> BasicTriangleArray;

class Plane;
class SplineBasis;
class ConnectMap;

template <typename FloatType>
class TrafoTpl;
typedef TrafoTpl<double> Trafo3d;
typedef TrafoTpl<float> Trafo3f;

class Color;
typedef std::vector<Color> ColorArray;
class CgMesh;
typedef boost::shared_ptr<CgMesh> CgMeshPtr;
typedef std::vector<CgMeshPtr> CgMeshArray;

class CgnsBoco;
class CgnsFile;
class CgnsSection;
class CgnsZone;
class CgnsDescriptor;
class CgnsSol;

class FFANode;
typedef boost::shared_ptr<FFANode> FFANodePtr;
typedef std::vector<FFANodePtr> FFANodeArray;

class MxMesh;
typedef boost::shared_ptr<MxMesh> MxMeshPtr;
class MxMeshSection;
class MxMeshBoco;
class MxMeshField;
class MxElementTree;
class MxMeshSlice;
class MxSolutionTree;
class MxElementFunction;
typedef boost::shared_ptr<MxSolutionTree> MxSolutionTreePtr;
typedef std::vector<MxSolutionTreePtr> MxSolutionTreeArray;

class SurfaceStreamlines;

class TriMesh;
class TriFace;
class TriEdge;
typedef boost::shared_ptr<TriMesh> TriMeshPtr;

class TriSet;

class ImplicitTree;
template <int ND, class FloatType>
class NDPointTree;
class BSearchTree;
class RctSearchTree;

class McOctreeNode;
typedef boost::shared_ptr<McOctreeNode> McOctreeNodePtr;

class SysInfo;
class ConfigParser;
class ThreadPool;
class Logger;

class XmlElement;
class Lz4Stream;
class ZipFile;
class BufferedFile;
class SyncedStreamDevice;

class Hdf5Group;
typedef std::vector<Hdf5Group> Hdf5GroupArray;
class Hdf5File;

class AttributeTree;
typedef boost::shared_ptr<AttributeTree> AttributeTreePtr;
typedef std::vector<AttributeTreePtr> AttributeTreeArray;

class BinFileNode;
typedef boost::shared_ptr<BinFileNode> BinFileNodePtr;
typedef std::vector<BinFileNodePtr> BinFileNodeArray;

class SpinBarrier;
class ThreadGroup;
template <class Item>
class LockedQueue;
template <class TaskType>
class ForkJoinStack;
template <class TaskType>
class ForkJoinQueue;
template <class TaskType, class Context>
class CtxForkJoinQueue;

// template definitions and typedefs for stack-based vector and matrix

template <uint N, class Type = Real>
class SVector;

typedef SVector<2, Real> Vct2;
typedef SVector<3, Real> Vct3;
typedef SVector<4, Real> Vct4;
typedef SVector<6, Real> Vct6;

typedef SVector<2, float> Vct2f;
typedef SVector<3, float> Vct3f;
typedef SVector<4, float> Vct4f;
typedef SVector<6, float> Vct6f;

typedef SVector<2, Complex> CpxVct2;
typedef SVector<3, Complex> CpxVct3;
typedef SVector<4, Complex> CpxVct4;
typedef SVector<6, Complex> CpxVct6;

typedef SVector<2, int> Vct2i;
typedef SVector<3, int> Vct3i;
typedef SVector<4, int> Vct4i;
typedef SVector<6, int> Vct6i;

typedef SVector<2, uint> Vct2u;
typedef SVector<3, uint> Vct3u;
typedef SVector<4, uint> Vct4u;
typedef SVector<6, uint> Vct6u;

template <uint N, uint M, class Type = Real>
class SMatrix;

typedef SMatrix<2, 2, Real> Mtx22;
typedef SMatrix<3, 3, Real> Mtx33;
typedef SMatrix<4, 4, Real> Mtx44;
typedef SMatrix<3, 4, Real> Mtx34;

typedef SMatrix<2, 2, float> Mtx22f;
typedef SMatrix<3, 3, float> Mtx33f;
typedef SMatrix<4, 4, float> Mtx44f;
typedef SMatrix<3, 4, float> Mtx34f;

// templates and typedefs for dynamically allocated vectors and matrices

template <class Type = Real>
class DVector;

typedef DVector<Real> Vector;
typedef DVector<Complex> CpxVector;
typedef std::vector<Vector> VectorArray;
typedef std::vector<CpxVector> CpxVectorArray;

template <class Type = Real>
class DMatrix;

typedef DMatrix<Real> Matrix;
typedef DMatrix<Complex> CpxMatrix;
typedef std::vector<Matrix> MatrixArray;
typedef std::vector<CpxMatrix> CpxMatrixArray;

// n-dimensional arrays, where the number of dimensions is known at compile time

template <int ND, typename Type>
class NDArrayBase;
template <int ND, typename Type>
class NDArrayView;
template <int ND, typename Type>
class NDArray;

// sparse matrices

template <class Type, int N>
class CsrMatrix;
typedef CsrMatrix<double, 1> CsrMatrixD;
typedef CsrMatrix<float, 1> CsrMatrixF;
typedef CsrMatrix<std::complex<double>, 1> CsrMatrixZ;
typedef CsrMatrix<std::complex<float>, 1> CsrMatrixC;

template <typename Type>
class SpMatrixT;
typedef SpMatrixT<Real> SpMatrix;
typedef SpMatrixT<Complex> CpxSpMatrix;

// bounding boxes and friends

class BndRect;
class BndBox;
// template <int N, typename FloatType> class AABBox;
template <class Type, int N>
class DopBase;
template <class Type>
class Dop2d2;
template <class Type>
class Dop3d3;
template <class Type>
class Dop3d4;
template <class Type>
class Dop4d4;
template <class Type>
class Dop3d9;
template <class Type>
class Dop4d16;

// point grids and lists

template <uint N, class Type = Real>
class PointGrid;
template <uint N, class Type = Real>
class PointList;
typedef PointList<2, double> PointList2d;
typedef PointList<3, double> PointList3d;
typedef PointList<4, double> PointList4d;
typedef PointList<6, double> PointList6d;
typedef PointList<2, float> PointList2f;
typedef PointList<3, float> PointList3f;
typedef PointList<4, float> PointList4f;
typedef PointList<6, float> PointList6f;

// sparse solver interfaces

template <class FloatType>
class AbstractLinearSolverTpl;
typedef AbstractLinearSolverTpl<float> SSparseSolver;
typedef AbstractLinearSolverTpl<double> DSparseSolver;
typedef AbstractLinearSolverTpl<std::complex<float>> CSparseSolver;
typedef AbstractLinearSolverTpl<std::complex<double>> ZSparseSolver;
typedef boost::shared_ptr<SSparseSolver> SSparseSolverPtr;
typedef boost::shared_ptr<DSparseSolver> DSparseSolverPtr;
typedef boost::shared_ptr<CSparseSolver> CSparseSolverPtr;
typedef boost::shared_ptr<ZSparseSolver> ZSparseSolverPtr;

// time-integration of differential equation systems

class SecondOrderSystem;
class StdSecondOrderSystem;
class OwrenSimonsen22;
class OwrenSimonsen23;
class OwrenSimonsen34;

// FFT interfaces
class FftBase;
typedef boost::shared_ptr<FftBase> FftBasePtr;

// interface to yaml-cpp
class YamlDoc;
class YamlMap;
class YamlSeq;

namespace YAML
{
  class Node;
}

#endif // GENUA_FORWARD_H
