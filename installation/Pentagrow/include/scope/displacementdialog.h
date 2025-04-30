
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
 
#ifndef DISPLACEMENTDIALOG_H
#define DISPLACEMENTDIALOG_H

#include "ui_displacementdialog.h"
#include "forward.h"

/** Visualize mesh deformation.
 *
 *  This is a dialog to control display of mesh deformations. These can be
 *  displayed as statically deformed meshes or as animations.
 *
 */
class DisplacementDialog : public QDialog, private Ui::DisplacementDialog
{
  Q_OBJECT

public:

  /// create GUI
  explicit DisplacementDialog(QWidget *parent = 0);

  /// assign plot controller
  void assign(PlotController *plc);

signals:

  /// called when static redraw is required
  void needRedraw();

  /// emitted when play button pressed
  void startAnimation();

  /// emitted when stop button pressed
  void stopAnimation();

public slots:

  /// switch deformation field
  void selectField(int ifield);

private slots:

  /// show undeformed mesh
  void modeUndeformed(bool flag);

  /// show simple deformed mesh
  void modeDeformation(bool flag);

  /// trajectory or flutter mode display
  void modeTrajectory(bool flag);

  /// apply static deformation
  void deform();

  /// react to progress of animation, set slider position
  void animationAt(float rtime);

  /// react to end of animation
  void animationDone();

  /// react on slider motion
  void scrub(int pos);

  /// play button pressed
  void play();

  /// animation speed slider moved
  void adaptAnimationSpeed(int slider);

private:

  /// convert animation speed setting to slider position
  int speedToSlider(float speed) const;

  /// convert slider setting to speed
  float sliderToSpeed(int pos) const;

private:

  /// interface for mesh display management
  PlotController *m_plc;

  /// fields identified as deformations
  Indices m_dsp;

  /// indicate whether animation is running
  bool m_animating;
};

#endif // DISPLACEMENTDIALOG_H
