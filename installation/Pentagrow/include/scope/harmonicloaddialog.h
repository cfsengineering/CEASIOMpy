
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
 
#ifndef HARMONICLOADDIALOG_H
#define HARMONICLOADDIALOG_H

#include "ui_harmonicloaddialog.h"
#ifndef Q_MOC_RUN
#include "forward.h"
#include <genua/dvector.h>
#endif

class PLoadDialog;

/** Dialog for defining loads for harmonic response analyses.
  */
class HarmonicLoadDialog : public QDialog, private Ui::HarmonicLoadDialog
{
  Q_OBJECT

public:

  /// setup dialog
  explicit HarmonicLoadDialog(QWidget *parent = 0);

  /// set aerodynamic mesh to use
  void assign(MxMeshPtr am);

private slots:

  /// extract fields
  void extractFields();

  /// proceed to next step
  void proceed();

protected:

  /// runtime changes
  void changeEvent(QEvent *e);

private:

  /// aerodynamic mesh
  MxMeshPtr amesh;

  /// list of fields to use
  Indices cpFields;

  /// list of reduced frequencies
  Vector redFreq;

  /// child dialog
  PLoadDialog *cplDlg;
};

#endif // HARMONICLOADDIALOG_H
