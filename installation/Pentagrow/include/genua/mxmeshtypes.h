
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
 
#ifndef GENUA_MXMESHTYPES_H
#define GENUA_MXMESHTYPES_H

#include <string>
#include "cgnsfwd.h"

namespace Mx
{

enum FileFormat { NativeFormat, ZippedXmlFormat, TextXmlFormat, GbfFormat,
                  StdCgnsFormat, SecCgnsFormat, FfaFormat, LegacyVtkFormat,
                  AbaqusFormat, NastranBulkFormat, Su2Format, TauFormat,
                  StlTextFormat, StlBinaryFormat,
                  PlyTextFormat, PlyBinaryFormat};

enum ElementType { Undefined = 0, Point = 1, Line2 = 2, Line3 = 3,
               Tri3 = 4, Tri6 = 5, Quad4 = 6, Quad8 = 7, Quad9 = 8,
               Tet4 = 9, Tet10 = 10, Pyra5 = 11, Pyra14 = 12,
               Hex8 = 13, Hex20 = 14, Hex27 = 15,
               Penta6 = 16, Penta15 = 17, Penta18 = 18,
               NElmTypes };

inline std::string str(Mx::ElementType t)
{
  switch (t) {
  case Mx::Undefined:
    return std::string("Undefined");
  case Mx::Point:
    return std::string("Point");
  case Mx::Line2:
    return std::string("Line2");
  case Mx::Line3:
    return std::string("Line3");
  case Mx::Tri3:
    return std::string("Triangle3");
  case Mx::Tri6:
    return std::string("Triangle6");
  case Mx::Quad4:
    return std::string("Quad4");
  case Mx::Quad8:
    return std::string("Quad8");
  case Mx::Quad9:
    return std::string("Quad9");
  case Mx::Tet4:
    return std::string("Tetra4");
  case Mx::Tet10:
    return std::string("Tetra10");
  case Mx::Pyra5:
    return std::string("Pyramid5");
  case Mx::Pyra14:
    return std::string("Pyramid14");
  case Mx::Hex8:
    return std::string("Hexa8");
  case Mx::Hex20:
    return std::string("Hexa20");
  case Mx::Hex27:
    return std::string("Hexa27");
  case Mx::Penta6:
    return std::string("Penta6");
  case Mx::Penta15:
    return std::string("Penta15");
  case Mx::Penta18:
    return std::string("Penta18");
  case Mx::NElmTypes:
    return std::string("Undefined");
  };
  return std::string("Undefined");
}

// element type for FFA-format files
inline std::string ffastr(Mx::ElementType t)
{
  switch (t) {
  case Mx::Undefined:
  case Mx::Point:
    return std::string("undefined");
  case Mx::Line2:
    return std::string("bar2");
  case Mx::Line3:
    return std::string("bar3");
  case Mx::Tri3:
    return std::string("tria3");
  case Mx::Tri6:
    return std::string("tria6");
  case Mx::Quad4:
    return std::string("quad4");
  case Mx::Quad8:
    return std::string("quad8");
  case Mx::Quad9:
    return std::string("quad9");
  case Mx::Tet4:
    return std::string("tetra4");
  case Mx::Tet10:
    return std::string("tetra10");
  case Mx::Pyra5:
    return std::string("penta5");  // 5-node pentahedron is a pyramid
  case Mx::Pyra14:
    return std::string("pyramid14");
  case Mx::Hex8:
    return std::string("hexa8");
  case Mx::Hex20:
    return std::string("hexa20");
  case Mx::Hex27:
    return std::string("hexa27");
  case Mx::Penta6:
    return std::string("penta6");
  case Mx::Penta15:
    return std::string("penta15");
  case Mx::Penta18:
    return std::string("penta18");
  case Mx::NElmTypes:
    return std::string("undefined");
  };
  return std::string("undefined");
}

enum EnsightFlags { OffId = 1,
                    AssignId = 2,
                    GivenId = 3,
                    IgnoreId = 4 };

// element type string for ensight format
inline std::string ensightstr(Mx::ElementType t)
{
  switch (t) {
  case Mx::Undefined:
  case Mx::Point:
    return std::string("point");
  case Mx::Line2:
    return std::string("bar2");
  case Mx::Line3:
    return std::string("bar3");
  case Mx::Tri3:
    return std::string("tria3");
  case Mx::Tri6:
    return std::string("tria6");
  case Mx::Quad4:
    return std::string("quad4");
  case Mx::Quad8:
    return std::string("quad8");
  case Mx::Quad9:
    return std::string("undefined");
  case Mx::Tet4:
    return std::string("tetra4");
  case Mx::Tet10:
    return std::string("tetra10");
  case Mx::Pyra5:
    return std::string("pyramid5");
  case Mx::Pyra14:
    return std::string("undefined");
  case Mx::Hex8:
    return std::string("hexa8");
  case Mx::Hex20:
    return std::string("hexa20");
  case Mx::Hex27:
    return std::string("undefined");
  case Mx::Penta6:
    return std::string("penta6");
  case Mx::Penta15:
    return std::string("penta15");
  case Mx::Penta18:
    return std::string("undefined");
  case Mx::NElmTypes:
    return std::string("undefined");
  };
  return std::string("undefined");
}

inline Mx::ElementType decodeEnsightStr(const std::string &s)
{
  if (s == "point")
    return Mx::Point;
  else if (s == "bar2")
    return Mx::Line2;
  else if (s == "bar3")
    return Mx::Line3;
  else if (s == "tria3")
    return Mx::Tri3;
  else if (s == "tria6")
    return Mx::Tri6;
  else if (s == "quad4")
    return Mx::Quad4;
  else if (s == "quad8")
    return Mx::Quad8;
  else if (s == "tetra4")
    return Mx::Tet4;
  else if (s == "tetra10")
    return Mx::Tet10;
  else if (s == "hexa8")
    return Mx::Hex8;
  else if (s == "hexa20")
    return Mx::Hex20;
  else if (s == "penta6")
    return Mx::Penta6;
  else if (s == "penta15")
    return Mx::Penta15;
  else if (s == "pyramid5")
    return Mx::Pyra5;
  else
    return Mx::Undefined;
}

inline Mx::ElementType decodeElementType(const std::string & s)
{
  const int ntypes = (int) Mx::NElmTypes;
  for (int i=0; i<ntypes; ++i) {
    Mx::ElementType t = (Mx::ElementType) i;
    if (s == str(t))
      return t;
  }

  // catch special case : some meshes use 'pyramid5'
  if (s == "pyramid5")
    return Mx::Pyra5;

  int num = strtol(s.c_str(), 0, 10);
  if (num < Mx::NElmTypes)
    return (Mx::ElementType) num;

  return Mx::Undefined;
}

inline Mx::ElementType decodeFfaElementType(const std::string & s)
{
  const int ntypes = (int) Mx::NElmTypes;
  for (int i=0; i<ntypes; ++i) {
    Mx::ElementType t = (Mx::ElementType) i;
    if (s == ffastr(t))
      return t;
  }

  int num = strtol(s.c_str(), 0, 10);
  if (num < Mx::NElmTypes)
    return (Mx::ElementType) num;

  return Mx::Undefined;
}

enum BocoType { BcUndefined = 0, BcUserDefined = 1, BcExtrapolate = 2, BcDirichlet = 3,
               BcFarfield = 4, BcNeumann = 5, BcGeneral = 6, BcInflow = 7, BcOutflow = 8,
               BcSymmetryPlane = 9, BcWall = 10, BcWakeSurface = 11,
               BcMassflowIn = 12, BcMassflowOut = 13, BcAdiabaticWall = 14,
               BcSlipWall = 15, BcElementSet = 16, BcNodeSet = 17, BcNTypes };

inline std::string str(Mx::BocoType t)
{
  switch (t) {
  case BcUndefined:
    return std::string("Undefined");
  case BcUserDefined:
    return std::string("UserDefined");
  case BcExtrapolate:
    return std::string("Extrapolate");
  case BcDirichlet:
    return std::string("Dirichlet");
  case BcFarfield:
    return std::string("Farfield");
  case BcNeumann:
    return std::string("Neumann");
  case BcGeneral:
    return std::string("General");
  case BcInflow:
    return std::string("Inflow");
  case BcOutflow:
    return std::string("Outflow");
  case BcSymmetryPlane:
    return std::string("SymmetryPlane");
  case BcWall:
    return std::string("Wall");
  case BcWakeSurface:
    return std::string("WakeSurface");
  case BcMassflowIn:
    return std::string("MassflowInlet");
  case BcMassflowOut:
    return std::string("MassflowOutlet");
  case BcAdiabaticWall:
    return std::string("AdiabaticWall");
  case BcSlipWall:
    return std::string("SlipWall");
  case BcElementSet:
    return std::string("ElementSet");
  case BcNodeSet:
    return std::string("NodeSet");
  case BcNTypes:
    return std::string("Undefined");
  };
  return std::string("Undefined");
}

inline Mx::BocoType decodeBocoType(const std::string & s)
{
  const int ntypes = (int) BcNTypes;
  for (int i=0; i<ntypes; ++i) {
    Mx::BocoType t = (Mx::BocoType) i;
    if (s == str(t))
      return t;
  }

  int num = strtol(s.c_str(), 0, 10);
  if (num < BcNTypes)
    return (Mx::BocoType) num;

  return BcUndefined;
}

const uint vtkCellMap[] = {0, 1, 3, 21, 5, 22, 9, 23, 0, 10, 24,
                           14, 0, 12, 25, 0, 13, 0, 0};

inline int elementType2Vtk(int mxt)
{
  const int nvtmax = sizeof(Mx::vtkCellMap) / sizeof(uint);
  return (mxt <= nvtmax) ? Mx::vtkCellMap[mxt] : 0;
}

inline Mx::ElementType vtk2ElementType(uint code)
{
  const int nvtmax = sizeof(Mx::vtkCellMap) / sizeof(uint);
  for (int i=0; i<nvtmax; ++i)
    if (code == Mx::vtkCellMap[i])
      return Mx::ElementType(i);
  return Mx::Undefined;
}

} // namespace Mx


