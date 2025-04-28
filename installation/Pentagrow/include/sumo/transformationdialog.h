
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
#endif

/** Dialog for editing coordinate transformations.


*/
class TransformationDialog : public QDialog, private Ui::TransformationDialog
{
  Q_OBJECT

public:

  /// construct dialog
  explicit TransformationDialog(QWidget *parent = 0);

  /// access current transformation state
  const Trafo3d & currentTrafo() const {return trafo;}

  /// change transformation to display
  void setTrafo(const Trafo3d & t);

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
};

#endif // TRANSFORMATIONDIALOG_H
