//
// project:      scope
// file:         nodeinfobox.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Display information about a node

#ifndef SCOPE_NODEINFOBOX_H
#define SCOPE_NODEINFOBOX_H

#include "forward.h"
#include <QDialog>

class FieldDataModel;

namespace Ui {
  class NodeInfoBox;
}

/** Dialog to display nodal data.
  */
class NodeInfoBox : public QDialog
{
  Q_OBJECT
public:

  /// create information box (not assigned)
  NodeInfoBox(QWidget *parent = 0);

  /// destroy UI
  ~NodeInfoBox();

  /// assign to mesh mx
  void assign(MxMeshPtr mx);

public slots:

  /// display information for node idx
  void showInfo(int idx);

private slots:

  /// open simple dialog to enter node ID
  void lookup();

protected:

  /// change language etc
  void changeEvent(QEvent *e);

private:

  /// mesh to use for display
  MxMeshPtr pmx;

  /// table data model
  FieldDataModel *dataModel;

  /// Nastran GIDs
  Indices gids;

  /// UI elements
  Ui::NodeInfoBox *ui;
};

#endif // NODEINFOBOX_H
