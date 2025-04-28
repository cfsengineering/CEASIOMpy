
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
 
#ifndef FRFLOADDIALOG_H
#define FRFLOADDIALOG_H

#include "ui_inrelloaddialog.h"

#ifndef Q_MOC_RUN
#include "frfspec.h"
#include "tdlspec.h"
#include "flightpath.h"
#include "forward.h"
#endif

class PLoadDialog;

/** Interface for inertial-relief load generation.

  This dialog collects input needed to generate input data for a modal
  acceleration load analysis in the frequency domain, or a quasi-steady
  inertial relief maneuver load run (time domain).

  Frequency response

  The idea is to generate the right-hand side of the linear equation
  \f[
    K \hat{u}(\omega) = [q_{\infty} Q + \omega^2 M ] \hat{\xi}(\omega)
  \f]
  for each angular frequency.

  Quasi-steady inertial relief

  \f[
    K u(t) = q_{\infty} Q \xi(t) - M Z \ddot{\xi}
  \f]

  \ingroup LoadGeneration
  */
class InrelLoadDialog : public QDialog, private Ui::FRFLoadDialog
{
  Q_OBJECT

public:

  /// create dialog
  explicit InrelLoadDialog(QWidget *parent = 0);

  /// assign aerodynamic mesh, prepare for FRF analysis before calling show()
  void assignFrf(MxMeshPtr pm);

  /// assign aerodynamic mesh, prepare for time-domain analysis before calling show()
  void assignTdl(MxMeshPtr pm);

signals:

  /// notify parent/main widget of current work step
  void statusMessage(const QString & msg);

private slots:

  /// ask for nastran mesh file
  void browseNastranMesh();

  /// ask for state FRF file
  void browseStateFile();

  /// establish default state mapping
  void defaultMapping();

  /// selected state file column changed
  void columnChanged(int icol);

  /// update column mapping
  void updateMapping();

  /// load xml settings
  void loadSettings();

  /// store xml settings
  void storeSettings();

  /// proceed to next dialog (pressure mapping)
  void proceed();

protected:

  /// number of eigenmodes found in structural mesh
  uint nmodes() const {
    return (smesh) ? iModeField.size() : 0;
  }

  /// set structural mesh file in UI
  void setStructuralMeshFile(const QString &fname);

  /// set state history/FRF file name in UI
  void setStateHistoryFile(const QString &fname);

  /// load nastran file from filename
  void loadNastran();

  /// extract mass matrix, eigenmodes, and compute M*Z
  QString setupMZ();

  /// enable/disable tag/mode input elements
  void enableInput(bool flag);

  /// fetch FRF data from file
  void parseFRF();

  /// fetch time-domain data from file
  void fetchFlightPath();

  /// construct interpolation coefficients for mode k, frequency f
  uint linearCoefficients(uint k, Real f, uint fi[], Real icf[]) const;

  /// proceed to next dialog (pressure mapping)
  void proceedTdl();

  /// proceed to next dialog (pressure mapping)
  void proceedFrf();

  /// runtime events
  void changeEvent(QEvent *e);

private:

  enum OpMode {FrqResponse, TimeDomain};

  /// frequency response or time domain?
  OpMode opm;

  /// dataset to be passed to frequency response load interpolation
  FRFSpec fspec;

  /// parameters for time-domain inertial relief analysis
  TdlSpec tspec;

  /// file names
  QString strFileName, stateFileName;

  /// aerodynamic mesh to use
  MxMeshPtr amesh;

  /// fields which contain excitation response data
  Indices xcpFields;

  /// reduced frequencies for the above fields
  Vector xcpRedFreq;

  /// mode identifiers for the above fields
  Indices xcpModeTag;

  /// unique set of mode tags
  Indices xcpUniqueTag;

  /// unique set of reduced frequencies
  Vector xcpUniqueFreq;

  /// structural mesh loaded
  MxMeshPtr smesh;

  /// indices of fields containing eigenmodes
  Indices iModeField;

  /// inertial terms M_{GG}*Z
  VectorArray mggz;

  /// frequencies for which FRF is defined
  Vector freq;

  /// state FRF
  CpxMatrix frf;

  /// flight path (for time-domain case)
  FlightPath fpath;

  /// mapping of states to eigenmode indices
  Indices eigenModes;

  /// mapping of states to aerodynamic excitation
  Indices exciteTag;

  /// settings loaded will be passed to the pressure mapping dialog
  XmlElement userSettings;

  /// load interpolation dialog
  PLoadDialog *cplDlg;

  /// last used directory
  QString lastdir;
};

#endif // FRFLOADDIALOG_H
