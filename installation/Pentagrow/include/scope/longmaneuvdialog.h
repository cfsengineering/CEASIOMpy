
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
 
#ifndef LONGLDIPDIALOG_H
#define LONGLDIPDIALOG_H

#include "ui_longmaneuvdialog.h"
#include "forward.h"

#ifndef Q_MOC_RUN
#include <genua/point.h>
#endif

class PLoadDialog;

/** Longitudinal maneuver load interpolation.

  This dialog is used to set longitudinal maneuver parameters. From these
  parameters, it will compute the full quasi-steady flight state and
  create a load interpolation object

*/
class LongManeuvDialog : public QDialog, private Ui::LongLdipDialog
{
  Q_OBJECT

public:

  /// construct dialog, setup UI
  explicit LongManeuvDialog(QWidget *parent = 0);

  /// attach to mesh, test for compatibility
  bool assign(const MxMeshPtr & amsh);

signals:

  /// request that top-level view object switches mesh display
  void displayMesh(MxMeshPtr pmx);

private slots:

  /// update derived parameters
  void derive();

  /// proceed to structural load interpolation
  void nextStep();

protected:

  /// runtime language change etc.
  void changeEvent(QEvent *e);

private:

  /// child dialog
  PLoadDialog *cplDlg;

  /// pointer to aerodynamic mesh
  MxMeshPtr amp;

  /// field indices (ref, alpha, pitch rate)
  Indices ifield;

  /// reference point for pitch moment
  Vct3 refPoint;

  /// reference conditions
  double refAlpha, refChord;

  /// longitudinal force coefficients
  double Czo, Cza, Czq, CzDe;

  /// pitch moment coefficients
  double Cmo, Cma, Cmq, CmDe;

  /// derived values
  double Cz, qoo, alpha, deltaElevator, qhat;
};

#endif // LONGLDIPDIALOG_H
