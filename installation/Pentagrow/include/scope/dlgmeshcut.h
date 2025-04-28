/* ------------------------------------------------------------------------
 * project:    scope
 * file:       dlgmeshcut.h
 * copyright:  (c) 2009 by <dlr@kth.se>
 * ------------------------------------------------------------------------
 * Specify plane for volume mesh cuts
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#ifndef SCOPE_DLGMESHCUT_H
#define SCOPE_DLGMESHCUT_H

#include "forward.h"
#include <QDialog>

namespace Ui {
class DlgMeshCut;
}

/** Specify plane for volume mesh cuts.
 *
 * Dialog used to define one or multiple slicing planes for volume mesh
 * sections. whenever a new slicing plane is defined, the volume elements
 * intersected by this plane will be added to the visible set.
 *
 * \sa MeshPlotter, SectionPlotter
*/
class MeshCutDialog : public QDialog
{
  Q_OBJECT
public:

  /// construct given a view widget
  MeshCutDialog(QWidget *parent);

  /// destroy dialog
  ~MeshCutDialog();

  /// assign plot controller
  void assign(PlotController *plc);

signals:

  /// emitted when drawing needs update
  void needRedraw();

private slots:

  /// fill normal direction values
  void fillNormal();

  /// remove current mesh cut
  void clearCurrent();

  /// compute volume mesh slice and ask for redraw
  void applyCut();

protected:

  /// change language
  void changeEvent(QEvent *e);

private:

  /// controller widget for the OpenGL display
  PlotController *m_plc;

  /// UI object
  Ui::DlgMeshCut *m_ui;
};

#endif // DLGMESHCUT_H
