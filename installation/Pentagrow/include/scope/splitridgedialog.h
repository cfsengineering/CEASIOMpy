
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
 
#ifndef SPLITRIDGEDIALOG_H
#define SPLITRIDGEDIALOG_H

#include <QDialog>

namespace Ui {
class SplitRidgeDialog;
}

/** Dialog for mesh split option.
 *
 *  Requests whether/how a mesh shall be split along feature edges, e.g. on
 *  import of STL geometry.
 *
 */
class SplitRidgeDialog : public QDialog
{
  Q_OBJECT

public:

  /// create dialog
  explicit SplitRidgeDialog(QWidget *parent = 0);

  /// destroy UI
  ~SplitRidgeDialog();

  /// selected feature angle, negative if splitting deactive
  double featureAngle() const;

  /// point merge threshold
  double mergeThreshold() const;

private:

  /// user interface components
  Ui::SplitRidgeDialog *ui;
};

#endif // SPLITRIDGEDIALOG_H