inline cgns::ElementType_t MxElementType2Cgns(Mx::ElementType t)
{
  const cgns::ElementType_t etypeMap[] = { cgns::ElementTypeNull, // Mx::Undefined
                                           cgns::NODE, // Mx::Point
                                           cgns::BAR_2, // Mx::Line2
                                           cgns::BAR_3, // Mx::Line3
                                           cgns::TRI_3, // Mx::Tri3
                                           cgns::TRI_6, // Mx::Tri6
                                           cgns::QUAD_4, // Mx::Quad4
                                           cgns::QUAD_8, // Mx::Quad8
                                           cgns::QUAD_9, // Mx::Quad9
                                           cgns::TETRA_4, // Mx::Tet4
                                           cgns::TETRA_10, // Mx::Tet10
                                           cgns::PYRA_5, // Mx::Pyra5
                                           cgns::PYRA_14, // Mx::Pyra14
                                           cgns::HEXA_8, // Mx::Hex8
                                           cgns::HEXA_20, // Mx::Hex20
                                           cgns::HEXA_27, // Mx::Hex27
                                           cgns::PENTA_6, // Mx::Penta6
                                           cgns::PENTA_15, // Mx::Penta15
                                           cgns::PENTA_18, // Mx::Penta18
                                           cgns::ElementTypeNull // Mx::NElmTypes
                                         };
  
  const int nct = sizeof(etypeMap) / sizeof(cgns::ElementType_t);
  int i = (int) t;
  if (i < nct)
    return etypeMap[i];
  else
    return cgns::ElementTypeNull;
}

