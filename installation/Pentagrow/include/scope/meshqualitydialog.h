
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
 
#ifndef MESHQUALITYDIALOG_H
#define MESHQUALITYDIALOG_H

#include "ui_meshqualitydialog.h"
#include "forward.h"

/** Dialog to control display of lousy elements.
 *
 *
 *
 */
class MeshQualityDialog : public QDialog, private Ui::MeshQualityDialog
{
  Q_OBJECT
  
public:

  /// create dialog
  explicit MeshQualityDialog(QWidget *parent = 0);

  /// assign a plot controller
  void assign(PlotController *plc);

signals:

  /// set of elements to display has changed
  void requestRepaint();

  /// short text message for simple diagnostics
  void postMessage(const QString &msg);

private slots:

  /// show critical elements
  void displayElements();

  /// hide critical elements
  void hideElements();

private:

  /// generate a text list of critical elements
  void listBadElements(const Indices &elx);

protected:

  /// runtime change
  void changeEvent(QEvent *e);

  /// plot controller
  PlotController *m_plc;
};

#endif // MESHQUALITYDIALOG_H
