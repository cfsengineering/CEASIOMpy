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

#include "unv58dataset.h"
#include "algo.h"
#include "hdf5file.h"
#include "strutils.h"
#include <iostream>
#include <fstream>
#include <sstream>

using namespace std;

const char *Unv58Dataset::s_quantity_names[] = {
                        "Unknown",
                        "General",
                        "Stress",
                        "Strain",
                        "Temperature",
                        "HeatFlux",
                        "Displacement",
                        "ReactionForce",
                        "Velocity",
                        "Acceleration",
                        "ExcitationForce",
                        "Pressure",
                        "Mass",
                        "Time",
                        "Frequency",
                        "RPM",
                        "Order",
                        "SoundPressure",
                        "SoundIntensity",
                        "SoundPower"};

const char *Unv58Dataset::s_function_names[] = {
           "GeneralOrUnknown",
           "TimeResponse",
           "AutoSpectrum",
           "CrossSpectrum",
           "FRF",
           "Transmissibility",
           "Coherence",
           "AutoCorrelation",
           "CrossCorrelation",
           "PowerSpectralDensity",
           "EnergySpectralDensity",
           "ProbabilityDensityFunction",
           "Spectrum",
           "CumulativeFrequencyDistribution",
           "PeaksValley",
           "StressCycles",
           "StrainCycles",
           "Orbit",
           "ModeIndicatorFunction",
           "ForcePattern",
           "PartialPower",
           "PartialCoherence",
           "Eigenvalue",
           "Eigenvector",
           "ShockResponseSpectrum",
           "FiniteImpulseResponseFilter",
           "MultipleCoherence",
           "OrderFunction"};

bool Unv58Dataset::read(std::istream &in)
{
  int byteOrder(0), fpFormat(0), nlines(0), nbytes(0);
  bool blockFound(false), is58b(false);

  string line, word;
  int nskip = 0;
  while (getline(in, line)) {

    // skip forward until header line found
    blockFound = (line.find("    58") == 0);
    if (blockFound)
      break;

    ++nskip;
  }

  if (not blockFound)
    return false;

  // interpret header
  {
    is58b = (line.find("    58b") != string::npos);
    stringstream ss(line.substr(8, string::npos));
    ss >> byteOrder >> fpFormat >> nlines >> nbytes;
    //clog << "byteOrder: " << byteOrder << " fp: " << fpFormat
    //     << " lines: " << nlines << " bytes: " << nbytes << endl;
  }

  bool endianConvert = (is_bigendian() != (byteOrder == 2));
  // clog << "Endianness conversion: " << endianConvert << endl;
  if (fpFormat != 2)
    return false;

  if (nlines != 11)
    return false;

  getline(in, m_label);
  m_label = strip(m_label);
  getline(in, line);
  getline(in, m_date);
  m_date = strip(m_date);
  getline(in, line);
  getline(in, line);

  // function type etc
  getline(in, line);
  {
    stringstream ss(line);
    int a, b, c;
    ss >> m_functionType >> a >> b >> c
       >> m_respEntity >> m_respNode >> m_respDirection
       >> m_refEntity >> m_refNode >> m_refDirection;
  }

  // number format and x-axis
  getline(in, line);
  int fpType(0), nval(0), xregular(0);
  double xbegin(0), xincr(0);
  {
    stringstream ss(line);
    ss >> fpType >> nval >> xregular >> xbegin >> xincr;
    //clog << "fpType: " << fpType << " nval: " << nval << " xreg: " << xregular
    //     << " xbegin: " << xbegin << " xincr: " << xincr << endl;
  }

  if (fpType == 2)
    m_ordinateType = TypeCode(TypeCode::Float32);
  else if (fpType == 4)
    m_ordinateType = TypeCode(TypeCode::Float64);
  else if (fpType == 5)
    m_ordinateType = TypeCode(TypeCode::Complex64);
  else if (fpType == 6)
    m_ordinateType = TypeCode(TypeCode::Complex128);
  else
    return false;

  // clog << "Stored typecode: " << m_ordinateType.value() << endl;

  m_nvalues = nval;
  m_abscissa.resize(nval);
  if (xregular == 1) {
    for (size_t i=0; i<m_nvalues; ++i)
      m_abscissa[i] = xbegin + double(i)*xincr;
  }

  // value and unit for x-axis
  getline(in, line);
  {
    int a, b, c;
    stringstream ss(line);
    ss >> m_absQuantity >> a >> b >> c >> word >> m_xunit;
  }

  // value and unit for y-axis
  getline(in, line);
  {
    int a, b, c;
    stringstream ss(line);
    ss >> m_ordQuantity >> a >> b >> c >> word >> m_yunit;
  }

  // ignore: z-axis
  getline(in, line);
  getline(in, line);

  // load binary data
  if (is58b) {

    std::vector<char> raw(nbytes);
    std::fill(raw.begin(), raw.end(), 0);
    in.read(&raw[0], nbytes);

    if (endianConvert) {
      if (m_ordinateType.value() == TypeCode::Float32)
        swap_bytes<4>(nbytes, &raw[0]);
      else if (m_ordinateType.value() == TypeCode::Float64)
        swap_bytes<8>(nbytes, &raw[0]);
      else if (m_ordinateType.value() == TypeCode::Complex64)
        swap_bytes<4>(nbytes, &raw[0]);
      else if (m_ordinateType.value() == TypeCode::Complex128)
        swap_bytes<8>(nbytes, &raw[0]);
    }

    m_ordinateReal.resize(m_nvalues);

    // convert
    if (m_ordinateType.value() == TypeCode::Float32) {
      TypeCode::copy<float,float>(&raw[0], m_nvalues, m_ordinateReal.pointer());
    } else if (m_ordinateType.value() == TypeCode::Float64) {
      TypeCode::copy<double,float>(&raw[0], m_nvalues, m_ordinateReal.pointer());
    } else if (m_ordinateType.value() == TypeCode::Complex64) {
      m_ordinateImag.resize(m_nvalues);
      for (size_t i=0; i<m_nvalues; ++i) {
        m_ordinateReal[i] = TypeCode::recast<float,float>(&raw[0], 2*i+0);
        m_ordinateImag[i] = TypeCode::recast<float,float>(&raw[0], 2*i+1);
      }
    } else if (m_ordinateType.value() == TypeCode::Complex128) {
      m_ordinateImag.resize(m_nvalues);
      for (size_t i=0; i<m_nvalues; ++i) {
        m_ordinateReal[i] = TypeCode::recast<double,float>(&raw[0], 2*i+0);
        m_ordinateImag[i] = TypeCode::recast<double,float>(&raw[0], 2*i+1);
      }
    }
  } else {
    return false;
  }

  return true;
}

