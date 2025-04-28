//
// project:      scope
// file:         fielddatamodel.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Model class for element/node data display

#ifndef FIELDDATAMODEL_H
#define FIELDDATAMODEL_H

#ifndef Q_MOC_RUN
#include "forward.h"
#endif
#include <QAbstractTableModel>
#include <QModelIndex>
#include <QObject>

/** Data model for element/node field data display.
*/
class FieldDataModel : public QAbstractTableModel
{
  Q_OBJECT

public:

  /// construct an empty model
  explicit FieldDataModel(QObject *parent = 0);

  /// associate model with mesh and node number
  void bindNode(MxMeshPtr pm);

  /// associate model with mesh and element number
  void bindElement(MxMeshPtr pm);

  /// change display item
  void changeItem(uint k) {iitem = k;}

  /// overloaded table model method
  int columnCount(const QModelIndex & parent = QModelIndex()) const {
    return (parent.isValid() ? 0 : 3);
  }

  /// overloaded table model method
  int rowCount(const QModelIndex & parent = QModelIndex()) const {
    return (parent.isValid() ? 0 : fieldMap.size());
  }

  /// generate data for display
  QVariant data(const QModelIndex & index, int role = Qt::DisplayRole) const;

private:

  /// mesh from which to extract data
  MxMeshPtr pmesh;

  /// item (node/element) index for which to display field data
  uint iitem;

  /// mapping from table row to field index
  Indices fieldMap;
};

#endif // FIELDDATAMODEL_H
