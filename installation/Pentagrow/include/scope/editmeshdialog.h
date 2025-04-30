
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
 
#ifndef SCOPE_EDITMESHDIALOG_H
#define SCOPE_EDITMESHDIALOG_H

#include "ui_editmeshdialog.h"
#include "forward.h"

#ifndef Q_MOC_RUN
#include <genua/xmlelement.h>
#endif

/** Display and edit mesh prperties.

  This dialog displays node and element count etc. and allows to erase
  or add trajectory (time-dependent modal deformation) data.

*/
class EditMeshDialog : public QDialog, private Ui::EditMeshDialog
{
  Q_OBJECT

public:

  /// construct
  explicit EditMeshDialog(QWidget *parent = 0);

  /// assign mesh, update display
  void assign(MeshPlotterPtr pm);

signals:

  /// trajectory load requested
  void loadTrajectory();

public slots:

  /// update the number of visible display primitives
  void countPrimitives();

private slots:

  /// update display for changed path selection
  void selectPath(int i);

  /// remove trajectory from mesh
  void erasePath();

protected:

  /// change language etc.
  void changeEvent(QEvent *e);

private:

  /// mesh to display data for
  MxMeshPtr pmsh;

  /// mesh plotter which owns mesh data
  MeshPlotterPtr plotter;

  /// copy (!) of xml annotation currently displayed
  XmlElement note;
};

#endif // EDITMESHDIALOG_H
