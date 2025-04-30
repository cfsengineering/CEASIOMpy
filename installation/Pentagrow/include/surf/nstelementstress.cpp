
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
 
#include "nstelementstress.h"
#include <genua/dbprint.h>
#include <boost/regex.hpp>

using namespace std;

void NstElementStressRecord::compile(uint icode)
{
  setup(icode);

  // regular expression to extract deformation data
  static const string rxint("([0-9]+)");
  static const string rxfloat("([+-]?([0-9]*\\.?[0-9]+|[0-9]+\\.?[0-9]*)"
                              "([eE][+-]?[0-9]+)?)");

  // blank, int, int, float, float
  static const string biiff = "\\s*" + rxint + "\\s*" + rxint + "\\s*"
      + rxfloat + "\\s*" + rxfloat + ".*";

  // blank, int, float, float, float
  static const string bifff = "\\s*" + rxint + "\\s*" + rxfloat + "\\s*"
      + rxfloat + "\\s*" + rxfloat + ".*";

  // -CONT-, int, float, float
  static const string ciff = "\\s*-CONT-\\s*"
      + rxint + "\\s*" + rxfloat + "\\s*" + rxfloat + ".*";

  // -CONT-, float, float, float
  static const string cfff = "\\s*-CONT-\\s*"
      + rxfloat + "\\s*" + rxfloat + "\\s*" + rxfloat + ".*";

  // -CONT-, float, anything
  static const string cf = "\\s*-CONT-\\s*" + rxfloat + ".*";

  if ( isCompositeShell(itemCode) ) {

    // CQUAD4/R, CTRIA3/R composite

    // pattern for the first line
    // EID  PLY  float float
    pattern[0] = boost::regex(biiff);

    // pattern for the second/third line
    pattern[1] = pattern[2] = boost::regex(cfff);

    // pattern for the second/third line
    pattern[3] = boost::regex(cf);

  } else if ( isLinearShell(itemCode) ) {

    // CQUAD4/R, CTRIA3/R linear isotropic

    // pattern for the first line
    // EID  float  float float
    pattern[0] = boost::regex(bifff);

    // pattern for the intermediate lines
    for (int i=1; i<5; ++i)
      pattern[i] = boost::regex(cfff);

    // pattern for the last line
    pattern[5] = boost::regex(cf);

  } else if ( isSolid(itemCode) ) {

    // CHEXA linear
    // read only center-point values, visualization can't handle anything else
    // yet because that requires element-specific shaders

    //   2                 0        GRID                       8          225573
    const string l0("\\s*"+rxint+"\\s*"+rxint+"\\s*GRID\\s*"+rxint+".*");
    pattern[0] = boost::regex(l0);
    pattern[1] = boost::regex(ciff);
    for (int i=2; i<8; ++i)
      pattern[i] = boost::regex(cfff);

  }
}

uint NstElementStressRecord::process(const string &ln)
{
  if ( isCompositeShell(itemCode) )
    return process95(ln.substr(0,72));
  else if ( isLinearShell(itemCode) )
    return process33(ln.substr(0,72));
  else if ( isSolid(itemCode) )
    return process67(ln.substr(0,72));

  return NotFound;
}

uint NstElementStressRecord::process33(const std::string &ln)
{
  switch (stage) {
  case 0:
    if ( boost::regex_match(ln, matches, pattern[0]) ) {
      eid = genua_strtol(matches[1].str().c_str(),nullptr, 10);
      sigma[0] = genua_strtod(matches[3].str().c_str(),nullptr);
      sigma[1] = genua_strtod(matches[6].str().c_str(),nullptr);
      sigma[2] = genua_strtod(matches[9].str().c_str(),nullptr);
      stage = 1;
    } else
      return NotFound;
    break;
  case 1:
  case 2:
  case 3:
  case 4:
    if ( boost::regex_match(ln, matches, pattern[stage]) ) {
      uint k = 3*stage;
      sigma[k+0] = genua_strtod(matches[1].str().c_str(),nullptr);
      sigma[k+1] = genua_strtod(matches[4].str().c_str(),nullptr);
      sigma[k+2] = genua_strtod(matches[7].str().c_str(),nullptr);
      ++stage;
    } else
      return NotFound;
    break;
  case 5:
    if ( boost::regex_match(ln, matches, pattern[5]) ) {
      sigma[15] = genua_strtod(matches[1].str().c_str(),nullptr);
      stage = 0;
    } else
      return NotFound;
    break;
  default:
    return NotFound;
  }

  return stage;
}

