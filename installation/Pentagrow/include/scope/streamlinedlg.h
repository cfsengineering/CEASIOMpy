
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
 
#ifndef SCOPE_STREAMLINEDLG_H
#define SCOPE_STREAMLINEDLG_H

#include "forward.h"
#include <QDialog>

namespace Ui {
class StreamlineDlg;
}

class HedgehogDialog : public QDialog
{
  Q_OBJECT

public:

  /// construct dialog
  HedgehogDialog(QWidget *parent = 0);

  /// destroy UI Object
  ~HedgehogDialog();

  /// assign plot controller
  void assign(PlotController *pc);

signals:

  /// emitted when display changes require a repaint
  void redrawNeeded();

private slots:

  /// apply changes to view object
  void apply();

  /// determine default scaling factor
  void defaultScaling();

  /// adapt dialog to user selected mode
  void adaptUi();

protected:

  /// chaneg language
  void changeEvent(QEvent *e);

private:

  /// display control interface
  PlotController *m_pc;

  /// 3-component vector fields
  Indices m_ivf;

  /// UI object
  Ui::StreamlineDlg *m_ui;
};

#endif
