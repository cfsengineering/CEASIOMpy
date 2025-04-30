//
// project:      scope
// file:         fielddatamodel.cpp
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Model class for element/node data display

#include "fielddatamodel.h"
#include "util.h"
#include <genua/mxmesh.h>

#include <iostream>
using namespace std;

FieldDataModel::FieldDataModel(QObject *parent) :
    QAbstractTableModel(parent), iitem(NotFound) { }

void FieldDataModel::bindNode(MxMeshPtr pm)
{
  pmesh = pm;
  iitem = 0;
  fieldMap.clear();

  const int nf = pmesh->nfields();
  for (int i=0; i<nf; ++i)
    if (pmesh->field(i).nodal())
      fieldMap.push_back(i);
}

void FieldDataModel::bindElement(MxMeshPtr pm)
{
  pmesh = pm;
  iitem = NotFound;
  fieldMap.clear();

  const int nf = pmesh->nfields();
  for (int i=0; i<nf; ++i)
    if (not pmesh->field(i).nodal())
      fieldMap.push_back(i);
}

QVariant FieldDataModel::data(const QModelIndex & index, int role) const
{
  const int row = index.row();
  const int col = index.column();

  if (role == Qt::DisplayRole) {

    if (pmesh != 0 and iitem != NotFound and uint(row) < fieldMap.size()) {
      const MxMeshField & field( pmesh->field(fieldMap[row]) );
      if (col == 0) {
        return QVariant( QString("[%1]").arg(fieldMap[row]) );
      } else if (col == 1) {
        return QVariant( qstr( field.name() ) );
      } else if (col == 2) {
        QString txt;
        int fdim = field.ndimension();
        if (field.realField()) {
          if (fdim == 1) {
            double v;
            field.scalar(iitem, v);
            txt = QString::number(v, 'g', 4);
          } else if (fdim == 2) {
            Vct2 v;
            field.value(iitem, v);
            txt = QString("(%1, %2)").arg(v[0], 0, 'g', 4).arg(v[1], 0, 'g', 4);
          } else if (fdim == 3) {
            Vct3 v;
            field.value(iitem, v);
            txt = QString("(%1, %2, %3)")
                  .arg(v[0], 0, 'g', 4).arg(v[1], 0, 'g', 4).arg(v[2], 0, 'g', 4);
          } else if (fdim == 6) {
            Vct6 v;
            field.value(iitem, v);
            txt = QString("(%1, %2, %3, %4, %5, %6)")
                  .arg(v[0], 0, 'g', 4).arg(v[1], 0, 'g', 4).arg(v[2], 0, 'g', 4)
                  .arg(v[3], 0, 'g', 4).arg(v[4], 0, 'g', 4).arg(v[5], 0, 'g', 4);
          }
        } else {
          int v;
          field.scalar(iitem, v);
          txt = QString::number(v);
        }
        return QVariant(txt);
      }
    }
  } else if (role == Qt::TextAlignmentRole) {
    if (col == 0)
      return QVariant( Qt::AlignLeft );
    else
      return QVariant( Qt::AlignRight );
  }

  return QVariant();
}
