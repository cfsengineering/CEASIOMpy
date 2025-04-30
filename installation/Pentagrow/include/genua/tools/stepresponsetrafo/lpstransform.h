#ifndef LPSTRANSFORM_H
#define LPSTRANSFORM_H

#include <genua/forward.h>
#include <genua/dmatrix.h>
#include <genua/trigo.h>
#include <genua/point.h>
#include <genua/steptransform.h>

/** Import step-response results and transform to Laplace domain.
 *
 *
 *
 */
class ModalStepImporter : public StepTransform
{
public:

  /// sets default parameters to prevent crash on meaningless input
  ModalStepImporter() : m_mach(0.5), m_vref(170.), m_density(1.225),
    m_refchord(1.0), m_amplitude(1.0), m_poo(101325.0),
    m_nlength(4.0), m_maxrelfreq(0.9), m_dredfreq(0.05),
    m_df(0), m_modeid(0) {}

  /// read parameters which are independent of excitation mode and not in files
  void configure(const ConfigParser &cfg);

  /// load parameters for one simulation run from .brom file (rom_parameters)
  void loadRomParameter(FFANodePtr pfile);

  /// read time-domain sequence file in FFA format (sampling_history)
  void loadSampling(FFANodePtr pfile,
                    const std::string &fieldName = "pressure");

  /// select frequencies to use and run transformation
  void transform();

  /// append result fields to mesh, call for each mode excitation
  void appendFields(MxMesh &mx);

  /// finalize: create solution groups, call once in the end
  void groupFields(MxMesh &mx) const;

protected:

  /// normalize pressure values to cp
  void normalize();

  /// import boundary nodes from FFA data
  size_t fetchNodeCoordinates(FFANodePtr pnode);

  /// compute reduced frequency
  Real reduce(Complex s) const {
    return 0.5 * m_refchord * s.imag() / m_vref;
  }

  /// assemble field name suffix for s
  std::string cpFieldName(Complex s) const;

private:

  /// dimensions of boundary regions (number of points)
  Indices m_bndsize;

  /// fields added for each call to trafo (accumulates)
  std::vector<Indices> m_dcpFields;

  /// boundary node coordinates (sampling .bout)
  PointList<3,float> m_bndpts;

  /// boundary names (sampling .bout)
  StringArray m_bndnames;

  /// stored initial cp at t = 0
  Vector m_cpo;

  /// output requested at these reduced frequencies
  Vector m_krequested;

  /// scalar variable extracted from sampling file
  std::string m_xfield;

  /// case parameters from .brom output file  (.brom)
  Real m_mach, m_vref, m_density, m_refchord, m_amplitude;

  /// static pressure for normalization to cp (.cfg)
  Real m_poo;

  /// duration of entire simulation in terms of step duration (.amot)
  Real m_nlength;

  /// limit value, highest frequency considered as function of 1/tramp (.cfg)
  Real m_maxrelfreq;

  /// frequency step for output
  Real m_dredfreq, m_df;

  /// excitation mode identifier from .brom file
  int m_modeid;
};

#endif // LPSTRANSFORM_H