inline Mx::ElementType cgns2MxElementType(cgns::ElementType_t t)
{
  const int nmx = (int) Mx::NElmTypes;
  for (int i=0; i<nmx; ++i) {
    Mx::ElementType mxt = (Mx::ElementType) i;
    if (MxElementType2Cgns(mxt) == t)
      return mxt;
  }
  return Mx::Undefined;
}

inline cgns::BCType_t MxBocoType2Cgns(Mx::BocoType t)
{
  const cgns::BCType_t bctypeMap[] = { cgns::BCTypeNull, // BcUndefined
                                       cgns::BCTypeUserDefined, // BcUserDefined
                                       cgns::BCExtrapolate, // BcExtrapolate
                                       cgns::BCDirichlet, // BcDirichlet
                                       cgns::BCFarfield, // BcFarfield
                                       cgns::BCNeumann, // BcNeumann
                                       cgns::BCGeneral, // BcGeneral
                                       cgns::BCInflow, // BcInflow
                                       cgns::BCOutflow, // BcOutflow
                                       cgns::BCSymmetryPlane, // BcSymmetryPlane
                                       cgns::BCWall,  // BcWall
                                       cgns::BCTypeUserDefined, // BcWake
                                       cgns::BCInflow, // BcMassflowIn
                                       cgns::BCOutflow, // BcMassflowOut
                                       cgns::BCWallViscous, // BcAdiabaticWall
                                       cgns::BCWallInviscid, // BcSlipWall
                                       cgns::BCTypeUserDefined, // BcElementSet
                                       cgns::BCTypeUserDefined, // BcNodeSet
                                       cgns::BCTypeNull }; // BcNTypes

  const int nct = sizeof(bctypeMap) / sizeof(cgns::BCType_t);
  int i = (int) t;
  if (i < nct)
    return bctypeMap[i];
  else
    return cgns::BCTypeNull;
}

inline Mx::BocoType cgns2MxBocoType(cgns::BCType_t t)
{
  const int nmx = (int) Mx::BcNTypes;
  for (int i=0; i<nmx; ++i) {
    Mx::BocoType mxt = (Mx::BocoType) i;
    if (MxBocoType2Cgns(mxt) == t)
      return mxt;
  }
  return Mx::BcUndefined;
}

#endif
