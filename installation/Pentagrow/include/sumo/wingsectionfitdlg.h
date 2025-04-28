
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
 
#ifndef WINGSECTIONFITDLG_H
#define WINGSECTIONFITDLG_H

#include "ui_wingsectionfitdlg.h"
#include "forward.h"

/** Control wing section fitting parameters.

  */
class WingSectionFitDlg : public QDialog, private Ui::WingSectionFitDlg
{
  Q_OBJECT
  
public:

  /// construct dialog
  explicit WingSectionFitDlg(QWidget *parent = 0);
  
  /// assign an assembly and geometry slicer
  void assign(AssemblyPtr pa, FrameProjectorPtr pf, FitIndicatorPtr indic);

signals:

  /// issued when any lifting surface was modified
  void geometryChanged();

  /// issued when indicator changes appearance
  void indicatorChanged();

public slots:

  /// preselect section j to fit
  void selectSection(int iwing, int jsection);

private slots:

  /// change list of sections when wing changed
  void showSections(int iwing);

  /// process and fit sections
  void apply();

  /// update visualization according to current selection
  void updateIndicator();

  /// clear fit indicator when dialog is closed
  void clearIndicator();

protected:

  /// runtime language change etc.
  void changeEvent(QEvent *e);

private:

  /// assembly from which components are used
  AssemblyPtr pasy;

  /// search data structure generating sections
  FrameProjectorPtr fpj;

  /// visualization helper
  FitIndicatorPtr findic;
};

#endif // WINGSECTIONFITDLG_H
