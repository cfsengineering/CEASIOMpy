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

#ifndef SCOPE_FORCEDISPLAYDIALOG_H
#define SCOPE_FORCEDISPLAYDIALOG_H

#include "ui_forcedisplaydialog.h"
#include <genua/forward.h>
#include <genua/propmacro.h>
#include <genua/dmatrix.h>
#include <QString>

class ForceDisplayDialog : public QDialog, private Ui::ForceDisplayDialog
{
  Q_OBJECT

public:

  /// construct
  explicit ForceDisplayDialog(QWidget *parent = 0);

  /// assign a mesh to dialog
  void assign(MxMeshPtr pmx);

public slots:

  /// change field to integrate
  void selectField(int fix);

  /// update forces and moments for currently selected field
  void computeForces();

  /// export displayed table to file
  void exportTable();

public:

  /// mesh to work with
  MxMeshPtr m_pmx;

  /// scalar fields
  Indices m_ifields;

  /// surface sections
  Indices m_isections;

  /// computed forces and moments
  Matrix m_fm;

  /// set while intializing
  bool m_initializing = true;

  GENUA_PROP(QString, lastDirectory)
};

#endif // FORCEDISPLAYDIALOG_H
