/* Copyright (C) 2019 David Eller <david@larosterna.com>
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

#ifndef GENUA_UNV58DATASET_H
#define GENUA_UNV58DATASET_H

#include "forward.h"
#include "typecode.h"
#include "dvector.h"

/** Helper class for importing files containing UNV dataset 58.
 *
 * \ingroup io
 *
 */
class Unv58Dataset
{
public:

  enum PhysQuantity { Unknown = 0,
                      General,
                      Stress,
                      Strain,
                      Temperature,
                      HeatFlux,
                      Displacement,
                      ReactionForce,
                      Velocity,
                      Acceleration,
                      ExcitationForce,
                      Pressure,
                      Mass,
                      Time,
                      Frequency,
                      RPM,
                      Order,
                      SoundPressure,
                      SoundIntensity,
                      SoundPower,
                      NQuantity};

  enum FieldFunction { GeneralOrUnknown = 0,
                       TimeResponse,
                       AutoSpectrum,
                       CrossSpectrum,
                       FRF,
                       Transmissibility,
                       Coherence,
                       AutoCorrelation,
                       CrossCorrelation,
                       PowerSpectralDensity,
                       EnergySpectralDensity,
                       ProbabilityDensityFunction,
                       Spectrum,
                       CumulativeFrequencyDistribution,
                       PeaksValley,
                       StressCycles,
                       StrainCycles,
                       Orbit,
                       ModeIndicatorFunction,
                       ForcePattern,
                       PartialPower,
                       PartialCoherence,
                       Eigenvalue,
                       Eigenvector,
                       ShockResponseSpectrum,
                       FiniteImpulseResponseFilter,
                       MultipleCoherence,
                       OrderFunction,
                       NFunction };


  /// import a single 58 or 58b dataset from binary (!) stream
  bool read(std::istream &in);

  /// append as a dataset to group in HDF5 file
  bool appendTo(const std::string &id, Hdf5Group &grp) const;

  /// construct a tag from response node and direction
  std::string tag() const;

  /// utility: put all datasets in a file into an HDF5 file
  static void convertFile(const std::string &fname);

protected:

  /// dataset label
  std::string m_label;

  /// date created
  std::string m_date;

  /// unit for x-axis
  std::string m_xunit;

  /// unit for y-axis
  std::string m_yunit;

  /// response part/entity
  std::string m_respEntity;

  /// reference part/entity
  std::string m_refEntity;

  /// quantity for abscissa
  int m_absQuantity = 0;

  /// quantity code
  int m_ordQuantity = 0;

  /// function recorded
  int m_functionType = 0;

  /// node at which response is measured
  int m_respNode = 0;

  /// direction of response
  int m_respDirection = 0;

  /// reference node
  int m_refNode = 0;

  /// reference direction
  int m_refDirection = 0;

  /// ordinate payload data type
  TypeCode m_ordinateType;

  /// number of values stored
  size_t m_nvalues = 0;

  /// abscissa values
  DVector<float> m_abscissa;

  /// ordinate values, real part
  DVector<float> m_ordinateReal;

  /// ordinate values, imaginary part
  DVector<float> m_ordinateImag;

  /// quantity names
  const static char *s_quantity_names[NQuantity];

  /// function names
  const static char *s_function_names[NFunction];
};

#endif // UNV58DATASET_H
