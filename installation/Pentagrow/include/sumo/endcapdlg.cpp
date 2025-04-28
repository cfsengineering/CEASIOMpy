//
// project:      dwfs core
// file:         endcapdlg.cpp
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Set end cap properties

#include "endcapdlg.h"
#include "ui_endcapdlg.h"
#include "wingskeleton.h"
#include <surf/endcap.h>

EndCapDlg::EndCapDlg(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::EndCapDlg)
{
  ui->setupUi(this);

  ui->cbFrontType->addItem(tr("Polar"));  // RingCap
  ui->cbFrontType->addItem(tr("Grid"));   // LongCap

  ui->cbRearType->addItem(tr("Polar"));  // RingCap
  ui->cbRearType->addItem(tr("Grid"));   // LongCap

  // change cap type when combo boc modified
  connect(ui->cbFrontType, SIGNAL(currentIndexChanged(int)),
          this, SLOT(frontTypeChanged(int)) );
  connect(ui->cbRearType, SIGNAL(currentIndexChanged(int)),
          this, SLOT(rearTypeChanged(int)) );

  // update height values when focues leaves spin boxes
  connect(ui->sbFrontHeight, SIGNAL(editingFinished()),
          this, SLOT(frontHeightChanged()));
  connect(ui->sbRearHeight, SIGNAL(editingFinished()),
          this, SLOT(rearHeightChanged()));
}

EndCapDlg::~EndCapDlg()
{
  delete ui;
}

void EndCapDlg::attach(ComponentPtr cp)
{
  cmp = cp;
  ui->lbComponent->setText(QString::fromStdString(cmp->name()));

  // access caps and fill form
  const EndCap & fcap( cmp->endCap( AsyComponent::CapVLo ) );
  const EndCap & rcap( cmp->endCap( AsyComponent::CapVHi ) );

  ui->sbFrontHeight->setValue( fcap.height() );
  if (fcap.capShape() == EndCap::RingCap)
    ui->cbFrontType->setCurrentIndex(0);
  else if (fcap.capShape() == EndCap::LongCap)
    ui->cbFrontType->setCurrentIndex(1);

  ui->sbRearHeight->setValue( rcap.height() );
  if (rcap.capShape() == EndCap::RingCap)
    ui->cbRearType->setCurrentIndex(0);
  else if (rcap.capShape() == EndCap::LongCap)
    ui->cbRearType->setCurrentIndex(1);

  if ( boost::dynamic_pointer_cast<WingSkeleton>(cmp) ) {
    ui->gbFront->setTitle(tr("Right tip cap"));
    ui->gbRear->setTitle(tr("Left tip cap"));
  }
}

void EndCapDlg::frontTypeChanged(int idx)
{
  if (not cmp)
    return;

  EndCap & fcap( cmp->endCap( AsyComponent::CapVLo ) );
  if (idx == 0)
    fcap.capShape( EndCap::RingCap );
  else if (idx == 1)
    fcap.capShape( EndCap::LongCap );
}

void EndCapDlg::rearTypeChanged(int idx)
{
  if (not cmp)
    return;

  EndCap & rcap( cmp->endCap( AsyComponent::CapVHi ) );
  if (idx == 0)
    rcap.capShape( EndCap::RingCap );
  else if (idx == 1)
    rcap.capShape( EndCap::LongCap );
}

void EndCapDlg::frontHeightChanged()
{
  if (not cmp)
    return;

  EndCap & fcap( cmp->endCap( AsyComponent::CapVLo ) );
  fcap.height( ui->sbFrontHeight->value() );
}

void EndCapDlg::rearHeightChanged()
{
  if (not cmp)
    return;

  EndCap & rcap( cmp->endCap( AsyComponent::CapVHi ) );
  rcap.height( ui->sbRearHeight->value() );
}

void EndCapDlg::changeEvent(QEvent *e)
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
