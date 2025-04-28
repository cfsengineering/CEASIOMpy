
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
 
#ifndef DIRECTPMAPDIALOG_H
#define DIRECTPMAPDIALOG_H

#include "ui_directpmapdialog.h"

#ifndef Q_MOC_RUN
#include <genua/mxmesh.h>
#endif

class PLoadDialog;

/** Query parameters for direct pressure mapping.

  This dialog is used to ask for Mach and altitude parameters needed to generate
  pressure loads on a structural model.

  */
class DirectPMapDialog : public QDialog, private Ui::DirectPMapDialog
{
  Q_OBJECT

public:

  /// construct dialog
  explicit DirectPMapDialog(QWidget *parent = 0);

  /// assign an aerodynamic mesh
  bool assign(MxMeshPtr amesh);

signals:

  /// request that top-level view object switches mesh display
  void displayMesh(MxMeshPtr pmx);

public slots:

  /// change field index
  void changeSelectedField(int idx);

private slots:

  /// adapt q when altitude modified
  void altChanged();

  /// airspeed value changed
  void airspeedChanged();

  /// speed unit changed
  void unitChanged();

  /// update displayed dynamic pressure
  void showDynamicPressure();

  /// proceed to next step
  void nextStep();

protected:

  /// runtime UI change
  void changeEvent(QEvent *e);

  /// retrieve airspeed in m/s
  double siSpeedConversion() const;

private:

  /// child dialog
  PLoadDialog *cplDlg;

  /// aerodynamic mesh
  MxMeshPtr amp;

  /// map between combo box list and field index
  Indices ifield;

  /// speed in m/s
  double sispeed;
};

#endif // DIRECTPMAPDIALOG_H
