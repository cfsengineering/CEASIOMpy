
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
 
#ifndef SURF_NSTRECORD_H
#define SURF_NSTRECORD_H

#include "nstelements.h"

class NstReader;

typedef enum { RidUndefined = 0,
               RidGRID,
               RidCONM2,
               RidCMASS2,
               RidCELAS2,
               RidCBEAM,
               RidCTRIA3,
               RidCTRIAR,
               RidCTRIA6,
               RidCQUAD4,
               RidCQUADR,
               RidCQUAD8,
               RidCHEXA,
               RidCTETRA,
               RidRBAR,
               RidRBE2,
               // RidRBE3,
               RidMPC,
               RidCORD2R,
               RidEigMode,
               RidPkSubspaceMode,
               RidDispl,
               RidElmStress,
               RidSubcase,
               RidEndBulk,
               RidEigTable } NstRecordId;

/** A group of lines in a NASTRAN text file.
 *
 * Each NstRecord represents a set of lines in a NASTRAN bulk data file, a
 * output "print" file (.f06) or a "punch" file (.pch). These records are
 * created by NstReader and NstRecord is responsible of parsing each of
 * type and instantiate the corresponding objects, such as elements or
 * data fields, inside a NstMesh object.
 *
 *  \ingroup structures
 * \sa NstReader, Nstmesh
 */
class NstRecord
{
public:

  /// construct record with id and reader ref
  NstRecord() : rid(RidUndefined), lbegin(0), lend(0) {}

  /// set first line of record
  void firstLine(uint i) {
    lbegin = i;
    lend = i+1;
  }

  /// add another line to record
  void lastLine(uint i) {
    lend = (i >= lend) ? i+1 : lend;
  }

  /// merge lines from another record
  void merge(const NstRecord & a) {
    lbegin = std::min(lbegin, a.lbegin);
    lend = std::max(lend, a.lend);
  }

  /// index of the first line
  uint first() const {return lbegin;}

  /// index of the last line
  uint last() const {
    return lend-1;
  }

  /// access record id
  void id(NstRecordId i) {rid = i;}

  /// access record id
  NstRecordId id() const {return rid;}

  /// check if record is empty
  bool empty() const {return lbegin == lend;}

  /// number of lines in this record
  uint size() const {return lend-lbegin;}

  /// clear lines and set id to undefined
  void clear() {
    rid = RidUndefined;
    lbegin = lend = 0;
  }

  /// scan line for grid point
  static bool gscan(const char *s) {
    const char *pos = strstr(s, "GRID");
    return (pos == s) ? true : false;
  }

  /// scan line for elements
  static NstRecordId toposcan(const char *s, bool ispunch=false);

  /// scan for eigenvector header
  static uint evscan(const char *s) {
    const char key[] = "E I G E N V E C T O R   N O .";
    const char *pos = strstr(s, key);
    return (pos == 0) ? 0 : atoi(pos+sizeof(key));
  }

  /// scan for eigenvector header
  static bool eigtablescan(const char *s) {
    const char key[] = "R E A L   E I G E N V A L U E S";
    const char *pos = strstr(s, key);
    return (pos != 0);
  }

  /// scan for flutter eigenvector header
  static bool pkzscan(const char *s) {
    const char key[] = "EIGENVECTOR FROM THE PK METHOD";
    const char *pos = strstr(s, key);
    return (pos != 0);
  }

  /// scan for subcase identifier
  static int subcasescan(const char *s) {
    const char key[] = "SUBCASE";
    const char *pos = strstr(s, key);
    if (pos == 0)
      return 0;
    pos += sizeof(key);
    while ((*pos != 0) and (not isdigit(*pos)))
      ++pos;
    return (*pos != 0) ? strtol(pos, 0, 10) : -1;
  }

  /// scan for timestep identifier
  static double timescan(const char *s) {
    const char key[] = "TIME";
    const char *pos = strstr(s, key);
    if (pos == 0)
      return NotDouble;
    const char *head = strchr(pos+sizeof(key), '=');
    if (head == 0)
      return NotDouble;
    char *tail;
    double t = strtod(head+1, &tail);
    return (tail != head+1) ? t : NotDouble;
  }

  /// scan for displacement header
  static bool dspscan(const char *s, bool ispunch) {
    if (ispunch) {
      const char key[] = "$DISPLACEMENTS";
      const char *pos = strstr(s, key);
      return (pos != 0);
    } else {
      const char key[] = "D I S P L A C E M E N T   V E C T O R";
      const char *pos = strstr(s, key);
      return (pos != 0);
    }
  }

  /// scan for stress header
  static bool sigscan(const char *s, bool ispunch) {
    if (ispunch) {
      const char key[] = "$ELEMENT STRESSES";
      const char *pos = strstr(s, key);
      return (pos != 0);
    } else {
      const char key[] = "S T R E S S E S";
      const char *pos = strstr(s, key);
      return (pos != 0);
    }
  }

  /// add elements to mesh, if any
  void process(NstReader & rdr) const;

  /// add modeshape to mesh
  bool mprocess(uint i, NstReader & rdr, bool ispunch) const;

  /// add displacement to mesh
  void dprocess(NstReader & rdr, bool ispunch) const;

  /// add flutter modes in modal subspace
  void pkprocess(NstReader &rdr) const;

  /// add stress results for supported element types
  void sigprocess(NstReader &rdr) const;

  /// read grid point coordinates and gid
  void readGrid(NstReader & rdr) const;

  // debugging : dump record to text stream
  void dump(const NstReader & rdr, std::ostream & os) const;

private:

  /// create CBEAM element
  void readBeam(NstReader & rdr) const;

  /// create CTRIA3 element
  void readTria3(NstReader & rdr) const;

  /// create CTRIAR element
  void readTriaR(NstReader & rdr) const;

  /// create CTRIA6 element
  void readTria6(NstReader & rdr) const;

  /// create CQUAD4 element
  void readQuad4(NstReader & rdr) const;

  /// create CQUADR element
  void readQuadR(NstReader & rdr) const;

  /// create CQUAD8 element
  void readQuad8(NstReader & rdr) const;

  /// create CHEXA element
  void readHexa(NstReader & rdr) const;

  /// create CTETRA element
  void readTetra(NstReader & rdr) const;

  /// create CONM2 element
  void readConm2(NstReader & rdr) const;

  /// create CMASS2 element
  void readCmass2(NstReader & rdr) const;

  /// create CELAS2 element
  void readCelas2(NstReader & rdr) const;

  /// create RBAR element
  void readRbar(NstReader & rdr) const;

  /// create RBE2 element
  void readRbe2(NstReader & rdr) const;

  /// create new coordinate system
  void readCord2r(NstReader & rdr) const;

  /// read eigenvector from punch file
  bool readPunchMode(uint mi, NstReader &rdr) const;

  /// read eigenvactor from .f06 file
  bool readPrintMode(uint mi, NstReader &rdr) const;

  /// insert eigenmode into mesh
  void appendMode(Matrix &z, uint mi, NstReader &rdr, Real kg=0) const;

private:

  /// typecode
  NstRecordId rid;
  
  /// line index : first and one-past last line
  uint lbegin, lend;
};

typedef std::vector<NstRecord> NstRecordArray;

#endif
