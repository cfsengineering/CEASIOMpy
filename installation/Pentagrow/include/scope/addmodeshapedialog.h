//
// project:      scope
// file:         addmodeshapedialog.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Add generated rigid-body modeshape

#ifndef ADDMODESHAPEDIALOG_H
#define ADDMODESHAPEDIALOG_H

#ifndef Q_MOC_RUN
#include "forward.h"
#endif

#include <QDialog>

namespace Ui {
  class AddModeshapeDialog;
}

class AddModeshapeDialog : public QDialog
{
  Q_OBJECT
public:

  /// setup empty dialog
  AddModeshapeDialog(QWidget *parent = 0);

  /// delete GUI
  ~AddModeshapeDialog();

  /// assign mesh
  void assign(MeshPlotterPtr plt);

signals:

  /// emitted when modes changed
  void addedModeshapes();

private slots:

  /// update dialog display
  void showMassBox(bool flag);

  /// prepend modes
  void addModes();

protected:

  /// language change
  void changeEvent(QEvent *e);

private:

  /// mesh to modify
  MeshPlotterPtr plotter;

  /// GUI elements
  Ui::AddModeshapeDialog *ui;
};

#endif // ADDMODESHAPEDIALOG_H
