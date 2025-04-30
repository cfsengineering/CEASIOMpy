
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
 
#ifndef MXELEMENTFUNCTION_H
#define MXELEMENTFUNCTION_H

#include "forward.h"

/** A real-valued function taking element vertex indices as argument.
 *
 * MxElementFunction is used to generate quality statistics in mesh generation.
 * Each child class implements a particular element quality criterion which
 * somehow can be expressed as a floating-point number. The criterion classes
 * must implement the eval() member function; the parent class then computes
 * suitable statistics.
 *
 * \ingroup mesh
 * \sa MxMesh
 */
class MxElementFunction
{
public:

  /// create with pointer to parent mesh
  MxElementFunction(const MxMesh *pm = 0) : m_pmsh(pm) {}

  /// base class
  virtual ~MxElementFunction();

  /** Evaluate a criterion for all elements in mesh section.
   *
   * If applicable, compute the quality criterion fro all elements in section
   * isec, put the values into val, and return true. Return false if the
   * criterion cannot be computed for elements of the type stored in isec.
   */
  virtual bool eval(uint isec, Vector &val) const = 0;

  /// collect global element indices for which value is in a prescribed range
  virtual size_t inRange(Real minValue, Real maxValue, Indices &elx) const;

  /// collect global element indices above threshold
  virtual size_t elementsAbove(Real threshold, Indices &elx) const;

  /// collect global element indices below threshold
  virtual size_t elementsBelow(Real threshold, Indices &elx) const;

  /// bin element values, return number of elements processed
  virtual size_t histogram(const Vector &thresholds, Indices &bins) const;

protected:

  /// mesh to evaluate
  const MxMesh *m_pmsh;
};

/** Function to test for tangled elements.
  *
  * This criterion is fundamentally binary; it returns the value -1 for
  * tangled (self-intersecting or inverted) elements and +1 for regular ones.
  *
  *
  * \ingroup mesh
  * \sa MxElementFunction
  */
class MxTangledElement : public MxElementFunction
{
public:

  /// create functor
  MxTangledElement(const MxMesh *pm) : MxElementFunction(pm) {}

  /// compute whether elements in section are tangled or not
  bool eval(uint isec, Vector &val) const;
};

/** Function to compute minimum dihedral angle for tetrahedral elements.
  *
  * \ingroup mesh
  * \sa MxElementFunction
  */
class MxMinDihedralAngle : public MxElementFunction
{
public:

  /// create functor
  MxMinDihedralAngle(const MxMesh *pm) : MxElementFunction(pm) {}

  /// compute minimum dihedral angle for tetrahedra sections only
  bool eval(uint isec, Vector &val) const;
};

/** Function to compute maxmimum dihedral angle for tetrahedral elements.
  *
  * \ingroup mesh
  * \sa MxElementFunction
  */
class MxMaxDihedralAngle : public MxElementFunction
{
public:

  /// create functor
  MxMaxDihedralAngle(const MxMesh *pm) : MxElementFunction(pm) {}

  /// compute maximum dihedral angle for tetrahedra sections only
  bool eval(uint isec, Vector &val) const;
};

/** Function to compute maxmimum skew angle for ideally parallel-sided elements.
  *
  * \ingroup mesh
  * \sa MxElementFunction
  */
class MxMaxSkewAngle : public MxElementFunction
{
public:

  /// create functor
  MxMaxSkewAngle(const MxMesh *pm) : MxElementFunction(pm) {}

  /// compute maximum skew angle
  bool eval(uint isec, Vector &val) const;
};

#endif // MXELEMENTFUNCTION_H
