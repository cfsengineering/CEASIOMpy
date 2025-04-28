
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
 
#ifndef DEFORMATIONMAPDLG_H
#define DEFORMATIONMAPDLG_H

#include "ui_deformationmapdlg.h"

#ifndef Q_MOC_RUN
#include <surf/forward.h>
#include <surf/rbfinterpolator.h>
#include <surf/surfinterpolator.h>
#endif


/** Dialog to control settings interpolation of deformations.

  RBF interpolation can be used to map the deformation stored in a
  file containing structural analysis results (modeshapes, displacements)
  to the surface elements of an aerodynamic mesh. The interpolated deformations
  will be added as 3-dimensional data fields.
*/
class DeformationMapDlg : public QDialog, private Ui::DeformationMapDlg
{
  Q_OBJECT
  
public:

  /// create dialog
  explicit DeformationMapDlg(QWidget *parent = 0);
  
  /// whether a structural mesh is already present
  bool haveStructure() const;

  /// assign aerodynamic mesh for which interpolation is performed
  void assign(MxMeshPtr pmx);

  /// access resulting mesh
  MxMeshPtr interpolated() {return m_amesh;}

  /// hint at last used directory location
  void lastDirectory(const QString &dir) {m_lastdir = dir;}

signals:

  /// set of deformations was updated with n new displacement fields
  void deformationsChanged(int n);

  /// user-selected search path changed
  void userPathChanged(const QString &path);

  /// please open user manual at the given link
  void requestHelp(const QString &link);

public slots:

  /// load structural mesh from file
  void loadStructure();

private slots:

  /// switch between interpolation methods
  void changeMethod();

  /// change the set of selectable aerodynamic boundaries
  void enableAeroBoundaries();

  /// apply deformation mapping
  void apply();

  /// export to .bdis files for edge
  void exportAs();

  /// store algorithm settings to file
  void saveSettings();

  /// load algorithm settings from file
  void loadSettings();

  /// open help depending on context
  void contextHelp();

  /// lines-only option changed
  void linesOnly(bool flag);

protected:

  /// set combo boxes from settings stored in config
  void loadBoundaryFlags(const ConfigParser &cfg,
                         const std::string &key, int idx);

  /// initialize interpolator from UI
  void init(DispInterpolator &dispi);

  /// map by means of RBF method
  void mapRbf();

  /// map by means of shell projection
  void mapSpj();

  /// suggest smoothing distance value
  Real estimateSmoothingRadius();

  /// language change
  void changeEvent(QEvent *e);

private:

  enum BoundaryMotion { Free, Fixed, Moving, Sliding, Ignore };

  /// private copy of aerodynamic mesh
  MxMeshPtr m_amesh;

  /// structural mesh used internally (not visible)
  MxMeshPtr m_smesh;

  /// interpolator for shell projection method
  SurfInterpolator m_sipol;

  /// interpolator for RBF method
  RbfInterpolator m_rbipol;

  /// track last directory used
  QString m_lastdir;

  /// combo boxes used to select which boundaries to move
  QList<QComboBox*> m_bdBoxes;

  /// labels for the boundary selection boxes
  QList<QLabel*> m_bdLabels;

  /// whether to apply automatic rescaling at the end
  bool m_autoRescale;
};


#endif // DEFORMATIONMAPDLG_H