uint NstElementStressRecord::process95(const std::string &ln)
{
  /*
$ELEMENT TYPE =          95                                                43719
      1151                 1             -2.507920E+05     -4.229074E+06   43720
-CONT-                  3.272627E+04      3.859382E+03     -1.508422E+05   43721
-CONT-                  4.712859E-01     -2.505228E+05     -4.229342E+06   43722
-CONT-                  1.989410E+06                                       43723
*/

  switch (stage) {
  case 0:
    if ( boost::regex_match(ln, matches, pattern[0]) ) {
      eid = genua_strtol(matches[1].str().c_str(),nullptr, 10);
      laminateIndex = genua_strtol(matches[2].str().c_str(),nullptr, 10);
      sigma[0] = genua_strtod(matches[3].str().c_str(),nullptr);
      assert(isfinite(sigma[0]));
      sigma[1] = genua_strtod(matches[6].str().c_str(),nullptr);
      assert(isfinite(sigma[1]));
      stage = 1;
    } else
      return NotFound;
    break;
  case 1:
    if ( boost::regex_match(ln, matches, pattern[1]) ) {
      sigma[2] = genua_strtod(matches[1].str().c_str(),nullptr);
      assert(isfinite(sigma[2]));
      sigma[3] = genua_strtod(matches[4].str().c_str(),nullptr);
      assert(isfinite(sigma[3]));
      sigma[4] = genua_strtod(matches[7].str().c_str(),nullptr);
      assert(isfinite(sigma[4]));
      stage = 2;
    } else
      return NotFound;
    break;
  case 2:
    if ( boost::regex_match(ln, matches, pattern[2]) ) {
      sigma[5] = genua_strtod(matches[1].str().c_str(),nullptr);
      assert(isfinite(sigma[5]));
      sigma[6] = genua_strtod(matches[4].str().c_str(),nullptr);
      assert(isfinite(sigma[6]));
      sigma[7] = genua_strtod(matches[7].str().c_str(),nullptr);
      assert(isfinite(sigma[7]));
      stage = 3;
    } else
      return NotFound;
    break;
  case 3:
    if ( boost::regex_match(ln, matches, pattern[3]) ) {
      sigma[8] = genua_strtod(matches[1].str().c_str(),nullptr);
      assert(isfinite(sigma[8]));
      stage = 0;
    } else
      return NotFound;
    break;
  default:
    return NotFound;
  }

  return stage;
}

uint NstElementStressRecord::process67(const string &ln)
{
  /*
         1                 0        GRID                       8          225509
-CONT-                     0              4.348845E+03     -9.120874E+02  225510
-CONT-                  1.117407E+04     -4.415751E-01      3.171620E-01  225511
-CONT-                 -8.392971E-01     -3.269060E+03      1.419451E+04  225512
-CONT-                  5.378865E+03      6.390392E+03     -5.188384E+03  225513
-CONT-                  6.950914E-01     -4.705615E-01     -5.435254E-01  225514
-CONT-                  7.947043E+01     -4.194874E+03      3.821499E+03  225515
-CONT-                  5.673265E-01      8.233955E-01      1.266836E-02  225516
-CONT-                  1001              7.869797E+03     -3.790611E+03  225517
-CONT-                  2.319960E+04      5.829163E-01     -2.066694E-01  225518
-CONT-                 -7.858093E-01     -4.985189E+03      2.851436E+04  225519
-CONT-                 -1.329813E+03     -1.079546E+04     -8.833632E+03  225520
-CONT-                 -4.010762E-01      7.678934E-01     -4.994773E-01  225521
-CONT-                  8.415584E+03      1.049420E+04      5.896014E+02  225522
-CONT-                  7.066445E-01      6.063229E-01      3.647274E-01  225523
*/

  switch (stage) {
  case 0:
    if ( boost::regex_match(ln, matches, pattern[stage]) ) {
      eid = genua_strtol(matches[1].str().c_str(),nullptr, 10);
      npoints = genua_strtol(matches[3].str().c_str(),nullptr, 10);
      ipoint = 0;
      stage = 1;
    } else
      return NotFound;
    break;
  case 1:
    if ( boost::regex_match(ln, matches, pattern[stage]) ) {
      gid = genua_strtol(matches[1].str().c_str(),nullptr, 10);
      if (gid == 0) {
        sigma[0] = genua_strtod(matches[2].str().c_str(),nullptr);
        sigma[1] = genua_strtod(matches[5].str().c_str(),nullptr);
      } else {
        ++ipoint;
      }
      stage = 2;
    } else
      return NotFound;
    break;
  case 2:
  case 3:
  case 4:
  case 5:
  case 6:
  case 7:
    if ( boost::regex_match(ln, matches, pattern[stage]) ) {
      if (gid == 0) {
        uint k = 3*stage - 4;
        sigma[k+0] = genua_strtod(matches[1].str().c_str(),nullptr);
        sigma[k+1] = genua_strtod(matches[4].str().c_str(),nullptr);
        sigma[k+2] = genua_strtod(matches[7].str().c_str(),nullptr);
      }
      if (stage < 7)
        ++stage;
      else if (ipoint < npoints)
        stage = 1;
      else
        stage = 0;
    } else
      return NotFound;
    break;
  default:
    return NotFound;
  }

  return stage;
}
