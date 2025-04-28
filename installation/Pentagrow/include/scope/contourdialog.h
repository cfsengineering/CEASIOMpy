
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
 
#ifndef CONTOURDIALOG_H
#define CONTOURDIALOG_H

#include "ui_contourdialog.h"
#include "forward.h"

/** Controls surface color contours.
 *
 */
class ContourDialog : public QDialog, private Ui::ContourDialog
{
  Q_OBJECT
  
public:

  /// construct dialog
  explicit ContourDialog(QWidget *parent = 0);

  /// assign plot controller
  void assign(PlotController *plc);

signals:

  /// emitted when color spread factor changed
  void spreadChanged(float sf);

public slots:

  /// programmatically change selected field
  void selectField(int ifield=0);

private slots:

  /// enable control of field settings
  void enableContourSettings(bool flag=true);

  /// update UI when selected field changed
  void fieldSelected(int ifield);

  /// update min/max values when condensation mode changed
  void condensationChanged(int vfm);

  /// convert integer slider value to float spread factor
  void changeSpread(int sliderPos = -1);

  /// react on locking/unlocking of color limit values
  void lockRange(bool flag);

  /// update plot settings from UI
  void applyLimits();

private:

  /// interface for display manager
  PlotController *m_plc;
};

#endif // CONTOURDIALOG_H
