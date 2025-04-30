//
// project:      scope
// file:         nodeinfobox.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Display information about a node

#include "nodeinfobox.h"
#include "ui_nodeinfobox.h"
#include "fielddatamodel.h"
#include <genua/mxmesh.h>

#include <QDebug>
#include <QInputDialog>

using namespace std;

NodeInfoBox::NodeInfoBox(QWidget *parent) :
    QDialog(parent, Qt::Tool), ui(new Ui::NodeInfoBox)
{
  ui->setupUi(this);
  dataModel = new FieldDataModel(this);

#ifdef Q_OS_MACX
  ui->gbFields->setFlat(true);
  ui->gbHeader->setFlat(true);
#endif

  connect(ui->pbLookup, SIGNAL(clicked()), this, SLOT(lookup()));
}

NodeInfoBox::~NodeInfoBox()
{
  delete dataModel;
  delete ui;
}

void NodeInfoBox::assign(MxMeshPtr mx)
{
  pmx = mx;
  dataModel->bindNode(pmx);
  ui->tvFields->setModel( dataModel );
  if (pmx == nullptr)
    return;

  // extract NASTRAN GIDs if present
  gids.clear();
  XmlElement::const_iterator itr, last = pmx->noteEnd();
  for (itr = pmx->noteBegin(); itr != last; ++itr) {
    const string & s = itr->name();
    if (s == "NastranGID") {
      gids.resize( Int(itr->attribute("count")) );
      itr->fetch(gids.size(), &gids[0]);
    }
  }

  // if this mesh does not own any nodal data fields,
  // hide the table view entirely
  if (dataModel->rowCount(QModelIndex()) == 0)
    ui->gbFields->hide();
  else
    ui->gbFields->show();

  adjustSize();
}

void NodeInfoBox::showInfo(int idx)
{
  if (pmx == 0)
    return;

  const MxMesh & mx(*pmx);
  const Vct3 & p( mx.node(idx) );
  ui->lbIndex->setText(QString::number(idx));
  ui->lbLocation->setText( tr("(%1, %2, %3)")
                           .arg(p[0], 0, 'e', 7)
                           .arg(p[1], 0, 'e', 7)
                           .arg(p[2], 0, 'e', 7) );

  if (gids.size() == pmx->nnodes())
    ui->lbGID->setText( tr("%1").arg(gids[idx]) );
  else
    ui->lbGID->setText( tr("n/a") );

  // update table view
  dataModel->changeItem(idx);

  // adapt display
  ui->tvFields->setVisible(false);
  ui->tvFields->resizeColumnsToContents();
  ui->tvFields->resizeRowsToContents();
  ui->tvFields->setVisible(true);
}

void NodeInfoBox::lookup()
{
  if (pmx == 0)
    return;

  int idx = ui->lbIndex->text().toInt();
  int eix = QInputDialog::getInt(this, tr("Lookup node info by index"),
                                       tr("Enter node index (0-based):"), idx,
                                       0, pmx->nnodes());
  if (eix > 0 and size_t(eix) < pmx->nnodes())
    showInfo(eix);
}

void NodeInfoBox::changeEvent(QEvent *e)
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
