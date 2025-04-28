
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
 
#ifndef SUMO_WAVEDRAGDLG_H
#define SUMO_WAVEDRAGDLG_H

#include "ui_wavedragdlg.h"
#ifndef Q_MOC_RUN
#include <genua/volwavedrag.h>
#endif

/** Wave drag dialog.

  This dialog provides access to the algorithm implemented in
  libgenua/VolWaveDrag, which makes use of a sine series of the
  longitudinal sequence of cross section area distributions to
  compute volume wave drag.

  */
class WaveDragDlg : public QDialog, private Ui::WaveDragDlg
{
  Q_OBJECT

public:

  /// create empty dialog
  explicit WaveDragDlg(QWidget *parent = 0);

  /// assign mesh to dialog
  void assign(const TriMesh & tm, const Indices & intakeTags);

  /// assign mesh to dialog
  void assign(const MxMesh & mx);

private slots:

  /// perform wave drag computations when 'Apply' pressed
  void apply();

  /// save area distribution
  void saveDistribution();

  /// update drag coefficient when reference area changes
  void areaChanged();

  /// update plotting widget
  void plotDistribution();

protected:

  /// determine local inlet streamtube section area to substract
  void effectiveStreamtube(Real mach);

  /// runtime change
  void changeEvent(QEvent *e);

private:

  /// contains actual wave drag computations
  VolWaveDrag vwd;

  /// longitudinal coordinate and area distribution
  Vector xv, Sv;

  /// intake streamtube area to be substracted
  Vector Svi;

  /// element center points for intake elements
  PointList<3> inCtr;

  /// area of intake elements
  Vector inArea;

  /// S*Cd
  Real SCdw;

  /// remember last used directory
  QString lastdir;
};

#endif // WAVEDRAGDLG_H
