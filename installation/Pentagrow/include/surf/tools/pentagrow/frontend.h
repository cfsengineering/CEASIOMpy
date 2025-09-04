#ifndef FRONTEND_H
#define FRONTEND_H

#include <surf/pentagrow.h>
#include <genua/configparser.h>

/** User interface for PentaGrow.
 *
 */
class FrontEnd
{
public:
  enum FileFormat
  {
    UnknownFormat = 0,
    MSH = 1,
    STL = 2,
    CGNS = 4,
    EDGE = 8,
    ZML = 16,
    SU2 = 32,
    TAU = 64
  };
  enum ProgPhase
  {
    FirstPass = 1,
    SecondPass = 2,
    TwoPass = 3
  };

  /// read configuration
  FrontEnd(int argc, char *argv[]);

  /// run first, second, or both passes
  void run(const std::string &fname);

  /// generate boundaries only
  void generateBoundaries(const std::string &fname);

  /// first tetgen call to generate first-pass (background) mesh
  void firstTetgenPass();

  /// create edge length field and write files for second tetgen pass
  int generateMetric(int iter = 1);

  /// second tetgen pass to refine mesh accordining to edge-length crit
  void secondTetgenPass(int iter = 1);

  /// read final tetgen output and generate pentahedra
  void generateLayer(int iter = 2);

  /// write output to requested formats
  void writeFinal();

  /// access core object
  PentaGrow &meshGenerator() { return m_pg; }

private:
  /// configuration
  ConfigParser m_cfg;

  /// hybrid mesh generator
  PentaGrow m_pg;

  /// default options for first tetgen pass
  std::string m_tgoDefault;

  /// whether a refinement pass is configured
  bool m_refinementPass;
};

#endif // FRONTEND_H
