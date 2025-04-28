
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
 
#ifndef COMPONENTDIALOG_H
#define COMPONENTDIALOG_H

#include "ui_componentdialog.h"
#include "forward.h"

class ComponentDialog : public QDialog, private Ui::ComponentDialog
{
  Q_OBJECT
  
public:

  /// construct UI
  explicit ComponentDialog(QWidget *parent = 0);

  /// assign plot control widget
  void assign(PlotController *plc);

signals:

  /// emitted whenever the OpenGL display needs to be redrawn
  void needRedraw();

  /// emitted when a section is hidden/shown
  void sectionVisibilityChanged(int isection, bool flag);

  /// emitted when a boco is hidden/shown from dialog
  void bocoVisibilityChanged(int isection, bool flag);

public slots:

  /// programmatically select a particular section
  void selectSection(int isection);

  /// programmatically select a particular boco
  void selectBoco(int iboco);

private slots:

  /// update UI elements on change of mesh structure
  void updateStructure();

  /// update UI when section changed
  void sectionSelected(int isection);

  /// update UI when boco selected
  void bocoSelected(int iboco);

  /// propagate change of boco type
  void changeBocoType(int bocoType);

  /// erase current section entirely
  void eraseSection();

  /// erase current boco entirely
  void eraseBoco();

  /// create a new boco
  void newBoco();

  /// change section display color
  void changeSectionColor();

  /// change boco display color
  void changeBocoColor();

  /// apply changes (connected to all changing widgets)
  void apply();

  /// toggle edge display settingd for all presently visible sections
  void toggleAllEdges();

private:

  /// plot control object
  PlotController *m_plc;

  /// mapping of element type ids to translated names
  std::map<int, QString> m_et2s;
};

#endif // COMPONENTDIALOG_H
