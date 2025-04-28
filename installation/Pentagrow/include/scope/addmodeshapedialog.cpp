//
// project:      scope
// file:         addmodeshapedialog.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Add generated rigid-body modeshape

#include "addmodeshapedialog.h"
#include "ui_addmodeshapedialog.h"
#include "meshplotter.h"

AddModeshapeDialog::AddModeshapeDialog(QWidget *parent) :
  QDialog(parent, Qt::Tool), ui(new Ui::AddModeshapeDialog)
{
  ui->setupUi(this);

#ifdef Q_OS_MACX
  ui->gbModeSelection->setFlat(true);
  ui->gbCenterOfRotation->setFlat(true);
  ui->gbMassProperties->setFlat(true);
#endif

  adjustSize();
  connect(this, SIGNAL(accepted()), this, SLOT(addModes()));
  connect(ui->cbStoreMassProperties, SIGNAL(toggled(bool)),
          this, SLOT(showMassBox(bool)) );
}

AddModeshapeDialog::~AddModeshapeDialog()
{
  delete ui;
}

void AddModeshapeDialog::showMassBox(bool flag)
{
  ui->gbMassProperties->setVisible(flag);
  adjustSize();
}

void AddModeshapeDialog::assign(MeshPlotterPtr plt)
{
  plotter = plt;

  const Vct3 & cg( plotter->rotCenter() );
  ui->sbCgX->setValue( cg[0] );
  ui->sbCgY->setValue( cg[1] );
  ui->sbCgZ->setValue( cg[2] );
}

void AddModeshapeDialog::addModes()
{
  if (not plotter)
    return;

  MxMeshPtr pmx = plotter->pmesh();
  if (not pmx)
    return;

  Vct3 rotctr;
  rotctr[0] = ui->sbCgX->value();
  rotctr[1] = ui->sbCgY->value();
  rotctr[2] = ui->sbCgZ->value();
  plotter->rotCenter(rotctr);

  Real mass = ui->sbMass->value();
  Real Ixx = ui->sbIxx->value();
  Real Iyy = ui->sbIyy->value();
  Real Izz = ui->sbIzz->value();
  Real Ixz = ui->sbIxz->value();

  if (ui->cbTransX->isChecked())
    pmx->appendRigidBodyMode(0, rotctr, mass);
  if (ui->cbTransY->isChecked())
    pmx->appendRigidBodyMode(1, rotctr, mass);
  if (ui->cbTransZ->isChecked())
    pmx->appendRigidBodyMode(2, rotctr, mass);

  if (ui->cbRotX->isChecked())
    pmx->appendRigidBodyMode(3, rotctr, Ixx);
  if (ui->cbRotY->isChecked())
    pmx->appendRigidBodyMode(4, rotctr, Iyy);
  if (ui->cbRotZ->isChecked())
    pmx->appendRigidBodyMode(5, rotctr, Izz);

  // annotate root element with mass properties
  if (ui->cbStoreMassProperties->isChecked()) {
    XmlElement xm("MassProperties");
    xm["mass"] = str(mass);
    xm["Ixx"] = str(Ixx);
    xm["Iyy"] = str(Iyy);
    xm["Izz"] = str(Izz);
    xm["Ixz"] = str(Ixz);
    pmx->annotate(xm);
  }

  emit addedModeshapes();
}

void AddModeshapeDialog::changeEvent(QEvent *e)
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
