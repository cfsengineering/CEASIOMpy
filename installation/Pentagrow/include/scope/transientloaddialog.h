
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
 
#ifndef TRANSIENTLOADDIALOG_H
#define TRANSIENTLOADDIALOG_H

#include "ui_transientloaddialog.h"
#ifndef Q_MOC_RUN
#include <genua/mxmesh.h>
#endif

class PLoadDialog;

/** Dialog to define settings used to map motion states to pressure fields.
  */
class TransientLoadDialog : public QDialog, private Ui::TransientLoadDialog
{
  Q_OBJECT

public:

  /// create dialog
  explicit TransientLoadDialog(QWidget *parent = 0);

  /// assign aerodynamic mesh
  void assign(MxMeshPtr am);

  /// change default directory
  void defaultDirectory(const QString & d) {lastdir = d;}

private slots:

  /// browse for history file
  void browseHistory();

  /// proceed to structural load generation
  void proceed();

  /// selected state changed
  void stateSelectionChanged(int istate);

  /// selected field changed
  void fieldSelectionChanged(int ifield);

  /// save settings to file
  void storeSettings();

  /// retrieve settings from file
  void loadSettings();

protected:

  /// runtime changes
  void changeEvent(QEvent *e);

  /// number of states
  uint nstate() const {return rawHistory.empty() ? 0 : rawHistory[0].size();}

  /// update table contents
  void parseHistory();

private:

  /// aerodynamic mesh
  MxMeshPtr amesh;

  /// fields possibly containing cp values
  Indices cpCandFields;

  /// mapping of states to fields (indices into cpCandFields)
  Indices stateMap;

  /// time values
  Vector timeSteps;

  /// state history
  VectorArray rawHistory;

  /// child dialog
  PLoadDialog *cplDlg;

  /// last directory used
  QString lastdir;
};

#endif // TRANSIENTLOADDIALOG_H
