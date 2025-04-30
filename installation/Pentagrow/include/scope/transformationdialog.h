
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
 
#ifndef TRANSFORMATIONDIALOG_H
#define TRANSFORMATIONDIALOG_H

#include "ui_transformationdialog.h"
#ifndef Q_MOC_RUN
#include <genua/transformation.h>
#include <genua/mxmesh.h>
#endif

/** Dialog for editing coordinate transformations.


*/
class TransformationDialog : public QDialog, private Ui::TransformationDialog
{
  Q_OBJECT

public:

  /// construct dialog
  explicit TransformationDialog(QWidget *parent = 0);

  /// set mesh object to transform (optional)
  void assign(MxMeshPtr msh);

  /// access current transformation state
  const Trafo3d & currentTrafo() const {return trafo;}

  /// change transformation to display
  void setTrafo(const Trafo3d & t);

  /// enable rotations
  void enableRotation(bool flag);

  /// enable translation
  void enableTranslation(bool flag);

  /// enable scaling
  void enableScaling(bool flag);

  /// modify for use as modal dialog
  void useModal(bool modal);

public slots:

  /// switch to absolute transformation display
  void displayAbsolute(bool flag);

  /// fetch form values and set transformation (emits trafoChanged())
  void apply();

signals:

  /// emitted whenever the absolute transformation was changed
  void trafoChanged();

protected:

  /// change language etc.
  void changeEvent(QEvent *e);

protected:

  /// double-precision transformation
  Trafo3d trafo;

  /// optionally assigned mesh object
  MxMeshPtr pmx;
};

#endif // TRANSFORMATIONDIALOG_H