bool Unv58Dataset::appendTo(const std::string &id, Hdf5Group &grp) const
{
  bool stat = true;
  Hdf5Group subg = grp.createGroup(id);
  stat &= subg.attach("label", m_label);
  stat &= subg.attach("date", m_date);
  stat &= subg.attach("xunit", m_xunit);
  stat &= subg.attach("xquantity", s_quantity_names[m_absQuantity]);
  stat &= subg.attach("yunit", m_yunit);
  stat &= subg.attach("yquantity", s_quantity_names[m_ordQuantity]);
  stat &= subg.attach("function", s_function_names[m_functionType]);
  stat &= subg.attach("responseEntity", m_respEntity);
  stat &= subg.attach("responseNode", m_respNode);
  stat &= subg.attach("responseDirection", m_respDirection);
  stat &= subg.attach("referenceEntity", m_refEntity);
  stat &= subg.attach("referenceNode", m_refNode);
  stat &= subg.attach("referenceDirection", m_refDirection);
  if (!stat) {
    clog << "Attribute attachment failed." << endl;
    return false;
  }

  Hdf5Dataset dsx = subg.createDataset("x", TypeCode::of<float>(),
                                       m_abscissa.size(), 1, 1);
  stat = dsx.write(m_abscissa.pointer());
  if (!stat) {
    clog << "x write failed." << endl;
    return false;
  }

  if (m_ordinateType.isComplex()) {
    Hdf5Dataset dsr = subg.createDataset("yr", TypeCode::of<float>(),
                                         m_nvalues, 1, 1);
    stat = dsr.write(m_ordinateReal.pointer());
    if (!stat) {
      clog << "yr write failed." << endl;
      return false;
    }

    Hdf5Dataset dsi = subg.createDataset("yi", TypeCode::of<float>(),
                                         m_nvalues, 1, 1);
    stat = dsi.write(m_ordinateImag.pointer());
    if (!stat) {
      clog << "yi write failed." << endl;
      return false;
    }

  } else {
    Hdf5Dataset ds = subg.createDataset("y", TypeCode::of<float>(),
                                        m_nvalues, 1, 1);
    stat = ds.write(m_ordinateReal.pointer());
    if (!stat) {
      clog << "y write failed." << endl;
      return false;
    }
  }

  return true;
}

string Unv58Dataset::tag() const
{
  string t = "N" + str(m_respNode);
  if (m_respDirection == 1)
    t += "pX";
  else if (m_respDirection == -1)
    t += "mX";
  else if (m_respDirection == 2)
    t += "pY";
  else if (m_respDirection == -2)
    t += "mY";
  else if (m_respDirection == 3)
    t += "pZ";
  else if (m_respDirection == -3)
    t += "mZ";
  return t;
}

void Unv58Dataset::convertFile(const string &fname)
{
  Hdf5File h5f;
  h5f.create( append_suffix(fname, ".h5") );

  int dsi = 1;
  ifstream in(fname, ios::binary | ios::in);
  while (in) {
    Unv58Dataset ds;
    bool stat = ds.read(in);
    if (stat) {
      clog << "Found dataset: " << ds.tag() << endl;
      stat = ds.appendTo("d" + str(dsi++), h5f);
      if (not stat)
        return;
    }
  }
}
