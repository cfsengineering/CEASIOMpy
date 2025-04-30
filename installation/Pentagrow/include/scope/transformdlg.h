
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
 
#ifndef SCOPE_TRANSFORMDLG_H
#define SCOPE_TRANSFORMDLG_H

#include <QDialog>
#ifndef Q_MOC_RUN
#include <genua/point.h>
#include <genua/smatrix.h>
#endif

namespace Ui {
    class TransformDlg;
}

/** Dialog to set mesh transformations.
  */
class TransformDlg : public QDialog
{
  Q_OBJECT
  public:

    /// create dialog
    TransformDlg(QWidget *parent, PointList<3> & pts);

    /// destroy UI object
    ~TransformDlg();

  signals:

    /// emitted when vertex coordinates where changed
    void geometryChanged();

  private slots:

    /// apply transformation
    void apply();

    /// reverse last transformation
    void revert();

  protected:

    /// runtime language change
    void changeEvent(QEvent *e);

  private:

    /// mesh vertices to modify
    PointList<3> & vtx;

    /// last transformation matrix applied
    SMatrix<4,4> lasttfm;

    ///  generated UI object
    Ui::TransformDlg *m_ui;
};

#endif // TRANSFORMDLG_H
