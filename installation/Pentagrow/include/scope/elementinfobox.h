//
// project:      scope
// file:         elementinfobox.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Display element data

#ifndef SCOPE_ELEMENTINFOBOX_H
#define SCOPE_ELEMENTINFOBOX_H

#include "forward.h"
#include <QDialog>

class FieldDataModel;
class MxMesh;

namespace Ui {
  class ElementInfoBox;
}

class ElementInfoBox : public QDialog
{
  Q_OBJECT
public:

  /// construct info box
  ElementInfoBox(QWidget *parent = 0);

  /// destroy ui
  ~ElementInfoBox();

  /// set contents
  void assign(MxMeshPtr mx);

signals:

  /// request node information
  void requestNodeInfo(int k);

public slots:

  /// fill fields with data for element gix
  void showInfo(int gix);

private slots:

  /// convert link string to node index
  void requestNodeInfo(const QString & s);

protected:

  /// clear out data
  void clearFields();

  /// language change
  void changeEvent(QEvent *e);

private:

  /// mesh pointer
  MxMeshPtr pmx;

  /// data model for table view
  FieldDataModel *dataModel;

  /// UI elements
  Ui::ElementInfoBox *ui;
};

#endif // ELEMENTINFOBOX_H
