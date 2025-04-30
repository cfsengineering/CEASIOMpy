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

#ifndef SURFACESTREAMLINEDIALOG_H
#define SURFACESTREAMLINEDIALOG_H

#include <genua/forward.h>
#include <genua/surfacestreamlines.h>
#include <QDialog>
#include <QVector>
#include <QCheckBox>
#include <QPointer>

namespace Ui {
class SurfaceStreamlineDialog;
}

class SurfaceStreamlineDialog : public QDialog
{
  Q_OBJECT

public:

  /// construct
  explicit SurfaceStreamlineDialog(QWidget *parent = 0);

  /// destroy GUI
  ~SurfaceStreamlineDialog();

  /// assign mesh
  void assign(MxMeshPtr pmx);

  /// access streamlines
  const SurfaceStreamlines &lines() const {return m_ssf;}

signals:

  /// streamline computation updated; flag true if streamlines should display
  void streamlinesChanged(bool flag=true);

  /// send info message
  void postStatusMessage(const QString &msg);

  /// user request to adjust streamline color
  void requestColorChange();

private slots:

  /// compute streamlines
  void apply();

  /// open file dialog to dump stored streamlines to many text files
  void exportLines();

private:

  /// mesh to be used
  MxMeshPtr m_pmx;

  /// indices of selectable fields
  Indices m_ivf;

  /// helper object for computation of streamlines
  SurfaceStreamlines m_ssf;

  /// GUI widgets
  Ui::SurfaceStreamlineDialog *m_ui;

  /// checkboxes for surface sections
  QVector<QPointer<QCheckBox> > m_box;

  /// set of surfaces has changed
  bool m_dirty = true;
};

#endif // SURFACESTREAMLINEDIALOG_H
