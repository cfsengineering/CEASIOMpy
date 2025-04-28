#ifndef BUILDFLUTTERMODEDIALOG_H
#define BUILDFLUTTERMODEDIALOG_H

#include "forward.h"
#include <QDialog>

namespace Ui {
class BuildFlutterModeDialog;
}

/** Manually assemble flutter mode.
 *
 * This dialog allows the user to specify a flutter mode in terms of
 * modal participation factors obtained from some external software.
 *
 *
 */
class BuildFlutterModeDialog : public QDialog
{
  Q_OBJECT

public:

  /// create dialog
  explicit BuildFlutterModeDialog(QWidget *parent = 0);

  /// destroy
  ~BuildFlutterModeDialog();

  /// assign a mesh to work with
  void assign(MxMeshPtr pmx);

signals:

  /// emitted when a new mode has been created
  void flutterModeCreated();

private slots:

  /// try to create mode from UI
  void buildMode();

  /// fill table with zeros
  void tabulaRasa();

private:

  /// user interface
  Ui::BuildFlutterModeDialog *m_ui;

  /// pointer to mesh
  MxMeshPtr m_pmx;

  /// indices of the fields contaning eigenmodes
  Indices m_dsp;
};

#endif // BUILDFLUTTERMODEDIALOG_H
