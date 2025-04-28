//
// project:      scope
// file:         elementinfobox.cpp
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Display element data

#include "elementinfobox.h"
#include "ui_elementinfobox.h"
#include "fielddatamodel.h"
#include <genua/mxmesh.h>
#include <QDebug>

ElementInfoBox::ElementInfoBox(QWidget *parent) :
    QDialog(parent, Qt::Tool), ui(new Ui::ElementInfoBox)
{
  ui->setupUi(this);
  dataModel = new FieldDataModel(this);

#ifdef Q_OS_MACX
  ui->gbFields->setFlat(true);
  ui->gbHeader->setFlat(true);
  ui->gbNodes->setFlat(true);
#endif
}

ElementInfoBox::~ElementInfoBox()
{
  delete dataModel;
  delete ui;
}

void ElementInfoBox::assign(MxMeshPtr mx)
{
  pmx = mx;
  dataModel->bindElement(pmx);
  ui->tvFields->setModel(dataModel);

  // if this mesh does not own any nodal data fields,
  // hide the table view entirely
  if (dataModel->rowCount(QModelIndex()) == 0)
    ui->gbFields->hide();
  else
    ui->gbFields->show();
}

void ElementInfoBox::showInfo(int gix)
{
  if (not pmx)
    return;

  clearFields();

  const MxMesh & mx(*pmx);
  uint nv, isec;
  const uint *vi = mx.globalElement(gix, nv, isec);

  ui->lbIndex->setText( QString::number(gix) );
  if (isec != NotFound) {
    const MxMeshSection & sec( mx.section(isec) );
    ui->lbType->setText( QString::fromStdString( str(sec.elementType()) ) );
    ui->lbSection->setText( QString::fromStdString(sec.name()) );
  } else {
    ui->lbType->setText(tr("n/a"));
    ui->lbSection->setText(tr("n/a"));
  }

  if (vi != 0) {
    ui->gbNodes->show();
    for (uint i=0; i<nv; ++i) {
      QLabel *pindex = new QLabel(ui->gbNodes);
      connect(pindex, SIGNAL(linkActivated(QString)),
              this, SLOT(requestNodeInfo(QString)));
      pindex->setTextInteractionFlags( Qt::TextBrowserInteraction );
      pindex->setText(tr("<a href=%1>%1</a> at ").arg(vi[i]));
      ui->loNodes->addWidget(pindex, i, 0);

      const Vct3 & p( mx.node(vi[i]) );
      QLabel *ploc = new QLabel(ui->gbNodes);
      ploc->setAlignment(Qt::AlignRight);
      ploc->setTextInteractionFlags( Qt::TextBrowserInteraction );
      ploc->setText(tr("(%1, %2, %3)").arg(p[0]).arg(p[1]).arg(p[2]));
      ui->loNodes->addWidget(ploc, i, 1);
    }
  } else {
    ui->gbNodes->hide();
  }

  dataModel->changeItem(gix);
  ui->tvFields->resizeColumnsToContents();
  adjustSize();
}

void ElementInfoBox::clearFields()
{
  ui->lbIndex->setText(tr("n/a"));
  ui->lbType->setText(tr("n/a"));
  ui->lbSection->setText(tr("n/a"));

  int nr, nc;
  nr = ui->loNodes->rowCount();
  nc = ui->loNodes->columnCount();
  for (int j=0; j<nc; ++j) {
    for (int i=0; i<nr; ++i) {
      QLayoutItem *item = ui->loNodes->itemAtPosition(i,j);
      if (item != 0) {
        ui->loNodes->removeItem( item );
        delete item->widget();
      }
    }
  }
}

void ElementInfoBox::requestNodeInfo(const QString & s)
{
  if (pmx == 0)
    return;

  int idx = s.toInt();
  if (uint(idx) < pmx->nnodes())
    emit requestNodeInfo( int(idx) );
}

void ElementInfoBox::changeEvent(QEvent *e)
{
  QDialog::changeEvent(e);
  switch (e->type()) {
  case QEvent::LanguageChange:
    ui->retranslateUi(this);
    break;
  default:
    break;
  }
}
